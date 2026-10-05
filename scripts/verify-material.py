"""Independent source hashes, official choice keys and decoded image checks."""
import hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'build/python-deps'))
import pymupdf
from PIL import Image
src=ROOT/'private-data/ipa';mat=ROOT/'private-data/material'
sources=json.loads((src/'sources.json').read_text(encoding='utf-8'))
for s in sources: assert hashlib.sha256((src/s['file']).read_bytes()).hexdigest()==s['sha256'],s['file']
verified=json.loads((src/'verified-starts.json').read_text(encoding='utf-8'))
questions=[s for s in sources if s['kind']=='qs']
assert all(s['file'] in verified for s in questions)
packs=json.loads((mat/'packs.json').read_text(encoding='utf-8'))
checked=0;images=set();covered=set()
for p in packs:
 stem=p['id'][:-len(p['examId'])-1];covered.add(stem+'_qs.pdf')
 rows=json.loads((mat/p['file']).read_text(encoding='utf-8'))
 for row in rows:
  for image in row['images']+row.get('solutionImages',[]): images.add(image['src'].split('/')[-1])
 if '_am' not in stem: continue
 d=pymupdf.open(src/(stem+'_ans.pdf'));text='\n'.join(page.get_text() for page in d)
 answers={int(n):'アイウエ'.index(a) for n,a in re.findall(r'問\s*(\d+)\s*([アイウエ])',text)}
 assert len(rows)==len(answers),(stem,len(rows),len(answers))
 for row in rows: assert row['answer']==answers[int(row['id'].rsplit('-q',1)[1])];checked+=1
assert covered=={s['file'] for s in questions}
for name in images:
 path=mat/'assets'/name
 with Image.open(path) as image:
  width,height=image.size;image.verify()
 page,rect=json.loads(path.with_suffix('.geometry.json').read_text())
 assert abs(width-(rect[2]-rect[0])*1.5)<2 and abs(height-(rect[3]-rect[1])*1.5)<2,name
audit=json.loads((mat/'audit.json').read_text(encoding='utf-8'))
for source in questions:
 used={page for q in audit['questions'] if q['file']==source['file'] for page in q['pages']}
 d=pymupdf.open(src/source['file'])
 for pn in range(min(used),len(d)-1):
  if pn+1 in used: continue
  page=d[pn];pix=page.get_pixmap(matrix=pymupdf.Matrix(.3,.3),colorspace=pymupdf.csGRAY,clip=pymupdf.Rect(20,30,page.rect.width-20,page.rect.height-30))
  assert sum(v<180 for v in pix.samples)/len(pix.samples)<=.005,(source['file'],pn+1,'omitted nonblank page')
report=dict(sources=len(sources),questionBooks=len(questions),officialChoiceAnswers=checked,decodedImages=len(images),sourceHashes='pass',coverage='pass',imageGeometry='pass',choiceAnswers='pass',nonblankPageCoverage='pass')
(mat/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
