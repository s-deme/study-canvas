"""Extract FP academic questions and official keys, excluding answer areas from images."""
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build/python-deps'))
import pymupdf as fitz
from PIL import Image

SRC = ROOT / 'private-data/fp'
OUT = ROOT / 'private-data/additions'
norm = lambda s: unicodedata.normalize('NFKC', s).strip()


def lines(page):
    return sorted([(norm(''.join(s['text'] for s in line['spans'])), fitz.Rect(line['bbox']))
                   for b in page.get_text('dict')['blocks'] for line in b.get('lines', [])],
                  key=lambda item: (item[1].y0, item[1].x0))


def separate_keys(path):
    doc = fitz.open(path)
    answers = {}
    # Answers are a grid: the numeral directly below each question label is its key.
    for page in doc:
        data = lines(page)
        for value, rect in data:
            match = re.fullmatch(r'問\s*(\d+)', value)
            if not match:
                continue
            candidates = [(t, r) for t, r in data if re.fullmatch('[1-4]', t)
                          and abs((r.x0+r.x1)-(rect.x0+rect.x1)) < 12
                          and 0 < r.y0-rect.y0 < 45]
            assert len(candidates) == 1, (path.name, value, candidates)
            number = int(match[1])
            assert number not in answers
            answers[number] = int(candidates[0][0])-1
    assert set(answers) == set(range(1, 61)), path.name
    return answers


def extract(source, by_name):
    path = SRC / source['file']
    doc = fitz.open(path)
    data = [lines(page) for page in doc]
    starts = [(int(m[1]), pn, rect.y0) for pn, page in enumerate(data) if pn
              for value, rect in page if (m := re.fullmatch(r'問(?:題)?\s*(\d+)', value))]
    assert [s[0] for s in starts] == list(range(1, 61)), source['file']
    header = re.sub(r'\s+', '', norm(doc[0].get_text()))
    law = re.search(r'(20\d{2}年\d{1,2}月\d{1,2}日)現在施行', header)
    assert law, source['file']
    answer_source = source if source['kind'] == 'qa' else by_name[source['file'].replace('_q.pdf', '_a.pdf')]
    answers = {} if source['kind'] == 'qa' else separate_keys(SRC / answer_source['file'])
    rows, audit = [], []
    stem = 'jafp-' + path.stem.removesuffix('_qa').removesuffix('_q')
    for i, (number, pn, y) in enumerate(starts):
        ep, ey = starts[i+1][1:] if i < 59 else (len(doc)-1, doc[-1].rect.height-40)
        inside = [(p, t, r) for p in range(pn, ep+1) for t, r in data[p]
                  if (p != pn or r.y0 >= y-.1) and (p != ep or r.y0 < ey-.1)
                  and 40 < r.y0 < doc[p].rect.height-40]
        if source['kind'] == 'qa':
            found = [(p, t, r) for p, t, r in inside if re.fullmatch(r'正解\s*([1-4]\)|[○〇×])', t)]
            assert len(found) == 1, (source['file'], number, found)
            ep, value, answer_rect = found[0]
            ey = answer_rect.y0
            symbol = re.search(r'([1-4]|[○〇×])', value)[0]
            answers[number] = 0 if symbol in '○〇' else 1 if symbol == '×' else int(symbol)-1
            inside = [(p,t,r) for p,t,r in inside if p < ep or p == ep and r.y0 < ey-.1]
        body = '\n'.join(t for _,t,_ in inside if t and not re.fullmatch(r'[-ー−―]\s*\d+.*[-ー−―]', t))
        assert '正解' not in body, (source['file'], number, 'answer leaked')
        is_bool = source['examId'] == 'fp3' and number <= 30
        options = ['○（正しい・適切）', '×（誤り・不適切）'] if is_bool else list('123' if source['examId']=='fp3' else '1234')
        if not is_bool:
            left = next(r.x0 for _,t,r in inside if re.fullmatch(r'問(?:題)?\s*\d+', t))
            labels = [int(m[1]) for _,t,r in inside if abs(r.x0-left)<3 and (m := re.match(r'^([1-4])[.)]', t))]
            assert labels == list(range(1, len(options)+1)), (source['file'], number, labels)
        assert 0 <= answers[number] < len(options)
        images, geometries = [], []
        for p in range(pn, ep+1):
            top, bottom = (y-2 if p==pn else 40), (ey-2 if p==ep else doc[p].rect.height-40)
            if bottom <= top:
                continue
            content = [(t,r) for pp,t,r in inside if pp==p and t]
            if not content:
                continue
            assert all(r.y0 >= top-.1 and r.y1 <= bottom+.1 for _,r in content), (source['file'], number, 'clipped text')
            rect = fitz.Rect(35, top, doc[p].rect.width-35, bottom)
            name = f'{stem}-q{number:02}-{p-pn+1}.png'
            file = OUT / 'assets' / name
            doc[p].get_pixmap(matrix=fitz.Matrix(1.5,1.5), clip=rect, alpha=False).save(file)
            with Image.open(file) as image:
                image.verify()
            images.append(dict(src='assets/additions/'+name, alt=f'日本FP協会 {source["year"]}年{source["month"]}月 学科 問{number}'))
            geometries.append(dict(page=p+1, rect=list(rect), file=name, sha256=hashlib.sha256(file.read_bytes()).hexdigest()))
        assert images
        section = (number-1)//10 if source['examId']=='fp2' else ((number-1)%30)//5
        category = ['ライフプランニング','リスク管理','金融資産運用','タックスプランニング','不動産','相続・事業承継'][section]
        qid = f'{stem}-q{number:02}'
        rows.append(dict(id=qid, examId=source['examId'], type='single', subject='学科', category=category,
                         topic=f'{source["year"]}年{source["month"]}月 問{number}', year=source['year'], term=source['month']+'月',
                         prompt=f'原本の問題文・図表を確認して回答してください。特に断りがなければ{law[1]}施行の法令等に基づきます。',
                         passage=body, images=images, options=options, answer=answers[number],
                         explanation=f'公式解答：{options[answers[number]]}。公式資料に理由の解説はありません。出題当時の法令等に基づく解答です。',
                         explanationSource='日本FP協会公式解答（独自解説なし）',
                         source=f'日本FP協会 {source["examId"][-1]}級ファイナンシャル・プランニング技能検定 学科 {source["year"]}年{source["month"]}月 問{number}（設問単位に切り出し、正解欄を分離）',
                         sourceUrl=source['url']))
        audit.append(dict(id=qid, examId=source['examId'], question=number, source=source['file'], answerSource=answer_source['file'],
                          answer=answers[number], lawAsOf=law[1], images=geometries))
    return stem, rows, audit


def main():
    (OUT / 'assets').mkdir(parents=True, exist_ok=True)
    sources = json.loads((SRC/'sources.json').read_text(encoding='utf-8'))
    for row in [sources['terms'], *sources['sources']]:
        assert hashlib.sha256((SRC/row['file']).read_bytes()).hexdigest() == row['sha256'], row['file']
    by_name = {s['file']:s for s in sources['sources']}
    packs, questions = [], []
    for source in sources['sources']:
        if source['kind']=='a':
            continue
        stem, rows, audit = extract(source, by_name)
        raw = json.dumps(rows, ensure_ascii=False)
        (OUT/(stem+'.json')).write_text(raw, encoding='utf-8')
        packs.append(dict(id=stem, file=stem+'.json', examId=source['examId'], year=source['year'], term=source['month']+'月', subject='学科',
                          kind='official', field='金融・生活', count=len(rows), sha256=hashlib.sha256(raw.encode()).hexdigest(),
                          sources=[source, by_name[source['file'].replace('_q.pdf','_a.pdf')]] if source['kind']=='q' else [source],
                          verification='設問連番・選択肢数・公式解答対応・切出し内の全文字包含・画像デコードを自動検査'))
        questions.extend(audit)
        print(stem, len(rows), flush=True)
    manifest = dict(archive='fp', exams=[dict(id='fp'+n,name='FP技能検定'+n+'級',field='金融・生活',subjects=['学科'],categories=[]) for n in ['2','3']],
                    packs=packs, sources=sources, questions=questions)
    (OUT/'fp-manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
