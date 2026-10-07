"""Import released electrical/telecommunications originals using the existing archive pipeline."""
import concurrent.futures,importlib.util,json,re,sys
from pathlib import Path
from urllib.parse import urljoin,quote
ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
fetch=module('electricity_fetch','fetch-github-material.py');nonit=module('electricity_nonit','prepare-nonit-material.py');ipa=nonit.ipa
SRC=ipa.SRC;OUT=ipa.OUT;fitz=ipa.fitz
clean=lambda s:re.sub(r'\s+','',ipa.norm(re.sub('<[^>]+>',' ',s)))
NAMES=dict(re.findall(r'^([\w-]+)\|([^\r\n`]+)',(ROOT/'web/exams.mjs').read_text(encoding='utf-8'),re.M))
def acquire():
 tasks=[]
 html=(SRC/'electricity-radio.html').read_text(encoding='utf-8')
 codes={'sogo-tu-1':'radio-general1','sogo-tu-2':'radio-general2','sogo-tu-3':'radio-general3','kaijyo-tu-4':'radio-maritime4','koku-tu':'radio-aeronautical','riku-gi-1':'radio-land1','riku-gi-2':'radio-land2','riku-toku-1':'radio-land-special1','riku-toku-2':'radio-land-special2','riku-toku-3':'radio-land-special3','ama-1':'radio-amateur1','ama-2':'radio-amateur2','ama-3':'radio-amateur3','ama-4':'radio-amateur4'}
 for block in re.split(r'<dt>',html)[1:]:
  date=clean(block.split('</dt>')[0]);m=re.search(r'令和(\d+)年(\d+)月',date)
  if not m:continue
  options=re.findall(r'<option value="([^"]+\.pdf)">([^<]+)',block)
  urls={urljoin('https://www.nichimu.or.jp/kshiken/siken/index.html',u):label for u,label in options}
  for u,label in urls.items():
   if '問題' not in label or 'eigo' in u:continue
   code=next((c for c in codes if Path(u).name.startswith(c+'-')),None)
   if not code:continue
   a=u.removesuffix('.pdf')+'-kaito.pdf'
   if a not in urls:continue
   tasks.append(dict(kind='radio',examId=codes[code],year=str(2018+int(m[1])),term=m[2]+'月期',subject=label.split('＿')[0],url=u,answerUrl=a))
 for category in ['chief','charge']:
  html=(SRC/('electricity-'+category+'.html')).read_text(encoding='utf-8')
  for block in re.split(r'<dt>',html)[1:]:
   label=clean(block.split('</dt>')[0]);m=re.search(r'令和(\d+)年度第(\d+)回',label)
   if not m:continue
   qs=re.search(r'<div class="questions">(.*?)</div>',block,re.S);ans=re.search(r'<div class="answers">(.*?)</div>',block,re.S)
   if not qs or not ans:continue
   links=lambda b:{clean(t):u for u,t in re.findall(r'<a href="([^"]+\.pdf)"[^>]*>(.*?)</a>',b,re.S)}
   answers=links(ans[1])
   for subject,u in links(qs[1]).items():
    if subject not in answers:continue
    ids=['telecom-line'] if '線路' in subject else ['telecom-transmission'] if '伝送' in subject else ['telecom-transmission','telecom-line'] if category=='chief' else ['telecom-installer-'+{'第一級アナログ通信':'analog1','第二級アナログ通信':'analog2','第一級デジタル通信':'digital1','第二級デジタル通信':'digital2','総合通信':'general'}[subject]]
    for exam in ids:tasks.append(dict(kind=category,examId=exam,year=str(2018+int(m[1])),term='第'+m[2]+'回',subject=subject,url=u,answerUrl=answers[subject]))
 for code in ['denken1','denken2']:
  url='https://www.shiken.or.jp/chief/'+('first' if code=='denken1' else 'second')+'/qa/'
  pages=[(SRC/('electricity-'+code+'.html')).read_text(encoding='utf-8')]
  for path in sorted(set(re.findall(r'href="([^"]*index_\d+\.html)"',pages[0]))):
   r=fetch.fetch(urljoin(url,path),'electricity-'+code+'-'+Path(path).name);pages.append((SRC/r['file']).read_text(encoding='utf-8'))
  for u,label in re.findall(r'<a[^>]*href="([^"]+\.pdf)"[^>]*>(.*?)</a>',''.join(pages),re.S):
   label=clean(label);m=re.search(r'(令和|平成)(元|\d+)年度',label)
   if not m or '一次試験' not in label or not re.search(r'_q\d+\.pdf$',u):continue
   q=urljoin(url,u);a=re.sub(r'_q\d+\.pdf$','_a01.pdf',q)
   tasks.append(dict(kind='denken',examId=code,year=str((2018 if m[1]=='令和' else 1988)+(1 if m[2]=='元' else int(m[2]))),term='一次試験',subject=label.split('一次試験')[-1].removesuffix('科目'),url=q,answerUrl=a))
 html=(SRC/'electricity-radio-external.html').read_text(encoding='cp932')
 urls=set(re.findall(r'href="([^"]+\.pdf)',html,re.I))
 for path in sorted(urls):
  m=re.match(r'(\d{2})\.(\d{2})(kougaku|hoki)-Q\.pdf',path,re.I)
  if not m:continue
  answer=re.sub('-Q.pdf$','-A.pdf',path,flags=re.I)
  if answer not in urls:continue
  tasks.append(dict(kind='radio',examId='radio-amateur1',year=str(2000+int(m[1])),term=str(int(m[2]))+'月期',subject='無線工学' if m[3]=='kougaku' else '法規',url=urljoin('https://240sxa.net/1ama-qa.html',path),answerUrl=urljoin('https://240sxa.net/1ama-qa.html',answer),external=True))
 html=(SRC/'electricity-chief-external.html').read_text(encoding='utf-8');urls=set(re.findall(r'href="(https://[^" ]+\.pdf)',html))
 for u in sorted(urls):
  m=re.search(r'/([rh])(\d+)_(\d+)_(system|houki|setubi|senro)\.pdf$',u)
  if not m or u.removesuffix('.pdf')+'_ans.pdf' not in urls:continue
  y=str((2018 if m[1]=='r' else 1988)+int(m[2]));term='第'+m[3]+'回';subject={'system':'電気通信システム','houki':'法規','setubi':'伝送交換設備及び設備管理','senro':'線路設備及び設備管理'}[m[4]]
  ids=['telecom-line'] if m[4]=='senro' else ['telecom-transmission'] if m[4]=='setubi' else ['telecom-transmission','telecom-line']
  for exam in ids:
   if any(t['examId']==exam and t['year']==y and t['term']==term and t['subject']==subject for t in tasks):continue
   tasks.append(dict(kind='chief',examId=exam,year=y,term=term,subject=subject,url=u,answerUrl=u.removesuffix('.pdf')+'_ans.pdf',external=True))
 for code in ['general','land2']:
  html=(SRC/('electricity-'+code+'-external.html')).read_text(encoding='utf-8');urls=set(re.findall(r'<option value="([^"]+\.pdf)"',html))
  for u in sorted(urls):
   if code=='general':
    m=re.search(r'/(令和|平成)(\d+)年度第(\d+)回/sougou_question\.pdf$',u);a=u.replace('sougou_question.pdf','sougou_answer.pdf')
    if not m or a not in urls:continue
    year=str((2018 if m[1]=='令和' else 1988)+int(m[2]));term='第'+m[3]+'回';exam='telecom-installer-general';subject='総合通信';kind='charge'
   else:
    m=re.search(r'/(令和|平成)(\d+)年(\d+)月/[^/]*-(hoki|kogaku)\.pdf$',u);a=u.removesuffix('.pdf')+'-kaito.pdf'
    if not m or a not in urls:continue
    year=str((2018 if m[1]=='令和' else 1988)+int(m[2]));term=m[3]+'月期';exam='radio-land-special2';subject='法規' if m[4]=='hoki' else '無線工学';kind='radio'
   if any(t['examId']==exam and t['year']==year and t['term']==term and t['subject']==subject for t in tasks):continue
   tasks.append(dict(kind=kind,examId=exam,year=year,term=term,subject=subject,url=quote(u,safe=':/?=&%()-_.'),answerUrl=quote(a,safe=':/?=&%()-_.'),external=True))
 # Older papers remain available at public official URLs linked by archive indexes.
 for slot in ['2','4']:
  for code,exam in [('riku-toku-2','radio-land-special2'),('riku-toku-3','radio-land-special3')]:
   for subject,suffix in [('法規','hoki'),('無線工学','kogaku')]:
    url=f'https://www.nichimu.or.jp/vc-files/kshiken/pdf/siken/{slot}/{code}-{suffix}.pdf';answer=url.removesuffix('.pdf')+'-kaito.pdf'
    try:
     a=fetch.fetch(answer,f'electricity-retained-{code}-{slot}-{suffix}-a.pdf');text=clean(''.join(p.get_text() for p in fitz.open(SRC/a['file'])));m=re.search(r'(令和|平成)(\d+)年(\d+)月',text)
     if not m:continue
     tasks.append(dict(kind='radio',examId=exam,year=str((2018 if m[1]=='令和' else 1988)+int(m[2])),term=m[3]+'月期',subject=subject,url=url,answerUrl=answer))
    except Exception:pass
 tasks=list({(t['examId'],t['url']):t for t in tasks}.values())
 def download(t):
  stem='electricity-'+t['examId']+'-'+t['year']+'-'+ipa.sha((t['url']+t['term']).encode())[:10]
  try:
   q=fetch.fetch(t['url'],stem+'-q.pdf');a=fetch.fetch(t['answerUrl'],stem+'-a.pdf')
   return {**t,'sources':[q,a],'sourceFile':q['file'],'answerFile':a['file'],'file':stem+'.json','provider':'ELECTRICITY','status':'downloaded','localOnly':True}
  except Exception as e:return {**t,'status':'download-failed','reason':str(e)}
 with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
  result=[]
  for i,t in enumerate(pool.map(download,tasks)):
   result.append(t)
   if i%25==0:print('download',i+1,'/',len(tasks),flush=True)
 (SRC/'electricity-discovery.json').write_bytes(ipa.encode(dict(tasks=result)))
 print('Tasks',len(result),'downloaded',sum(t['status']=='downloaded' for t in result),flush=True)

def line_items(page):
 return [(ipa.norm(''.join(s['text'] for s in l['spans'])).strip(),l['bbox']) for l in ipa.lines(page.get_text('dict',flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES))]

def radio_keys(doc,task=None):
 keys={}
 for page in doc:
  words=page.get_text('words');labels=[]
  for w in words:
   m=re.fullmatch(r'〔?([AB])[-−ー](\d+)〕?',clean(w[4]))
   if m:labels.append((m[1]+'-'+m[2],w))
  for key,w in labels:
   if key.startswith('A'):
    cells=[c for c in words if c[0]>w[2] and c[0]<w[2]+100 and abs(c[1]-w[1])<3 and re.fullmatch(r'[1-5]',clean(c[4]))]
    assert len(cells)==1,('A answer cell',key);keys[key]={'':clean(cells[0][4])}
   else:
    # The B number sits at the centre of five consecutive kana answer rows.
    kana=sorted((c for c in words if w[2]<c[0]<w[2]+60 and abs(c[1]-w[1])<40 and clean(c[4]) in 'アイウエオ' and len(clean(c[4]))==1),key=lambda c:c[1])
    if [clean(c[4]) for c in kana]!=list('アイウエオ'):
     column=sorted(((k,v) for k,v in labels if k.startswith('B') and abs(v[0]-w[0])<20),key=lambda kv:kv[1][1])
     all_kana=sorted((c for c in words if w[2]<c[0]<w[2]+70 and column[0][1][1]-110<c[1]<column[-1][1][1]+100 and clean(c[4]) in 'アイウエオ' and len(clean(c[4]))==1),key=lambda c:c[1])
     assert len(all_kana)==5*len(column),('B column rows',key)
     offset=next(i for i,(k,v) in enumerate(column) if k==key)*5;kana=all_kana[offset:offset+5]
    assert [clean(c[4]) for c in kana]==list('アイウエオ'),('B answer rows',key)
    answer={}
    for c in kana:
     cells=[v for v in words if c[2]<v[0]<c[2]+75 and abs(v[1]-c[1])<3 and re.fullmatch(r'\d+',clean(v[4]))]
     assert len(cells)==1;answer[clean(c[4])]=clean(cells[0][4])
    keys[key]=answer
 if not keys and task and task['examId'].startswith('radio-land-special'):
  for page in doc:
   words=page.get_text('words');labels=[w for w in words if re.fullmatch(r'〔\d+〕',clean(w[4]))]
   lefts=[]
   for x in sorted(w[0] for w in labels):
    if not lefts or x-lefts[-1]>30:lefts.append(x)
   if task['examId']=='radio-land-special1':assert len(lefts)==2,'Two special radio variants'
   chosen=1 if task['subject'].endswith('B') else 0
   for w in labels:
    if task['examId']=='radio-land-special1' and abs(w[0]-lefts[chosen])>30:continue
    cells=[c for c in words if w[2]<c[0]<w[2]+100 and abs(c[1]-w[1])<3 and re.fullmatch('[1-5]',clean(c[4]))]
    key=clean(w[4]).strip('〔〕');assert len(cells)==1 and key not in keys;keys[key]={'':clean(cells[0][4])}
 assert keys;return keys

def telecom_keys(doc,task):
 keys={};group=-1
 for page in doc:
  words=page.get_text('words')
  labels=sorted(([box[0],box[1],box[2],box[3],clean(value)] for value,box in line_items(page) if re.fullmatch(r'(?:第)?問\d+|第\d+問',clean(value))),key=lambda w:w[1])
  for w in labels:
   n=int(re.search(r'\d+',clean(w[4]))[0])
   if n==1:group+=1
   if task['kind']=='chief':group=0
   y=w[1] if task['kind']=='chief' else w[1]+8.5
   cells=sorted((v for v in words if v[0]>w[2] and abs(v[1]-y)<4 and re.fullmatch(r'\d+|-',clean(v[4]))),key=lambda v:v[0])
   assert cells,('No telecom answer cells',n)
   values=[clean(c[4]) for c in cells];answer={k:v for k,v in zip('アイウエオカキクケコ',values) if v!='-'}
   if not answer:continue
   assert len(values)<=10 and f'{group}:{n}' not in keys;keys[f'{group}:{n}']=answer
 assert keys;return keys

def denken_keys(doc,task):
 subject=['理論','電力','機械','法規'].index(clean(task['subject']));keys={}
 for page in doc:
  words=page.get_text('words')
  headings=sorted((w for w in words if re.fullmatch(r'<(?:理論|電力|機械|法規)>',clean(w[4]))),key=lambda w:w[1])
  if len(headings)==4 and headings[-1][1]-headings[0][1]>100:
   h=next(w for w in headings if clean(w[4])=='<'+clean(task['subject'])+'>');bottom=next((w[1] for w in headings if w[1]>h[1]+10),page.rect.height)
   labels=sorted((w for w in words if h[1]<w[1]<bottom and re.fullmatch(r'\(\d+\)',clean(w[4]))),key=lambda w:(round(w[1]/3),w[0]));group=0
   for w in labels:
    n=int(re.search(r'\d+',clean(w[4]))[0])
    if n==1:group+=1
    cells=[c for c in words if 3<c[1]-w[1]<35 and abs((c[0]+c[2]-w[0]-w[2])/2)<5 and re.fullmatch(r'[ァ-ヶ]',clean(c[4]))]
    assert len(cells)==1,('Horizontal primary cell',group,n)
    keys.setdefault(str(group),{})[str(n)]=clean(cells[0][4])
   continue
  anchors=sorted(set(round(w[0],1) for w in words if clean(w[4])=='(1)'))
  assert len(anchors)==4,'Four primary exam answer columns required'
  left=anchors[subject]-3;right=anchors[subject+1]-3 if subject<3 else page.rect.width
  labels=sorted((w for w in words if left<w[0]<right and re.fullmatch(r'\(\d+\)',clean(w[4]))),key=lambda w:w[1]);group=0
  for w in labels:
   n=int(re.search(r'\d+',clean(w[4]))[0])
   if n==1:group+=1
   cells=[c for c in nonit.at_row(words,w,right) if re.fullmatch(r'[ァ-ヶ]',clean(c[4]))]
   assert len(cells)==1,('Primary answer cell',subject,group,n)
   keys.setdefault(str(group),{})[str(n)]=clean(cells[0][4])
 assert keys;return keys

def official_keys(doc,task):
 return radio_keys(doc,task) if task['kind']=='radio' else denken_keys(doc,task) if task['kind']=='denken' else telecom_keys(doc,task)

def question_starts(doc,task,ocr=False):
 starts=[];group=-1
 for pn,page in enumerate(doc):
  items=[(ipa.norm(''.join(s['text'] for s in l['spans'])).strip(),l['bbox']) for l in ipa.lines(ipa.layout(doc,pn,force_ocr=True)[0])] if ocr else line_items(page)
  for value,box in sorted(items,key=lambda item:(item[1][1],item[1][0])):
   value=ipa.norm(value)
   pattern=r'^〔\s*(\d+)\s*〕' if task['examId'].startswith('radio-land-special') else r'^([AB])\s*[-−ー]\s*(\d+)(?!\d)' if task['kind']=='radio' else r'^第\s*(\d+)\s*問' if task['kind']=='charge' else r'^[問間]\s*(\d+)(?:\s|$)' if task['kind']=='denken' else r'^問\s*(\d+)(?!\d)'
   m=re.match(pattern,value)
   if not m or box[0]>(page.rect.width if task['examId'] in ('radio-land-special2','radio-land-special3') else 160) or box[1]<20 or box[1]>page.rect.height-25:continue
   if task['kind']=='denken' and box[0]>100:continue
   if task['examId'].startswith('radio-land-special'):key=m[1]
   elif task['kind']=='radio':key=m[1]+'-'+m[2]
   elif task['kind']=='denken':key=m[1]
   else:
    n=int(m[1])
    if n==1:group+=1
    if task['kind']=='chief':group=0
    key=f'{group}:{n}'
   if starts and starts[-1][0]==key:continue
   starts.append((key,pn,box[1]))
 if not starts and not ocr:return question_starts(doc,task,True)
 return starts

def radio_options(doc,starts,i):
 key,pn,y=starts[i];ep,ey=starts[i+1][1:] if i+1<len(starts) else (len(doc)-1,doc[-1].rect.height)
 labels=set()
 for p in range(pn,ep+1):
  for value,box in line_items(doc[p]):
   if p==pn and box[1]<=y or p==ep and box[1]>=ey:continue
   m=re.match(r'^([1-5])(?:\s|$)',value)
   if m:labels.add(int(m[1]))
 return list(map(str,sorted(labels))) if labels in ({1,2,3,4},{1,2,3,4,5}) else []

def verified_starts(doc,task,keys):
 starts=question_starts(doc,task)
 if len(starts)!=len(keys) or {k for k,p,y in starts}!=set(keys):starts=question_starts(doc,task,True)
 assert len(starts)==len(keys) and {k for k,p,y in starts}==set(keys),('Question/answer headings',len(starts),len(keys),[k for k,p,y in starts])
 return starts

def paper_identity(doc,answer,task):
 if task['kind']!='radio':return
 qtext=clean(''.join(p.get_text() for p in doc));atext=clean(''.join(p.get_text() for p in answer))
 codes=lambda text:set(re.findall(r'[A-Z]{2,3}\d{3}',text))
 if codes(qtext) and codes(atext):assert codes(qtext)&codes(atext),'Question/answer paper code differs'
 m=re.search(r'(令和|平成)(\d+)年(\d+)月',atext)
 if m:
  assert str((2018 if m[1]=='令和' else 1988)+int(m[2]))==task['year'] and int(m[3])==int(re.search(r'\d+',task['term'])[0]),'Archive label differs from answer date'

def question_id(stem,key,blank):
 return stem+'-q'+key.replace(':','-')+('-b'+(blank if blank.isdigit() else str('アイウエオカキクケコ'.index(blank)+1)) if blank else '')

def prepare(task):
 if task['status']!='downloaded':return task
 try:
  doc=fitz.open(SRC/task['sourceFile']);answer=fitz.open(SRC/task['answerFile']);paper_identity(doc,answer,task);keys=official_keys(answer,task);starts=verified_starts(doc,task,keys)
  rows=[];evidence=[];cache={};stem=Path(task['file']).stem
  for i,(key,pn,y) in enumerate(starts):
   end=starts[i+1][1] if i+1<len(starts) else len(doc)-1
   if i+1<len(starts) and starts[i+1][2]<70 and end>pn:end-=1
   pages=list(range(pn,end+1));images,records=zip(*(nonit.picture(doc,p,stem,cache) for p in pages))
   subject=task['subject']
   if task['kind']=='charge':subject=['基礎','技術及び理論','法規'][int(key.split(':')[0])]
   # Each blank is a distinct answer task. Shared original pages retain its full context.
   for blank,value in keys[key].items():
    number=key+('('+blank+')' if blank else '');display=number.split(':')[-1];title=f'{task["year"]}年度 {NAMES[task["examId"]]} {task["term"]} {subject} 問{display}'
    options=radio_options(doc,starts,i) if task['kind']=='radio' and (key.startswith('A') or task['examId'].startswith('radio-land-special')) else []
    single=bool(options)
    q=dict(id=question_id(stem,key,blank),examId=task['examId'],type='single' if single else 'written',year=task['year'],term=task['term'],subject=subject,category='過去問',topic=title,
     prompt=title+'\n原本画像の該当問題・空欄だけに解答してください。'+('' if single else '選択肢の番号（電験は記号）を入力し、公表正答と比較して自己採点してください。'),images=list(images),sourceUrl=task['url'],source='出典：'+('日本無線協会' if task['kind']=='radio' else '電気技術者試験センター' if task['kind']=='denken' else '日本データ通信協会 電気通信国家試験センター')+'。'+('外部サイト掲載の原本PDF。' if task.get('external') else '公式公開PDF。')+'ページ画像に加工（本文・図表変更なし）。',
     explanation='公表正答：'+value+'。理由解説は未収録です。実施当時の制度・規格を前提とします。',explanationSource='公表正答表（外部取得分は発行団体サイトとの独立照合未実施）' if task.get('external') else '公式正答表')
    if single:
     assert value in options;q.update(options=options,answer=int(value)-1)
    else:q.update(modelAnswer=value,answer=None)
    rows.append(q);evidence.append(dict(id=q['id'],number=number,answer=q['answer'],modelAnswer=q.get('modelAnswer',''),images=list(records)))
  return nonit.finish({**task,'verificationLabel':'公表正答セル・原本問題番号と全画像画素一致。空欄は番号/記号入力の自己採点。外部取得分は掲載原本との照合。全問目視・理由解説未実施。'},rows,evidence,[])
 except Exception as e:return {**task,'status':'pending-review','reason':str(e) or type(e).__name__}

def main():
 sys.stdout.reconfigure(encoding='utf-8');(OUT/'assets').mkdir(parents=True,exist_ok=True)
 if '--fetch' in sys.argv:acquire();return
 tasks=json.loads((SRC/'electricity-discovery.json').read_bytes())['tasks'];packs=[];seen=set()
 with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
  for result in pool.map(prepare,tasks):
   if result['status']=='prepared':
    key=(result['examId'],result['sources'][0]['sha256'])
    if key in seen:result.update(status='duplicate-excluded',reason='同一原本を先行パックに収録')
    else:seen.add(key)
   packs.append(result);print(result['examId'],result['year'],result['subject'],result['status'],result.get('count',result.get('reason','')),flush=True)
 (OUT/'electricity-report.json').write_bytes(ipa.encode(dict(packs=packs)))
if __name__=='__main__':main()
