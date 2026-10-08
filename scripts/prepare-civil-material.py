"""Archive and prepare official civil-service papers for the private build."""
import concurrent.futures, importlib.util, json, os, re, sys
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('archive',ROOT/'scripts/prepare-github-material.py')
ipa=importlib.util.module_from_spec(spec);spec.loader.exec_module(ipa)
spec=importlib.util.spec_from_file_location('fetcher',ROOT/'scripts/fetch-github-material.py')
fetcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(fetcher)
SRC=ipa.SRC;OUT=ipa.OUT;fitz=ipa.fitz
BASE='https://www.jinji.go.jp'
EXAMS={'総合職試験(院卒者試験)':'civil-general-grad','総合職試験(大卒程度試験)':'civil-general-univ',
       '総合職試験(大卒程度試験)教養区分':'civil-general-univ','一般職試験(大卒程度試験)':'civil-regular-univ',
       '一般職試験(高卒者試験)':'civil-regular-high','国税専門官採用試験':'tax-specialist',
       '財務専門官採用試験':'finance-specialist','労働基準監督官採用試験':'labor-inspector'}
EXAMS.update(dict(zip([
    '皇宮護衛官採用試験(大卒程度試験)','刑務官採用試験(大卒程度試験)','法務省専門職員(人間科学)採用試験',
    '食品衛生監視員採用試験','航空管制官採用試験','海上保安官採用試験','一般職試験(社会人試験(係員級))',
    '皇宮護衛官採用試験(高卒程度試験)','刑務官採用試験(高卒程度試験)','入国警備官採用試験','税務職員採用試験',
    '航空保安大学校学生採用試験','海上保安大学校学生採用試験','海上保安学校学生採用試験','気象大学校学生採用試験','経験者採用試験'],[
    'imperial-guard-univ','prison-officer-univ','justice-human-science','food-sanitation-inspector','air-traffic-controller',
    'coast-guard-officer','civil-regular-career','imperial-guard-high','prison-officer-high','immigration-guard','tax-officer',
    'aviation-security-student','coast-guard-academy','coast-guard-school','meteorological-college','civil-experienced'])))
EXAMS.update(dict(zip([
    '皇宮護衛官採用試験(大卒程度試験)','刑務官採用試験(大卒程度試験)','法務省専門職員(人間科学)採用試験',
    '食品衛生監視員採用試験','航空管制官採用試験','海上保安官採用試験','一般職試験(社会人試験(係員級))',
    '皇宮護衛官採用試験(高卒程度試験)','刑務官採用試験(高卒程度試験)','入国警備官採用試験','税務職員採用試験',
    '航空保安大学校学生採用試験','海上保安大学校学生採用試験','海上保安学校学生採用試験','気象大学校学生採用試験','経験者採用試験'],[
    'imperial-guard-univ','prison-officer-univ','justice-human-science','food-sanitation-inspector','air-traffic-controller',
    'coast-guard-officer','civil-regular-career','imperial-guard-high','prison-officer-high','immigration-guard','tax-officer',
    'aviation-security-student','coast-guard-academy','coast-guard-school','meteorological-college','civil-experienced'])))
def compact(value):return re.sub(r'\s+','',ipa.norm(value))
def reviewed_key(doc):
    file=SRC/'civil-reviewed-keys.json'
    reviewed=json.loads(file.read_bytes()) if file.exists() else {}
    record=reviewed.get(Path(doc.name).name)
    if not record:return None
    assert record['sha256']==ipa.sha(Path(doc.name).read_bytes()) and record['review']=='agent-visual-table-check'
    return {int(n):a for n,a in record['keys'].items()}

def page_words(doc,pn):
    page=doc[pn]
    if page.get_text().strip():return page.get_text('words')
    cache=SRC/'ocr'/f'{Path(doc.name).stem}-civil-{pn}.json'
    if cache.exists():return json.loads(cache.read_bytes())['words']
    tp=page.get_textpage_ocr(language='jpn+eng',dpi=150,full=True,tessdata=str(ROOT/'build/tessdata'))
    data={'words':page.get_text('words',textpage=tp),'text':page.get_text(textpage=tp)}
    cache.write_bytes(ipa.encode(data))
    return data['words']

def page_text(doc,pn):
    text=doc[pn].get_text()
    if text.strip():return text
    page_words(doc,pn)
    return json.loads((SRC/'ocr'/f'{Path(doc.name).stem}-civil-{pn}.json').read_bytes())['text']

def official_keys(doc):
    """Read native answer table cells, rejecting duplicated or ambiguous numbers."""
    page=doc[-1];text=compact(page.get_text())
    if '正答番号表' not in text:
        keys=reviewed_key(doc)
        assert keys,'Native official answer table unavailable; scanned table not visually reviewed'
        return keys
    words=page.get_text('words');headers=sorted((w for w in words if compact(w[4])=='No'),key=lambda w:w[0])
    assert headers,'No official table headers'
    keys={};ambiguous=set()
    for i,header in enumerate(headers):
        right=headers[i+1][0] if i+1<len(headers) else page.rect.width
        labels=[w for w in words if abs((w[0]+w[2]-header[0]-header[2])/2)<12 and w[1]>header[3] and re.fullmatch(r'\d+',compact(w[4]))]
        for label in labels:
            cells=[w for w in words if label[2]<w[0]<right and abs((w[1]+w[3]-label[1]-label[3])/2)<3 and re.fullmatch('[1-5]',compact(w[4]))]
            n=int(compact(label[4]))
            if n in keys or len(cells)!=1:ambiguous.add(n);continue
            keys[n]=int(compact(cells[0][4]))-1
    for n in ambiguous:keys.pop(n,None)
    assert keys,'No unambiguous official answers'
    return keys

def question_starts(doc):
    starts=[]
    for pn,page in enumerate(doc):
        if pn==len(doc)-1:continue
        words=page_words(doc,pn)
        for word in words:
            if word[0]>110 or not re.search(r'[【\[(I]No[.,、]?',compact(word[4])):continue
            row=sorted((w for w in words if abs((w[1]+w[3]-word[1]-word[3])/2)<4 and word[0]-1<=w[0]<180),key=lambda w:w[0])
            value=compact(''.join(w[4] for w in row))
            m=re.match(r'[【\[(I]No[.,、]?(\d+)[】\])]',value)
            if m:starts.append((int(m[1]),pn,word[1]))
    file=SRC/'civil-reviewed-keys.json'
    record=json.loads(file.read_bytes()).get(Path(doc.name).name) if file.exists() else None
    if record and record.get('headings'):
        assert reviewed_key(doc),'Heading corrections need the reviewed source hash'
        for heading in record['headings']:
            starts=[s for s in starts if s[1]!=heading['page']]+[(heading['number'],heading['page'],heading['y'])]
    starts.sort(key=lambda s:(s[1],s[2]))
    assert starts and len({n for n,p,y in starts})==len(starts),'Missing or duplicated question headings'
    assert [n for n,p,y in starts]==sorted(n for n,p,y in starts),'Question order'
    return starts

def prepare(task):
    stem=Path(task['sourceFile']).stem
    result={**task,'provider':'JINJI','file':stem+'.json','answerFile':task['sourceFile'],'term':'公開過去問','subject':task.get('sourceLabel','筆記'),'sources':[task.get('source',{})]}
    try:
        assert task['status']=='downloaded','Source download failed'
        exam=EXAMS.get(compact(task['examName']))
        assert exam,'Exam definition not mapped yet'
        result['examId']=exam
        doc=fitz.open(SRC/task['sourceFile']);keys=official_keys(doc)
        # ponytail: scanned keys require a hash-pinned visual review before OCR is used for headings.
        assert reviewed_key(doc) or all(p.get_text().strip() for p in doc[:-1]),'Scanned question pages need reviewed headings'
        starts=question_starts(doc)
        assert set(keys).issubset({n for n,p,y in starts}),'Some officially answered questions have no reliable heading'
        texts=[compact(page_text(doc,pn)) for pn in range(len(doc)-1)]+[''];shared=[]
        for pn,text in enumerate(texts[:-1]):
            for m in re.finditer(r'No[.]?(\d+)[~〜～―－-](?:No[.]?)?(\d+)',text):
                context=text[max(0,m.start()-140):m.end()+140]
                if re.search(r'次の(?:文章|文|資料|図|表|会話)|以下の(?:文章|資料)|共通(?:本文|資料)',context):shared.append((int(m[1]),int(m[2]),pn))
        rows=[];evidence=[];excluded=[];cache={}
        def picture(pn):
            if pn not in cache:
                page=doc[pn];file=stem+f'-p{pn+1:03}.png';path=OUT/'assets'/file
                if not path.exists():page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(path)
                cache[pn]=({'src':'assets/github-material/'+file,'alt':f'人事院公式問題 {pn+1}ページ'},
                           {'file':file,'page':pn,'rect':list(page.rect),'sha256':ipa.sha(path.read_bytes())})
            return cache[pn]
        for i,(n,pn,y) in enumerate(starts):
            end=starts[i+1][1] if i+1<len(starts) else len(doc)-2
            # Full pages keep diagrams, continuation text and shared case passages intact.
            pages=set(range(pn,end+1))
            for first,last,sp in shared:
                if first<=n<=last and sp<=pn:pages.update(range(sp,pn+1))
            segment=''.join(texts[p] for p in sorted(pages))
            reason=('Missing/ambiguous official key' if n not in keys else 'Omitted copyrighted passage' if '掲載できません' in segment or '掲載していません' in segment else 'Shared context exceeds 30-page image limit' if len(pages)>30 else None)
            if reason:
                excluded.append({'number':n,'reason':reason});continue
            images,records=zip(*(picture(p) for p in sorted(pages)))
            title=f'{task["year"]}年度 {task["examName"]} {result["subject"]} No.{n}'
            q={'id':stem+f'-q{n:03}','examId':exam,'year':task['year'],'term':result['term'],'subject':result['subject'],
               'type':'single','category':'過去問','topic':title,'prompt':title+'\n原本画像の該当番号の問題を解答してください。',
               'options':['1','2','3','4','5'],'answer':keys[n],'images':list(images),
               'explanation':f'公式正答：{keys[n]+1}。理由解説は未収録です。実施当時の法令・制度を前提とします。',
               'explanationSource':'人事院公式正答番号表（理由解説なし）','sourceUrl':task['url'],
               'source':'出典：人事院 '+title+'。原本PDFをページ画像へ加工（PDL1.0）。人事院によるアプリではありません。'}
            rows.append(q);evidence.append({'id':q['id'],'number':n,'answer':keys[n],'images':list(records)})
        assert rows,'No complete questions'
        raw=ipa.encode(rows);(OUT/result['file']).write_bytes(raw)
        return {**result,'status':'prepared','count':len(rows),'sha256':ipa.sha(raw),'questions':evidence,'excluded':excluded}
    except Exception as e:return {**result,'status':'pending-review','reason':str(e)}

def prepare_all():
    discovery=json.loads((SRC/'civil-discovery.json').read_bytes());results=[]
    reviewed_file=SRC/'civil-reviewed-keys.json'
    reviewed=json.loads(reviewed_file.read_bytes()) if reviewed_file.exists() else {}
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        for i,result in enumerate(pool.map(prepare,discovery['tasks'])):
            results.append(result)
            if (i+1)%20==0:print('Prepared civil papers',i+1,'questions',sum(r.get('count',0) for r in results),flush=True)
            if result['sourceFile'] in reviewed:
                print(result['sourceFile'],result['status'],result.get('count',result.get('reason')),flush=True)
    (OUT/'civil-report.json').write_bytes(ipa.encode({'packs':results}))
    print('Civil questions',sum(r.get('count',0) for r in results),flush=True)
def links(text,url):
    return [(urljoin(url,u.replace('&amp;','&')),ipa.norm(re.sub('<[^>]+>','',label)).strip()) for u,label in re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',text,re.S)]
def archive():
    top=fetcher.fetch(BASE+'/saiyo/siken/mondairei/mondairei_top.html','jinji-index.html')
    terms=fetcher.fetch(BASE+'/shinsei/notice.html','jinji-terms.html')
    pages=[];tasks={}
    for url,label in links((SRC/top['file']).read_text(encoding='utf-8'),top['url']):
        if not re.search(r'/mondairei_\d+\.html$',url):continue
        source=fetcher.fetch(url,'jinji-'+Path(urlparse(url).path).name);pages.append({**source,'label':label})
        text=(SRC/source['file']).read_text(encoding='utf-8');year=None;labels=dict(links(text,url))
        for token in re.split(r'(<[^>]+>)',text):
            m=re.search(r'(20\d\d)年度',ipa.norm(token))
            if m:year=m[1]
            if not year:continue
            m=re.search(r'href=["\']([^"\']+\.pdf)["\']',token)
            if m:
                pdf=urljoin(url,m[1]);name='jinji-'+Path(urlparse(pdf).path).name
                tasks.setdefault(pdf,{'url':pdf,'sourceFile':name,'year':year,'examName':label,'sourceLabel':labels.get(pdf,'筆記'),'indexUrl':url})
    def download(task):
        try:return {**task,'source':fetcher.fetch(task['url'],task['sourceFile']),'status':'downloaded'}
        except Exception as e:return {**task,'status':'pending-download','reason':str(e)}
    results=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,result in enumerate(pool.map(download,tasks.values())):
            results.append(result)
            if (i+1)%20==0:print('Archived civil papers',i+1,'/',len(tasks),flush=True)
    (SRC/'civil-discovery.json').write_bytes(ipa.encode({'pages':pages,'terms':terms,'tasks':results}))
    print('Civil papers',len(results),flush=True)

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    os.environ['OMP_THREAD_LIMIT']='1'
    prepare_all() if '--prepare' in sys.argv else archive()
