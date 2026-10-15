"""Re-extract original cover and official answer cells. No OCR-derived answer authority."""
import hashlib,importlib.util,json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('expansion',root/'scripts/expand-github-material.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
proof=json.loads((root/'private-data/material-transcription/answer-correspondence.json').read_bytes());sha=lambda raw:hashlib.sha256(raw).hexdigest()
for r in proof['records']:
    raw=(m.SRC/r['sourceFile']).read_bytes();assert sha(raw)==r['sourceSha256']
    with m.fitz.open(stream=raw,filetype='pdf') as doc:text=doc[0].get_text()
    assert sha(text.encode())==r['coverTextSha256']
    assert sorted({('AM' if v=='前' else 'PM') for v in re.findall(r'午(?:\s|ご)*([前後])',text)})==r['detectedSections']
total=0
for p in proof['corrections']:
    raw=(m.SRC/p['answerFile']).read_bytes();assert sha(raw)==p['answerSha256']
    with m.fitz.open(stream=raw,filetype='pdf') as doc:
        for r in p['questions']:
            page=doc[r['page']-1];words=page.get_text('words');labels=[w for w in words if re.fullmatch(r'(?:AM|PM|A|B)\d+',m.material.tidy(w[4]))]
            found=[w for w in labels if m.material.tidy(w[4])==r['label']];assert len(found)==1
            columns=sorted(set(round(w[0]) for w in labels));w=found[0];right=next((x-3 for x in columns if x>w[0]+15),page.rect.width)
            assert [m.material.tidy(c[4]) for c in m.material.at_row(words,w,right)]==r['cells'],r['key']
            assert [w[0]-3,w[1]-3,right,w[3]+3]==r['rect'];total+=1
assert not proof['unresolved']
print(f'PASS: {len(proof["records"])} original covers; {total} original answer rows across {len(proof["corrections"])} corrected papers; unchanged PDF hashes')
