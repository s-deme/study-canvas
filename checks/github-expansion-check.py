"""Run: python checks/github-expansion-check.py (archived PDFs required)."""
import importlib.util, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('expansion',ROOT/'scripts/expand-github-material.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

# Real rendered official table: AM1–AM50, including its multi-column layout.
expected=[3,1,4,2,1,2,1,2,2,3,2,3,4,4,3,2,3,3,4,2,3,3,3,4,4,4,2,4,1,3,1,4,1,1,2,1,2,4,1,1,2,2,1,4,1,4,3,3,1,4]
doc=m.fitz.open(m.SRC/'expansion-tp250428-05seitou.pdf')
keys=m.official_keys(doc,{'section':'AM'})
assert [keys[str(i)] for i in range(1,51)]==[[v-1] for v in expected]
assert keys['83']==[0,3] and keys['101']==[2,4]

# Distinguish multi-select in one cell from alternative accepted answer cells.
doc=m.fitz.open();page=doc.new_page()
for i,(label,values) in enumerate([('A001',['3']),('A002',['14']),('A003',['3','4']),('A004',['200'])]):
    page.insert_text((20,50+i*20),label)
    for j,value in enumerate(values):page.insert_text((90+j*35,50+i*20),value)
assert m.official_keys(doc,{'section':'AM'})=={'1':[2],'2':[0,3],'3':None,'4':None}

tasks=json.loads((m.SRC/'expansion-discovery.json').read_bytes())['tasks']
for year,exam in [('2015','nurse'),('2017','clinical-lab'),('2023','clinical-lab'),('2025','nurse')]:
    task=next(t for t in tasks if t['year']==year and t['examId']==exam and t['section']=='AM')
    starts=m.question_starts(m.fitz.open(m.SRC/task['sourceFile']),task)
    assert [n for n,p,y in starts]==list(range(1,121 if exam=='nurse' else 101))

report=json.loads((m.OUT/'expansion-report.json').read_bytes())
packs=[p for p in report['packs'] if p['status']=='prepared']
assert {p['examId'] for p in packs}==set(m.NAMES)
assert len({(p['examId'],p['url']) for p in packs})==len(packs)
for pack in packs:
    rows=json.loads((m.OUT/pack['file']).read_bytes())
    assert len(rows)==pack['count'] and len(rows)==len(pack['questions'])
    assert all(len(q['options'])==e['optionCount'] for q,e in zip(rows,pack['questions']))
    assert all(e['reason'] in ('deleted/alternative answer or numeric-entry question','option labels cannot be verified','separate figure booklet needed') for e in pack['excludedQuestions'])
print('PASS: official answer columns, alternatives, numeric entry, centered/right-aligned/split numbering, and',sum(p['count'] for p in packs),'new questions')
