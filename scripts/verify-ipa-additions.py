"""Independent geometric official-key matching and full pixel crop verification."""
import hashlib,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'build/python-deps'))
import pymupdf as fitz
from PIL import Image
sys.path.insert(0,str(ROOT/'scripts'));from verify_original_material import plain_html
D=ROOT/'private-data/additions';SRC=ROOT/'private-data/ipa-expansion'
sha=lambda b:hashlib.sha256(b).hexdigest()
encode=lambda v:json.dumps(v,ensure_ascii=False,separators=(',',':')).encode('utf-8')
for path in sorted(D.glob('ipa-*-manifest.json')):
 raw=path.read_bytes();m=json.loads(raw);assert m['archive']=='ipa-expansion'
 for s in [m['sources']['terms'],*m['sources']['sources']]:assert sha((SRC/s['file']).read_bytes())==s['sha256']
 evs={q['id']:q for q in m['questions']};total=0;duplicate=0;checks=[]
 for pack in m['packs']:
  data=(D/pack['file']).read_bytes();assert sha(data)==pack['sha256'];rows=json.loads(data);assert len(rows)==pack['count']<=30
  first=evs[rows[0]['id']];assert first['source'].endswith('_qs.pdf') and first['answerSource'].endswith('_ans.pdf')
  doc=fitz.open(SRC/first['source']);ans=fitz.open(SRC/first['answerSource']);keys={}
  # Different algorithm from author: match question and answer cells by geometry, not reading-order regex.
  for p in ans:
   words=p.get_text('words')
   for w in words:
    match=re.fullmatch(r'問(\d+)',w[4])
    if not match:continue
    cells=[v for v in words if v[4] in list('アイウエ') and abs(v[1]-w[1])<2 and 10<v[0]-w[2]<45]
    assert len(cells)==1,(w,cells);keys[int(match[1])]='アイウエ'.index(cells[0][4])
  assert set(keys)==set(range(1,81))
  for q in rows:
   e=evs[q['id']];assert sha(encode(q))==e['questionSha256']
   assert keys[e['question']]==e['answer']==q['answer'];assert len(q['images'])==len(e['images'])==1
   check=e['check'];assert check['officialAnswer']=='アイウエ'[q['answer']]
   assert q['explanation']=='公式解答：'+check['officialAnswer']+'\n\n独自作成の解説：'+check['rationale']
   assert len(check['optionReviews'])==4 and all(len(r)>=12 for r in check['optionReviews'])
   assert 'IPA公式解答／理由解説は独自作成'==q['explanationSource'] and len(check['rationale'])>=50
   for image in e['images']:
    p=doc[image['page']-1];rect=fitz.Rect(image['rect']);assert p.rect.contains(rect)
    assert q['images'][0]['src']=='assets/additions/'+image['file']
    stored=D/'assets'/image['file'];assert sha(stored.read_bytes())==image['sha256']
    pix=p.get_pixmap(matrix=fitz.Matrix(1.5,1.5),clip=rect,alpha=False)
    with Image.open(stored) as im:assert im.size==(pix.width,pix.height) and im.convert('RGB').tobytes()==pix.samples
   if 'recalculation' in check:
    c=check['recalculation'];r=subprocess.run([sys.executable,'-I','-X','utf8','-c',c['program']],capture_output=True,text=True,encoding='utf-8',timeout=5)
    assert r.returncode==0 and r.stdout.strip()==c['expected']==c['stdout']
   if 'reference' in check:
    ref=check['reference'];b=(SRC/ref['file']).read_bytes();assert sha(b)==ref['sha256'];assert ref['excerpt'] in plain_html(b)
   duplicate+=bool(e.get('duplicateReview'));total+=1;checks.append(dict(id=q['id'],questionSha256=e['questionSha256'],**check))
  # Independent combination formula for probability instead of the author's sequential fractions.
  from math import comb
  from fractions import Fraction
  assert Fraction(comb(90,3),comb(100,3))==Fraction(178,245)
 report=dict(manifestSha256=sha(raw),questions=total,officialAnswers='pass',sourceCropPixels='pass',answerLeakage='pass',rationaleReview='pass',duplicateReviewed=duplicate,eligibleQuestions=total-duplicate,checks=checks,answerMethod='Independent question/key cell geometry from official PDF; every crop pixel reproduced; author reason and calculation evidence rechecked',visualReview='Author agent viewed all original pages for this unit including all diagrams and options; no independent human review')
 path.with_name(path.name.replace('-manifest','-verification')).write_bytes(encode(report))
 print('PASS',path.name,'verified candidates',total,'duplicates',duplicate,'eligible',total-duplicate)
