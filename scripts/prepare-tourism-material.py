"""Archive tourism/transport papers with native answer cells and original pages."""
import importlib.util,json,re,sys
from pathlib import Path
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
ipa=module('tourism_ipa','prepare-github-material.py')
fetch=module('tourism_fetch','fetch-github-material.py')
nonit=module('tourism_nonit','prepare-nonit-material.py')
SRC,OUT,fitz,norm=ipa.SRC,ipa.OUT,ipa.fitz,ipa.norm

def acquire():
    from bs4 import BeautifulSoup
    indexes=[('https://www.unkan.or.jp/contents/after_pdf.json','tourism-unkan-index.json'),('https://www.anta.or.jp/exam/shiken/kakomon.html','tourism-anta.html'),('https://www.kouronpub.com/past_issues/unkan/unkan_index.html','tourism-kouron.html')]
    indexes += [(f'https://www.jata-net.or.jp/seminar/r{year-2018}_question',f'tourism-jata-r{year-2018}.html') for year in range(2021,2026)]
    indexes += [(f'https://www.jnto.go.jp/projects/visitor-support/interpreter-guide-exams/past-exam-archives/{year}.html',f'tourism-jnto-{year}.html') for year in range(2022,2027)]
    with ThreadPoolExecutor(max_workers=6) as pool:list(pool.map(lambda item:fetch.fetch(*item),indexes))
    tasks=[]
    def add(kind,exam,year,subject,url,answer,extra=None):
        slug={'法令':'law','約款':'terms','国内実務':'domestic','海外実務':'overseas','全科目':'all'}.get(subject,subject)
        stem=f'tourism-{kind}-{year}-{slug}'
        tasks.append(dict(provider='TOURISM',kind=kind,examId=exam,year=str(year),subject=subject,term='公開過去問',localOnly=True,
                          file=stem+'.json',sourceFile=stem+'.pdf',answerFile=stem+'-answer.pdf' if answer!=url else stem+'.pdf',url=url,answerUrl=answer,extraUrls=extra or []))
    for year in range(2022,2027):
        html=BeautifulSoup((SRC/f'tourism-jnto-{year}.html').read_bytes(),'html.parser')
        for a in html.find_all('a',href=True):
            if re.search(r'guide_(geo|his|com|pra)_',a['href']):
                url=urljoin('https://www.jnto.go.jp',a['href']);subject=re.search(r'guide_(\w+)_',url)[1]
                add('jnto','tour-guide',year,subject,url,url)
    html=BeautifulSoup((SRC/'tourism-anta.html').read_bytes(),'html.parser')
    urls=[urljoin('https://www.anta.or.jp/exam/shiken/kakomon.html',a['href']) for a in html.find_all('a',href=True) if '.pdf' in a['href']]
    for year in range(2022,2027):
        tag=f'R{year-2018:02}'
        url=next(u for u in urls if tag in u and ('mondai' in u))
        answer=next(u for u in urls if tag in u and ('kaitou' in u) and (u.endswith('_2.pdf') or u.endswith('_1.pdf')))
        add('anta','travel-domestic',year,'全科目',url,answer)
    index=json.loads((SRC/'tourism-unkan-index.json').read_bytes())
    for entry in index['pdfs']['past']:
        year=2018+int(re.search(r'\d+',entry['nendo'])[0])
        for subject,exam in [('kamotsu','transport-cargo'),('ryokaku','transport-passenger')]:
            add('unkan',exam,year,subject,entry[subject]['mondai'],entry[subject]['seitou'])
    for subject,exam in [('kamotsu','transport-cargo'),('ryokaku','transport-passenger')]:
        url='https://www.unkan.or.jp/after/answer/pdf/04_cbt'+subject+'mondai.pdf'
        add('unkan',exam,2022,subject,url,url.replace('mondai','seito'))
    html=BeautifulSoup((SRC/'tourism-kouron.html').read_bytes(),'html.parser')
    for a in html.find_all('a',href=True):
        href=a['href'];m=re.search(r'(freightcar|passenger)/(\d{3}|r\d{4})([kr])_(m|mk|ma)\.pdf$',href)
        if not m:continue
        code=m[2];year=2018+int(code[1:3]) if code.startswith('r') else 1988+int(code[:2]);month=code[-2:] if code.startswith('r') else code[-1]
        url=urljoin('https://www.kouronpub.com/past_issues/unkan/unkan_index.html',href)
        answer=url.replace('_m.pdf','_k.pdf') if m[4]=='m' else url
        add('kouron','transport-cargo' if m[1]=='freightcar' else 'transport-passenger',year,m[3]+month,url,answer)
    for year in range(2021,2026):
        html=BeautifulSoup((SRC/f'tourism-jata-r{year-2018}.html').read_bytes(),'html.parser')
        urls=[urljoin('https://www.jata-net.or.jp',a['href']) for a in html.find_all('a',href=True) if '.pdf' in a['href']]
        questions=[u for u in urls if re.search(r'(?:eqq|issue)',u,re.I)]
        answer=next(u for u in urls if 'correctan' in u)
        assert len(questions)==5,(year,questions)
        for subject,url in zip(['法令','約款','国内実務','海外実務'],questions[:4]):
            add('jata','travel-general',year,subject,url,answer,[questions[4]] if subject in ('国内実務','海外実務') else [])
    def download(task):
        pairs=[(task['url'],task['sourceFile']),(task['answerUrl'],task['answerFile'])]+[(u,Path(task['file']).stem+f'-reference-{i}.pdf') for i,u in enumerate(task['extraUrls'])]
        try:task['sources']=[fetch.fetch(u,n) for u,n in dict(pairs).items()]
        except Exception as error:task['downloadError']=str(error)
        return task
    with ThreadPoolExecutor(max_workers=6) as pool:tasks=list(pool.map(download,tasks))
    (SRC/'tourism-discovery.json').write_bytes(ipa.encode({'tasks':tasks}));return tasks

def native_lines(page):
    return [(norm(''.join(s['text'] for s in l['spans'])).strip(),l['bbox']) for l in ipa.lines(page.get_text('dict',flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES))]

def ocr_lines(doc,pn,file):
    cache=SRC/'ocr'/f'{file}-tourism-{pn}.json'
    if cache.exists():return json.loads(cache.read_bytes())
    page=doc[pn];textpage=page.get_textpage_ocr(language='jpn+eng',dpi=144,full=True,tessdata=str(ROOT/'build/tessdata'))
    result=[(norm(''.join(s['text'] for s in l['spans'])).strip(),l['bbox']) for l in ipa.lines(page.get_text('dict',textpage=textpage))]
    cache.parent.mkdir(exist_ok=True);cache.write_bytes(ipa.encode(result));return result

def official_keys(doc,task):
    keys={}
    if task['kind']=='jnto':
        reviewed_file=SRC/'tourism-reviewed-keys.json'
        reviewed=json.loads(reviewed_file.read_bytes()).get(task['sourceFile']) if reviewed_file.exists() else None
        if reviewed:
            assert ipa.sha((SRC/task['sourceFile']).read_bytes())==reviewed['sha256'],'Visually reviewed source changed'
            return {str(i+1):a for i,a in enumerate(reviewed['answers'])}
        assert task['subject']!='pra','実務科目は4〜6選択肢・枝問の個別確認が必要'
        lines=native_lines(doc[-1]);header=next(b for t,b in lines if t=='解答番号');ans=next(b for t,b in lines if t=='解答')
        for text,b in lines:
            if not text.isdigit() or abs((b[0]+b[2]-header[0]-header[2])/2)>12 or b[1]<header[3]:continue
            cells=[int(t)-1 for t,c in lines if t in '1234' and len(t)==1 and abs((c[0]+c[2]-ans[0]-ans[2])/2)<12 and abs(c[1]-b[1])<2]
            assert len(cells)==1;(keys.update({text:cells[0]}))
        assert set(keys)==set(map(str,range(1,len(keys)+1))) and keys
        return keys
    if task['kind']=='anta':
        lines=native_lines(doc[0])
        if int(task['year'])>=2024:
            headings=sorted(b[1] for t,b in lines if re.match(r'[123]\.\s*.*旅行',t))
            assert len(headings)==3
            for section,lo in enumerate(headings):
                hi=headings[section+1] if section<2 else doc[0].rect.height
                columns=[[t for t,b in sorted(lines,key=lambda item:item[1][1]) if lo<b[1]<hi and re.fullmatch(r'[アイウエ・]+',t) and (b[0]<300)==(column==0)] for column in (0,1)]
                numbers={2024:[*range(51,57),57,57,*range(58,69),69,69,69,69,*range(70,85)],2025:[*range(51,70),70,70,70,70,*range(71,86)],2026:[*range(51,71),71,71,71,71,*range(72,86)]}[int(task['year'])]
                counts=[13,12] if section<2 else [19,19] if int(task['year'])<2026 else [20,18]
                assert list(map(len,columns))==counts,('Answer table layout changed',section,list(map(len,columns)))
                cells=columns[0]+columns[1]
                for i,t in enumerate(cells):
                    n=section*25+i+1 if section<2 else numbers[i]
                    values=sorted({'アイウエ'.index(c) for c in t if c in 'アイウエ'})
                    keys[str(n)]=None if section==2 and numbers.count(n)>1 else values[0] if len(values)==1 else values
            return keys
        if int(task['year'])<2024:
            headings=sorted((b[1],t) for t,b in lines if re.match(r'[123]\.\s*.*旅行',t))
            index=0 if task['subject']=='法令' else 1
            assert task['subject'] in ('法令','約款') and len(headings)==3
            lo,hi=headings[index][0],headings[index+1][0]
            cells=sorted([(0 if b[0]<300 else 1,b[1],t) for t,b in lines if lo<b[1]<hi and re.fullmatch(r'[アイウエ・]+',t)])
            assert len(cells)==25 and sum(c==0 for c,y,t in cells)==13
            return {str(i+1):'アイウエ'.index(t) for i,(c,y,t) in enumerate(cells)}
    for page in (doc if task['kind'] in ('jata','unkan') or task['answerFile']!=task['sourceFile'] else [doc[-1]]):
        lines=native_lines(page)
        labels=[(int(m[1]),box) for text,box in lines if (m:=re.fullmatch(r'問\s*(\d+)\.?',text))]
        columns=[]
        for x in sorted(box[0] for n,box in labels):
            if not columns or x-columns[-1]>35:columns.append(x)
        for n,box in labels:
            x,y,x1,y1=box
            if task['kind']=='jata':
                column=min(range(len(columns)),key=lambda i:abs(columns[i]-x))
                wanted=['法令','約款','国内実務','海外実務','海外実務'][column]
                if wanted!=task['subject']:continue
                candidates=[(b[0],t) for t,b in lines if b[0]>x1 and b[0]-x1<65 and abs(b[1]-y)<2 and re.fullmatch(r'[a-d.]+',t)]
            elif task['kind']=='unkan':
                candidates=[(b[1],t) for t,b in lines if abs((b[0]+b[2]-x-x1)/2)<20 and 0<b[1]-y<90 and t and not t.startswith('問')]
            elif task['answerFile']!=task['sourceFile']:
                candidates=[(b[1],t) for t,b in lines if 0<b[0]-x1<65 and y-2<=b[1]<y+30 and re.fullmatch(r'[1-6,、 ]+',t)]
            else:
                candidates=[(b[1],t) for t,b in lines if abs((b[0]+b[2]-x-x1)/2)<15 and 0<b[1]-y<45 and re.fullmatch(r'[1-6,、 ]+',t)]
                if not candidates:
                    candidates=[(b[0],t) for t,b in lines if 0<b[0]-x1<120 and abs(b[1]-y)<2 and re.fullmatch(r'[1-6,、 ]+',t)]
            symbol=min(candidates)[1] if candidates else ''
            if task['kind']=='jata':values=[ord(c)-97 for c in symbol if c in 'abcd']
            else:values=[int(c)-1 for c in re.findall(r'[1-6]',symbol)] if re.fullmatch(r'[1-6,、 ]+',symbol) else []
            keys[str(n)]=values[0] if len(values)==1 else sorted(set(values)) if values else None
    assert keys,'No native answer cells'
    return keys

def question_starts(doc,task):
    starts=[]
    if task['kind']=='anta' and int(task['year'])<2024:
        lo,hi=anta_bounds(doc,task)
        for pn in range(lo,hi+1):
            for text,b in native_lines(doc[pn]):
                if b[0]<65 and (re.match(r'^\([0-9\x00-\x1f]+\)',text) or task['subject']=='約款' and len(starts)>=20 and b[0]<53 and re.match(r'^[\x00-\x1f]+唖',text)):
                    starts.append((str(len(starts)+1),pn,b[1]))
        assert len(starts)==25,('Expected 25 native parenthesized headings',len(starts))
        return starts
    for pn,page in enumerate(doc):
        if task['kind']=='kouron' and any(re.fullmatch(r'解\s*答(?:&ポイント解説)?',t) for t,b in native_lines(page)):break
        for text,box in native_lines(page):
            m=re.match(r'^(?:第\s*)?問\s*(\d+)',text) if task['kind']!='unkan' else re.match(r'^(?:第\s*(\d+)\s*問|問\s*(\d+))',text)
            if m and box[0]<140 and box[1]<page.rect.height-35:
                n=str(int(next(v for v in m.groups() if v)))
                if n not in {v[0] for v in starts}:starts.append((n,pn,box[1]))
    return starts

def anta_bounds(doc,task):
    headings=[]
    for pn,page in enumerate(doc):
        if any(b[1]<100 and b[0]<80 and t.endswith(('旅行業法及びこれに基づく命令','旅行業約款、運送約款及び宿泊約款','国内旅行実務')) for t,b in native_lines(page)):headings.append(pn)
    assert len(headings)==3,headings
    index=0 if task['subject']=='法令' else 1
    return headings[index],headings[index+1]-1

def question_end(doc,task):
    if task['kind']=='anta' and int(task['year'])<2024:return anta_bounds(doc,task)[1]
    if task['answerFile']!=task['sourceFile']:return len(doc)-1
    for pn,page in enumerate(doc):
        if any(re.fullmatch(r'解\s*答(?:&ポイント解説)?',t) for t,b in native_lines(page)):return pn-1
    return len(doc)-2

def prepare(task):
    try:
        task={**task,'verificationLabel':('自動車公論社の掲載正答照合' if task['kind']=='kouron' else '公式掲載正答照合')+'・原本画像の画素一致（全問の目視・理由解説は未実施）'}
        assert 'downloadError' not in task,task.get('downloadError')
        doc=fitz.open(SRC/task['sourceFile']);keys=official_keys(fitz.open(SRC/task['answerFile']),task)
        if task['kind']=='jnto':return prepare_jnto(task,doc,keys)
        starts=question_starts(doc,task)
        assert set(keys)=={n for n,p,y in starts},('Question/key mismatch',len(starts),len(keys),set(keys)-{n for n,p,y in starts})
        rows=[];evidence=[];excluded=[];cache={};stem=Path(task['file']).stem
        for i,(number,pn,y) in enumerate(starts):
            answer=keys[number]
            limit=question_end(doc,task)
            endp,endy=starts[i+1][1:] if i+1<len(starts) else (limit,doc[limit].rect.height)
            endp=min(endp,limit)
            segment=[text for p in range(pn,endp+1) for text,b in native_lines(doc[p]) if (p!=pn or b[1]>=y) and (i+1==len(starts) or p!=endp or b[1]<endy)]
            labels=list(range(1,5)) if task['kind'] in ('jata','anta') else sorted({int(m[1]) for text in segment if (m:=re.match(r'^([1-6])\s*[.．]',text))})
            if answer is None or labels!=list(range(1,len(labels)+1)) or len(labels)<2:
                excluded.append({'number':number,'reason':'複合正誤・字句の正答、または選択肢を自動確定できない'});continue
            options=list('abcd') if task['kind']=='jata' else list('アイウエ') if task['kind']=='anta' else list(map(str,labels))
            assert all(a<len(options) for a in (answer if isinstance(answer,list) else [answer]))
            ep=starts[i+1][1] if i+1<len(starts) else endp
            if i+1<len(starts) and ep>pn and starts[i+1][2]<65:ep-=1
            ep=min(ep,endp)
            pages=range(1,len(doc)) if task['kind']=='jata' and task['subject'] in ('国内実務','海外実務') else range(pn,ep+1)
            if task['kind']=='jata' and task['subject'] in ('国内実務','海外実務'):assert starts[0][1]>0,'Cover page contains a question'
            images,records=map(list,zip(*(nonit.picture(doc,p,stem,cache) for p in pages)))
            for source in task['sources'][2:]:
                reference=fitz.open(SRC/source['file']);reference_cache={}
                for p in range(len(reference)):
                    image,record=nonit.picture(reference,p,Path(source['file']).stem,reference_cache);record={**record,'sourceFile':source['file']};images.append(image);records.append(record)
            title=f'{task["year"]}年 {task["subject"]} 問{number}'
            if task['kind']=='anta' and int(task['year'])<2024 and task['subject']=='約款' and int(number)>20:title=f'{task["year"]}年 約款 設問{int(number)-19}（科目内通し番号{number}）'
            source='公式公開資料' if task['kind']!='kouron' else '自動車公論社公開過去問（正答は同社掲載。一部問題に変更の注記がある公開版）'
            term='公式公表CBT出題例' if task['kind']=='unkan' or task['kind']=='anta' and int(task['year'])>=2024 else task['term']
            q=dict(id=stem+f'-q{int(number):03}',examId=task['examId'],type='multiple' if isinstance(answer,list) else 'single',year=task['year'],term=term,subject=task['subject'],category='過去問',topic=title,
                   prompt=title+'\n原本画像の該当問題を解答してください。共通資料も画像で確認できます。',options=options,answer=answer,images=images,
                   sourceUrl=task['url'],source=source+'。本人用教材。',explanation='掲載正答：'+', '.join(options[a] for a in (answer if isinstance(answer,list) else [answer]))+'。理由解説は未収録です。試験実施当時の制度を前提とします。',explanationSource=source)
            rows.append(q);evidence.append(dict(id=q['id'],number=number,answer=answer,images=records))
        assert rows,'No verified questions'
        return nonit.finish(task,rows,evidence,excluded)
    except Exception as error:return {**task,'status':'pending-review','reason':str(error) or ('公式正答表の文字を取得できない' if isinstance(error,StopIteration) else type(error).__name__)}

def prepare_jnto(task,doc,keys):
    # ponytail: shared complete paper images preserve passages/maps; per-question crops can reduce scrolling later.
    texts=['\n'.join(t for t,b in ocr_lines(doc,p,task['sourceFile'])) for p in range(1,len(doc)-1)]
    assert not any(re.search(r'著作権|非公開|削除|掲載.{0,8}(でき|していません)',t) for t in texts),'欠落した著作物を含むため要目視確認'
    assert task['subject'] in ('geo','his','his_2023','com'),'実務科目は設問ごとの選択肢数を要確認'
    assert not any('⑤' in t or '⑥' in t for t in texts),'Four-choice format unconfirmed'
    stem=Path(task['file']).stem;cache={};images,records=map(list,zip(*(nonit.picture(doc,p,stem,cache) for p in range(1,len(doc)-1))))
    rows=[];evidence=[];excluded=[]
    for n,answer in keys.items():
        if answer is None:
            excluded.append({'number':n,'reason':'複数の許容解答による単一採点不能'});continue
        title=f'{task["year"]}年 全国通訳案内士 {task["subject"]} 解答番号{n}'
        q=dict(id=stem+f'-q{int(n):03}',examId=task['examId'],type='single',year=task['year'],term=task['term'],subject=task['subject'],category='過去問',topic=title,
               prompt=title+'\n原本画像の四角で囲まれた「解答番号」の該当設問を解答してください。共通の文章・図表を含む科目全体の問題画像です。',options=list('①②③④'),answer=answer,images=images,
               sourceUrl=task['url'],source='JNTO公式公開PDF（本人参考用の個人使用）。',explanation='公式正答：'+list('①②③④')[answer]+'。理由解説は未収録です。',explanationSource='JNTO公式解答・配点表')
        rows.append(q);evidence.append(dict(id=q['id'],number=n,answer=answer,images=records))
    return nonit.finish(task,rows,evidence,excluded)

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    tasks=acquire() if '--fetch' in sys.argv else json.loads((SRC/'tourism-discovery.json').read_bytes())['tasks']
    if '--fetch' in sys.argv:return
    tasks=[variant for task in tasks for variant in ([{**task,'subject':s,'file':task['file'].replace('-all','-'+slug),'url':task['url']+'#'+slug} for s,slug in [('法令','law'),('約款','terms')]] if task['kind']=='anta' and int(task['year'])<2024 else [task])]
    packs=[prepare(t) for t in tasks]
    (OUT/'tourism-report.json').write_bytes(ipa.encode({'packs':packs}))
    for p in packs:print(p['file'],p['status'],p.get('count',p.get('reason')))

if __name__=='__main__':main()
