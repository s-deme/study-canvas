"""Prepare marker review sheets; no corrections are approved by this script."""
import json,re,sys,unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'build/python-deps'))
import pymupdf as f
from PIL import Image,ImageDraw
SRC=ROOT/'private-data/ipa';OUT=ROOT/'build/material-review';OUT.mkdir(parents=True,exist_ok=True)
norm=lambda t:unicodedata.normalize('NFKC',t)
sources=json.loads((SRC/'sources.json').read_text(encoding='utf-8'))
adjustments=json.loads((SRC/'marker-adjustments.json').read_text(encoding='utf-8')) if (SRC/'marker-adjustments.json').exists() else {}
verified=json.loads((SRC/'verified-starts.json').read_text(encoding='utf-8')) if (SRC/'verified-starts.json').exists() else {}
proposed={};issues=[];review=[]
for source in sources:
 if source['kind']!='qs':continue
 name=source['file'];doc=f.open(SRC/name)
 if name in verified:continue
 if not all((SRC/'ocr'/f'{name}-{pn}.json').exists() for pn in range(len(doc))):continue
 ans=f.open(SRC/name.replace('_qs.pdf','_ans.pdf'))
 at=norm('\n'.join(p.get_text() for p in ans))
 nums=[int(n) for n in re.findall(r'^問\s*(\d+)',at,re.M)]
 count=max(nums) if nums else 0
 candidates=[]
 for pn in range(1,len(doc)):
  layout=json.loads((SRC/'ocr'/f'{name}-{pn}.json').read_text(encoding='utf-8'))
  lines=sorted([l for b in layout['blocks'] for l in b.get('lines',[])],key=lambda l:(l['bbox'][1],l['bbox'][0]))
  proper=[l for l in lines if re.match(r'^[問間]\s*\d+',norm(''.join(s['text'] for s in l['spans'])).strip()) and l['bbox'][0]<100]
  left=min((l['bbox'][0] for l in proper),default=None)
  for l in lines:
   x,y=l['bbox'][:2];t=norm(''.join(s['text'] for s in l['spans'])).strip();m=re.match(r'^[問間]\s*(\d+)',t)
   short=45<x<70 and re.match(r'^[A-Za-z0-9|\[\]!?]{1,7}(?:\s|$)',t) and (y<90 or left is not None and abs(x-left)<5)
   if source['subject'].startswith('pm') and y>120: continue
   if x<100 and y>45 and (m or short):candidates.append(dict(number=int(m[1]) if m else None,page=pn,x=x,y=y,text=t))
 rules=adjustments.get(name,{})
 candidates=[c for c in candidates if c['page'] not in rules.get('removePages',[])]
 candidates.extend(dict(number=None,page=pn,x=x,y=y,text=f'manual candidate {n}') for n,pn,x,y in rules.get('add',[]))
 candidates.sort(key=lambda c:(c['page'],c['y']))
 if len(candidates)!=count:
  issues.append(dict(file=name,expected=count,found=len(candidates),candidates=candidates));continue
 proposed[name]=[[i+1,c['page'],c['y']] for i,c in enumerate(candidates)]
 for i,c in enumerate(candidates):
  if c['number']!=i+1:review.append(dict(file=name,expected=i+1,**c))
(OUT/'proposed.json').write_text(json.dumps(proposed),encoding='utf-8')
(OUT/'issues.json').write_text(json.dumps(issues,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
for page in range((len(review)+39)//40):
 image=Image.new('RGB',(1200,40*48),'white');draw=ImageDraw.Draw(image)
 for i,r in enumerate(review[page*40:(page+1)*40]):
  doc=f.open(SRC/r['file']);p=doc[r['page']];pix=p.get_pixmap(matrix=f.Matrix(2,2),clip=f.Rect(r['x']-4,r['y']-5,r['x']+90,r['y']+17))
  crop=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
  image.paste(crop,(830,i*48));draw.text((5,i*48+12),f'{page*40+i}: {r["file"]} page {r["page"]+1} expected {r["expected"]}',fill='black')
 image.save(OUT/f'markers-{page}.png')
print(json.dumps(dict(ready=len(proposed),issues=[dict(file=i['file'],expected=i['expected'],found=i['found']) for i in issues],review=len(review)),ensure_ascii=False))
