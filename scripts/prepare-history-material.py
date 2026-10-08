"""Import official history practice and geography papers into private local packs."""
import json, re, sys, urllib.request, urllib.parse, http.cookiejar
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from importlib import import_module
tourism=import_module('prepare-tourism-material')
ipa,nonit,fetch=tourism.ipa,tourism.nonit,tourism.fetch
SRC,OUT,fitz=ipa.SRC,ipa.OUT,ipa.fitz
from bs4 import BeautifulSoup
from PIL import Image
GRADES={'5':'rekiken5','4':'rekiken4','3s':'rekiken-pre3','3':'rekiken-japan3','3w':'rekiken-world3','2':'rekiken-japan2','2w':'rekiken-world2','1':'rekiken-japan1','1w':'rekiken-world1'}

def soup(file):return BeautifulSoup((SRC/file).read_text(encoding='utf-8'),'html.parser')

def source(url,file):
    data=(SRC/file).read_bytes()
    return dict(url=url,file=file,sha256=ipa.sha(data),bytes=len(data))

def acquire_practice(grade):
    url='https://www.kentei-uketsuke.com/sys/rekiken/practice'+grade
    stem='history-rekiken-practice'+grade
    jar=http.cookiejar.CookieJar()
    client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
    raw=client.open(url,timeout=45).read()
    page=BeautifulSoup(raw.decode('utf-8'),'html.parser');form=page.find('form')
    data={i['name']:i.get('value','') for i in form.select('input[type=hidden][name]')}
    data.update({i['name']:'1' for i in form.select('input[type=radio]')})
    answer_url=urllib.parse.urljoin(url,form['action'])
    answer=client.open(urllib.request.Request(answer_url,urllib.parse.urlencode(data).encode()),timeout=45).read()
    assert BeautifulSoup(answer.decode('utf-8'),'html.parser').select('.p-sysPractice__correctAnswer')
    # Archive content only; authentication and anti-CSRF form fields are not教材.
    for content,name in [(raw,stem+'.html'),(answer,stem+'-result.html')]:
        clean=BeautifulSoup(content.decode('utf-8'),'html.parser')
        for item in clean.select('input[type=hidden]'):item.decompose()
        (SRC/name).write_text(str(clean),encoding='utf-8')
    sources=[source(url,stem+'.html'),source(answer_url,stem+'-result.html')]
    for i,img in enumerate(page.select('.p-sysPractice__question img')):
        u=urllib.parse.urljoin(url,img['src']);name=stem+f'-figure{i}.png'
        sources.append(fetch.fetch(u,name))
    return dict(provider='HISTORY',kind='practice',examId=GRADES[grade],year='',term='公式無料練習問題（実施年度不明・本試験過去問とは区別）',subject='世界史' if 'world' in GRADES[grade] else '日本史',
                localOnly=True,file=stem+'.json',sourceFile=stem+'.html',answerFile=stem+'-result.html',url=url,answerUrl=answer_url,sources=sources)

def acquire():
    tasks=[]
    with ThreadPoolExecutor(max_workers=4) as pool:tasks.extend(pool.map(acquire_practice,GRADES))
    index=soup('history-jmc-index.html')
    for a in index.find_all('a',href=True):
        m=re.search(r'/(4[345](?:th|rd))_([ks])_mon.pdf$',a['href'])
        if not m:continue
        stem='history-jmc-'+m[1]+'_'+m[2];file=stem+'.pdf';s=fetch.fetch(a['href'],file)
        tasks.append(dict(provider='HISTORY',kind='geography',examId='map-geography-'+('basic' if m[2]=='k' else 'specialist'),year='2026' if m[1].startswith('45') else '2025',term='第'+m[1][:2]+'回',subject='基礎' if m[2]=='k' else '専門',localOnly=True,
                          file=stem+'.json',sourceFile=file,answerFile=file,url=a['href'],answerUrl=a['href'],sources=[s]))
    (SRC/'history-discovery.json').write_bytes(ipa.encode({'tasks':tasks}))

def plain(node,mark_underlines=False):
    copy=BeautifulSoup(str(node),'html.parser')
    for rt in copy.select('rt,rp'):rt.decompose()
    for br in copy.select('br'):br.replace_with('\n')
    if mark_underlines:
        for span in copy.select('[style]'):
            if 'underline' in span['style']:span.replace_with('【下線：'+span.get_text('',strip=True)+'】')
    text=copy.get_text('',strip=False)
    return re.sub(r'[ \t]+',' ',text).strip()

def practice_rows(task):
    page=soup(task['sourceFile']);result=soup(task['answerFile'])
    items=page.select('.p-sysPractice__item');answers=result.select('.p-sysPractice__item')
    assert len(items)==len(answers) and items
    # ponytail: the full shared passage retains cross-question references; split it only if scrolling becomes a problem.
    passage='\n\n'.join(plain(i.select_one('.p-sysPractice__question'),True) for i in items)
    assert '\ufffd' not in passage
    images=[];records=[]
    for s in task['sources'][2:]:
        path=OUT/'assets'/s['file']
        with Image.open(SRC/s['file']) as image:image.convert('RGB').save(path)
        images.append(dict(src='assets/github-material/'+s['file'],alt='公式練習問題の共通資料・地図'))
        records.append(dict(file=s['file'],sha256=ipa.sha(path.read_bytes()),sourceFile=s['file']))
    rows=[];evidence=[]
    for n,(item,answer_item) in enumerate(zip(items,answers),1):
        choices=[plain(l) for l in item.select('.c-form-radio__label')]
        correct=plain(answer_item.select_one('.p-sysPractice__correctAnswer dd'))
        assert choices.count(correct)==1,(task['file'],n,correct)
        answer=choices.index(correct)
        explanation=plain(answer_item.select_one('.p-sysPractice__comment dd'))
        title=task['subject']+' 公式無料練習問題 設問'+str(n)
        q=dict(id=Path(task['file']).stem+f'-q{n:03}',examId=task['examId'],type='single',year='',term=task['term'],subject=task['subject'],category='公式練習問題',topic=title,
               prompt=plain(item.select_one('.p-sysPractice__question'),True),passage=passage,options=choices,answer=answer,images=images,sourceUrl=task['url'],source='歴史能力検定・日販検定ポータル公式無料練習問題（本人用）。',explanation=explanation,explanationSource='公式採点結果の解説')
        rows.append(q);evidence.append(dict(id=q['id'],number=str(n),answer=answer,images=records))
    return rows,evidence

def geography_layout(doc,task):
    boundary=next(p for p,page in enumerate(doc) if re.search(r'第\s*4[345]\s*回地図地理検定\s*\((?:基礎|専門)\)\s*(?:正解表|解答)',ipa.norm(page.get_text())))
    starts=[]
    for p in range(boundary):
        for t,b in tourism.native_lines(doc[p]):
            m=re.match(r'^[◆\x00-\x1f\s]*問\s*(\d+)',t)
            if m and b[0]<100:starts.append((int(m[1]),p,b[1]))
    total=20 if task['subject']=='基礎' else 24
    assert [n for n,p,y in starts]==list(range(1,total+1)),starts
    return boundary,starts

def geography_keys(doc,boundary):
    keys={};lines=tourism.native_lines(doc[boundary])
    for t,b in lines:
        m=re.fullmatch(r'問\s*(\d+)',t)
        if not m:continue
        # NFKC converts circled option labels to digits, so use raw words.
        cells=[w for w in doc[boundary].get_text('words') if re.fullmatch('[①②③④⑤⑥]',w[4]) and 0<w[0]-b[2]<140 and abs(w[1]-b[1])<2]
        if len(cells)==1:keys[str(int(m[1]))]='①②③④⑤⑥'.index(cells[0][4])
    count=20 if '基礎' in doc[boundary].get_text() else 15
    assert set(keys)==set(map(str,range(1,count+1))),keys
    return keys

def geography_rows(task):
    doc=fitz.open(SRC/task['sourceFile']);boundary,starts=geography_layout(doc,task);keys=geography_keys(doc,boundary)
    rows=[];evidence=[];cache={};stem=Path(task['file']).stem
    for i,(n,p,y) in enumerate(starts):
        ep,ey=starts[i+1][1:] if i+1<len(starts) else (boundary,0)
        last=ep-1 if ep>p and ey<75 else ep
        last=min(last,boundary-1)
        # Shared maps can precede both questions of a pair; retain the preceding question and its previous page.
        context=max(starts[0][1],starts[i-1][1]-1) if i else p
        images,records=map(list,zip(*(nonit.picture(doc,pn,stem,cache) for pn in range(context,last+1))))
        title=task['year']+'年 '+task['term']+' 地図地理検定 '+task['subject']+' 問'+str(n)
        q=dict(id=stem+f'-q{n:03}',examId=task['examId'],year=task['year'],term=task['term'],subject=task['subject'],category='過去問',topic=title,prompt=title+'\n原本画像の該当する問番号に解答してください。複数の枝問がある場合はすべて回答してください。',images=images,sourceUrl=task['url'],source='日本地図センター公式過去問PDF。本人用ローカル教材。',explanationSource='公式正解表・解答例')
        if str(n) in keys:
            # The problem heading explicitly specifies the complete option range.
            head=''.join(doc[p].get_text().split()).translate(str.maketrans('０１２３４５６７８９','0123456789'))
            start=head.index('問'+str(n));match=re.search(r'①[~〜～]([④⑥])',head[start:])
            assert match,(task['file'],n,'Missing option range')
            count='①②③④⑤⑥'.index(match[1])+1
            assert keys[str(n)]<count
            q.update(type='single',options=list('①②③④⑤⑥')[:count],answer=keys[str(n)],explanation='公式正答：'+'①②③④⑤⑥'[keys[str(n)]]+'。理由解説は未収録です。')
        else:
            solution,solution_records=map(list,zip(*(nonit.picture(doc,pn,stem,cache) for pn in range(boundary,len(doc)))))
            q.update(type='essay',modelAnswer='公式解答画像の「問'+str(n)+'」を参照してください。作図を含む設問は、解答例の図と照合して自己採点してください。',solutionImages=solution,explanation='公式解答例は解答後に表示します。記述・作図は自己採点です。')
        rows.append(q);evidence.append(dict(id=q['id'],number=str(n),answer=q.get('answer'),images=records,solutionImages=solution_records if q['type']=='essay' else []))
    return rows,evidence

def verify_pack(task):
    for s in task['sources']:assert ipa.sha((SRC/s['file']).read_bytes())==s['sha256']
    rows,evidence=practice_rows(task) if task['kind']=='practice' else geography_rows(task)
    data=(OUT/task['file']).read_bytes();assert ipa.sha(data)==task['sha256']
    assert json.loads(data)==rows and evidence==task['questions'] and len(rows)==task['count']
    if task['kind']=='geography':
        doc=fitz.open(SRC/task['sourceFile']);boundary,_=geography_layout(doc,task)
        checked=set()
        for q,e in zip(rows,evidence):
            assert all(r['page']<boundary for r in e['images'])
            for r in e['images']+e['solutionImages']:
                if r['file'] in checked:continue
                pix=doc[r['page']].get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False)
                with Image.open(OUT/'assets'/r['file']) as image:assert image.convert('RGB').tobytes()==pix.samples
                assert ipa.sha((OUT/'assets'/r['file']).read_bytes())==r['sha256'];checked.add(r['file'])
    return len(rows)

def main():
    sys.stdout.reconfigure(encoding='utf-8');(OUT/'assets').mkdir(exist_ok=True)
    baseline=SRC/'history-baseline.json'
    if not baseline.exists():baseline.write_bytes(ipa.encode({p['id']:p['sha256'] for p in json.loads((ROOT/'build/private/manifest.json').read_bytes())['packs']}))
    if '--fetch' in sys.argv:acquire()
    tasks=json.loads((SRC/'history-discovery.json').read_bytes())['tasks'];packs=[]
    for task in tasks:
        try:
            rows,evidence=practice_rows(task) if task['kind']=='practice' else geography_rows(task)
            pack=nonit.finish({**task,'verificationLabel':'公式正答・問題対応を検査。地理は原本画素一致、記述・作図は自己採点。全設問の目視は未実施。'},rows,evidence,[])
            verify_pack(pack)
        except Exception as e:pack={**task,'status':'pending-review','reason':str(e)}
        packs.append(pack);print(task['file'],pack['status'],pack.get('count',pack.get('reason')))
    raw=ipa.encode({'packs':packs});(OUT/'history-report.json').write_bytes(raw)
    if all(p['status']=='prepared' for p in packs):
        (OUT/'history-verification.json').write_bytes(ipa.encode(dict(reportSha256=ipa.sha(raw),questions=sum(p['count'] for p in packs),officialAnswers='pass',originalPixels='pass',method='Official practice grading pages and geography answer cell coordinates matched; every geography page pixel checked; essays use official solution images for self-grading.')))

if __name__=='__main__':main()
