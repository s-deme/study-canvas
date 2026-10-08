"""Compare every imported practice answer and choice with its pinned source data."""
import importlib.util, json, re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('literal', ROOT/'scripts/github-literals.py')
literal = importlib.util.module_from_spec(spec); spec.loader.exec_module(literal)
src = ROOT/'private-data/github-candidates'
report = json.loads((src/'prepared/report.json').read_bytes())
count = 0
for pack in report['packs']:
    if not pack['examId'].startswith('hazmat-b'): continue
    repo = pack['repo']; sources = {}
    for source in pack['sources']:
        file = source['path']; path = src/repo/file
        text = path.read_text(encoding='utf-8')
        if repo.startswith('akiina') and file.startswith('questions-'):
            start = re.search(r'(?:push\(\.\.\.|concat\()\s*', text).end()
            items = literal.Literal(text, start).value()
        elif repo.startswith('M-HMMY') and file.startswith('src/data/questions/'):
            items = literal.assignment(text, re.search(r'export const (\w+)', text)[1])
        elif repo.startswith('tetsu') and file == 'index.html':
            items = [dict(id=str(i),question=q['q'],choices=q['a'],answer=0) for i,q in enumerate(literal.assignment(text,'rawData'),1)]
        elif file.startswith('Resources/questions/class1_'):
            items = [dict(q,question=q['text'],answer=q['correct']) for q in json.loads(text)]
        else: continue
        sources[source['url']] = items
    rows = json.loads((src/'prepared'/pack['file']).read_bytes())
    for q in rows:
        matches = [original for original in sources[q['sourceUrl']] if original['question'].strip() == q['prompt'] and original['choices'] == q['options']]
        assert len(matches) == 1, q['id']
        original = matches[0]
        assert original['answer'] == q['answer'], q['id']
        if original.get('explanation'): assert original['explanation'] in q['explanation']
        for key,target in [('image','images'),('detailImage','solutionImages')]:
            if original.get(key): assert len(q[target]) == 1
        count += 1
assert count == 606, count
print('PASS: all 606 practice prompts, choices, source answers, explanations and diagram references')
