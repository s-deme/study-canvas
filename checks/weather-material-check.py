"""Runnable source, numbering, corrected-key and original-image checks."""
import importlib.util, json, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('weather',ROOT/'scripts/prepare-weather-material.py')
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
report = json.loads((w.OUT/'weather-report.json').read_bytes())
mirrors=any(s['file']=='weather-mirror-index.html' for s in report['sources'])
assert len(report['packs']) == (38 if mirrors else 20)
count=sum(p['count'] for p in report['packs'])
assert count == (566 if mirrors else 296)
assert w.labels('໲\x14\x13') == '問10'
assert w.labels('໲̐') == '問2'
assert w.labels('ᶅᶆᶇᶈᶉ') == '12345'
for source in report['sources']:
    data = (w.SRC/source['file']).read_bytes()
    assert len(data) == source['bytes'] and w.archive.sha(data) == source['sha256']
    if source.get('archive'):
        with zipfile.ZipFile(w.SRC/source['archive']) as z: assert z.read(source['member']) == data
checked=set()
for pack in report['packs']:
    raw = (w.OUT/pack['file']).read_bytes(); assert w.archive.sha(raw) == pack['sha256']
    rows = json.loads(raw); assert len(rows) == pack['count']
    with w.fitz.open(w.SRC/pack['answerFile']) as ans, w.fitz.open(w.SRC/pack['sourceFile']) as doc:
        keys = w.official_keys(ans,pack); starts = w.question_starts(doc)
        assert {e['number'] for e in pack['questions']} == {n for n,a in keys.items() if a is not None}
        for q,e in zip(rows,pack['questions']):
            assert q['answer'] == e['answer'] == keys[e['number']]
            assert q['options'] == list('12345') and pack['localOnly']
            for image in e['images']:
                path=w.OUT/'assets'/image['file']
                assert w.archive.sha(path.read_bytes()) == image['sha256']
                if image['file'] not in checked:
                    pix=doc[image['page']].get_pixmap(matrix=w.fitz.Matrix(1.5,1.5),alpha=False)
                    with w.archive.Image.open(path) as stored:assert stored.size==(pix.width,pix.height) and stored.convert('RGB').tobytes()==pix.samples
                    checked.add(image['file'])
print(f'PASS: {count} questions, {len(report["packs"])} papers, ZIP members, source/image hashes, original pixels, numbering and official corrected keys')
