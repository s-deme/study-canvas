"""Acquire and prepare real-estate papers for the private local collection."""
import json,re,sys
from urllib.parse import urljoin,quote
from concurrent.futures import ThreadPoolExecutor
from bs4 import BeautifulSoup
import importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
tour=module('estate_tour','prepare-tourism-material.py');ipa,fetch,nonit=tour.ipa,tour.fetch,tour.nonit
SRC,OUT,fitz=ipa.SRC,ipa.OUT,ipa.fitz
INDEXES={'takken':'https://www.retio.or.jp/exam/past_ques_ans/other/','management-chief':'https://www.kanrikyo.or.jp/kanri/mondaiseikai/index.html','chief-recent':'https://kanrikyo.or.jp/kanri/siken.html','mankan':'https://www.mankan.org/kakomondai.html'}
def acquire():
 tasks=[]
 for exam,url in INDEXES.items():
  record=fetch.fetch(url,'estate-index-'+exam+'.html');html=BeautifulSoup((SRC/record['file']).read_bytes(),'html.parser')
  for a in html.find_all('a',href=True):
   label=a.get_text(' ',strip=True);href=urljoin(url,a['href'])
   if '.pdf' not in href:continue
   if exam=='takken':
    if '試験問題' not in label:continue
    m=re.search(r'/([RHS])(\d+)[-_]',href);year={'R':2018,'H':1988,'S':1925}[m[1]]+int(m[2]);answer=href
   elif exam in ('management-chief','chief-recent'):
    if not ('mondai' in href or '問題' in label):continue
    if exam=='chief-recent' and '正解' not in label:continue
    m=re.search(r'(?:shiken_|/)([rh])(\d+)',href,re.I)
    if not m:continue
    year=(2018 if m[1].lower()=='r' else 1988)+int(m[2]);answer=href
   else:
    if '試験問題' not in label:continue
    m=re.search(r'令和([元０-９0-9]+)',label);n=1 if m[1]=='元' else int(ipa.norm(m[1]));year=2018+n;answer=urljoin(url,a.find_next('a',href=True)['href'])
   target='management-chief' if exam=='chief-recent' else exam
   href=quote(href,safe=':/%?=&');answer=quote(answer,safe=':/%?=&')
   if any(t['examId']==target and t['url']==href for t in tasks):continue
   stem=(f'estate-mankan-native-{year}' if target=='mankan' else f'estate-{target}-{year}')+('-dec' if target=='takken' and '_002' in href else '')
   # The archive may contain several links to the same year's paper.
   if any(t['file']==stem+'.json' for t in tasks):continue
   tasks.append(dict(provider='ESTATE',kind=target,examId=target,year=str(year),subject='全科目',term='公開過去問',localOnly=True,file=stem+'.json',sourceFile=stem+'.pdf',answerFile=stem+('-answer.pdf' if answer!=href else '.pdf'),url=href,answerUrl=answer))
 def get(t):
  try:
   t['sources']=[fetch.fetch(t['url'],t['sourceFile'])]
   if t['answerFile']!=t['sourceFile']:t['sources'].append(fetch.fetch(t['answerUrl'],t['answerFile']))
  except Exception as e:t['downloadError']=str(e)
  return t
 with ThreadPoolExecutor(max_workers=6) as pool:tasks=list(pool.map(get,tasks))
 (SRC/'estate-discovery.json').write_bytes(ipa.encode({'tasks':tasks}))
 for t in tasks:print(t['file'],t.get('downloadError','downloaded'))

def official_keys(doc,task):
 if task['examId']=='takken':
  reviewed_file=SRC/'estate-reviewed-keys.json'
  reviewed=(json.loads(reviewed_file.read_bytes()) if reviewed_file.exists() else {}).get(task['answerFile'])
  if reviewed:
   assert ipa.sha((SRC/task['answerFile']).read_bytes())==reviewed['sha256']
   return {str(i+1):a for i,a in enumerate(reviewed['answers'])}
  keys={n:a if isinstance(a,int) else None for n,a in tour.official_keys(doc,{'kind':'estate','answerFile':'same','sourceFile':'same'}).items()}
  lines=tour.native_lines(doc[-1])
  for text,b in lines:
   if text!='問':continue
   digits=[(t,c) for t,c in lines if t.isdigit() and 0<c[0]-b[2]<20 and abs(c[1]-b[1])<1]
   assert len(digits)==1
   n,c=digits[0];cx=(b[0]+c[2])/2
   cells=[(r[1],t) for t,r in lines if 0<r[1]-b[1]<65 and abs((r[0]+r[2])/2-cx)<15 and t in '1234' and len(t)==1]
   assert len(cells)==1 and n not in keys
   keys[n]=int(cells[0][1])-1
  assert set(keys)==set(map(str,range(1,51))),'Incomplete official answer table'
  return keys
 lines=tour.native_lines(doc[-1]);headers=[b for t,b in lines if re.sub(r'\s','',t) in ('問','問番号','問題番号','問題')];keys={}
 assert len(headers)==2,'Answer column headers missing'
 for h in headers:
  cx=(h[0]+h[2])/2
  for t,b in lines:
   t=re.sub(r'^問\s*','',t)
   if not t.isdigit() or not 1<=int(t)<=50 or abs((b[0]+b[2])/2-cx)>15 or b[1]<=h[3]:continue
   cells=[v for v,c in lines if b[2]<c[0]<b[2]+140 and abs(c[1]-b[1])<3 and (re.fullmatch(r'[1-4](?:[、,及び ]+[1-4])*',v) or v=='正解なし')]
   assert len(cells)==1,('Ambiguous answer',t,cells)
   values=sorted({int(v)-1 for v in re.findall('[1-4]',cells[0])});keys[str(int(t))]=values[0] if len(values)==1 else None
 assert set(keys)==set(map(str,range(1,51))),('Incomplete answers',len(keys))
 return keys

def rendered_ocr(doc,pn,task):
 cache=SRC/'ocr'/f"{task['sourceFile']}-estate-rendered-{pn}.json"
 if cache.exists():return json.loads(cache.read_bytes())
 page=doc[pn];pix=page.get_pixmap(matrix=fitz.Matrix(2.5,2.5));pix.set_dpi(180,180)
 ocr=fitz.open('pdf',pix.pdfocr_tobytes(language='jpn+eng',tessdata=str(ROOT/'build/tessdata')))
 sx,sy=page.rect.width/ocr[0].rect.width,page.rect.height/ocr[0].rect.height
 result=[(ipa.norm(''.join(span['text'] for span in line['spans'])).strip(),[line['bbox'][i]*(sx if i%2==0 else sy) for i in range(4)]) for line in ipa.lines(ocr[0].get_text('dict',flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES))]
 cache.write_bytes(ipa.encode(result));return result

def page_lines(doc,pn,task,force_ocr=False):
 native=tour.native_lines(doc[pn])
 if not force_ocr and not doc[pn].rotation and sum(len(t) for t,b in native)>300 and not any(re.search(r'[\x00-\x08]',t) for t,b in native):return native,False
 raw=rendered_ocr(doc,pn,task) if force_ocr or doc[pn].rotation else tour.ocr_lines(doc,pn,task['sourceFile']);groups=[]
 for t,b in sorted(raw,key=lambda row:(row[1][1],row[1][0])):
  group=next((g for g in reversed(groups[-3:]) if abs(g[0][1][1]-b[1])<4),None)
  if group is None:groups.append([(t,b)])
  else:group.append((t,b))
 merged=[]
 for group in groups:
  group.sort(key=lambda row:row[1][0]);merged.append((''.join(t for t,b in group),(min(b[0] for t,b in group),min(b[1] for t,b in group),max(b[2] for t,b in group),max(b[3] for t,b in group))))
 return merged,True

def header_number(doc,pn,y,task):
 cache=SRC/'ocr'/f"{task['sourceFile']}-header-{pn}-{int(y*10)}.json"
 if cache.exists():return json.loads(cache.read_bytes())
 page=doc[pn];native=tour.native_lines(page)
 boxes=[b for t,b in native if abs(b[1]-y)<3 and t.startswith(('〔','【','['))]
 left=min((b[0] for b in boxes),default=55 if task['examId']=='takken' else 80)-3
 rect=fitz.Rect(max(0,left),max(0,y-4),min(page.rect.width,left+90),min(page.rect.height,y+18))
 pix=page.get_pixmap(matrix=fitz.Matrix(4,4),clip=rect);pix.set_dpi(288,288)
 ocr=fitz.open('pdf',pix.pdfocr_tobytes(language='jpn+eng',tessdata=str(ROOT/'build/tessdata')))
 numbers=re.findall(r'(\d+)\s*[】〕\]}）)]',ipa.norm(ocr[0].get_text()))
 cache.write_bytes(ipa.encode(numbers));return numbers

def question_starts(doc,task):
 starts=[]
 for pn,page in enumerate(doc):
  if task['answerFile']==task['sourceFile'] and pn==len(doc)-1:continue
  lines,ocr=page_lines(doc,pn,task)
  if pn==0 and not any(re.match(r'^[【〔\[]\s*[問間]\s*[1-3]\s*[】〕\]]',''.join(t for t,b in lines[i:i+4])) for i in range(len(lines))):continue
  for i,(text,b) in enumerate(lines):
   heading=''.join(t for t,c in lines[i:i+4])
   pattern=r'^[【〔\[(［（][^\d]{1,6}(\d+)\s*[】〕\]］）)]' if ocr else r'^[【〔\[]\s*[問間]\s*(\d+)\s*[】〕\]]'
   m=re.match(pattern,heading)
   ocr_hint=(text.startswith(('【','〔')) and re.search(r'[問間0-9]',text[:10])) or text.startswith(('[Fl','(Fl','[Fi','(Fi'))
   is_header=m or (not ocr and (text.startswith('〔') or re.match(r'^[【〔\[]\s*[問間]',text))) or (ocr and b[0]<100 and ocr_hint)
   if b[0]<150 and is_header:
    starts.append((str(int(m[1])) if m else None,pn,b[1]))
 starts.sort(key=lambda row:row[1:])
 numbered=[row for row in starts if row[0] is not None and 1<=int(row[0])<=50]
 if [int(n) for n,p,y in numbered]==list(range(1,51)):starts=numbered
 if len(starts)<50:
  present={int(n) for n,p,y in starts if n is not None}
  for missing in sorted(set(range(1,51))-present):
   prior=[p for n,p,y in starts if n is not None and int(n)<missing];later=[p for n,p,y in starts if n is not None and int(n)>missing]
   lo=max(prior,default=1);hi=min(later,default=len(doc)-2 if task['answerFile']==task['sourceFile'] else len(doc)-1)
   candidates=[]
   for pn in range(lo,hi+1):
    for t,b in page_lines(doc,pn,task,True)[0]:
     m=re.match(r'^[【〔\[(［（][^\d]{1,6}(\d+)\s*[】〕\]］）)]',t)
     if m and int(m[1])==missing and b[0]<150 and not any(p==pn and abs(y-b[1])<12 for n,p,y in starts):candidates.append((str(missing),pn,b[1]))
   if len(candidates)==1:starts+=candidates
  starts.sort(key=lambda row:row[1:])
 assert len(starts)==50,('Incomplete headings',len(starts))
 for i,(n,p,y) in enumerate(starts):
  if n is None or int(n)!=i+1:
   raw=page_lines(doc,p,task,True)[0];nearby=[]
   for j,(t,b) in enumerate(raw):
    joined=''.join(v for v,c in raw[j:j+4])
    m=re.match(r'^[【〔\[(［（][^\d]{1,6}(\d+)\s*[】〕\]］）)]',joined)
    if m and b[0]<150 and abs(b[1]-y)<12:nearby.append(str(int(m[1])))
   if nearby!=[str(i+1)]:nearby=header_number(doc,p,y,task)
   assert nearby==[str(i+1)],('Unreadable native heading',i+1,p,y,nearby)
   starts[i]=(str(i+1),p,y)
 assert all(n is not None and int(n)==i+1 for i,(n,p,y) in enumerate(starts)),('Heading order mismatch',starts)
 return starts

def compact(text):return re.sub(r'[^\w一-龯ぁ-んァ-ヶ]','',ipa.norm(text))
def declared_paper(q):
 source=q.get('source','')
 if source.startswith('hangonkou-ux/takken-app / '):
  m=re.search(r'/ (平成|令和)(\d+|元)年-(\d+)',source)
  if m:return (q['examId'],str((1988 if m[1]=='平成' else 2018)+(1 if m[2]=='元' else int(m[2]))),str(int(m[3])))
 if source.startswith('pousan/mansion-exam-prediction / '):
  m=re.search(r'/ (20\d{2})-(\d+)',source)
  if m:return (q['examId'],m[1],str(int(m[2])))
 return None

def existing_questions():
 # ponytail: fixed import baseline; refresh this snapshot when adding new candidate sources.
 snapshot=SRC/'estate-existing.json'
 if snapshot.exists():rows=json.loads(snapshot.read_bytes())
 else:
  rows=[];manifest=json.loads((ROOT/'build/private/manifest.json').read_bytes())
  for p in manifest['packs']:
   if p['examId'] in ('takken','mankan','management-chief'):
    rows+=json.loads((ROOT/'build/private/web'/p['url']).read_bytes())
  snapshot.write_bytes(ipa.encode(rows))
 for q in rows:
  q['_paper']=declared_paper(q);q['_prompt']=compact(q['prompt']);q['_options']=[compact(v) for v in q.get('options',[])[:3]]
 return rows

def prepare(task,existing):
 try:
  assert 'downloadError' not in task,task.get('downloadError')
  doc=fitz.open(SRC/task['sourceFile']);keys=official_keys(fitz.open(SRC/task['answerFile']),task);starts=question_starts(doc,task)
  rows=[];evidence=[];excluded=[];cache={};stem=Path(task['file']).stem
  texts=[page_lines(doc,p,task)[0] if (p<len(doc)-1 or task['answerFile']!=task['sourceFile']) else tour.native_lines(doc[p]) for p in range(len(doc))]
  for i,(n,pn,y) in enumerate(starts):
   ep,ey=starts[i+1][1:] if i<49 else (len(doc)-2 if task['answerFile']==task['sourceFile'] else len(doc)-1,doc[-2 if task['answerFile']==task['sourceFile'] else -1].rect.height)
   segment='\n'.join(t for p in range(pn,ep+1) for t,b in texts[p] if (p!=pn or b[1]>=y-1) and (p!=ep or b[1]<ey or i==49))
   body=compact(segment)
   duplicate=next((q for q in existing if q['examId']==task['examId'] and ((q['_paper']==(task['examId'],task['year'],n) and q['answer']==keys[n] and '-dec' not in stem) or (len(q['_prompt'])>30 and q['_prompt'] in body and len(q.get('options',[]))==4 and all(v in body for v in q['_options'])))),None)
   if duplicate:excluded.append({'number':n,'reason':'既存の同年度・同設問番号・同正答、または本文と先頭3選択肢が一致','existingId':duplicate['id']});continue
   if keys[n] is None:excluded.append({'number':n,'reason':'複数許容正答・採点不能'});continue
   last=ep
   if i<49 and ep>pn and ey<65:last-=1
   images,records=map(list,zip(*(nonit.picture(doc,p,stem,cache) for p in range(pn,last+1))))
   title=f'{task["year"]}年 '+({'takken':'宅建','management-chief':'管理業務主任者','mankan':'マンション管理士'}[task['examId']])+f' 問{n}'
   if '-dec' in stem:title+='（12月試験）'
   q=dict(id=stem+f'-q{int(n):03}',examId=task['examId'],type='single',year=task['year'],term=task['term']+('（12月）' if '-dec' in stem else ''),subject=task['subject'],category='過去問',topic=title,prompt=title+'\n原本画像の該当問題を解答してください。試験実施当時の法令・制度を前提とする問題です。',options=list('1234'),answer=keys[n],images=images,sourceUrl=task['url'],source=f'出典：{title} 公式公開試験問題（本人用ローカル教材）。原本ページ画像。',explanation=f'公式正答：{keys[n]+1}。理由解説は未収録です。現在の法令とは異なる場合があります。',explanationSource='公式正解番号表')
   rows.append(q);evidence.append(dict(id=q['id'],number=n,answer=keys[n],images=records))
  assert rows,'All questions already present'
  return nonit.finish({**task,'verificationLabel':'公式正答セル・問題番号の照合・原本画像の画素一致（全問目視・理由解説は未実施）'},rows,evidence,excluded)
 except Exception as error:return {**task,'status':'pending-review','reason':str(error)}

def main():
 sys.stdout.reconfigure(encoding='utf-8')
 if '--fetch' in sys.argv:acquire();return
 tasks=json.loads((SRC/'estate-discovery.json').read_bytes())['tasks'];existing=existing_questions()
 from concurrent.futures import ProcessPoolExecutor
 with ProcessPoolExecutor(max_workers=4) as pool:packs=list(pool.map(prepare,tasks,[existing]*len(tasks)))
 (OUT/'estate-report.json').write_bytes(ipa.encode({'packs':packs}))
 for p in packs:print(p['file'],p['status'],p.get('count',p.get('reason')),flush=True)

if __name__=='__main__':main()
