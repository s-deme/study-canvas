"""Re-read official answer text independently and reproduce every stored image crop."""
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'build/python-deps'))
import pymupdf as fitz
from PIL import Image

SRC=ROOT/'private-data/fp'
OUT=ROOT/'private-data/additions'
manifest_file=OUT/'fp-manifest.json'
raw=manifest_file.read_bytes()
manifest=json.loads(raw)
evidence={q['id']:q for q in manifest['questions']}
assert len(evidence)==len(manifest['questions'])
total=0
for pack in manifest['packs']:
    rows=json.loads((OUT/pack['file']).read_text(encoding='utf-8'))
    assert len(rows)==60
    first=evidence[rows[0]['id']]
    answer_doc=fitz.open(SRC/first['answerSource'])
    answer_text=unicodedata.normalize('NFKC','\n'.join(page.get_text() for page in answer_doc))
    if first['source']==first['answerSource']:
        matches=re.findall(r'^問[ \t]*(\d+)[ \t]*\r?\n.*?正解\s*([1-4]|[○〇×])',answer_text,re.S|re.M)
        assert [int(n) for n,_ in matches]==list(range(1,61)),pack['id']
        keys={int(n):0 if a in '○〇' else 1 if a=='×' else int(a)-1 for n,a in matches}
    else:
        # A second algorithm: PDF reading order is ten headers then ten answers.
        cells=[line.strip() for line in answer_text.splitlines() if re.fullmatch(r'問\s*\d+|[1-4]',line.strip())]
        assert len(cells)==120
        keys={}
        for offset in range(0,120,20):
            for j in range(10):
                number=int(re.fullmatch(r'問\s*(\d+)',cells[offset+j])[1])
                keys[number]=int(cells[offset+10+j])-1
    assert set(keys)==set(range(1,61)),pack['id']
    doc=fitz.open(SRC/first['source'])
    for row in rows:
        ev=evidence[row['id']]
        assert row['answer']==keys[ev['question']]==ev['answer'],row['id']
        assert len(row['images'])==len(ev['images'])
        assert '正解' not in row['passage']
        for image in ev['images']:
            rect=fitz.Rect(image['rect']);page=doc[image['page']-1]
            assert page.rect.contains(rect)
            # Embedded answer text must not intersect any published crop.
            for block in page.get_text('dict')['blocks']:
                for line in block.get('lines',[]):
                    text=unicodedata.normalize('NFKC',''.join(s['text'] for s in line['spans'])).strip()
                    if text.startswith('正解'):
                        assert not rect.intersects(fitz.Rect(line['bbox'])),row['id']
            pix=page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),clip=rect,alpha=False)
            with Image.open(OUT/'assets'/image['file']) as stored:
                assert stored.size==(pix.width,pix.height)
                assert stored.convert('RGB').tobytes()==pix.samples,row['id']
        total+=1
report=dict(manifestSha256=hashlib.sha256(raw).hexdigest(),questions=total,
            officialAnswers='pass',sourceCropPixels='pass',answerLeakage='pass',
            visualReview='24 representative questions; full visual review not performed')
(OUT/'fp-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
