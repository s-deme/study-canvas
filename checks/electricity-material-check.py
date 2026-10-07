"""Verify imported answers, heading correspondence, hashes and every original pixel."""
import importlib.util,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('electricity',ROOT/'scripts/prepare-electricity-material.py');e=importlib.util.module_from_spec(s);s.loader.exec_module(e)
sys.path.insert(0,str(ROOT/'build/python-deps'))
from PIL import Image
def main():
 sys.stdout.reconfigure(encoding='utf-8')
 assert e.question_id('sample','0:1','ア')!=e.question_id('sample','0:1','イ')
 assert e.radio_keys(e.fitz.open(e.SRC/'electricity-sample-radio-a.pdf'))['A-1']=={'':'2'}
 qdoc=e.fitz.open(e.SRC/'electricity-sample-radio-q.pdf');adoc=e.fitz.open(e.SRC/'electricity-sample-radio-a.pdf')
 e.paper_identity(qdoc,adoc,dict(kind='radio',year='2026',term='9月期'))
 try:e.paper_identity(qdoc,adoc,dict(kind='radio',year='2025',term='9月期'))
 except AssertionError:pass
 else:raise AssertionError('Wrong archive year must be rejected')
 assert e.telecom_keys(e.fitz.open(e.SRC/'electricity-sample-chief-a.pdf'),dict(kind='chief'))['0:1']==dict(zip('アイウエオカ',['9','3','5','6','5','3']))
 assert e.telecom_keys(e.fitz.open(e.SRC/'electricity-sample-charge-a.pdf'),dict(kind='charge'))['1:1']['イ']=='6'
 assert e.denken_keys(e.fitz.open(e.SRC/'electricity-sample-denken-a.pdf'),dict(subject='理論'))['1']==dict(zip('12345','トワイヌル'))
 raw=(e.OUT/'electricity-report.json').read_bytes();report=json.loads(raw);checked=set();count=0
 for pack in report['packs']:
  if pack['status']!='prepared':continue
  e.fitz.TOOLS.store_shrink(100)
  for source in pack['sources']:assert e.ipa.sha((e.SRC/source['file']).read_bytes())==source['sha256']
  doc=e.fitz.open(e.SRC/pack['sourceFile']);answer=e.fitz.open(e.SRC/pack['answerFile']);e.paper_identity(doc,answer,pack);keys=e.official_keys(answer,pack);starts=e.verified_starts(doc,pack,keys);expected={}
  for i,(key,pn,y) in enumerate(starts):
   end=starts[i+1][1] if i+1<len(starts) else len(doc)-1
   if i+1<len(starts) and starts[i+1][2]<70 and end>pn:end-=1
   for blank,value in keys[key].items():expected[key+('('+blank+')' if blank else '')]=(value,list(range(pn,end+1)))
  data=(e.OUT/pack['file']).read_bytes();assert e.ipa.sha(data)==pack['sha256'];rows=json.loads(data)
  assert len(rows)==pack['count']==len(pack['questions'])==len(expected)
  assert len({q['id'] for q in rows})==len(rows),'Duplicate blank IDs'
  for q,r in zip(rows,pack['questions']):
   value,pages=expected[r['number']];assert q['id']==r['id'] and q['answer']==r['answer']
   assert (str(q['answer']+1) if q['type']=='single' else q['modelAnswer'])==value
   if q['type']=='single':
    i=next(i for i,(k,p,y) in enumerate(starts) if r['number']==k);assert q['options']==e.radio_options(doc,starts,i)
   assert q['sourceUrl']==pack['url'] and [v['page'] for v in r['images']]==pages
   assert len(q['images'])==len(r['images'])
   for image,v in zip(q['images'],r['images']):
    assert image['src']=='assets/github-material/'+v['file']
    if v['file'] in checked:continue
    saved=e.OUT/'assets'/v['file'];assert e.ipa.sha(saved.read_bytes())==v['sha256']
    page=doc[v['page']];assert list(page.rect)==v['rect'];pix=page.get_pixmap(matrix=e.fitz.Matrix(1.5,1.5),alpha=False)
    with Image.open(saved) as stored:assert stored.size==(pix.width,pix.height) and stored.convert('RGB').tobytes()==pix.samples,v['file']
    checked.add(v['file'])
   count+=1
  print('PASS',pack['file'],pack['count'],flush=True)
 (e.OUT/'electricity-verification.json').write_bytes(e.ipa.encode(dict(reportSha256=e.ipa.sha(raw),questions=count,officialAnswers='pass',originalPixels='pass',method='Native published answer cells and heading correspondence; source/pack/image hashes and every original pixel. Mirror answers checked against supplied originals, not independently confirmed with issuing body. Representative visual review only.')))
 print('PASS electricity',count,'questions',len(checked),'images')
if __name__=='__main__':main()
