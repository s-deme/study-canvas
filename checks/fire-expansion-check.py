"""Check archived answer mappings, local-only output and preservation of existing packs."""
import hashlib, importlib.util, json, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'private-data/github-candidates'
spec = importlib.util.spec_from_file_location('literals', ROOT/'scripts/github-literals.py')
literal = importlib.util.module_from_spec(spec); spec.loader.exec_module(literal)
read = lambda p: json.loads(p.read_bytes())
def js(repo, file, name):
    return literal.assignment((SRC/repo/file).read_text(encoding='utf-8'), name)

manifest = read(ROOT/'build/private/manifest.json')
before = read(SRC/'fire-expansion-baseline.json')
before_ids = {p['id'] for p in before['packs']}
current = {p['id']: p for p in manifest['packs']}
for p in before['packs']:
    assert current[p['id']] == p, 'Existing pack changed: '+p['id']
    assert hashlib.sha256((ROOT/'build/private/web'/p['url']).read_bytes()).hexdigest() == p['sha256']

expected = {}
def add(repo, identity, exam, prompt, options=None, answer=None, model=''):
    if isinstance(answer, list): answer = sorted(answer) if len(answer)>1 else answer[0]
    key = 'github-'+hashlib.sha256((repo+'|'+str(identity)).encode()).hexdigest()[:24]
    expected[key] = (exam, prompt.strip(), [o.strip() for o in options or []], answer, model)

r='shinki5301-art/-6'
for n,q in enumerate(js(r,'6','quizData'),1): add(r,n,'fire-b6',q['q'],q['options'],q['ans'])
r='mitsugeek/shoubo-shiken'; t=(SRC/r/'src/App.vue').read_text(encoding='utf-8')
items=literal.Literal(t,re.search(r'const tests = reactive\(',t).end()).value()
for n,q in enumerate(items,1):
    answers=[i for i,c in enumerate(q['choices']) if c['answer']]
    if len(answers)==1: add(r,n,'fire-b6',q['question'],[c['choice'] for c in q['choices']],answers[0])
r='hkosu813-ux/shobo-quiz'
for q in js(r,'index.html','DATA'): add(r,q['id'],'fire-a4',q['q'],q['ch'],[a-1 for a in q['ans']])
r='terukatsu58-hash/Shobo-quiz'
for n,q in enumerate(js(r,'questions.js','allQuestions'),1): add(r,n,'fire-a1',q['question'],q['choices'],q['answer'])
r='jiagyebo19891011/shoubou-otsu6'; seen={}
for n,q in enumerate(js(r,'index.html','questions'),1):
    assert seen.setdefault(q['q'],q['a']) == q['a'], 'Conflicting answer for duplicate prompt'
    add(r,n,'fire-b6',q['q'],['正しい','誤り'],0 if q['a'] else 1)
r='yousukeee/otsu6-cards'
primary=js(r,'index.html','ALL_CARDS'); alternate=js(r,'index (2).html','ALL_CARDS')
assert [q['id'] for q in primary] == [q['id'] for q in alternate]
# Reviewed wording/answer elaborations of the same cards, not additional learning items.
assert {a['id'] for a,b in zip(primary,alternate) if a!=b} == {16,17,20,21,35,59}
for q in js(r,'index.html','ALL_CARDS'): add(r,q['id'],'fire-b6',q['front'],model=q['back'])
r='altxxxtla-lab/shoubou-setsubishi-drill'; bank=js(r,'index.html','BANK')
for key,exam in [('common','github-fire-common'),('ko1','fire-a1'),('ko4','fire-a4'),('otsu6','fire-b6')]:
    for q in bank[key] if key=='common' else bank[key]['q']: add(r,q['i'],exam,q['q'],q['o'],q['a'])

added=0
for p in manifest['packs']:
    if p['id'] in before_ids: continue
    if not (p['examId'].startswith('fire-') or p['examId']=='github-fire-common'): continue
    assert p.get('localOnly') is True
    for q in read(ROOT/'build/private/web'/p['url']):
        assert (q['examId'],q['prompt'],q['options'],q['answer'],q['modelAnswer']) == expected[q['id']]
        assert '未検証' in q['source'] and re.search(r'/[a-f0-9]{40}/',q['sourceUrl'])
        assert not re.search(r'下図|上図|次の図|図に示|図の|写真に|写真の|下表|次の表|<img|<svg',q['prompt']+'\n'+'\n'.join(q['options']))
        added+=1
assert added == 1271
assert sum(e['count'] for e in manifest['exams'] if e['id'].startswith('fire-') or e['id']=='github-fire-common') == 1885
print(f'PASS: {added} new questions; original answer mappings and all existing packs preserved')
