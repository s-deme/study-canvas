"""Source mapping and preservation checks for the previously deferred practice packs."""
import hashlib, importlib.util, json, re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT/'private-data/github-candidates'
spec = importlib.util.spec_from_file_location('literal', ROOT/'scripts/github-literals.py')
literal = importlib.util.module_from_spec(spec); spec.loader.exec_module(literal)
@lru_cache(maxsize=None)
def read(p): return json.loads(p.read_bytes())
digest = lambda q: hashlib.sha256(json.dumps(q, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
manifest = read(ROOT/'build/private/manifest.json')
built = {q['examId']+'|'+q['id']: q for p in manifest['packs'] for q in read(ROOT/'build/private/web'/p['url'])}
baseline = read(SRC/'practice-baseline-questions.json')
assert len(baseline) == 97510
report = read(SRC/'prepared/report.json')
missing = [r for r in report['excluded'] if r['repo']=='furumix2000/fp3-quiz-app' and r['reason']=='必要図版が仮URLまたは未取得']
assert len(missing)==14
for row in missing:
    key='github-'+hashlib.sha256((row['repo']+'|'+row['identity']).encode()).hexdigest()[:24]
    assert 'fp3|'+key not in built
for key, expected in baseline.items():
    assert key in built and digest(built[key]) == expected, 'Previous question changed: '+key

repos = ['ikuma-hiroyuki/python_engineer_basic_demo','ThREE100/chosashi-app',
         'ronodera662/fp-study-app','furumix2000/fp3-quiz-app',
         'xinyue119-code/boki1-cards','nktkt/bookkeeping-practice']
checked = 0
for repo in repos:
    packs = [p for p in manifest['packs'] if p.get('repo') == repo]
    assert packs and all(p.get('localOnly') for p in packs), repo
    for pack in packs:
        for q in read(ROOT/'build/private/web'/pack['url']):
            assert '未検証' in q['source'] and q['term']
            identity = q['source'].split(' / ',1)[1].split(' — ',1)[0]
            assert q['id'] == 'github-'+hashlib.sha256((repo+'|'+identity).encode()).hexdigest()[:24]
            if repo.startswith('ikuma'):
                file, number = identity.rsplit('#',1)
                original = next(v for v in read(SRC/repo/file) if str(v['id']) == number)
                assert q['prompt'] == original['question'].strip()
                assert q['options'] == list(original['choices'][0].values())
                assert q['options'][q['answer']] == original['choices'][0][original['answer']]
            elif repo.startswith('ronodera'):
                originals = [v for p in (SRC/repo/'public/data').glob('*.json') for v in read(p)]
                original = next(v for v in originals if v['id'] == identity)
                assert q['prompt'] == original['questionText'].strip()
                assert q['answer'] == original['correctAnswer'] and q['options'] == original['options']
            elif repo.startswith('furumix'):
                file, number = identity.rsplit('#',1); text = (SRC/repo/file).read_text(encoding='utf-8')
                original = next(v for v in literal.assignment(text,re.search(r'const (\w+)',text)[1]) if str(v['id']) == number)
                assert q['prompt'] == original['question'].strip()
                assert q['answer'] == original['answer'] and q['options'] == original['choices']
                assert len(q['images']) == len(original.get('imageChoices',[])) + bool(original.get('questionImage'))
            elif repo.startswith('ThREE'):
                if identity.startswith('term'):
                    original = next(v for v in read(SRC/repo/'src/data/ankicards.json')['terms'] if v['id']==identity)
                    assert q['modelAnswer'] == original['definition']
                elif identity.startswith('q0'):
                    assert identity not in ('q00001','q00069')
                    original = next(v for v in read(SRC/repo/'src/data/ankicards.json')['ox'] if v['id']==identity)
                    assert q['answer'] == (0 if original['correct'] else 1)
                elif q['type']=='written':
                    original = next(v for v in read(SRC/repo/'src/data/kijutsu.json')['problems'] if v['id']==identity)
                    assert q['modelAnswer']==original['modelAnswerText'].strip() and q['images']
                else:
                    original = next(v for v in read(SRC/repo/'src/data/takuitsu.json')['questions'] if v['id']==identity)
                    assert q['answer']+1 == original['correctAnswer']
                    assert '取得不可' not in q['prompt'] and '404' not in q['prompt']
            elif repo.startswith('xinyue'):
                text = (SRC/repo/'cards.js').read_text(encoding='utf-8')
                for m in re.finditer(r'^K\(',text,re.M):
                    parser=literal.Literal(text,m.end()); values=[parser.value()]
                    while parser.take(','): values.append(parser.value())
                    if values[0]==identity: break
                assert values[0]==identity
                kind,prompt,answer=values[3:6]
                if kind=='cloze':
                    assert q['modelAnswer']=='\n'.join(re.findall(r'\{\{(.*?)\}\}',prompt))
                    assert '{{' not in q['prompt']
                elif kind=='qa': assert q['modelAnswer']==answer.strip()
                elif kind=='tf': assert q['options'][q['answer']]==answer
                else: assert q['answer']==int(answer)-1
            checked += 1

workbook = [q for q in built.values() if q['source'].startswith('nktkt/bookkeeping-practice / ')]
chapters = [q for q in workbook if '章単位' in q['term']]
assert len(chapters)==22
assert all(q['type']=='written' and q['modelAnswer'] for q in workbook)
assert all(not re.search(r'模\s*範\s*解\s*答',q['prompt']) for q in chapters)
assert all({q['examId'] for q in read(ROOT/'build/private/web'/p['url'])}=={p['examId']} for p in manifest['packs'])
print(f'PASS: {len(baseline)} previous questions unchanged; {checked} added practice questions checked; 22 workbook chapters retain shared context')
