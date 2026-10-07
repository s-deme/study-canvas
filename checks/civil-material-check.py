"""Run with python checks/civil-material-check.py; no network is required."""
import collections,hashlib,importlib.util,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('civil',ROOT/'scripts/prepare-civil-material.py')
civil=importlib.util.module_from_spec(spec);spec.loader.exec_module(civil)

class Page:
    def get_text(self,kind=None):
        if kind!='words':return '正答番号表'
        return [(10,10,20,20,'No'),(30,10,40,20,'正答'),
                (12,30,18,40,'1'),(32,30,38,40,'４'),
                (12,50,18,60,'2'),(32,50,38,60,'１'),
                (12,70,18,80,'2'),(32,70,38,80,'５')]
    rect=type('Rect',(),{'width':100})()
assert civil.official_keys([Page()])=={1:3},'Duplicated official labels must be excluded'
report=ROOT/'private-data/github-material/prepared/civil-report.json'
if report.exists():
    data=json.loads(report.read_bytes());count=0
    for pack in data['packs']:
        if pack['status']!='prepared':continue
        doc=civil.fitz.open(civil.SRC/pack['sourceFile']);keys=civil.official_keys(doc)
        # Read native table text in stream order, independently of the cell-coordinate parser.
        text=civil.ipa.norm(doc[-1].get_text())
        pairs=[(int(n),int(a)-1) for n,a in re.findall(r'(?:^|\n)(\d+)\n([1-5])(?=\n|$)',text)]
        counts=collections.Counter(n for n,a in pairs)
        stream={n:a for n,a in pairs if counts[n]==1}
        starts=civil.question_starts(doc)
        rows=json.loads((civil.OUT/pack['file']).read_bytes())
        assert len(rows)==pack['count']==len(pack['questions'])
        for q,e in zip(rows,pack['questions']):
            assert q['answer']==keys[e['number']]==e['answer']
            if '正答番号表' in text:assert q['answer']==stream[e['number']],'Native table stream and cell geometry disagree'
            assert q['options']==['1','2','3','4','5']
            pages={r['page'] for r in e['images']}
            assert next(p for n,p,y in starts if n==e['number']) in pages
            assert len(doc)-1 not in pages,'Question must not display the answer table'
        count+=len(rows)
    print('PASS: civil questions',count,'keys, headings, answer-page separation; duplicate-label rejection')
    manifest=ROOT/'build/private/manifest.json'
    baseline=ROOT/'private-data/github-material/civil-baseline.json'
    if manifest.exists() and baseline.exists():
        current=json.loads(manifest.read_bytes());old=json.loads(baseline.read_bytes())
        packs={p['id']:p for p in current['packs']}
        if any(p.startswith('archive-jinji-') for p in packs):
            assert sum(p['count'] for id,p in packs.items() if id.startswith('archive-jinji-'))==count
            for id,expected in old['packs'].items():
                assert id in packs,'Pre-existing pack missing: '+id
                raw=(ROOT/'build/private/web'/packs[id]['url']).read_bytes()
                assert hashlib.sha256(raw).hexdigest()==expected,'Pre-existing pack changed: '+id
            print('PASS: private build contains all civil questions;',len(old['packs']),'previous packs unchanged')
else:print('PASS: duplicate-label rejection (private archive unavailable)')
