"""Check question/answer correspondence and rejection of deleted official items."""
import collections, importlib.util, json, re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('food',ROOT/'scripts/prepare-food-material.py')
food=importlib.util.module_from_spec(spec);spec.loader.exec_module(food)
report=json.loads((food.OUT/'food-report.json').read_bytes())
assert len(report['packs'])==28
count=0
checked=set()
for pack in report['packs']:
    assert pack['status']=='prepared',pack
    keys=food.official_keys(food.fitz.open(food.SRC/pack['answerFile']),pack)
    starts=food.question_starts(food.fitz.open(food.SRC/pack['sourceFile']),pack)
    assert len(starts)==len(keys) and {n for n,p,y in starts}==set(keys)
    assert set(int(n.split(':')[0]) for n in keys)==set(range(1,(50 if pack['examId']=='agri3' else 70 if pack['examId'].startswith('agri') else 60)+1))
    rows=json.loads((food.OUT/pack['file']).read_bytes())
    assert len(rows)==pack['count']==len(pack['questions'])
    for q,e in zip(rows,pack['questions']):
        assert q['answer']==e['answer']==keys[e['number']]
        assert 0<=q['answer']<len(q['options'])
        assert q['images'] and q['sourceUrl']==pack['url']
        for record in e['images']:
            file=record['file']
            if file in checked:continue
            source=food.fitz.open(food.SRC/pack['sourceFile'])
            expected=source[record['page']].get_pixmap(matrix=food.fitz.Matrix(1.5,1.5),clip=food.fitz.Rect(record['rect']),alpha=False)
            from PIL import Image
            with Image.open(food.OUT/'assets'/file) as stored:
                assert stored.size==(expected.width,expected.height) and stored.convert('RGB').tobytes()==expected.samples
            assert food.ipa.sha((food.OUT/'assets'/file).read_bytes())==record['sha256']
            checked.add(file)
    assert {e['number'] for e in pack['questions']}=={n for n,a in keys.items() if a is not None}
    count+=len(rows)
deleted=next(p for p in report['packs'] if p['file']=='food-tochigi-00.json')
assert '1:0' in {e['number'] for e in deleted['excludedQuestions']}
print(f'PASS: {len(report["packs"])} food papers, {count} questions, official numbering/options/deleted items')
(food.OUT/'food-verification.json').write_bytes(food.ipa.encode(dict(reportSha256=food.ipa.sha((food.OUT/'food-report.json').read_bytes()),questions=count,officialAnswers='pass',originalPixels='pass')))
