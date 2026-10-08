"""Archive official mathematics/statistics papers, preserving equations as images."""
import json,re,sys
from pathlib import Path
from urllib.parse import urljoin,urlparse,parse_qs
from concurrent.futures import ThreadPoolExecutor
from importlib import import_module
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
h=import_module('prepare-history-material')
ipa,nonit,fetch,fitz,SRC,OUT=h.ipa,h.nonit,h.fetch,h.fitz,h.SRC,h.OUT
from bs4 import BeautifulSoup

def acquire():
    fetch.fetch('https://www.su-gaku.net/suken/support/past_questions/','math-suken-index.html')
    fetch.fetch('https://www.toukei-kentei.jp/preparation/kakomon/','math-statistics-index.html')
    tasks=[]
    for a in h.soup('math-suken-index.html').find_all('a',href=True):
        u=a['href'];f=parse_qs(urlparse(u).query).get('file',[''])[0]
        m=re.search(r'(j?\d+)q_que(?:_(\d)ji)?\.pdf$',f)
        if not m:continue
        grade=m[1];exam='suken-'+('pre'+grade[1:] if grade.startswith('j') else grade)
        if not grade.startswith('j'):exam='suken'+grade
        stem='math-suken-'+grade+('-'+m[2]+'ji' if m[2] else '')
        tasks.append(dict(examId=exam,subject=a.get_text(strip=True).split('：')[0],stem=stem,url=urljoin(u,f),answerUrl=urljoin(u,f.replace('_que','_ans')),year='',term='公式公開過去問（実施年度不明）'))
    for a in h.soup('math-statistics-index.html').find_all('a',href=True):
        if re.search(r'202511grade1(?:suri|ouyo)\.pdf$',a['href']):
            u=a['href'];s='suri' if 'suri.pdf' in u else 'ouyo'
            ans='ans2025n_grade1'+s+('_2' if s=='suri' else '_3')+'.pdf'
            tasks.append(dict(examId='statistics1',subject='統計数理' if s=='suri' else '統計応用',stem='math-statistics1-202511-'+s,url=u,answerUrl=urljoin(u,ans),year='2025',term='11月'))
    for exam,g,ans in [('statistics-ds-advanced','12','sample_answer'),('statistics-ds-expert','13','sample_answer'),('statistics-ds-basic','11','sample_answer_and_tips')]:
        base='https://www.toukei-kentei.jp/hubfs/files/grade/grade'+g+'_'
        tasks.append(dict(examId=exam,subject=exam,stem='math-'+exam+'-sample',url=base+'sample_exercises.pdf',answerUrl=base+ans+'.pdf',year='',term='公式サンプル（本試験過去問とは区別）',kind='sample'))
    base='https://www.su-gaku.net/suken/wp-content/themes/su-ken/pdf/support/past_question/pdfjs/web/en2023/'
    for grade in ['1','j1','2','j2']:
        for section in ['1','2']:
            tasks.append(dict(examId='suken-pre'+grade[1:]if grade.startswith('j')else'suken'+grade,subject=('準'+grade[1:]+'級'if grade.startswith('j')else grade+'級')+' '+section+'次（英語版）',stem='math-suken-en-'+grade+'-'+section+'ji',url=base+grade+'q_que_'+section+'ji.pdf',answerUrl=base+grade+'q_ans_'+section+'ji.pdf',year='',term='英語版公式公開過去問（実施年度不明）'))
    def get(t):
        t.update(provider='MATH',kind=t.get('kind','past'),localOnly=True,file=t['stem']+'.json',sourceFile=t['stem']+'.pdf',answerFile=t['stem']+'-answer.pdf')
        t['sources']=[fetch.fetch(t['url'],t['sourceFile']),fetch.fetch(t['answerUrl'],t['answerFile'])]
        return t
    with ThreadPoolExecutor(max_workers=4) as pool:tasks=list(pool.map(get,tasks))
    (SRC/'math-discovery.json').write_bytes(ipa.encode({'tasks':tasks}))

def suken_units(t,d,a):
    main=[];leaves=[]
    for p in range(1,7):
        for text,b in h.tourism.native_lines(d[p]):
            text=ipa.norm(text).strip();m=re.match(r'^問題(\d+)\.',text)
            if m:main.append((int(m[1]),p,b[1]))
            elif re.fullmatch(r'\d+',text) and b[0]<85 and b[2]-b[0]>17:main.append((int(text),p,b[1]))
            m=re.match(r'^\((\d+)\)',text)
            if m and b[0]<400 and not text[m.end():].startswith(','):leaves.append((int(m[1]),p,b[1]))
    main=sorted(set(main),key=lambda x:(x[1],x[2]));assert [n for n,p,y in main]==list(range(1,len(main)+1)),t['stem']
    # Upper grades repeat branch numbers in each big question; retain those as one complete question.
    split=t['examId'] not in ('suken1','suken-pre1','suken2')
    if split:
        expected=set(map(int,re.findall(r'\((\d+)\)',ipa.norm(''.join(p.get_text() for p in a)))))
        found={n for n,p,y in leaves};assert found==expected==set(range(1,max(expected)+1)),(t['stem'],expected-found,found-expected)
        leaves=sorted(set(leaves),key=lambda x:(x[1],x[2]));unique={}
        for n,p,y in leaves:
            group=max((x for x in main if (x[1],x[2])<=(p,y)),key=lambda x:(x[1],x[2]))
            if n in unique:assert unique[n][0]==group[0]
            unique[n]=(group[0],p,y)
        units=[(g,n,p) for n,(g,p,y) in sorted(unique.items())]
    else:units=[(g,None,p)for g,p,y in main]
    result=[]
    for g,n,p in units:
        i=next(i for i,x in enumerate(main) if x[0]==g);start=main[i][1]
        end=main[i+1][1] if i+1<len(main) else 6
        # Whole shared pages preserve diagrams and preceding conditions; no inferred equation transcription.
        pages=list(range(start,end+1));label='問題'+str(g)+(('（'+str(n)+'）')if n else '')
        result.append(dict(number=str(n or g),label=label,pages=pages,answers=list(range(len(a))),subject=t['subject']))
    return result

def units(t,d,a):
    if t['stem'].startswith('math-suken-en-'):
        if t['examId']=='suken-pre2':
            heads=[]
            for p in range(1,len(d)):
                for text,b in h.tourism.native_lines(d[p]):
                    m=re.match(r'^\((\d+)\)',text.strip())
                    if m and b[0]<100:heads.append(int(m[1]))
            expected=15 if '1次'in t['subject']else 10
            assert heads==list(range(1,expected+1))
            answer_numbers=set(map(int,re.findall(r'\((\d+)\)',ipa.norm(''.join(p.get_text()for p in a)))))
            if expected==15:
                # Answer-sheet page 2 labels (11)..(15) were visually checked; its embedded text splits digits.
                assert answer_numbers==set(range(1,11))and len(a)==2
                assert ipa.sha((SRC/t['answerFile']).read_bytes())=='f66fd3162811338e8856db81b3f8565f62f027b0e0dd71e15a229cac1d75f405'
            else:assert set(heads)==answer_numbers
            return [dict(number=str(n),label='('+str(n)+')',pages=list(range(1,len(d))),answers=list(range(len(a))),subject=t['subject'])for n in heads]
        heads=[]
        for p in range(1,len(d)):
            for text,b in h.tourism.native_lines(d[p]):
                text=text.strip()
                if re.fullmatch(r'\d+',text)and 55<=b[0]<=85 and b[2]<100:heads.append((int(text),p,b[1]))
        heads=sorted(set(heads),key=lambda x:(x[1],x[2]));expected=15 if t['examId']=='suken2'and '1次'in t['subject']else 7
        assert [n for n,p,y in heads]==list(range(1,expected+1)),heads
        return [dict(number=str(n),label='Question '+str(n),pages=list(range(p,(heads[i+1][1]if i+1<len(heads)else len(d)-1)+1)),answers=[n-1]if '2次'in t['subject']else list(range(len(a))),subject=t['subject'])for i,(n,p,y)in enumerate(heads)]
    if t['stem'].startswith('math-suken'):return suken_units(t,d,a)
    if t['examId']=='statistics1':
        if t['subject']=='統計応用':
            def shared_text(p):
                text=''.join(d[i].get_text().split('\n',1)[1]for i in [p,p+1])
                return re.sub(r'\s+','',re.sub('\u0ef0[1-5]','',text))
            for first,duplicate in [(3,15),(9,31),(11,23),(11,35),(11,47)]:
                assert shared_text(first)==shared_text(duplicate),'Application questions differ'
        groups=[('統計数理',0)]if t['subject']=='統計数理' else [('人文科学',0),('社会科学',12),('理工学',24),('医薬生物学',36)]
        out=[]
        for gi,(subject,offset) in enumerate(groups):
            for n in range(1,6):
                # Officially shared questions are included once across the four application fields.
                if t['subject']=='統計応用' and ((gi>0 and n==5)or(gi==1 and n==1)or(gi==2 and n==3)):continue
                p=offset+2*n+1;assert '\u0ef0'+str(n) in d[p].get_text()[:60],(p,n)
                answers=list(range(len(a)))if t['subject']=='統計数理' else [gi*2,gi*2+1]
                text=ipa.norm(''.join(a[x].get_text() for x in answers));assert re.search(r'問\s*'+str(n),text)
                tables=list(range(15,20))if t['subject']=='統計数理' else list(range(51,56))
                out.append(dict(number=subject+'-'+str(n),label=subject+' 問'+str(n),pages=[p,p+1]+tables,answers=answers,subject=subject))
        return out
    if t['examId']=='statistics-ds-advanced':
        out=[];heads=[]
        for p,page in enumerate(d):
            for text,b in h.tourism.native_lines(page):
                m=re.fullmatch(r'問\s*(\d+)',ipa.norm(text).strip())
                if m:heads.append((int(m[1]),p))
        assert [n for n,p in heads]==list(range(1,9))
        for i,(n,p) in enumerate(heads):
            end=heads[i+1][1]if i+1<len(heads)else len(d)-1
            assert re.search(r'問\s*'+str(n),ipa.norm(''.join(x.get_text()for x in a)))
            out.append(dict(number=str(n),label='問'+str(n),pages=list(range(p,end+1)),answers=list(range(1,len(a))),subject='DS発展'))
        return out
    if t['examId']=='statistics-ds-expert':
        return [dict(number=str(n),label='問題'+str(n),pages=list(range((n-1)*4,n*4)),answers=[(n-1)*2,(n-1)*2+1],subject='DSエキスパート')for n in(1,2)]
    raise ValueError('DS基礎は数値の完全な公式解答がなく、外部データ操作が必要なため保留')

def prepare(t):
    d=fitz.open(SRC/t['sourceFile']);a=fitz.open(SRC/t['answerFile']);rows=[];evidence=[];cache={};acache={}
    for i,u in enumerate(units(t,d,a),1):
        images,records=map(list,zip(*(nonit.picture(d,p,t['stem'],cache)for p in u['pages'])))
        answers,arecords=map(list,zip(*(nonit.picture(a,p,t['stem']+'-answer',acache)for p in u['answers'])))
        label=t['subject']+' '+u['label'];q=dict(id=t['stem']+f'-q{i:03}',examId=t['examId'],type='essay',year=t['year'],term=t['term'],subject=u['subject'],category='公式サンプル'if t['kind']=='sample'else'過去問',topic=label,prompt=label+'\n原本画像の該当する問番号に解答してください。指定された小問番号がある場合はその小問に、ない場合は枝問すべてに回答してください。',images=images,solutionImages=answers,modelAnswer='公式解答画像の「'+u['label']+'」と照合して自己採点してください。数式・証明・作図の表記は原本を参照してください。',sourceUrl=t['url'],source='公式公開PDF。本人用ローカル教材。',explanation='公式解答は解答後に表示します。自己採点形式です。',explanationSource=t['answerUrl'])
        rows.append(q);evidence.append(dict(id=q['id'],number=u['number'],answer=None,images=records,solutionImages=arecords))
    checked=set()
    for e in evidence:
        for key,doc in [('images',d),('solutionImages',a)]:
            for r in e[key]:
                if r['file']in checked:continue
                pix=doc[r['page']].get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False)
                with h.Image.open(OUT/'assets'/r['file'])as im:assert im.convert('RGB').tobytes()==pix.samples
                assert ipa.sha((OUT/'assets'/r['file']).read_bytes())==r['sha256'];checked.add(r['file'])
    for s in t['sources']:assert ipa.sha((SRC/s['file']).read_bytes())==s['sha256']
    return nonit.finish({**t,'verificationLabel':'公式問題・解答番号対応と原本画像の画素一致を検査。数式・証明は自己採点。全問の目視確認は未実施。'},rows,evidence,[])

def main():
    (OUT/'assets').mkdir(exist_ok=True)
    if '--fetch'in sys.argv:acquire();return
    baseline=SRC/'math-baseline.json'
    if not baseline.exists():baseline.write_bytes(ipa.encode({p['id']:p['sha256']for p in json.loads((ROOT/'build/private/manifest.json').read_bytes())['packs']}))
    packs=[]
    for t in json.loads((SRC/'math-discovery.json').read_bytes())['tasks']:
        try:p=prepare(t)
        except Exception as e:p={**t,'status':'pending-review','reason':str(e)or repr(e)}
        print(t['stem'],p['status'],p.get('count',p.get('reason')));packs.append(p)
    raw=ipa.encode({'packs':packs});(OUT/'math-report.json').write_bytes(raw)
    ready=[p for p in packs if p['status']=='prepared']
    (OUT/'math-verification.json').write_bytes(ipa.encode(dict(reportSha256=ipa.sha(raw),questions=sum(p['count']for p in ready),officialAnswers='pass',originalPixels='pass',method='Only prepared packs: original numbered problem headings matched to official solution labels; every problem and solution image checked against original PDF pixels. Essays are self-assessed.')))

if __name__=='__main__':main()
