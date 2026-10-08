"""Archive official JLPT samples for private study and preserve original page images."""
import concurrent.futures, importlib.util, json, re, sys, unicodedata
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('archive', ROOT / 'scripts/prepare-github-material.py')
archive = importlib.util.module_from_spec(spec); spec.loader.exec_module(archive)
spec = importlib.util.spec_from_file_location('fetcher', ROOT / 'scripts/fetch-github-material.py')
fetcher = importlib.util.module_from_spec(spec); spec.loader.exec_module(fetcher)
SRC, OUT, fitz = archive.SRC, archive.OUT, archive.fitz
norm, encode, sha = archive.norm, archive.encode, archive.sha

def fetch():
    tasks = []
    for name in ('jlpt-index.html', 'jlpt-sample09.html'):
        for href in dict.fromkeys(re.findall(r'href="([^"]+\.(?:pdf|mp3))"', (SRC / name).read_text(encoding='utf-8'))):
            url = urljoin('https://www.jlpt.jp/samples/', href)
            file = 'jlpt-' + href.replace('/', '-')
            tasks.append((url, file))
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        sources = list(pool.map(lambda task: fetcher.fetch(*task), tasks))
    (SRC / 'jlpt-discovery.json').write_bytes(encode({'sources': sources}))
    print('JLPT archived', len(sources), 'official files', flush=True)

def official_keys(doc, pack):
    if pack['year'] == '2009':
        reviewed = json.loads((SRC / 'jlpt-2009-verified-answers.json').read_bytes())[pack['examId']]
        assert reviewed['sha256'] == sha(Path(doc.name).read_bytes()), 'Reviewed answer PDF changed'
        return {k: v - 1 for k, v in reviewed['keys'].items()}
    keys = {}; section = 'V'; previous = 0
    limits = {1: (4, 7), 2: (6, 9), 3: (5, 3), 4: (5, 3), 5: (4, 3)}
    level = int(pack['examId'][-1])
    for page in doc:
        words = page.get_text('words')
        headings = sorted((w for w in words if re.fullmatch(r'問題[0-9０-９]+', w[4])), key=lambda w: w[1])
        for i, heading in enumerate(headings):
            group = int(norm(heading[4])[2:]); end = headings[i+1][1] - 1 if i+1 < len(headings) else page.rect.height - 30
            cells = [w for w in words if w[0] > heading[2] + 10 and heading[1] - 1 <= w[1] < end]
            pairs = []; answer_cells = set()
            for word in sorted(cells,key=lambda w:w[1]):
                if tuple(word) in answer_cells: continue
                label = re.sub(r'^質問(\d+)$', r'(\1)', norm(word[4]))
                if not re.fullmatch(r'\d+|\(\d+\)|例', label): continue
                x = (word[0] + word[2]) / 2
                below = [a for a in cells if 12 < a[1] - word[1] < 40 and abs((a[0]+a[2])/2-x) < 3 and norm(a[4]) in ('1','2','3','4')]
                if len(below) != 1: continue
                answer = below[0]; answer_cells.add(tuple(answer))
                if label == '例': continue
                if label.startswith('('):
                    parents = [p for p in cells if re.fullmatch(r'\d+', norm(p[4])) and 5 < word[1]-p[1] < 20 and abs((p[0]+p[2])/2-x)<25]
                    assert len(parents) == 1, 'Ambiguous listening subquestion'
                    label = norm(parents[0][4]) + label
                pairs.append((label, int(norm(answer[4])) - 1, answer[4] != norm(answer[4])))
            assert pairs, ('Empty answer group', doc.name, group)
            listening = any('聴' in w[4] and w[1] < heading[1] for w in words)
            if listening: subject = 'L'
            else:
                if level >= 3 and group == 1 and previous > 1: section = 'G'
                previous = group
                subject = ('V' if group <= limits[level][0] else 'G' if group <= limits[level][1] else 'R') if level <= 2 else ('V' if section == 'V' else 'G' if group <= 3 else 'R')
            for label, answer, _ in pairs:
                identity = f'{subject}:{group}:{label}'
                assert identity not in keys, 'Duplicate official key: ' + identity
                keys[identity] = answer
    for sections in ((('V','G','R'),) if level <= 2 else (('V',),('G','R'))):
        numbers = sorted(int(k.split(':')[2]) for k in keys if k.split(':')[0] in sections)
        assert numbers == list(range(1,len(numbers)+1)), 'Missing or duplicate answer numbers'
    return keys

def prepare():
    sources = json.loads((SRC / 'jlpt-discovery.json').read_bytes())['sources']
    by_file = {s['file']: s for s in sources}; packs = []
    labels = {'V':'文字・語彙','G':'文法','R':'読解','GR':'文法・読解','ALL':'言語知識・読解','L':'聴解'}
    (OUT / 'assets').mkdir(exist_ok=True)
    for year in (2009, 2012, 2018):
        for level in range(1,6):
            stem = f'jlpt-{year}-n{level}'; exam = f'jlpt-n{level}'
            answer_file = f'jlpt-pdf-N{level}-seikai.pdf' if year == 2009 else f'jlpt-sample{year}-pdf-N{level}answer.pdf'
            base = {'examId':exam,'year':str(year)}
            keys = official_keys(fitz.open(SRC / answer_file), base)
            subjects = list(dict.fromkeys(k.split(':')[0] for k in keys))
            for subject in subjects:
                source_file = f'jlpt-pdf-N{level}-mondai.pdf' if year == 2009 else f'jlpt-sample{year}-pdf-N{level}{subject}.pdf'
                source = by_file[source_file]; answer = by_file[answer_file]; doc = fitz.open(SRC / source_file)
                images = []; records = []
                # ponytail: shared booklet pages preserve every context/diagram; crop per question if page navigation becomes burdensome.
                for pn, page in enumerate(doc):
                    file = stem + '-' + subject + f'-p{pn+1:02}.png'; path = OUT / 'assets' / file
                    page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(path)
                    images.append({'src':'assets/github-material/'+file,'alt':f'N{level} {year} {labels[subject]} 原本 {pn+1}ページ'})
                    records.append({'file':file,'sourceFile':source_file,'page':pn,'rect':list(page.rect),'sha256':sha(path.read_bytes())})
                assert len(images) <= 30
                rows = []; evidence = []; used = {source_file:source,answer_file:answer}
                for identity, correct in keys.items():
                    kind, group, number = identity.split(':')
                    if kind != subject: continue
                    audio = []
                    if kind == 'L':
                        audio_file = f'jlpt-mp3-N{level}Sample.mp3' if year == 2009 else f'jlpt-sample{year}-mp3-N{level}Q{group}.mp3'
                        if year == 2012 and group == '2': audio_file = f'jlpt-sample2017-mp3-N{level}Q2.mp3'  # Official index replaces this audio.
                        record = by_file[audio_file]; used[audio_file] = record
                        (OUT / 'assets' / audio_file).write_bytes((SRC / audio_file).read_bytes())
                        audio = [{'src':'assets/github-material/'+audio_file,'label':f'聴解 問題{group}の音声（大問全体）'}]
                    count = 3 if kind == 'L' and int(group) in ({1:{4},2:{4},3:{4,5},4:{3,4},5:{3,4}}[level]) else 4
                    assert 0 <= correct < count
                    title = f'N{level} {year}年発行 '+('問題例集' if year == 2009 else '公式問題集')+' '+labels[subject]+(f' 問題{group}・解答番号{number}' if group != '0' else f' 解答番号{number}')
                    q = {'id':stem+'-'+identity.replace(':','-').replace('(','-').replace(')',''),'examId':exam,'type':'single','year':str(year),'term':'問題例集' if year == 2009 else '公式問題集','subject':labels[subject],'category':labels[subject],'topic':title,
                         'prompt':title+'\n原本画像の該当する解答番号の問題を解いてください。冊子全体を表示し、共通本文・例題・図版を保持しています。'+ ('音声は大問全体です。該当の番号まで再生してください。' if audio else ''),
                         'options':list(map(str,range(1,count+1))),'answer':correct,'images':images,'audio':audio,
                         'source':'出典：日本語能力試験公式ウェブサイト（https://www.jlpt.jp/）。個人学習用。原本PDFを画像化。主催者の作成したアプリではありません。',
                         'sourceUrl':source['url'],'explanation':'公式正答：'+str(correct+1)+'。理由解説は未収録です。','explanationSource':'JLPT公式正答表'}
                    rows.append(q); evidence.append({'id':q['id'],'number':identity,'answer':correct,'sourceUrl':source['url'],'images':records,'audio':audio})
                file = stem+'-'+subject+'.json'; raw = encode(rows); (OUT / file).write_bytes(raw)
                packs.append({**base,'term':rows[0]['term'],'subject':labels[subject],'file':file,'status':'prepared','provider':'JLPT','count':len(rows),'sha256':sha(raw),'sourceFile':source_file,'answerFile':answer_file,'url':source['url'],'sources':list(used.values()),'questions':evidence})
            print(year,exam,'prepared',len(keys),flush=True)
    (OUT / 'jlpt-report.json').write_bytes(encode({'packs':packs}))

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if '--fetch' in sys.argv: fetch()
    else: prepare()
