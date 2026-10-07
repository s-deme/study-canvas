"""Verify construction archives, question mappings and every generated pixel."""
import importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('construction',ROOT/'scripts/prepare-construction-material.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)
sys.path.insert(0,str(ROOT/'build/python-deps'))
from PIL import Image
SRC=c.SRC;OUT=c.OUT

def main():
 sys.stdout.reconfigure(encoding='utf-8')
 sample=c.official_keys(c.fitz.open(SRC/'construction-architect2-2026-main-ans.pdf'),dict(examId='architect2'))
 assert [sample[f'0:{n}'] for n in range(1,11)]==[3,0,4,3,4,3,1,0,2,1]
 sample=c.official_keys(c.fitz.open(SRC/'construction-landscape-management2-2026-early-ans.pdf'),dict(examId='landscape-management2'))
 assert sample['0:37']==[0,1,2] and sample['0:39']==[0,2,3] and sample['0:40']==[1,3]
 raw=(OUT/'construction-report.json').read_bytes();report=json.loads(raw);checked=set();count=0
 for pack in report['packs']:
  if pack['status']!='prepared':continue
  docs={}
  for source in pack['sources']:
   assert c.ipa.sha((SRC/source['file']).read_bytes())==source['sha256']
   docs[source['file']]=c.fitz.open(SRC/source['file'])
  keys=c.official_keys(docs[pack['answerFile']],pack);expected={};group=-1
  for source in pack['sources'][:-1]:
   starts=c.question_starts(docs[source['file']]);assert starts
   for i,(n,pn,y) in enumerate(starts):
    if n==1 or i==0:group+=1
    key=f'{group}:{n}';assert key not in expected
    end=starts[i+1][1] if i+1<len(starts) else len(docs[source['file']])-1
    if i+1<len(starts) and starts[i+1][2]<70 and end>pn:end-=1
    expected[key]=(source['file'],list(range(pn,end+1)))
  data=(OUT/pack['file']).read_bytes();assert c.ipa.sha(data)==pack['sha256'];rows=json.loads(data)
  assert len(rows)==pack['count']==len(pack['questions'])
  assert len(rows)+len(pack['excludedQuestions'])==len(keys)
  assert {e['number'] for e in pack['questions']}|{e['number'] for e in pack['excludedQuestions']}==set(keys)
  for q,e in zip(rows,pack['questions']):
   assert q['id']==e['id'] and q['answer']==e['answer']==keys[e['number']]
   source,pages=expected[e['number']]
   assert source!=pack['answerFile'] and [r['page'] for r in e['images']]==pages
   assert q['sourceUrl']==e['sourceUrl']==next(s['url'] for s in pack['sources'] if s['file']==source)
   assert q['type']==('multiple' if isinstance(q['answer'],list) else 'single')
   cover=c.ipa.norm(docs[source][0].get_text())
   assert len(q['options'])==(5 if '五肢' in cover or q['examId'] in ('architect2','architect-wood') else 4)
   for image,r in zip(q['images'],e['images']):
    assert r['sourceFile']==source and image['src']=='assets/github-material/'+r['file']
    if r['file'] in checked:continue
    saved=OUT/'assets'/r['file'];assert c.ipa.sha(saved.read_bytes())==r['sha256']
    page=docs[source][r['page']];assert list(page.rect)==r['rect']
    pix=page.get_pixmap(matrix=c.fitz.Matrix(1.5,1.5),alpha=False)
    with Image.open(saved) as stored:assert stored.size==(pix.width,pix.height) and stored.convert('RGB').tobytes()==pix.samples
    checked.add(r['file'])
   count+=1
  print('PASS',pack['file'],pack['count'],flush=True)
 (OUT/'construction-verification.json').write_bytes(c.ipa.encode(dict(reportSha256=c.ipa.sha(raw),questions=count,officialAnswers='pass',originalPixels='pass',method='Published native answer cells, heading sequence and exact question page ranges; every archive/pack/image hash and original pixel. External mirror answers not independently confirmed with issuing body. Representative visual review only.')))
 print('PASS construction:',count,'questions,',len(checked),'page images')
if __name__=='__main__':main()
