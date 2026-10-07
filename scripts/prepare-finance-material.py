"""Discover linked CPA papers; preserve original pages and reject ambiguous keys."""
import json,re,sys
from pathlib import Path
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'build/python-deps'))
from bs4 import BeautifulSoup
import importlib.util
spec=importlib.util.spec_from_file_location('tourism',Path(__file__).with_name('prepare-tourism-material.py'))
tour=importlib.util.module_from_spec(spec);spec.loader.exec_module(tour)
ipa,fetch,nonit= tour.ipa,tour.fetch,tour.nonit
SRC,OUT,fitz=ipa.SRC,ipa.OUT,ipa.fitz
SUBJECTS=['企業法','管理会計論','監査論','財務会計論']

def links(url,name):
    name=Path(name).stem+'-'+ipa.sha(url.encode())[:8]+'.html'
    record=fetch.fetch(url,name)
    soup=BeautifulSoup((SRC/name).read_bytes(),'html.parser')
    return [(a.get_text(' ',strip=True),urljoin(url,a['href'])) for a in soup.find_all('a',href=True)]

def acquire():
    baseline=SRC/'finance-baseline.json'
    if not baseline.exists():baseline.write_bytes((ipa.ROOT/'build/private/manifest.json').read_bytes())
    pages=links('https://www.fsa.go.jp/cpaaob/kouninkaikeishi-shiken/kakoshiken.html','finance-cpa-past.html')
    years=sorted({u for t,u in pages if re.search(r'/(20(?:0[7-9]|1\d|2[0-6]))shiken.html$',u)})
    years.append('https://www.fsa.go.jp/cpaaob/kouninkaikeishi-shiken/2026shiken.html')
    tasks=[];pending=[]
    def discover(url):
        year=re.search(r'(20\d\d)shiken',url)[1]
        try:
            items=links(url,f'finance-cpa-{year}.html')
            questions=[(t,u) for t,u in items if '短答式' in t and ('試験問題' in t or '問題及び' in t) and '誤' not in t]
            answers=[(t,u) for t,u in items if '短答式' in t and '合格発表' in t and '方法' not in t and 'tantougoukaku' in u]
            found=[]
            for index,(title,page) in enumerate(dict.fromkeys(questions)):
                term='第Ⅱ回' if 'Ⅱ' in title or 'II' in title or '２回' in title or '2回' in title else '第Ⅰ回'
                matching=[u for t,u in answers if ('Ⅱ' in t or 'II' in t or '２回' in t or '2回' in t)==(term=='第Ⅱ回')]
                if len(set(matching))!=1:pending.append(dict(year=year,url=page,reason='正答掲載ページを一意に確定できない'));continue
                qlinks=links(page,f'finance-cpa-{year}-{index}-q.html')
                alinks=links(matching[0],f'finance-cpa-{year}-{index}-a.html')
                keys=[u for t,u in alinks if '正解' in t and u.endswith(('.pdf','.html'))]
                if len(set(keys))!=1:pending.append(dict(year=year,url=page,reason='公式正答PDFなし'));continue
                for subject in SUBJECTS:
                    urls=list(dict.fromkeys(u for t,u in qlinks if subject in re.sub(r'\s','',t) and '.pdf' in u))
                    if not urls:continue
                    # The first subject links are questions; later links are blank answer sheets.
                    session='II' if term=='第Ⅱ回' else 'I'
                    stem=f'finance-cpa-{year}-{session}-{SUBJECTS.index(subject)}'
                    found.append(dict(provider='FINANCE',examId='cpa',year=year,subject=subject,term=term,localOnly=True,
                        file=stem+'.json',sourceFile=stem+'.pdf',answerFile=f'finance-cpa-{year}-{session}-answer'+Path(keys[0]).suffix,url=urls[0],answerUrl=keys[0]))
            return found
        except Exception as e:pending.append(dict(url=url,reason=str(e)));return []
    with ThreadPoolExecutor(max_workers=5) as pool:
        for rows in pool.map(discover,dict.fromkeys(years)):tasks.extend(rows)
    fp=links('https://www.jafp.or.jp/exam/mohan/','finance-fp-current.html')
    for text,url in fp:
        m=re.search(r'/j3_(20\d{2})(\d{2})_q.pdf$',url)
        if not m:continue
        stem=f'finance-fp3-{m[1]}{m[2]}'
        tasks.append(dict(provider='FINANCE',examId='fp3',year=m[1],subject='実技（資産設計提案業務）',term=m[2]+'月公表',localOnly=True,
            file=stem+'.json',sourceFile=stem+'-q.pdf',answerFile=stem+'-a.pdf',url=url,answerUrl=url.replace('_q.pdf','_a.pdf')))
    def download(t):
        try:t['sources']=[fetch.fetch(t['url'],t['sourceFile']),fetch.fetch(t['answerUrl'],t['answerFile'])]
        except Exception as e:t['downloadError']=str(e)
        return t
    with ThreadPoolExecutor(max_workers=5) as pool:tasks=list(pool.map(download,tasks))
    (SRC/'finance-discovery.json').write_bytes(ipa.encode(dict(tasks=tasks,pending=pending)))
    print('Linked CPA papers:',len(tasks),'pending:',len(pending),flush=True)

def official_keys(doc,subject):
    keys={}
    # Tables may share one page: keep only rows beneath this subject's heading.
    pages=[p for p in doc if subject in ipa.norm(p.get_text())]
    assert len(pages)==1,('Subject page ambiguous',subject,len(pages))
    lines=tour.native_lines(pages[0])
    headings=sorted(((b[0]+b[2])/2,t,b) for t,b in lines if t.strip('【】[] ') in SUBJECTS)
    target=next((x,t,b) for x,t,b in headings if t.strip('【】[] ')==subject)
    for text,b in lines:
        m=re.fullmatch(r'問題\s*(\d+)',text)
        if not m:continue
        if min(headings,key=lambda h:abs(h[0]-(b[0]+b[2])/2))[1]!=target[1] or b[1]<=target[2][1]:continue
        cells=[(c[0],t) for t,c in lines if 0<c[0]-b[2]<90 and abs(c[1]-b[1])<4 and re.fullmatch(r'[1-9](?:[,、・\s]+[1-9])*|[-−―ー]|全員正解|全員に加点',t)]
        assert cells,('Missing answer cell',m[1])
        symbol=min(cells)[1];values=sorted({int(v)-1 for v in re.findall(r'[1-9]',symbol)})
        keys[str(int(m[1]))]=values[0] if len(values)==1 else None
    assert keys and set(map(int,keys))==set(range(1,len(keys)+1)),('Key sequence',subject,len(keys))
    return keys

def html_keys(path,subject):
    soup=BeautifulSoup(path.read_bytes(),'html.parser')
    text=ipa.norm(soup.get_text(' ',strip=True))
    segment=text.split('【'+subject+'】',1)[1].split('【')[0]
    cells=re.findall(r'問題\s*(\d+)\s+([1-9]|[-−―ー])(?=\s|$)',segment)
    keys={str(int(n)):int(a)-1 if a.isdigit() else None for n,a in cells}
    assert keys and set(map(int,keys))==set(range(1,len(keys)+1))
    return keys

def fp_keys(doc):
    keys={}
    for page in doc:
        lines=tour.native_lines(page)
        for text,b in lines:
            m=re.fullmatch(r'問\s*(\d+)',text)
            if not m:continue
            cells=[int(t)-1 for t,c in lines if t in ('1','2','3') and abs((c[0]+c[2]-b[0]-b[2])/2)<3 and 0<c[1]-b[1]<30]
            assert len(cells)==1,(text,cells)
            keys[str(int(m[1]))]=cells[0]
    assert set(map(int,keys))==set(range(1,21))
    return keys

def starts(doc,subject=None,page_lines=None):
    result=[]
    for pn,page in enumerate(doc):
        for text,b in page_lines[pn] if page_lines is not None else tour.native_lines(page):
            m=re.match(r'^問題\s*(\d+)(?:\s|[.．]|$)',text)
            if m and b[0]<110 and 30<b[1]<page.rect.height-30:
                entry=(str(int(m[1])),pn,b[1])
                if not any(n==entry[0] and p==pn and abs(y-b[1])<1 for n,p,y in result):result.append(entry)
    if result and sum(n=='1' for n,p,y in result)==2 and subject in ('管理会計論','監査論'):
        split=next(i for i,(n,p,y) in enumerate(result) if i and n=='1')
        result=result[:split] if subject=='管理会計論' else result[split:]
    assert result and [int(n) for n,p,y in result]==list(range(1,len(result)+1)),('Question sequence',result)
    return result

def option_labels(doc,positions,i,page_lines=None):
    n,pn,y=positions[i];ep,ey=positions[i+1][1:] if i+1<len(positions) else (len(doc)-1,doc[-1].rect.height)
    labels=[]
    for p in range(pn,ep+1):
        for t,b in page_lines[p] if page_lines is not None else tour.native_lines(doc[p]):
            if (p!=pn or b[1]>y) and (p!=ep or b[1]<ey):
                m=re.match(r'^([1-9])\s*[.．]',t)
                if m:labels.append(int(m[1]))
    unique=sorted(set(labels))
    assert 2<=len(unique)<=9 and unique==list(range(1,len(unique)+1)),('Option sequence',n,unique)
    return list(map(str,unique))

def prepare(t):
    try:
        assert 'downloadError' not in t,t.get('downloadError')
        doc=fitz.open(SRC/t['sourceFile'])
        page_lines=[tour.native_lines(page) for page in doc]
        if t['examId']=='fp3':
            keys=fp_keys(fitz.open(SRC/t['answerFile']))
            positions=tour.question_starts(doc,{**t,'kind':'fp'})
        else:
            keys=html_keys(SRC/t['answerFile'],t['subject']) if t['answerFile'].endswith('.html') else official_keys(fitz.open(SRC/t['answerFile']),t['subject'])
            positions=starts(doc,t['subject'],page_lines)
        assert {n for n,p,y in positions}==set(keys),('Question/key mismatch',len(positions),len(keys))
        rows=[];evidence=[];excluded=[];cache={};stem=Path(t['file']).stem
        for i,(n,p,y) in enumerate(positions):
            try:options=option_labels(doc,positions,i,page_lines)
            except AssertionError as e:excluded.append(dict(number=n,reason=str(e)));continue
            answer=keys[n]
            if answer is None:excluded.append(dict(number=n,reason='複数許容・全員加点のため採点対象外'));continue
            assert 0<=answer<len(options),(n,answer,options)
            ep=positions[i+1][1] if i+1<len(positions) else next((pn-1 for pn in range(p+1,len(doc)) if t['subject']=='管理会計論' and '監査論' in ipa.norm(doc[pn].get_text()) and '問題' not in ipa.norm(doc[pn].get_text())),len(doc)-1)
            if i+1<len(positions) and ep>p and positions[i+1][2]<90:ep-=1
            context=[pn for pn in range(p+1) for text,b in page_lines[pn]
                if (m:=re.fullmatch(r'問題\s*(\d+)\s*[~〜～-]\s*(\d+)',text)) and int(m[1])<=int(n)<=int(m[2])]
            # ponytail: shared original pages retain tables; crop individual questions if scrolling becomes a problem.
            first=min([p]+context)
            images,records=map(list,zip(*(nonit.picture(doc,pn,stem,cache) for pn in range(first,ep+1))))
            provider='日本FP協会' if t['examId']=='fp3' else '公認会計士・監査審査会'
            title=f'{t["year"]}年 '+('FP技能検定3級' if t['examId']=='fp3' else '公認会計士')+f' {t["term"]} {t["subject"]} 問題{n}'
            rows.append(dict(id=stem+'-q'+n,examId=t['examId'],type='single',year=t['year'],term=t['term'],subject=t['subject'],category='過去問',topic=title,
                prompt=title+'\n原本画像の該当問題に解答してください。共通資料と図表は原本で確認できます。',options=options,answer=answer,images=images,
                sourceUrl=t['url'],source='出典：'+provider+' '+title+'。'+('日本FP協会の試験問題利用条件に基づく。' if t['examId']=='fp3' else 'PDL1.0。')+'公式PDFをページ画像に加工して作成。提供元が作成したアプリではありません。',
                explanation='公式正答：'+options[answer]+'。理由解説は未収録です。試験実施当時の法令・会計基準を前提とします。',explanationSource=provider+'公式正答'))
            evidence.append(dict(id=rows[-1]['id'],number=n,answer=answer,images=records))
        assert rows,'No verified questions'
        return nonit.finish({**t,'verificationLabel':'公式正答セル・設問連番・選択肢番号・原本画素を自動検査（全問目視・理由解説は未実施）'},rows,evidence,excluded)
    except Exception as e:return {**t,'status':'pending-review','reason':str(e)}

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    if '--fetch' in sys.argv:acquire();return
    tasks=json.loads((SRC/'finance-discovery.json').read_bytes())['tasks']
    packs=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for t,p in zip(tasks,pool.map(prepare,tasks)):
            packs.append(p);print(t['file'],p['status'],p.get('count',p.get('reason')),flush=True)
    (OUT/'finance-report.json').write_bytes(ipa.encode(dict(packs=packs)))

if __name__=='__main__':main()
