"""Import RBC released papers privately; uncertain OCR/answer marks stay excluded."""
import concurrent.futures, importlib.util, json, os, re, sys
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build/python-deps'))
import pymupdf as fitz
from PIL import Image, ImageChops
spec = importlib.util.spec_from_file_location('nonit', ROOT / 'scripts/prepare-nonit-material.py')
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
SRC, OUT = base.SRC, base.OUT

def fetch():
    spec=importlib.util.spec_from_file_location('fetcher',ROOT/'scripts/fetch-github-material.py')
    fetcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(fetcher)
    page=fetcher.fetch('https://www.rbc.or.jp/exam/past_question/','rbc-index.html')
    tasks=[]
    for url,label in re.findall(r'<a[^>]*href=["\x27]([^"\x27]+)["\x27][^>]*>(.*?)</a>',(SRC/page['file']).read_text(encoding='utf-8'),re.S):
        if '.pdf' not in url:continue
        label=re.sub('<[^>]*>','',label).strip();match=re.search(r'第(\d+)回(理容師|美容師)',label)
        if not match:continue
        url=urljoin(page['url'],url)
        tasks.append(dict(url=url,label=label,number=int(match[1]),examId='barber' if match[2]=='理容師' else 'beautician',sourceFile='rbc-'+url.rsplit('/',1)[-1]))
    def download(task):
        return {**task,'source':fetcher.fetch(task['url'],task['sourceFile']),'status':'downloaded'}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:tasks=list(pool.map(download,tasks))
    (SRC/'rbc-discovery.json').write_bytes(base.ipa.encode(tasks))

def cleaned(page, scale=1.5):
    pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
    image = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    r, g, b = image.split()
    red = ImageChops.darker(ImageChops.subtract(r, g), ImageChops.subtract(r, b))
    mask = red.point(lambda n: 255 if n > 18 else 0)
    # Only answer-label margins are edited; diagrams and body text retain their pixels.
    margin = Image.new('L', image.size); margin.paste(mask.crop((0, 0, int(165*scale), image.height)), (0, 0))
    removal = Image.new('L', image.size)
    removal.paste(red.point(lambda n: 255 if n > 3 else 0).crop((0, 0, int(165*scale), image.height)), (0, 0))
    # Faded scan edges can become almost gray; clear light pixels in the label margin too.
    light=ImageChops.darker(ImageChops.darker(r,g),b).point(lambda n:255 if n>180 else 0)
    removal.paste(ImageChops.lighter(removal,light).crop((0,0,int(165*scale),image.height)),(0,0))
    image.paste((255, 255, 255), mask=removal)
    return image, margin

def layout(page, file, pn):
    cache = SRC / 'ocr' / f'{file}-rbc-v2-{pn}.json'
    if cache.exists(): return json.loads(cache.read_bytes())
    image, _ = cleaned(page, 3)
    rect = (45, 65, 165, page.rect.height-45)
    crop = image.crop(tuple(round(v*3) for v in rect))
    pix = fitz.Pixmap(fitz.csRGB, crop.width, crop.height, crop.tobytes(), False)
    pix.set_dpi(216, 216)
    doc = fitz.open(stream=pix.pdfocr_tobytes(language='jpn+eng', tessdata=str(ROOT/'build/tessdata')), filetype='pdf')
    words = [[w[0]+rect[0], w[1]+rect[1], w[2]+rect[0], w[3]+rect[1], base.norm(w[4])] for w in doc[0].get_text('words')]
    cache.parent.mkdir(exist_ok=True); cache.write_bytes(base.ipa.encode(words))
    return words

def items(doc, file):
    starts, options = [], []
    for pn, page in enumerate(doc):
        words = layout(page, file, pn)
        for w in words:
            m = re.fullmatch(r'[問間]題\s*(\d+)', w[4])
            if w[4] in ('問題','間題'):
                nums = [v for v in words if re.fullmatch(r'\d{1,2}', v[4]) and 0 <= v[0]-w[2] < 35 and abs(v[1]-w[1]) < 4]
                if len(nums) == 1: m = re.fullmatch(r'(\d+)', nums[0][4])
            if m: starts.append((int(m[1]), pn, w[1]))
            elif w[4] in ('問題','間題'): starts.append((None, pn, w[1]))
            m = re.fullmatch(r'\(([1-4])\)', w[4])
            if m: options.append((int(m[1]), pn, w[:4]))
    assert starts, 'No question headings'
    result = []
    masks = {}
    for i, (n, pn, y) in enumerate(starts):
        if n is None or not 1 <= n <= 55: continue
        if i+1 < len(starts) and starts[i+1][0] != n+1: continue
        if i+1 == len(starts) and n not in (50,55): continue
        end = starts[i+1][1:] if i+1 < len(starts) else (len(doc)-1, doc[-1].rect.height)
        labels = [(k,p,box) for k,p,box in options if (pn,y) < (p,box[1]) < end]
        if [k for k,p,box in labels] != [1,2,3,4]: continue
        marked = []
        for k,p,box in labels:
            if p not in masks: masks[p] = cleaned(doc[p])[1]
            x0,y0,x1,y1 = box
            rect = tuple(round(v*1.5) for v in (x0-5,y0-5,x1+5,y1+5))
            if masks[p].crop(rect).histogram()[255] > 12: marked.append(k)
        if len(marked) == 1: result.append(dict(number=n, answer=marked[0]-1, pages=list(range(pn,end[0]+1 if end[1]>20 else end[0]))))
    return result

def prepare(task):
    try:
        assert task['number']>=29, 'Before official answer marks were published (29th exam)'
        doc = fitz.open(SRC/task['sourceFile']); verified = items(doc, task['sourceFile'])
        assert verified, 'No unambiguous official marks'
        stem = Path(task['sourceFile']).stem; rows=[]; evidence=[]; assets={}
        for item in verified:
            images=[]; solutions=[]; records=[]; solution_records=[]
            for pn in item['pages']:
                if pn not in assets:
                    records_pair=[]
                    for suffix in ['question-v2','solution']:
                        file=f'{stem}-p{pn+1:03}-{suffix}.png'; path=OUT/'assets'/file
                        if not path.exists():
                            if suffix=='solution': doc[pn].get_pixmap(matrix=fitz.Matrix(1.5,1.5), alpha=False).save(path)
                            else: cleaned(doc[pn])[0].save(path)
                        records_pair.append(dict(file=file,page=pn,rect=list(doc[pn].rect),sha256=base.ipa.sha(path.read_bytes())))
                    assets[pn]=records_pair
                a,b=assets[pn]; records.append(a); solution_records.append(b)
                images.append(dict(src='assets/github-material/'+a['file'],alt=f'問題原本（正答印を除去）{pn+1}ページ'))
                solutions.append(dict(src='assets/github-material/'+b['file'],alt=f'公式正答印付き原本 {pn+1}ページ'))
            n=item['number']; year=str(2000+(task['number']-1)//2); title=f"{task['label']} 問{n}"
            q=dict(id=f'{stem}-q{n}',examId=task['examId'],type='single',year=year,term=task['label'],subject='筆記',category='過去問',topic=title,
                   prompt=title+'\n画像の該当番号に解答してください。正答の丸印だけを除去しています。',options=['1','2','3','4'],answer=item['answer'],images=images,solutionImages=solutions,
                   sourceUrl=task['url'],source='理容師美容師試験研修センター公開過去問。本人の学習用。問題画像は正答印を除去した加工版、解答画像は原本。',
                   explanation=f"公式正答：{item['answer']+1}。理由解説は未収録。実施当時の制度を前提とします。",explanationSource='公式PDFの正答印')
            rows.append(q);evidence.append(dict(id=q['id'],number=n,answer=q['answer'],images=records,solutionImages=solution_records))
        file=stem+'.json';raw=base.ipa.encode(rows);(OUT/file).write_bytes(raw)
        return dict(provider='RBC',localOnly=True,examId=task['examId'],year=year,term=task['label'],subject='筆記',file=file,url=task['url'],sourceFile=task['sourceFile'],answerFile=task['sourceFile'],sources=[task['source']],status='prepared',count=len(rows),sha256=base.ipa.sha(raw),questions=evidence,excludedCount=(55 if task['number']>=41 and '旧' not in task['label'] else 50)-len(rows))
    except Exception as e: return {**task,'provider':'RBC','status':'pending-review','reason':str(e)}

def main():
    sys.stdout.reconfigure(encoding='utf-8');os.environ['OMP_THREAD_LIMIT']='1';(OUT/'assets').mkdir(exist_ok=True)
    if '--fetch' in sys.argv:fetch()
    tasks=json.loads((SRC/'rbc-discovery.json').read_bytes());report={'packs':[]}
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        for result in pool.map(prepare,tasks):
            report['packs'].append(result);print(result.get('term',result.get('label')),result['status'],result.get('count',result.get('reason')),flush=True)
            (OUT/'design-report.json').write_bytes(base.ipa.encode(report))

if __name__=='__main__': main()
