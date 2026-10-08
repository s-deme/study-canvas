"""Archive safety examination originals locally; reject ambiguous answer marks."""
import importlib.util, json, re, sys, subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin
ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
base=module('safety_base','prepare-nonit-material.py')
fetcher=module('safety_fetch','fetch-github-material.py')
SRC,OUT,fitz,norm=base.SRC,base.OUT,base.fitz,base.norm
NAMES={'一級ボイラー技士':'boiler1','二級ボイラー技士':'boiler2','ボイラー整備士':'boiler-maintenance','クレーン・デリック運転士（限定なし）':'crane-derrick','移動式クレーン運転士':'mobile-crane','揚貨装置運転士':'lifting-derrick','第一種衛生管理者':'health1','第二種衛生管理者':'health2','潜水士':'diver'}
def acquire():
    from bs4 import BeautifulSoup
    tasks=[]
    for kind,url in [('license','https://www.exam.or.jp/lckohyo/'),('measure','https://www.exam.or.jp/emkohyo/'),('consult','https://www.exam.or.jp/cskohyo/')]:
        source=fetcher.fetch(url,'safety-'+kind+'.html')
        html=BeautifulSoup((SRC/source['file']).read_bytes(),'html.parser')
        for row in html.find_all('tr'):
            cells=row.find_all('td')
            if not cells:continue
            label=cells[0].get_text(strip=True)
            exam=('boiler-special' if label=='特級ボイラー技士' else NAMES.get(label)) if kind=='license' else 'work-environment1' if kind=='measure' else 'health-consultant' if label.startswith('労働衛生') else 'safety-consultant' if label.startswith('産業安全') else None
            if not exam:continue
            for a in row.find_all('a',href=True):
                feb=re.search(r'/20260217(?:-([2-4]))?/$',a['href']) if kind=='measure' else None
                if not a['href'].lower().endswith('.pdf') and not feb:continue
                link=urljoin(url,a['href']);year=re.search(r'令和(\d+)',a.get_text())[1]
                stem='safety-measure-feb-'+(feb[1] or '1') if feb else 'safety-'+Path(link).stem
                tasks.append(dict(provider='SAFETY',examId=exam,year=str(2018+int(year)),term=a.get_text(strip=True),subject=label,sourceFile=stem+'.pdf',answerFile=stem+'.pdf',file=stem+'.json',url=link,localOnly=True))
                if exam=='boiler-special':tasks[-1].update(kind='special-boiler',year=str(2017+int(year)),term=str(2017+int(year))+'年度実施・正答例付き',subject='特級ボイラー技士 4科目')
                if kind=='measure' and label in ('労働衛生一般','労働衛生関係法令','デザイン・サンプリング','分析に関する概論'):
                    tasks.append({**tasks[-1],'examId':'work-environment2','file':stem+'-second.json'})
    external='https://kouronpub.com/past_issues/boiler/2qboiler_index.html'
    source=fetcher.fetch(external,'safety-external-boiler.html')
    html=BeautifulSoup((SRC/source['file']).read_bytes(),'html.parser')
    for a in html.find_all('a',href=True):
        match=re.search(r'pdf/(\d{4})b_exa\.pdf$',a['href'])
        if not match:continue
        code=match[1]
        if code=='0804':continue  # Same publication as the official April 2026 paper.
        year=(1988 if int(code[:2])>=20 else 2018)+int(code[:2]);link=urljoin(external,a['href']);stem='safety-external-'+code
        tasks.append(dict(provider='SAFETY',kind='external',examId='boiler2',year=str(year),term=f'{code[2:]}月公表',subject='二級ボイラー技士',sourceFile=stem+'.pdf',answerFile=stem+'-answer.pdf',file=stem+'.json',url=link,answerUrl=link.replace('_exa.pdf','_a.pdf'),localOnly=True))
    for kind,exam in [('kou','hazmat-a'),('otsu4','hazmat-b4'),('hei','hazmat-c')]:
        stem='safety-kikenbutsu-'+kind;link='https://www.shoubo-shiken.or.jp/content/kikenbutsu_'+kind+'.pdf'
        tasks.append(dict(provider='SAFETY',kind='hazmat',examId=exam,year='2026',term='2026年6月更新・過去問抜粋（実施年度不明）',subject='危険物取扱者',sourceFile=stem+'.pdf',answerFile=stem+'.pdf',file=stem+'.json',url=link,localOnly=True))
    for suffix,exam in [('kou','fire-a-public'),('otsu','fire-b-public')]:
        stem='safety-shoubou_'+suffix;link='https://www.shoubo-shiken.or.jp/pdf_files/shoubou_'+suffix+'.pdf'
        tasks.append(dict(provider='SAFETY',kind='fire',examId=exam,year='2026',term='2026年6月掲載案内・実施年度不明',subject='消防設備士 筆記公開問題（各類の抜粋）',sourceFile=stem+'.pdf',answerFile=stem+'.pdf',file=stem+'.json',url=link,localOnly=True))
    def download(t):
        sources=[fetcher.fetch(t['url'],t['sourceFile'])]
        if t.get('answerUrl'):sources.append(fetcher.fetch(t['answerUrl'],t['answerFile']))
        return {**t,'sources':sources}
    with ThreadPoolExecutor(max_workers=6) as pool:tasks=list(pool.map(download,tasks))
    (SRC/'safety-discovery.json').write_bytes(base.ipa.encode(tasks))
    print('Downloaded',len(tasks),'papers')

def scanned_review(doc):
    path=SRC/'safety-scanned-review.json'
    if not path.exists() or not doc.name:return None
    review=json.loads(path.read_bytes())
    if Path(doc.name).name!=review['file']:return None
    assert base.ipa.sha(Path(doc.name).read_bytes())==review['sha256'],'Reviewed PDF changed'
    assert len(review['starts'])==len(review['answers'])==45
    return review

def starts(doc,expected=None):
    review=scanned_review(doc)
    if review:return [tuple(row) for row in review['starts']]
    found=[]
    for pn,page in enumerate(doc):
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines',[]):
                text=norm(''.join(s['text'] for s in line['spans'])).strip()
                m=re.match(r'^[\[〔【]?(?:問|問\s*題)\s*(\d+)\s*(?:\D|$)',text)
                if m:found.append((int(m[1]),pn,line['bbox'][1]))
                elif text=='問':
                    words=page.get_text('words')
                    nums=[w for w in words if re.fullmatch(r'\d+',norm(w[4])) and abs(w[1]-line['bbox'][1])<3 and 0<w[0]-line['bbox'][2]<50]
                    if len(nums)==1:found.append((int(norm(nums[0][4])),pn,line['bbox'][1]))
    if expected:found=found[:expected]
    assert found and [n for n,p,y in found]==list(range(1,len(found)+1)),('Question headings',found)
    return found

def keys(doc):
    seq=starts(doc)
    result={};extra={p:extra_marks(doc[p]) for p in range(len(doc))}
    for i,(number,pn,y) in enumerate(seq):
        ep,ey=seq[i+1][1:] if i+1<len(seq) else (len(doc)-1,doc[-1].rect.height)
        body='\n'.join(norm(''.join(s['text'] for s in line['spans'])) for p in range(pn,ep+1) for b in doc[p].get_text('dict')['blocks'] for line in b.get('lines',[]) if (p,line['bbox'][1])>=(pn,y) and (p,line['bbox'][1])<(ep,ey))
        marks=re.findall(r'[○〇◯]\s*\(([1-5])\)',body)
        if not marks:
            marks=[str(a+1) for p in range(pn,ep+1) for a,r in extra[p] if (p,r[1])>=(pn,y-2) and (p,r[1])<(ep,ey-2)]
        assert len(marks)==1,(number,marks)
        result[number]=int(marks[0])-1
    assert result and sorted(result)==list(range(1,len(result)+1))
    return result

def extra_marks(page):
    """Read separately positioned text circles and outlined circles beside option labels."""
    labels=[];circles=[];result=[]
    for block in page.get_text('dict')['blocks']:
        for line in block.get('lines',[]):
            value=norm(''.join(s['text'] for s in line['spans'])).strip()
            m=re.match(r'^\(([1-5])\)|^([1-5])(?:\s|$)',value)
            if m:labels.append((int(m[1] or m[2])-1,fitz.Rect(line['bbox'])))
            if value in '○〇◯' and value:
                circles.extend(fitz.Rect(s['bbox']) for s in line['spans'] if s['text'].strip() in ('○','〇','◯'))
    for rect in circles:
        near=[a for a,r in labels if abs((r.y0+r.y1-rect.y0-rect.y1)/2)<4 and -8<r.x0-rect.x1<15]
        if not near:near=[a for a,r in labels if abs((r.x0+r.x1-rect.x0-rect.x1)/2)<5 and 5<r.y0-rect.y1<18]
        assert len(near)==1,('Separate answer mark',page.number,rect,near)
        result.append((near[0],list(rect)))
    drawings=page.get_drawings()
    vector_labels=[(int(m[1])-1,fitz.Rect(w[:4])) for w in page.get_text('words') if (m:=re.match(r'^([1-5])(?:\s|$)',norm(w[4]).strip()))]
    for answer,label in vector_labels:
        # ponytail: fixed official margin; reject changed PDF layouts instead of guessing.
        if not 80<label.x0<400:continue
        region=fitz.Rect(label.x0-22,label.y0-4,label.x0+.2,label.y1+4)
        pieces=[d['rect'] for d in drawings if region.contains(d['rect']) and (d.get('fill')==(0.0,0.0,0.0) or d.get('color')==(0.0,0.0,0.0))]
        if not pieces:continue
        rect=fitz.Rect(pieces[0])
        for piece in pieces[1:]:rect|=piece
        if not (6<rect.width<15 and 6<rect.height<15 and .8<rect.width/rect.height<1.2):continue
        center=fitz.Rect(rect.x0+rect.width*.35,rect.y0+rect.height*.35,rect.x1-rect.width*.35,rect.y1-rect.height*.35)
        pix=page.get_pixmap(clip=center,colorspace=fitz.csGRAY,alpha=False)
        assert min(pix.samples)>220,('Answer mark is not a hollow circle',page.number,rect)
        result.append((answer,list(rect+(-.5,-.5,.5,.5))))
    review=SRC/'safety-mark-review.json'
    if review.exists() and page.parent.name:
        for item in json.loads(review.read_bytes()):
            if item['file']==Path(page.parent.name).name and item['page']==page.number:
                assert base.ipa.sha(Path(page.parent.name).read_bytes())==item['sha256']
                assert not any(fitz.Rect(r).intersects(fitz.Rect(item['rect'])) for a,r in result),'Duplicate reviewed mark'
                result.append((item['answer'],item['rect']))
    return result

def clean(page,extra=None):
    # Only the official answer circle before an option label is removed.
    rects=[]
    for block in page.get_text('rawdict')['blocks']:
        for line in block.get('lines',[]):
            chars=[c for s in line['spans'] for c in s['chars']]
            for i,c in enumerate(chars):
                if c['c'] in '○〇◯' and re.match(r'\s*\([1-5]\)',norm(''.join(v['c'] for v in chars[i+1:]))):
                    rects.append(list(c['bbox']))
    if extra is None:extra=[r for a,r in extra_marks(page)]
    rects+=extra
    for rect in rects:page.add_redact_annot(rect,fill=(1,1,1))
    if rects:page.apply_redactions(images=0,graphics=2 if extra else 0)
    return rects

def table_keys(doc,kind):
    review=scanned_review(doc)
    if review:return {n:a-1 for n,a in enumerate(review['answers'],1)}
    if kind in ('hazmat','fire'):
        page=next(p for p in doc if '問題番号' in p.get_text() and '解答' in p.get_text())
        numbers=re.findall(r'^\s*(\d+)\s*$',norm(page.get_text()),re.M)
        assert len(numbers)%2==0
        result={int(n):int(a)-1 for n,a in zip(numbers[::2],numbers[1::2])}
    else:
        result={}
        for page in doc:
            words=page.get_text('words')
            if not any(re.fullmatch('[1-5]',norm(w[4])) for w in words):continue
            for w in words:
                m=re.fullmatch(r'問\s*(\d+)',norm(w[4]))
                if not m:continue
                values=[v for v in words if abs((v[0]+v[2]-w[0]-w[2])/2)<12 and 0<v[1]-w[3]<85 and re.fullmatch('[1-5]',norm(v[4]))]
                if values:values=[v for v in values if abs(v[1]-min(x[1] for x in values))<2]
                assert len(values)==1,(w,values)
                result[int(m[1])]=int(norm(values[0][4]))-1
    assert result and sorted(result)==list(range(1,len(result)+1)) and all(0<=a<5 for a in result.values())
    return result

def special_rows(task):
    doc=fitz.open(SRC/task['sourceFile']);stem=Path(task['file']).stem
    covers=[p.number for p in doc if norm(p.get_text()).startswith('特級ボイラー技士免許試験問題')]
    solutions=[p.number for p in doc if re.search(r'(構造|取扱|燃料|法令)正答例1/',norm(p.get_text()))]
    assert len(covers)==len(solutions)==4
    rows=[];evidence=[];cache={}
    for group,cover in enumerate(covers):
        end=covers[group+1] if group<3 else solutions[0]
        part=fitz.open();part.insert_pdf(doc,from_page=cover+1,to_page=end-1)
        seq=starts(part);assert len(seq)==6
        subject=norm(doc[cover].get_text()).splitlines()[1]
        answer_end=solutions[group+1] if group<3 else len(doc)
        answer_pictures=[base.picture(doc,p,stem,cache) for p in range(solutions[group],answer_end)]
        for i,(number,pn,y) in enumerate(seq):
            last=seq[i+1][1] if i<5 else len(part)
            pictures=[base.picture(doc,p+cover+1,stem,cache) for p in range(pn,last)]
            assert pictures
            title=f'{task["year"]}年 特級ボイラー技士 {subject} 問{number}'
            q=dict(id=stem+f'-q{group*6+number:03}',examId=task['examId'],type='written',year=task['year'],term=task['term'],subject=subject,category='過去問',topic=title,prompt=title+'\n原本画像の該当問題を解答し、公式正答・正答例で自己採点してください。',options=[],answer=None,modelAnswer=f'{subject} 問{number}の公式正答・正答例は解答画像を参照してください。',images=[x[0] for x in pictures],solutionImages=[x[0] for x in answer_pictures],source='安全衛生技術試験協会 公式公表問題・正答例（本人用）',sourceUrl=task['url'],explanation='原本の数式・図表を保持しています。公表当時の法令・制度が前提です。',explanationSource='公式PDFの正答・正答例')
            rows.append(q);evidence.append(dict(id=q['id'],number=group*6+number,answer=None,images=[x[1] for x in pictures],solutionImages=[x[1] for x in answer_pictures]))
    return rows,evidence

def prepare(task):
    task={**task,'verificationLabel':('提供元掲載正答表・問題番号・原本画像の画素一致を検査（公論出版の正答、全問目視・理由解説は未実施）' if task.get('kind')=='external' else '公式正答・問題番号・画像を検査。正答印付き資料は印のみ除去した演習画像と原本解答画像を保持（全問目視・理由解説は未実施）')}
    try:
        if task.get('kind')=='special-boiler':
            rows,evidence=special_rows(task)
            task['verificationLabel']='公式問題24問・4科目と正答例画像を照合。原本画像で自己採点（全問目視・理由解説は未実施）'
            return base.finish(task,rows,evidence,[])
        doc=fitz.open(SRC/task['sourceFile'])
        kind=task.get('kind');answers=table_keys(fitz.open(SRC/task['answerFile']),kind) if kind else keys(doc)
        seq=starts(doc,len(answers) if kind=='fire' else None)
        assert set(answers)=={n for n,p,y in seq}
        original=fitz.open(SRC/task['sourceFile']);stem=Path(task['file']).stem
        cache={};rows=[];evidence=[]
        for i,(number,pn,y) in enumerate(seq):
            ep=seq[i+1][1] if i+1<len(seq) else pn if kind=='fire' else len(doc)-2 if kind=='hazmat' else len(doc)-1
            if i+1<len(seq) and seq[i+1][2]<65:ep-=1
            images=[];solutions=[];records=[];solution_records=[]
            for p in range(pn,ep+1):
                if p not in cache:
                    solution,srecord=base.picture(original,p,stem+'-answer',{})
                    removed=clean(doc[p]) if not kind else []
                    image,record=base.picture(doc,p,stem+'-question',{})
                    cache[p]=(image,{**record,'removedMarks':removed},solution,srecord)
                image,record,solution,srecord=cache[p]
                images.append(image);records.append(record);solutions.append(solution);solution_records.append(srecord)
            title=f'{task["year"]}年 {task["subject"]} {task["term"]} 問{number}'
            q=dict(id=stem+f'-q{number:03}',examId=task['examId'],type='single',year=task['year'],term=task['term'],subject=task['subject'],category='過去問',topic=title,prompt=title+'\n画像の該当問題番号を解答してください。演習画像は正答の丸印のみ除去しています。',options=list('12345'),answer=answers[number],images=images,solutionImages=solutions,source='安全衛生技術試験協会 公式公表問題（本人用）',sourceUrl=task['url'],explanation=f'公式正答：{answers[number]+1}。理由解説は未収録です。公表時点の法令・制度を前提とします。',explanationSource='公式PDFの正答印')
            rows.append(q);evidence.append(dict(id=q['id'],number=number,answer=q['answer'],images=records,solutionImages=solution_records))
            if kind:
                q['prompt']=title+'\n原本画像の該当問題番号を解答してください。'
                q['solutionImages']=[];evidence[-1]['solutionImages']=[]
                q['source']='消防試験研究センター 公式公開過去問' if kind in ('hazmat','fire') else '公論出版 公開過去問・掲載正答（本人用・再配布禁止）'
                if kind=='fire':q['options']=list('1234')
                q['explanationSource']=q['source']
                q['explanation']=f'掲載正答：{answers[number]+1}。理由解説は未収録です。問題公表当時の制度・法令を前提とします。'
        return base.finish(task,rows,evidence,[])
    except Exception as error:return {**task,'status':'pending-review','reason':str(error)}

def main():
    sys.stdout.reconfigure(encoding='utf-8');(OUT/'assets').mkdir(exist_ok=True)
    if '--verification' in sys.argv:
        raw=(OUT/'safety-report.json').read_bytes();report=json.loads(raw)
        cache=json.loads((OUT/'verification-cache.json').read_bytes());count=0
        for pack in report['packs']:
            if pack['status']!='prepared':continue
            fingerprint=base.ipa.sha(json.dumps(pack,ensure_ascii=False,sort_keys=True).encode())
            if cache.get(pack['file'])!=fingerprint:
                subprocess.run([sys.executable,str(Path(__file__)),'--verify',pack['file']],check=True)
                cache[pack['file']]=fingerprint
                (OUT/'verification-cache.json').write_text(json.dumps(cache),encoding='utf-8')
            assert base.ipa.sha((OUT/pack['file']).read_bytes())==pack['sha256']
            for source in pack['sources']:assert base.ipa.sha((SRC/source['file']).read_bytes())==source['sha256']
            for q in pack['questions']:
                for record in q['images']+q['solutionImages']:assert base.ipa.sha((OUT/'assets'/record['file']).read_bytes())==record['sha256']
            count+=pack['count']
        (OUT/'safety-verification.json').write_bytes(base.ipa.encode(dict(reportSha256=base.ipa.sha(raw),questions=count,officialAnswers='pass',originalPixels='pass',method='Per-paper isolated --verify checks; verified fingerprints and all source/pack/image hashes rechecked. Publisher answers identified separately.')))
        print('PASS: safety verified',count);return
    if '--verify' in sys.argv:
        from PIL import Image
        pack=next(p for p in json.loads((OUT/'safety-report.json').read_bytes())['packs'] if p.get('file')==sys.argv[-1])
        data=(OUT/pack['file']).read_bytes();assert base.ipa.sha(data)==pack['sha256']
        for source in pack['sources']:assert base.ipa.sha((SRC/source['file']).read_bytes())==source['sha256']
        doc=fitz.open(SRC/pack['sourceFile']);ans=fitz.open(SRC/pack['answerFile'])
        special=pack.get('kind')=='special-boiler'
        if special:
            expected,evidence=special_rows(pack)
            assert json.loads(data)==expected and pack['questions']==evidence
            answers={n:None for n in range(1,25)}
        else:
            answers=table_keys(ans,pack['kind']) if pack.get('kind') else keys(ans)
            seq=starts(doc,len(answers) if pack.get('kind')=='fire' else None)
            assert set(answers)=={n for n,p,y in seq}
        rows=json.loads(data);assert len(rows)==len(pack['questions'])==pack['count']==len(answers)
        seen=set()
        for q,e in zip(rows,pack['questions']):
            assert q['id']==e['id'] and q['answer']==e['answer']==answers[e['number']]
            assert q['examId']==pack['examId'] and q['sourceUrl']==pack['url'] and q['year']==pack['year']
            if special:assert q['type']=='written' and q['modelAnswer'] and q['solutionImages']
            else:assert 0<=q['answer']<len(q['options'])
            for image,record in zip(q['images']+q['solutionImages'],e['images']+e['solutionImages']):
                assert image['src']=='assets/github-material/'+record['file']
                if record['file'] in seen:continue
                seen.add(record['file']);path=OUT/'assets'/record['file'];assert base.ipa.sha(path.read_bytes())==record['sha256']
                page=doc[record['page']]
                if record.get('removedMarks'):
                    copy=fitz.open();copy.insert_pdf(doc,from_page=page.number,to_page=page.number)
                    assert clean(copy[0],[r for a,r in extra_marks(page)])==record['removedMarks'];page=copy[0]
                pix=page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False)
                with Image.open(path) as image:assert image.size==(pix.width,pix.height) and image.convert('RGB').tobytes()==pix.samples,record['file']
        return
    if '--fetch' in sys.argv:return acquire()
    previous={p['file']:p for p in json.loads((OUT/'safety-report.json').read_bytes())['packs']} if '--retry' in sys.argv else {}
    packs=[previous[t['file']] if previous.get(t['file'],{}).get('status')=='prepared' else prepare(t) for t in json.loads((SRC/'safety-discovery.json').read_bytes())]
    (OUT/'safety-report.json').write_bytes(base.ipa.encode({'packs':packs}))
    for p in packs:print(p['file'],p['status'],p.get('count',p.get('reason')))
if __name__=='__main__':main()
