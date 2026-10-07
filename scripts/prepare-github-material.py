"""Prepare image-faithful IPA question packs; ambiguous OCR remains unregistered."""
import concurrent.futures, hashlib, json, os, re, sys, unicodedata, statistics
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build/python-deps'))
import pymupdf as fitz
from PIL import Image, ImageChops

SRC = ROOT / 'private-data/github-material'
OUT = SRC / 'prepared'
LETTERS = 'アイウエオカキクケコ'
sha = lambda data: hashlib.sha256(data).hexdigest()
norm = lambda text: unicodedata.normalize('NFKC', text)
encode = lambda value: json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
NAMES = dict(ip='ITパスポート',sg='情報セキュリティマネジメント',fe='基本情報技術者',ap='応用情報技術者',st='ITストラテジスト',sa='システムアーキテクト',pm='プロジェクトマネージャ',nw='ネットワークスペシャリスト',db='データベーススペシャリスト',es='エンベデッドシステムスペシャリスト',sm='ITサービスマネージャ',au='システム監査技術者',sc='情報処理安全確保支援士')

def layout(doc, pn, force_ocr=False):
    page = doc[pn]
    if not force_ocr and page.get_text().strip():
        return page.get_text('dict'), 'native'
    cache = SRC / 'ocr' / f'{Path(doc.name).name}-{pn}.json'
    if cache.exists():
        return json.loads(cache.read_text(encoding='utf-8')), 'ocr'
    old = ROOT / 'private-data/ipa/ocr' / cache.name
    original = ROOT / 'private-data/ipa' / Path(doc.name).name
    if old.exists() and original.exists() and sha(original.read_bytes()) == sha(Path(doc.name).read_bytes()):
        return json.loads(old.read_text(encoding='utf-8')), 'ocr'
    # Only the question-number/option-label margin needs OCR; bodies stay as original pixels.
    rect = fitz.Rect(35, 38, min(145, page.rect.width), page.rect.height - 38)
    pix = page.get_pixmap(dpi=180, clip=rect, alpha=False)
    ocr = fitz.open(stream=pix.pdfocr_tobytes(language='jpn+eng', tessdata=str(ROOT/'build/tessdata')), filetype='pdf')
    data = ocr[0].get_text('dict')
    data['blocks'] = [block for block in data['blocks'] if block.get('type')==0]
    sx, sy = rect.width / ocr[0].rect.width, rect.height / ocr[0].rect.height
    for block in data['blocks']:
        for line in block.get('lines', []):
            x0, y0, x1, y1 = line['bbox']
            line['bbox'] = [rect.x0+x0*sx, rect.y0+y0*sy, rect.x0+x1*sx, rect.y0+y1*sy]
    cache.write_bytes(encode(data))
    return data, 'ocr'

def lines(data):
    return [line for block in data['blocks'] for line in block.get('lines', [])]

def number_glyph(page, x, y):
    rect=fitz.Rect(x-3,y-5,x+12,y+16)
    pix=page.get_pixmap(matrix=fitz.Matrix(3,3),clip=rect,colorspace=fitz.csGRAY,alpha=False)
    image=Image.frombytes('L',(pix.width,pix.height),pix.samples).point(lambda v:255 if v<160 else 0)
    # Keep the first connected glyph; question numerals must not affect the comparison.
    occupied=[any(image.getpixel((xx,yy)) for yy in range(image.height)) for xx in range(image.width)]
    left=next((i for i,v in enumerate(occupied) if v),None)
    if left is None:return None
    right=left+1
    while right<len(occupied) and occupied[right]:right+=1
    image=image.crop((left,0,right,image.height));box=image.getbbox()
    return image.crop(box).resize((20,24)) if box else None

def markers(doc,layouts):
    recognized=[];candidates=[];templates=[]
    for pn,(data,method) in layouts.items():
        for line in lines(data):
            text=norm(''.join(s['text'] for s in line['spans'])).strip();x,y=line['bbox'][:2]
            match=re.match(r'^[問間]\s*(\d+)(?:\D|$)',text)
            if match and x<95:recognized.append((int(match[1]),pn,x,y,method))
            if 45<x<75 and 45<y<doc[pn].rect.height-45:
                candidates.append((pn,x,y,method))
    if not recognized:return [],[]
    anchor=statistics.median(x for _,_,x,_,_ in recognized)
    anchors={pn:statistics.median(x for _,p,x,_,_ in recognized if p==pn) for pn in layouts if any(p==pn for _,p,_,_,_ in recognized)}
    for _,pn,x,y,method in recognized:
        if method=='ocr' and abs(x-anchors.get(pn,anchor))<4:
            glyph=number_glyph(doc[pn],x,y)
            if glyph is not None:templates.append(glyph)
    starts=[];comparisons=[]
    for pn,x,y,method in candidates:
        if abs(x-anchors.get(pn,anchor))>4:continue
        exact=[n for n,p,xx,yy,_ in recognized if p==pn and abs(yy-y)<1 and abs(xx-x)<1]
        if method=='native':
            if exact:starts.append((exact[0],pn,y))
            continue
        glyph=number_glyph(doc[pn],x,y)
        if glyph is None:continue
        distance=min((sum(ImageChops.difference(glyph,t).getdata())/(255*480) for t in templates),default=1)
        if distance<0.18:
            starts.append((exact[0] if exact else None,pn,y));comparisons.append({'page':pn,'x':x,'y':y,'distance':distance})
    starts.sort(key=lambda marker:(marker[1],marker[2]))
    return starts,comparisons

def answer_keys(doc):
    text = norm('\n'.join(page.get_text() for page in doc))
    keys = {int(n): LETTERS.index(a) for n, a in re.findall(r'問\s*(\d+)\s*(['+LETTERS+'])', text)}
    # Independently match each official table row by geometry, not PDF reading order.
    cells = {}
    for page in doc:
        rows = lines(page.get_text('dict'))
        for line in rows:
            label = norm(''.join(s['text'] for s in line['spans'])).strip()
            match = re.fullmatch(r'問\s*(\d+)', label)
            if not match:
                continue
            x0,y0,x1,y1 = line['bbox']
            answers = [norm(''.join(s['text'] for s in other['spans'])).strip() for other in rows
                       if abs((other['bbox'][1]+other['bbox'][3]-y0-y1)/2)<3.5 and 0<other['bbox'][0]-x1<85]
            answers = [a for a in answers if a in LETTERS and len(a)==1]
            assert len(answers)==1, ('ambiguous official answer cell', label, answers)
            cells[int(match[1])] = LETTERS.index(answers[0])
    assert cells and sorted(cells)==list(range(1,max(cells)+1)), 'official answer mismatch'
    if sorted(keys)==sorted(cells):assert keys==cells,'official answer mismatch'
    return cells

def prepare(task):
    pair, existing = task
    name = pair['file']
    result = {k:v for k,v in pair.items() if k not in ('question','answer')}
    if pair['status'] != 'downloaded':
        return {**result, 'status': 'pending-download'}
    try:
        for source in (pair['question'], pair['answer']):
            assert sha((SRC/source['file']).read_bytes())==source['sha256'], 'source changed'
        doc = fitz.open(SRC/name)
        answers = answer_keys(fitz.open(SRC/pair['answerFile']))
        prior = set(existing.get(name, []))
        if set(answers) <= prior:
            return {**result, 'status': 'already-registered', 'excluded':len(answers)}
        layouts = {}
        for pn in range(1, len(doc)):
            data, method = layout(doc, pn)
            layouts[pn] = (data,method)
        starts,comparisons = markers(doc,layouts)
        assert len(starts)==len(answers), ('question markers mismatch',len(starts),len(answers),[n for n,_,_ in starts])
        if comparisons:
            # The official count plus glyph/left-margin geometry determines the sequence;
            # OCR numeral guesses are recorded but never silently treated as authoritative.
            starts=[(i+1,pn,y) for i,(_,pn,y) in enumerate(starts)]
        else:
            assert [n for n,_,_ in starts]==sorted(answers),'native question sequence mismatch'
        rows, evidence, excluded = [], [], 0
        for index,(number,pn,y) in enumerate(starts):
            if number in prior:
                excluded += 1
                continue
            ep,ey = (starts[index+1][1],starts[index+1][2]-3) if index+1<len(starts) else (len(doc)-1,doc[-1].rect.height-45)
            images, checks, text = [], [], []
            for page_number in range(pn,ep+1):
                page = doc[page_number]
                top = y-4 if page_number==pn else 38
                bottom = ey if page_number==ep else page.rect.height-45
                if bottom <= top:
                    continue
                rect = fitz.Rect(0,top,page.rect.width,bottom)
                image_name = name[:-7]+f'-q{number:03}-{page_number+1}.png'
                path = OUT/'assets'/image_name
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),clip=rect,alpha=False)
                pix.save(path)
                images.append({'src':'assets/github-material/'+image_name,'alt':f'{pair["year"]} {NAMES[pair["examId"]]} {pair["subject"]} 問{number} 原本 {page_number+1}ページ'})
                checks.append({'file':image_name,'sha256':sha(path.read_bytes()),'page':page_number,'rect':list(rect)})
                if layouts[page_number][1]=='native':
                    text.extend(norm(''.join(s['text'] for s in line['spans'])) for line in lines(layouts[page_number][0]) if top<=line['bbox'][1]<bottom)
            assert images and len(images)<=30, 'image count'
            option_count = 4
            if pair['examId']=='sg' and pair['subject']=='公開問題' or pair['examId']=='fe' and pair['subject']=='科目B':
                labels = re.findall(r'^\s*(['+LETTERS+r'])(?:\s|$)', '\n'.join(text), re.M)
                assert labels and set(labels)==set(LETTERS[:max(LETTERS.index(a) for a in labels)+1]), 'ambiguous option labels'
                option_count = max(LETTERS.index(a) for a in labels)+1
            assert answers[number] < option_count, 'answer out of options'
            title = f'{pair["year"]}年度 {pair["term"]} {NAMES[pair["examId"]]} {pair["subject"]} 問{number}'
            body = '\n'.join(text).strip()
            question = dict(id=name[:-7]+f'-q{number:03}',examId=pair['examId'],type='single',year=pair['year'],term=pair['term'],subject=pair['subject'],category='過去問',topic=title,
                            prompt=title+'\n原本画像の該当問題を解答してください。選択肢の内容は画像に記載されています。',
                            passage=body if body else '',options=list(LETTERS[:option_count]),answer=answers[number],images=images,
                            explanation='公式解答：'+LETTERS[answers[number]]+'。理由解説は未収録です。\n過去問は実施当時の制度・規格を前提とします。',
                            source='出典：IPA '+title+'（原本画像・本文変更なし）',sourceUrl=pair['url'],explanationSource='IPA公式解答（理由解説なし）')
            rows.append(question)
            evidence.append({'id':question['id'],'number':number,'answer':question['answer'],'images':checks})
        pack_name = name[:-7]+'.json'
        raw = encode(rows)
        (OUT/pack_name).write_bytes(raw)
        return {**result,'status':'prepared','file':pack_name,'sourceFile':name,'count':len(rows),'sha256':sha(raw),'excluded':excluded,
                'sources':[pair['question'],pair['answer']],'questions':evidence,'markerChecks':comparisons}
    except Exception as error:
        return {**result,'status':'pending-review','reason':str(error)}

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    os.environ['OMP_THREAD_LIMIT']='1'
    (OUT/'assets').mkdir(parents=True,exist_ok=True)
    (SRC/'ocr').mkdir(exist_ok=True)
    baseline_file = SRC/'baseline.json'
    if not baseline_file.exists():
        manifest = json.loads((ROOT/'build/private/manifest.json').read_text(encoding='utf-8'))
        baseline = {'manifest':manifest,'packs':{}}
        for pack in manifest['packs']:
            data=(ROOT/'build/private/web'/pack['url']).read_bytes()
            baseline['packs'][pack['id']]={'sha256':sha(data),'rows':json.loads(data)}
        baseline_file.write_bytes(encode(baseline))
    baseline = json.loads(baseline_file.read_text(encoding='utf-8'))
    existing = {}
    for pack in baseline['packs'].values():
        for q in pack['rows']:
            source = Path(urlparse(q.get('sourceUrl','')).path).name
            match = re.search(r'-q(\d+)$',q['id'])
            if source.endswith('_qs.pdf') and match:
                existing.setdefault(source,[]).append(int(match[1]))
    discovery = json.loads((SRC/'discovery.json').read_text(encoding='utf-8'))
    report = {'baselineQuestions':baseline['manifest']['questions'],'discovery':discovery['discovery'],'packs':[]}
    if '--retry-pending' in sys.argv:
        previous=json.loads((OUT/'report.json').read_text(encoding='utf-8'))
        pending={p['file'] for p in previous['packs'] if p['status']=='pending-review'}
        retained=[p for p in previous['packs'] if p['status']!='pending-review']
        report['packs']=retained
        selected=[p for p in discovery['pairs'] if p['file'] in pending]
    else:selected=discovery['pairs']
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        for index,result in enumerate(pool.map(prepare, ((p,existing) for p in selected),chunksize=1)):
            report['packs'].append(result)
            if (index+1)%10==0:
                print('Prepared/reviewed',index+1,'/',len(selected),flush=True)
                (OUT/'report.json').write_bytes(encode(report))
    (OUT/'report.json').write_bytes(encode(report))
    from collections import Counter
    print('Papers',dict(Counter(p['status'] for p in report['packs'])),flush=True)
    print('Added questions',sum(p.get('count',0) for p in report['packs']),flush=True)

if __name__=='__main__':
    main()
