"""Extend the local Denken archive; keep source PDFs and auditable page mappings."""
import concurrent.futures, json, re, sys
from pathlib import Path
from urllib.parse import urljoin, urlparse
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('electricity',ROOT/'scripts/prepare-electricity-material.py')
e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
SRC,OUT,ipa,fitz=e.SRC,e.OUT,e.ipa,e.fitz

def discover():
    baseline=SRC/'denken-baseline.json'
    if not baseline.exists():
        manifest=json.loads((ROOT/'build/private/manifest.json').read_bytes())
        rows=[q for p in manifest['packs'] if p['examId'].startswith('denken') for q in json.loads((ROOT/'build/private/web'/p['url']).read_bytes())]
        baseline.write_bytes(ipa.encode(dict(manifest=manifest,questions=rows)))
    prior=json.loads(baseline.read_bytes())['questions']
    paths={urlparse(q['sourceUrl']).path for q in prior if q.get('sourceUrl')}
    tasks=[]
    for code,category in [('denken1','first'),('denken2','second'),('denken3','third')]:
        base=f'https://www.shiken.or.jp/chief/{category}/qa/'
        pages=[(SRC/e.fetch.fetch(base,'denken-expand-'+code+'.html')['file']).read_text(encoding='utf-8')]
        for path in sorted(set(re.findall(r'href="([^"]*index_\d+\.html)"',pages[0]))):
            pages.append((SRC/e.fetch.fetch(urljoin(base,path),'denken-expand-'+code+'-'+Path(path).name)['file']).read_text(encoding='utf-8'))
        links=[(urljoin(base,u),e.clean(t)) for u,t in re.findall(r'<a[^>]*href="([^"]+\.pdf)"[^>]*>(.*?)</a>',''.join(pages),re.S)]
        for url,label in links:
            m=re.search(r'(令和|平成)(元|\d+)年度',label)
            subject=next((v for v in ['電力・管理','機械・制御','理論','電力','機械','法規'] if v+'科目' in label),None)
            if not m or not subject or urlparse(url).path in paths:continue
            year=str((2018 if m[1]=='令和' else 1988)+(1 if m[2]=='元' else int(m[2])))
            term=('下期' if '下期' in label else '上期' if '上期' in label else '筆記試験') if code=='denken3' else '二次試験' if '二次試験' in label else '一次試験'
            identity=label.split(subject)[0]
            answers=[u for u,t in links if t==identity and u!=url]
            if not answers:
                answers=[u for u,t in links if t==identity.removesuffix('科目') and u!=url]
            if len(set(answers))!=1:
                print('Unpaired',label,answers,flush=True);continue
            tasks.append(dict(examId=code,year=year,term=term,subject=subject,url=url,answerUrl=answers[0],kind='secondary' if term=='二次試験' else 'third' if code=='denken3' else 'denken'))
    # Reuse previously downloaded originals rather than fetch the same URLs again.
    sources={}
    for file in [SRC/'electricity-discovery.json',SRC/'nonit-discovery.json']:
        data=json.loads(file.read_bytes())
        for t in data.get('tasks',[]):
            for source in t.get('sources',[]):
                if (SRC/source['file']).exists():sources[source['url']]=source
    def download(t):
        stem='denken-'+t['examId']+'-'+t['year']+'-'+ipa.sha(t['url'].encode())[:10]
        try:
            q=sources.get(t['url']) or e.fetch.fetch(t['url'],stem+'-q.pdf')
            a=sources.get(t['answerUrl']) or e.fetch.fetch(t['answerUrl'],stem+'-a.pdf')
            return {**t,'sources':[q,a],'sourceFile':q['file'],'answerFile':a['file'],'file':stem+'.json','provider':'ECEE','status':'downloaded','localOnly':True}
        except Exception as error:return {**t,'status':'download-failed','reason':str(error)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        result=[]
        for t in pool.map(download,tasks):
            result.append(t);print(len(result),len(tasks),t['examId'],t['year'],t['term'],t['subject'],t['status'],flush=True)
    (SRC/'denken-discovery.json').write_bytes(ipa.encode(dict(tasks=result)))

def headings(doc, expected, secondary=False):
    """Require a complete number sequence; never infer a missing OCR numeral."""
    for ocr in [False,True]:
        starts=[]
        for pn,page in enumerate(doc):
            if pn<(2 if secondary else 3):continue
            lines=e.ipa.lines(e.ipa.layout(doc,pn,True)[0]) if ocr else []
            items=[(ipa.norm(''.join(s['text'] for s in l['spans'])),l['bbox']) for l in lines] if ocr else e.line_items(page)
            for value,box in items:
                m=re.match(r'^[問間]\s*(\d+)\s+(.+)',value)
                if m and box[0]<100 and 40<box[1]<page.rect.height-40 and not re.match(r'(?:及び|および|の解答|から|~|～)',m[2]):
                    starts.append((int(m[1]),pn,box[1]))
        if [n for n,p,y in starts]==list(range(1,expected+1)):return starts
    return []

def secondary_answers(doc,subject):
    starts=[];current=None
    for pn,page in enumerate(doc):
        for value,box in sorted(e.line_items(page),key=lambda item:(item[1][1],item[1][0])):
            value=re.sub(r'\s+','',ipa.norm(value))
            m=re.search(r'[<〈＜](電力・管理|機械・制御)(?:科目)?[>〉＞]',value)
            if m:current=m[1]
            m=re.fullmatch(r'[〔\[]?問(\d+)の標準解答[〕\]]?',value)
            if m:starts.append((current,int(m[1]),pn,box[1]))
    selected=[(n,p,y) for s,n,p,y in starts if s==subject]
    expected=6 if subject=='電力・管理' else 4
    assert [n for n,p,y in selected]==list(range(1,expected+1)),('Secondary answer headings',subject,starts)
    result={}
    for n,p,y in selected:
        i=starts.index((subject,n,p,y));end=starts[i+1][2] if i+1<len(starts) else len(doc)-1
        if i+1<len(starts) and starts[i+1][3]<90 and end>p:end-=1
        result[str(n)]=list(range(p,end+1))
    return result

def primary_image_keys(doc,task):
    """Retain an image answer when the PDF text layer cannot express a cell."""
    subject=['理論','電力','機械','法規'].index(task['subject']);keys={};solution={}
    if len(doc)==4:
        page=doc[subject]
        assert '<'+task['subject']+'>' in re.sub(r'\s+','',ipa.norm(page.get_text()))
        numbers=sorted({int(m[1]) for w in page.get_text('words') if (m:=re.fullmatch(r'問(\d+)',ipa.norm(w[4])))})
        assert numbers==list(range(1,len(numbers)+1))
        for n in numbers:keys[str(n)]={'':'公式解答画像の問'+str(n)+'を参照して自己採点してください。'};solution[str(n)]=[subject]
    elif len(doc) in (1,2) and any(len({round(b[1]/20) for v,b in e.line_items(p) if re.fullmatch(r'<(?:理論|電力|機械|法規)>',re.sub(r'\s+','',v))})>1 for p in doc):
        for pn,page in enumerate(doc):
            headings=[(re.sub(r'\s+','',v),b) for v,b in e.line_items(page) if re.fullmatch(r'<(?:理論|電力|機械|法規)>',re.sub(r'\s+','',v))]
            h=next((b for v,b in headings if v=='<'+task['subject']+'>'),None)
            if not h:continue
            bottom=min([b[1] for v,b in headings if b[1]>h[1]+10]+[page.rect.height])
            labels=sorted((w for w in page.get_text('words') if h[1]<w[1]<bottom and re.fullmatch(r'\(\d+\)',e.clean(w[4]))),key=lambda w:(round(w[1]/3),w[0]));group=0
            for w in labels:
                n=int(re.search(r'\d+',w[4])[0])
                if n==1:group+=1
                keys.setdefault(str(group),{})[str(n)]=f'公式解答画像の問{group}({n})を参照して自己採点してください。';solution[str(group)]=[pn]
    else:
        assert len(doc)==1
        words=doc[0].get_text('words');anchors=sorted(set(round(w[0],1) for w in words if e.clean(w[4])=='(1)'))
        assert len(anchors)==4
        left=anchors[subject]-3;right=anchors[subject+1]-3 if subject<3 else doc[0].rect.width
        labels=sorted((w for w in words if left<w[0]<right and re.fullmatch(r'\(\d+\)',e.clean(w[4]))),key=lambda w:w[1]);group=0
        for w in labels:
            n=int(re.search(r'\d+',w[4])[0])
            if n==1:group+=1
            keys.setdefault(str(group),{})[str(n)]=f'公式解答画像の問{group}({n})を参照して自己採点してください。';solution[str(group)]=[0]
        for values in keys.values():assert list(map(int,values))==list(range(1,len(values)+1))
    assert keys
    return keys,solution

def prepare(task):
    if task['status']!='downloaded':return task
    try:
        doc=fitz.open(SRC/task['sourceFile']);answer=fitz.open(SRC/task['answerFile'])
        solution={};keys={}
        if task['kind']=='secondary':
            solution=secondary_answers(answer,task['subject']);keys={k:{'':'標準解答画像を参照して、導出過程と結果を自己採点してください。'} for k in solution}
        elif task['kind']=='third':
            raw=e.nonit.official_keys(answer,task)
            for k,a in raw.items():
                m=re.fullmatch(r'(\d+)([ab]?)',k);keys.setdefault(m[1],{})
                if a is not None:keys[m[1]][m[2]]=str(a+1)
        else:
            try:keys=e.denken_keys(answer,task)
            except AssertionError:keys,solution=primary_image_keys(answer,task)
        assert sorted(map(int,keys))==list(range(1,len(keys)+1))
        starts=headings(doc,len(keys),task['kind']=='secondary')
        # ponytail: ambiguous OCR keeps the whole original booklet; narrow pages only after verified headings.
        assert starts or len(doc)<=30,'Booklet exceeds image limit; page mapping required'
        rows=[];evidence=[];cache={};acache={};stem=Path(task['file']).stem
        for n,blanks in keys.items():
            if starts:
                i=int(n)-1;pn=starts[i][1];end=starts[i+1][1] if i+1<len(starts) else len(doc)-1
                if i+1<len(starts) and starts[i+1][2]<110 and end>pn:end-=1
                pages=list(range(pn,end+1))
            else:pages=list(range(len(doc)))
            images,records=zip(*(e.nonit.picture(doc,p,stem,cache) for p in pages))
            simages,srecords=zip(*(e.nonit.picture(answer,p,stem+'-answer',acache) for p in solution[n])) if solution else ([],[])
            for blank,value in blanks.items():
                number=n+('('+blank+')' if blank else '')
                title=f'{task["year"]}年度 {e.NAMES[task["examId"]]} {task["term"]} {task["subject"]} 問{number}'
                single=task['kind']=='third'
                q=dict(id=stem+'-q'+n+('-b'+blank if blank else ''),examId=task['examId'],type='single' if single else 'written',year=task['year'],term=task['term'],subject=task['subject'],category='過去問',topic=title,
                    prompt=title+'\n'+('原本冊子全体を表示しています。指定した問題番号を探して解答してください。' if not starts else '原本画像の該当問題に解答してください。')+('空欄('+blank+')が対象です。' if blank else ''),images=list(images),solutionImages=list(simages),sourceUrl=task['url'],
                    source='出典：一般財団法人電気技術者試験センター。公式公開PDFをページ画像に加工（本文・図表変更なし）。',explanation='公式標準解答画像と比較して自己採点してください。' if solution else '公式正答：'+value+'。理由解説は未収録です。実施当時の制度・規格を前提とします。',explanationSource='電気技術者試験センター公式標準解答')
                if single:q.update(options=['1','2','3','4','5'],answer=int(value)-1)
                else:q.update(modelAnswer=value,answer=None)
                rows.append(q);evidence.append(dict(id=q['id'],number=number,answer=q['answer'],modelAnswer=q.get('modelAnswer',''),images=list(records),solutionImages=list(srecords)))
        return e.nonit.finish({**task,'pageMapping':'headings' if starts else 'whole-booklet','verificationLabel':'公式解答・原本画像ハッシュ照合。番号読取不確実な冊子は全ページを保持。二次は標準解答画像で自己採点。'},rows,evidence,[])
    except Exception as error:return {**task,'status':'pending-review','reason':str(error) or type(error).__name__}

def main():
    tasks=json.loads((SRC/'denken-discovery.json').read_bytes())['tasks']
    report={'packs':[]}
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        for t in pool.map(prepare,tasks):
            report['packs'].append(t)
            print(t['examId'],t['year'],t['term'],t['subject'],t['status'],t.get('count',t.get('reason')),t.get('pageMapping',''),flush=True)
            (OUT/'denken-report.json').write_bytes(ipa.encode(report))

if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if '--fetch' in sys.argv:discover()
    else:main()
