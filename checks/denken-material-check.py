"""Verify official answers, source hashes and every rendered PDF pixel."""
import importlib.util,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('denken',ROOT/'scripts/prepare-denken-material.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
from PIL import Image

def main():
 sys.stdout.reconfigure(encoding='utf-8')
 raw=(m.OUT/'denken-report.json').read_bytes();report=json.loads(raw)
 prior=json.loads((m.SRC/'denken-baseline.json').read_bytes())['questions']
 paths={m.urlparse(q['sourceUrl']).path for q in prior if q.get('sourceUrl')};seen=set();images=set();sources=set();count=0
 for p in report['packs']:
  if p['status']!='prepared':continue
  assert m.urlparse(p['url']).path not in paths,'Already registered paper';paths.add(m.urlparse(p['url']).path)
  for source in p['sources']:
   if source['file'] not in sources:assert m.ipa.sha((m.SRC/source['file']).read_bytes())==source['sha256'];sources.add(source['file'])
  data=(m.OUT/p['file']).read_bytes();assert m.ipa.sha(data)==p['sha256'];rows=json.loads(data)
  assert len(rows)==p['count']==len(p['questions'])
  doc=m.fitz.open(m.SRC/p['sourceFile']);answer=m.fitz.open(m.SRC/p['answerFile']);solution={}
  if p['kind']=='third':
   keys=m.e.nonit.official_keys(answer,p)
   expected={re.sub(r'([ab])$',r'(\1)',k):str(v+1) for k,v in keys.items() if v is not None}
   if p['year']=='2014' and p['subject']=='機械':assert keys['8'] is None and len(expected)==21
  elif p['kind']=='secondary':
   solution=m.secondary_answers(answer,p['subject']);expected={k:None for k in solution}
  else:
   try:keys=m.e.denken_keys(answer,p)
   except AssertionError:keys,solution=m.primary_image_keys(answer,p)
   expected={k+('('+b+')' if b else ''):v for k,blanks in keys.items() for b,v in blanks.items()}
  assert set(expected)=={r['number'] for r in p['questions']}
  for q,r in zip(rows,p['questions']):
   assert q['id']==r['id'] and q['id'] not in seen;seen.add(q['id'])
   assert q['examId']==p['examId'] and q['year']==p['year'] and q['subject']==p['subject'] and q['sourceUrl']==p['url']
   if p['kind']=='third':assert q['options']==['1','2','3','4','5'] and str(q['answer']+1)==expected[r['number']]
   elif p['kind']!='secondary':assert q['modelAnswer']==expected[r['number']]
   assert q.get('answer')==r['answer']
   if p['pageMapping']=='whole-booklet':assert [i['page'] for i in r['images']]==list(range(len(doc)))
   if solution:assert [i['page'] for i in r['solutionImages']]==solution[r['number'].split('(')[0]]
   for field,original in [('images',doc),('solutionImages',answer)]:
    assert len(q[field])==len(r[field])
    for img,record in zip(q[field],r[field]):
     assert img['src']=='assets/github-material/'+record['file']
     if record['file'] in images:continue
     file=m.OUT/'assets'/record['file'];assert m.ipa.sha(file.read_bytes())==record['sha256']
     page=original[record['page']];assert list(page.rect)==record['rect']
     pix=page.get_pixmap(matrix=m.fitz.Matrix(1.5,1.5),alpha=False)
     with Image.open(file) as saved:assert saved.size==(pix.width,pix.height) and saved.convert('RGB').tobytes()==pix.samples
     images.add(record['file'])
   count+=1
  doc.close();answer.close();m.fitz.TOOLS.store_shrink(100)
  print('PASS',p['file'],p['count'],flush=True)
 assert count>0
 (m.OUT/'denken-verification.json').write_bytes(m.ipa.encode(dict(reportSha256=m.ipa.sha(raw),questions=count,officialAnswers='pass',originalPixels='pass',method='Official answer cells or unchanged standard-answer images; all source/pack/image hashes and original pixels. Ambiguous question headings retain the entire booklet. Representative visual review only.')))
 print('PASS Denken',count,'questions',len(images),'images')

if __name__=='__main__':main()
