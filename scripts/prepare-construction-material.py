"""Archive architecture/civil papers; reuse the existing local material pipeline."""
import concurrent.futures,importlib.util,json,re,sys
from pathlib import Path
from urllib.parse import urljoin
ROOT=Path(__file__).resolve().parents[1]
def module(name,file):
 s=importlib.util.spec_from_file_location(name,ROOT/'scripts'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
fetch=module('construction_fetch','fetch-github-material.py');nonit=module('construction_nonit','prepare-nonit-material.py');ipa=nonit.ipa
SRC=ipa.SRC;OUT=ipa.OUT;fitz=ipa.fitz
SUBJECTS={'architect1':['計画','環境・設備','法規','構造','施工'],'architect2':['建築計画','建築法規','建築構造','建築施工'],'architect-wood':['建築計画','建築法規','建築構造','建築施工'],'building-equipment':['建築一般知識','建築法規','建築設備']}
NAMES=dict(re.findall(r'^([\w-]+)\|([^\r\n`]+)',(ROOT/'web/exams.mjs').read_text(encoding='utf-8'),re.M))
clean=lambda s:re.sub(r'\s+','',ipa.norm(re.sub('<[^>]+>',' ',s)))
def acquire():
 tasks=[];discovery=[]
 for code,exam in [('1k','architect1'),('2k','architect2'),('mk','architect-wood'),('bmee','building-equipment'),('ip','interior-planner')]:
  url=f'https://www.jaeic.or.jp/shiken/{code}/{code}-mondai.html'
  try:
   entry=fetch.fetch(url,f'construction-jaeic-{code}.html');discovery.append(entry);html=(SRC/entry['file']).read_text(encoding='utf-8')
   for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>',html,re.S):
    label=clean(row);year=re.search(r'(令和|平成)(元|\d+)年',label)
    row=re.sub(r'<!--.*?-->','',row,flags=re.S)
    urls=[urljoin(url,u) for u in re.findall(r'href=["\']([^"\']+\.pdf)',row)]
    if not year or not urls or not any(re.search(r'1st|gakka|_1_2|_3_4|gokakukiz|0622',u,re.I) for u in urls):continue
    y=str((2018 if year[1]=='令和' else 1988)+(1 if year[2]=='元' else int(year[2])))
    if any('2nd' in u for u in urls):continue
    if exam=='building-equipment':urls=[u for u in urls if f'bmee-{y}-' in u][:3]
    tasks.append(dict(kind='jaeic',examId=exam,year=y,term='学科',urls=urls[:-1],answerUrl=urls[-1],origin=url))
  except Exception as e:print(code,str(e),flush=True)
 html=(SRC/'construction-jctc.html').read_text(encoding='utf-8')
 names={'土木':'civil','管工事':'pipe','造園':'landscape','電気通信工事':'telecom'}
 for block in re.split(r'<p class="flexibleCenter_headline[^>]*>',html)[1:]:
  label=clean(block.split('</p>')[0]);m=re.search(r'令和(\d+)年度([12])級(.+?)施工管理',label)
  if not m:continue
  links=re.findall(r'href="([^"]+\.pdf)"[^>]*>(.*?)</a>',block,re.S)
  answers=[u for u,t in links if '正答' in clean(t)]
  qs=[u for u,t in links if '試験問題' in clean(t) and '第二次' not in clean(t)]
  if not answers or not qs:continue
  exam=names[m[3]]+'-management'+m[2]
  term='前期' if '前期' in label else '後期' if '後期' in label else '第一次検定'
  tasks.append(dict(kind='jctc',examId=exam,year=str(2018+int(m[1])),term=term,urls=qs,answerUrl=answers[0],origin='https://www.jctc.jp/mondai/'))
 html=(SRC/'construction-external.html').read_text(encoding='utf-8')
 pages=sorted(set(re.findall(r'href="(/pastproblems/(?:2doboku|1zou|2zou)/[^"?]+)"',html)))
 def external_page(path):
  record=fetch.fetch('https://doboku-torisetsu.com'+path,'construction-ext-'+path.replace('/','-').strip('-')+'.html')
  return (SRC/record['file']).read_text(encoding='utf-8')
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:html+=''.join(pool.map(external_page,pages))
 urls=sorted(set(re.findall(r'href=["\']([^"\']+\.pdf)',html)))
 groups={}
 for url in urls:
  m=re.search(r'/pastproblems/(1doboku|2doboku|1zou|2zou)/([RH])(\d+)([^/]*)\.pdf',url)
  if m:groups.setdefault((m[1],m[2],m[3]),[]).append((m[4],url))
 for (code,era,n),links in groups.items():
  exam=('civil' if 'doboku' in code else 'landscape')+'-management'+code[0];year=str((2018 if era=='R' else 1988)+int(n))
  for suffix,answer in links:
   if not suffix.endswith('_kaitou'):continue
   base=suffix.removesuffix('_kaitou')
   term='前期' if base in ('_1','_zenki') else '後期' if base in ('_2','_kouki') else '学科・第一次検定'
   if any(t['examId']==exam and t['year']==year and (code[0]=='1' or t['term']==term) for t in tasks):continue
   qs=[u for s,u in links if s in (base,base+'_A',base+'_B',base+'_gakka',base+'_mondai')]
   if qs:tasks.append(dict(kind='external',examId=exam,year=year,term=term,urls=qs,answerUrl=answer,origin='https://doboku-torisetsu.com/pastproblems'))
 def download(t):
  stem='construction-'+t['examId']+'-'+t['year']+'-'+('early' if t['term']=='前期' else 'late' if t['term']=='後期' else 'main')
  try:
   sources=[fetch.fetch(u,stem+f'-qs{i}.pdf') for i,u in enumerate(t['urls'])];ans=fetch.fetch(t['answerUrl'],stem+'-ans.pdf')
   return {**t,'sources':sources+[ans],'answerFile':ans['file'],'status':'downloaded','file':stem+'.json','provider':'CONSTRUCTION','localOnly':True}
  except Exception as e:return {**t,'status':'download-failed','reason':str(e)}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  result=list(pool.map(download,tasks))
 (SRC/'construction-discovery.json').write_bytes(ipa.encode(dict(discovery=discovery,tasks=result)))
 print('Tasks',len(result),'downloaded',sum(t['status']=='downloaded' for t in result),flush=True)
def numeric_rows(page):
 tokens=[]
 for block in page.get_text('rawdict')['blocks']:
  for line in block.get('lines',[]):
   run=[]
   for char in [c for span in line['spans'] for c in span['chars']]+[{'c':' '}]:
    value=ipa.norm(char['c'])
    if re.fullmatch('[0-9]',value):
     if run and char['bbox'][0]-run[-1][1][2]>3:
      tokens.append((''.join(v for v,b in run),(min(b[0] for v,b in run),min(b[1] for v,b in run),max(b[2] for v,b in run),max(b[3] for v,b in run))));run=[]
     run.append((value,char['bbox']))
    elif run:
     tokens.append((''.join(v for v,b in run),(min(b[0] for v,b in run),min(b[1] for v,b in run),max(b[2] for v,b in run),max(b[3] for v,b in run))));run=[]
 rows=[]
 for value,box in sorted(tokens,key=lambda t:(t[1][1],t[1][0])):
  row=next((r for r in rows if abs(r[0]-box[1])<3),None)
  if row is None:row=[box[1],[]];rows.append(row)
  row[1].append((int(value),(box[0]+box[2])/2))
 return [(y,sorted(cells,key=lambda c:c[1])) for y,cells in sorted(rows)]

def official_keys(doc,task):
 keys={};group=-1
 for page in doc:
  rows=numeric_rows(page)
  headers=[]
  for i,(y,cells) in enumerate(rows):
   consecutive=[v for v,x in cells]==list(range(cells[0][0],cells[0][0]+len(cells)))
   continuation=headers and cells[0][0]==headers[-1][2][-1][0]+1 and y-headers[-1][1]<90
   if consecutive and cells[-1][0]>5 and (len(cells)>=3 or continuation):headers.append((i,y,cells))
  for hi,(i,y,cells) in enumerate(headers):
   stop=headers[hi+1][1] if hi+1<len(headers) else y+(130 if task['examId'].startswith('architect') else 65)
   candidates=[(ay,[(v,x) for v,x in values if cells[0][1]-5<=x<=cells[-1][1]+5]) for ay,values in rows[i+1:] if y+5<ay<stop]
   def table_row(ay):
    if task['examId'].startswith('architect'):return True
    text=''.join(ipa.norm(char['c']) for block in page.get_text('rawdict')['blocks'] for line in block.get('lines',[]) for span in line['spans'] for char in span['chars'] if abs(char['bbox'][1]-ay)<3 and cells[0][1]-5<=(char['bbox'][0]+char['bbox'][2])/2<=cells[-1][1]+5)
    return not re.sub(r'[0-9\s]','',text)
   candidates=[(ay,values) for ay,values in candidates if values and all(1<=v<=5 for v,x in values) and table_row(ay)]
   if task['examId'].startswith('architect'):
    assert len(headers)==1 and len(candidates) in (4,5),'Architecture answer subject rows'
    for ay,values in candidates:
     group+=1
     for n,x in cells:
      found=[v-1 for v,ax in values if abs(ax-x)<5]
      keys[f'{group}:{n}']=found[0] if len(found)==1 else None
   else:
    if cells[0][0]==1:group+=1
    assert group>=0 and candidates,'Missing answer row'
    for n,x in cells:
     found=[v-1 for ay,values in candidates for v,ax in values if abs(ax-x)<5]
     key=f'{group}:{n}';assert key not in keys,'Duplicate official key'
     keys[key]=found[0] if len(found)==1 else sorted(set(found)) if len(found)>1 else None
 if task['examId']=='architect1':
  lengths=[20,20,30,30,25]
  assert all(a is None for k,a in keys.items() if int(k.split(':')[1])>lengths[int(k.split(':')[0])]),'Unexpected answer outside subject'
  keys={k:a for k,a in keys.items() if int(k.split(':')[1])<=lengths[int(k.split(':')[0])]}
 assert keys,'No native official answer table'
 return keys

def question_starts(doc):
 starts=[]
 for pn,page in enumerate(doc):
  lines=ipa.lines(page.get_text('dict',flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES))
  for line in lines:
   value=ipa.norm(''.join(s['text'] for s in line['spans'])).strip();box=line['bbox']
   if box[0]>150 or not re.match(r'^[〔【\[]\s*(?:N[oO]|問)',value):continue
   adjacent=sorted((l for l in lines if abs(l['bbox'][1]-box[1])<3 and box[2]-1<=l['bbox'][0]<150),key=lambda l:l['bbox'][0])
   value+=''.join(ipa.norm(''.join(s['text'] for s in l['spans'])) for l in adjacent)
   m=re.match(r'^[〔【\[]\s*(?:N[oO]\s*[.．]?|問\s*題)\s*(\d+)\s*[〕】\]]',value)
   assert m,('Incomplete question heading',pn,value)
   starts.append((int(m[1]),pn,box[1]))
 return starts

def prepare(task):
 if task['status']!='downloaded':return task
 try:
  keys=official_keys(fitz.open(SRC/task['answerFile']),task);rows=[];evidence=[];excluded=[];seen=set();group=-1;stem=Path(task['file']).stem
  for source in task['sources'][:-1]:
   doc=fitz.open(SRC/source['file']);starts=question_starts(doc);assert starts,'No native question headings'
   cache={};prior=0
   for i,(number,pn,y) in enumerate(starts):
    if number==1 or i==0:group+=1;prior=0
    assert number>prior,('Question numbering duplicate/order',number,prior);prior=number
    key=f'{group}:{number}';assert key in keys,('Missing official key',key)
    assert key not in seen;seen.add(key)
    answer=keys[key]
    end=starts[i+1][1] if i+1<len(starts) else len(doc)-1
    if i+1<len(starts) and starts[i+1][2]<70 and end>pn:end-=1
    pages=list(range(pn,end+1));text=''.join(ipa.norm(doc[p].get_text()) for p in pages)
    if answer is None or re.search(r'著作権.{0,30}(省略|掲載|削除)|問題.{0,10}(削除|省略)',text):
     excluded.append(dict(number=key,reason='正答不明・別正答許容または本文省略'));continue
    images=[];records=[]
    for p in pages:
     saved=OUT/'assets'/f'{Path(source["file"]).stem}-p{p+1:03}.png'
     if p not in cache and saved.exists():
      try:fitz.Pixmap(str(saved))
      except Exception:saved.unlink()
     image,record=nonit.picture(doc,p,Path(source['file']).stem,cache);images.append(image);records.append({**record,'sourceFile':source['file']})
    count=5 if '五肢' in ipa.norm(doc[0].get_text()) or task['examId'] in ('architect2','architect-wood') else 4
    options=list(map(str,range(1,count+1)))
    multi=isinstance(answer,list)
    assert all(0<=a<len(options) for a in (answer if multi else [answer]))
    subject=SUBJECTS[task['examId']][group] if task['examId'] in SUBJECTS else '学科' if len(task['sources'])==2 else f'問題{chr(65+group)}'
    title=f'{task["year"]}年度 {NAMES[task["examId"]]} {task["term"]} {subject} No.{number}'
    q=dict(id=stem+f'-s{group+1}-q{number:03}',examId=task['examId'],type='multiple' if multi else 'single',year=task['year'],term=task['term'],subject=subject,category='過去問',topic=title,
           prompt=title+'\n原本画像の該当問題を解答してください。科目内の問題番号です。',options=options,answer=answer,images=images,sourceUrl=source['url'],
           source='建築技術教育普及センター公開問題（個人利用）' if task['kind']=='jaeic' else '全国建設研修センター試験問題。'+('土木のトリセツ掲載の原本PDF' if task['kind']=='external' else '公式公開PDF'),
           explanation='掲載正答：'+','.join(options[a] for a in (answer if multi else [answer]))+'。理由解説は未収録です。実施当時の法令・規格を前提とします。',explanationSource='公表正答表（外部取得分は公式サイトとの独立照合未実施）' if task['kind']=='external' else '公式正答表')
    rows.append(q);evidence.append(dict(id=q['id'],number=key,answer=answer,sourceUrl=source['url'],images=records))
  expected={f'{g}:{n}' for g in range(group+1) for n in range(1,1+max(int(k.split(':')[1]) for k in keys if k.startswith(str(g)+':')))}
  assert expected<=set(keys),'Answer numbering gaps'
  excluded.extend(dict(number=k,reason='原本の問題見出しが欠落・非掲載。本文対応を確定できず除外') for k in sorted(set(keys)-seen))
  assert len(rows)+len(excluded)==len(keys),'Question/key count mismatch'
  assert rows,'No verified questions'
  return nonit.finish({**task,'sourceFile':task['sources'][0]['file'],'url':task['urls'][0],'subject':'学科','verificationLabel':'公表正答表のセル座標・問題番号・原本画像一致を検査。全問目視・理由解説は未実施。外部取得の正答は掲載表との照合。'},rows,evidence,excluded)
 except Exception as e:return {**task,'status':'pending-review','reason':str(e) or type(e).__name__}

def main():
 sys.stdout.reconfigure(encoding='utf-8')
 if '--fetch' in sys.argv:acquire();return
 tasks=json.loads((SRC/'construction-discovery.json').read_bytes())['tasks'];packs=[];papers=set()
 with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
  for result in pool.map(prepare,tasks):
   if result['status']=='prepared':
    repeated={s['file'] for s in result['sources'][:-1] if (result['examId'],s['sha256']) in papers}
    if repeated:
     data=json.loads((OUT/result['file']).read_bytes());kept=[];records=[]
     for q,e in zip(data,result['questions']):
      if e['images'][0]['sourceFile'] in repeated:result['excludedQuestions'].append(dict(number=e['number'],reason='取得経路違いの同一原本・問題。先行パックと重複'))
      else:kept.append(q);records.append(e)
     raw=ipa.encode(kept);(OUT/result['file']).write_bytes(raw);result.update(count=len(kept),questions=records,sha256=ipa.sha(raw))
     if not kept:result.update(status='duplicate-excluded',reason='全問が先行パックの同一原本と重複')
    if result['status']=='prepared':papers.update((result['examId'],s['sha256']) for s in result['sources'][:-1])
   packs.append(result);print(result['examId'],result['year'],result['status'],result.get('count',result.get('reason','')),flush=True)
 (OUT/'construction-report.json').write_bytes(ipa.encode(dict(packs=packs)))
if __name__=='__main__':main()
