"""Verify pinned numbering and every original problem/solution pixel."""
import importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('kanken',ROOT/'scripts/prepare-kanken-material.py')
k=importlib.util.module_from_spec(spec);spec.loader.exec_module(k)
raw_report=(k.OUT/'kanken-report.json').read_bytes()
report=json.loads(raw_report);seen=set();total=0
for pack in report['packs']:
    record=k.reviewed(pack);targets=k.targets(record)
    raw=(k.OUT/pack['file']).read_bytes();assert k.base.sha(raw)==pack['sha256']
    rows=json.loads(raw);assert len(rows)==len(targets)==pack['count']==len(pack['questions'])
    assert len({number for number,target in targets})==len(targets) and pack['localOnly']
    for q,e,(number,target) in zip(rows,pack['questions'],targets):
        assert q['id']==e['id'] and e['number']==number and q['topic']==e['target']==target
        assert q['answer']==e['answer']==None and q['type']=='written'
        assert q['modelAnswer']==f'標準解答画像の{target}を参照し、自己採点してください。'
        assert q['sourceUrl']==pack['url'] and q['year']==record['year'] and q['examId']==record['examId']
        for refs,records,source in [(q['images'],e['images'],pack['sourceFile']),
                                    (q['solutionImages'],e['solutionImages'],pack['answerFile'])]:
            assert len(refs)==len(records)==record['pages'][source]
            assert [r['page'] for r in records]==list(range(record['pages'][source]))
            for ref,r in zip(refs,records):
                assert r['sourceFile']==source and ref['src']=='assets/github-material/'+r['file']
                if r['file'] in seen:continue
                data=(k.OUT/'assets'/r['file']).read_bytes();assert k.base.sha(data)==r['sha256']
                with k.fitz.open(k.SRC/source) as doc:
                    page=doc[r['page']];assert list(page.rect)==r['rect']
                    pix=page.get_pixmap(matrix=k.fitz.Matrix(1.5,1.5),alpha=False)
                    with k.base.Image.open(k.OUT/'assets'/r['file']) as image:
                        assert image.size==(pix.width,pix.height) and image.convert('RGB').tobytes()==pix.samples
                seen.add(r['file'])
    total+=len(rows)
assert len(report['packs'])==24 and total==2772
(k.OUT/'kanken-verification.json').write_bytes(k.base.encode(dict(
    reportSha256=k.base.sha(raw_report),questions=total,officialAnswers='pass',originalPixels='pass',
    method='Pinned numbering and complete official solution images verified. Written self grading; no answer transcription or automated scoring.')))
print(f'PASS: Kanken {total} items, {len(seen)} original problem/answer page images')
