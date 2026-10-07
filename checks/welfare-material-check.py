"""Run after acquiring welfare originals; no network or writes."""
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('welfare', ROOT / 'scripts/prepare-welfare-material.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)
read = lambda name: json.loads((w.OUT / name).read_bytes())
rows = lambda stem: {int(q['id'].split('-q')[-1]): q for q in read('welfare-'+stem+'.json')}

# Malformed source HTML must retain the prompt continuation and fifth option.
q = rows('shakai-38-am')
assert '2つ選びなさい' in q[56]['prompt'] and q[56]['answer'] == [2, 4]
assert '倫理への対応' in q[79]['prompt'] and '仮説' in q[79]['options'][4]
assert '次の事例' not in rows('kaigo-38-pm')[109]['prompt']
q = rows('kaigo-38-pm')
assert q[110]['passage'] == q[111]['passage'] and '問題110' in q[110]['passage']
assert '問題110' not in q[112]['passage'] and '問題112' in q[112]['passage']
assert q[114]['passage'] == q[116]['passage'] and q[114]['passage'] != q[117]['passage']
assert 46 not in rows('kaigo-36-am')
for year in [26, 27, 28]:
    common = w.answers(f'welfare-seishin-{year}-answers.pdf', True)
    specialist = w.answers(f'welfare-seishin-{year}-answers.pdf', False)
    assert len(common) == (83 if year == 26 else 84)
    assert len(specialist) == (80 if year == 26 else 48)
    social = rows(f'shakai-{year+10}-am')
    mental = rows(f'seishin-{year}-am')
    assert {n: q['answer'] for n, q in social.items()} == {n: q['answer'] for n, q in mental.items()}
report = read('welfare-report.json')
assert sum(p['count'] for p in report['packs']) == 1209
for pack in report['packs']:
    for q in read(pack['file']):
        assert len(re.findall(r'^問題\d+\s', q['prompt'], re.M)) == 1, q['id']
        assert not any(re.search(r'^問題\d+\s', option, re.M) for option in q['options']), q['id']
        assert len(q['options']) == 5 and all(q['options'])
before = json.loads((w.SRC / 'welfare-baseline.json').read_bytes())
after = json.loads((ROOT / 'build/private/manifest.json').read_bytes())
packs = {p['id']: p for p in after['packs']}
assert all(packs[p['id']] == p for p in before['packs'])
assert after['questions'] == before['questions'] + 1221
print('PASS: 1209 welfare questions; shared cases, answer namespaces, source HTML quirks and existing pack preservation')
