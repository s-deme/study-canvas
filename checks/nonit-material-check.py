"""Run after fetching/preparing non-IT sources: python checks/nonit-material-check.py."""
import importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('nonit',ROOT/'scripts/prepare-nonit-material.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
tasks=json.loads((m.SRC/'nonit-discovery.json').read_bytes())['tasks']
by_file={t['sourceFile']:t for t in tasks}
for file in ['ecee-20261004_co_first_q01.pdf','ecee-20260524_co_second_q01.pdf','ecee-20241027_co_second_q01.pdf','ecee-20220529_co_second_q01.pdf']:
    task=by_file[file];starts=m.question_starts(m.fitz.open(m.SRC/file),task)
    assert [n for n,p,y in starts]==list(range(1,51)),file
task=by_file['ecee-20240818_ch_third_q01.pdf'];doc=m.fitz.open(m.SRC/task['answerFile'])
# Whole answer columns transcribed from the rendered official table, including hidden-number defects.
assert list(m.official_keys(doc,task).values())==[4,3,1,1,0,0,2,2,1,2,3,1,2,2,3,2,3,4,4,2,1,4]
assert list(m.official_keys(doc,{**task,'subject':'法規'}).values())==[1,3,2,2,2,3,4,2,3,0,2,1,4,2,3,4]
assert list(m.official_keys(doc,{**task,'subject':'電力'}).values())==[2,3,3,3,0,1,3,2,0,3,1,3,3,0,3,4,4,2,3,1]
assert list(m.official_keys(doc,{**task,'subject':'機械'}).values())==[4,1,2,2,1,2,4,3,1,2,2,0,1,4,1,2,4,1,1,0,1,3]
task=by_file['mhlw-doctor-116-A.pdf'];keys=m.official_keys(m.fitz.open(m.SRC/task['answerFile']),task)
assert keys['A001']==[2] and keys['A013']==[1,4] and keys['A071'] is None
report=json.loads((m.OUT/'nonit-report.json').read_bytes());packs=[p for p in report['packs'] if p['status']=='prepared']
assert {p['examId'] for p in packs}==set(m.NAMES)
pharm={int(e['number']):(q,e) for p in packs if p['examId']=='pharmacist' for q,e in zip(json.loads((m.OUT/p['file']).read_bytes()),p['questions'])}
assert len(pharm)==339
assert not set(pharm)&{92,199,220,221,287,316}
for number in (181,238,275,311,335):assert pharm[number][0]['options']==list('123456')
assert pharm[275][0]['answer']==5
assert min(r['page'] for r in pharm[197][1]['images'])==1 # Common case starts two pages before question 197.
assert '問196-197' in m.tidy(m.fitz.open(m.SRC/'mhlw-pharmacist-111-4.pdf')[1].get_text())
assert pharm[197][0]['type']=='multiple' and pharm[197][0]['answer']==[0,2]
print('PASS: official answer columns, numbering, alternatives excluded, six choices and shared pharmacist case')
