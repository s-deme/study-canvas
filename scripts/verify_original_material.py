"""Publish one reviewed original unit only after executing all checks.

Exercise text/check programs remain in private-data. No claim of official keys.
"""
import hashlib,json,subprocess,sys,unicodedata
from functools import lru_cache
from html import escape
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'private-data/additions'
ARCHIVE=ROOT/'private-data/original-foundations'
def encode(value): return json.dumps(value,ensure_ascii=False,separators=(',',':')).encode('utf-8')
def sha(data): return hashlib.sha256(data).hexdigest()
class Text(HTMLParser):
 def __init__(self):super().__init__(convert_charrefs=True);self.parts=[];self.skip=0
 def handle_starttag(self,tag,attrs):
  if tag in ('script','style'):self.skip+=1
 def handle_endtag(self,tag):
  if tag in ('script','style'):self.skip=max(0,self.skip-1)
 def handle_data(self,data):
  if not self.skip:self.parts.append(data)
def normalize(text):return ' '.join(unicodedata.normalize('NFKC',text).split())
def plain_html(raw):
 parser=Text();parser.feed(raw.decode('utf-8'));return normalize(' '.join(parser.parts))

@lru_cache(maxsize=4)
def pdf_reference_html(raw):
 """Deterministic private transcript; page layout remains authoritative in the PDF."""
 sys.path.insert(0,str(ROOT/'build/python-deps'))
 import pymupdf
 with pymupdf.open(stream=raw,filetype='pdf') as pdf:
  return ('<!doctype html><meta charset="utf-8">'+''.join(f'<pre id="page-{i+1}">{escape(p.get_text())}</pre>' for i,p in enumerate(pdf))).encode('utf-8')

def source_bytes(source,source_map):
 raw=(ARCHIVE/source['file']).read_bytes();assert sha(raw)==source['sha256']
 if 'derivation' in source:
  d=source['derivation'];assert d['method']=='pymupdf-text-to-html-v1'
  parent=source_map[d['file']];assert parent['file'].endswith('.pdf')
  pdf=(ARCHIVE/parent['file']).read_bytes()
  assert sha(pdf)==d['sha256']==parent['sha256'],'Derived reference parent changed'
  assert raw==pdf_reference_html(pdf),'Derived reference differs from PDF extraction'
 return raw
def check(item,source=None):
 if item.get('questionKind')=='knowledge':
  excerpt=item['referenceExcerpt'];assert len(excerpt)>=15
  assert normalize(excerpt) in plain_html(source),'Unmatched reference excerpt: '+item['slug']
  reviews=item['optionReviews'];assert len(reviews)==len(item['options'])
  assert all(isinstance(r,str) and len(r)>=12 for r in reviews)
  assert item['options'].count(item['correct'])==1
  return dict(method='knowledge-reference-review',referenceExcerpt=excerpt,correctOptionText=item['correct'],optionReviews=reviews,sourceSha256=sha(source),reviewer='author-agent; reference-grounded semantic review, no independent human review',reviewedOn='2026-10-05')
 result=subprocess.run([sys.executable,'-I','-X','utf8','-c',item['code']],capture_output=True,text=True,encoding='utf-8',timeout=5)
 assert result.returncode==0,(item['slug'],result.stderr)
 actual=result.stdout.strip()
 assert actual==item['correct'],(item['slug'],actual,item['correct'])
 assert item['options'].count(actual)==1,item['slug']
 return dict(method='python-3.12-execution' if item.get('questionKind','code')=='code' else 'independent-recalculation',program=item['code'],stdout=actual,pythonVersion=sys.version.split()[0])
def publish_unit(stem,exam,field,name,subject,items,terms_key='python-terms',attribution='Python Software Foundation, Python 3.12 Documentation',unit_term='自作・第1単元'):
 assert 1<=len(items)<=30,'Review small units before publication'
 assert len({v['slug'] for v in items})==len(items)
 source_map={s['file']:s for s in json.loads((ARCHIVE/'sources.json').read_text(encoding='utf-8')) if 'sha256' in s}
 sources=[];rows=[];evidence=[];coverage=set()
 for item in items:
  assert item['topic'] not in coverage,'Repeated learning objective in unit'
  coverage.add(item['topic'])
  source=source_map[item['source']+'.html']
  raw=source_bytes(source,source_map)
  assert item['locator'] in raw.decode('utf-8'),'Reference locator missing: '+item['locator']
  assert len(item['reason'])>=35 and len(set(item['options']))==len(item['options'])
  result=check(item,raw)
  explanationSource='独自作成の解説（根拠資料照合・選択肢別の内容確認済み）' if item.get('questionKind')=='knowledge' else '独自作成の解説（根拠資料照合・実行または再計算済み）'
  row=dict(id=stem+'-'+item['slug'],examId=exam,type='single',subject=subject,category=item.get('category',item['level']),topic=item['topic'],prompt=item['prompt'],options=item['options'],answer=item['options'].index(item['correct']),explanation=item['reason'],source='自作問題（根拠資料: '+attribution+'）',sourceUrl=source['url'],explanationSource=explanationSource,year='2026',term='2026-10-05作成')
  rows.append(row)
  evidence.append(dict(id=row['id'],examId=exam,answer=row['answer'],images=[],questionSha256=sha(encode(row)),reference=dict(file=source['file'],locator=item['locator'],url=source['url']),learningObjective=item['topic'],check=result,review=dict(status='pass',reviewedOn='2026-10-05',reviewer='author-agent; no independent human review claimed',rationale=item['reason'],uniqueness='この単元では'+item['topic']+'を一度のみ問う。既存本文との正規化重複はビルド時に除外。',distractors=' / '.join(item['optionReviews']) if item.get('questionKind')=='knowledge' else '他の選択肢は上記の計算・実行結果と一致しない。前提と出力順序を本文に明示。')))
  if source not in sources:sources.append(source)
  if 'derivation' in source:
   parent=source_map[source['derivation']['file']]
   if parent not in sources:sources.append(parent)
 terms=source_map[terms_key+'.html']
 source_bytes(terms,source_map)
 if 'derivation' in terms:
  for s in [terms,source_map[terms['derivation']['file']]]:
   if s not in sources:sources.append(s)
 pack_bytes=encode(rows);file=stem+'.json'
 manifest=dict(archive='original-foundations',exams=[dict(id=exam,name=name,field=field)],sources=dict(terms=terms,sources=sources),questions=evidence,packs=[dict(id=stem,file=file,examId=exam,year='2026',term=unit_term,subject=subject,field=field,kind='original',count=len(rows),sha256=sha(pack_bytes),verification='自作問題: 根拠資料・各問の根拠記述/再計算/コード実行・選択肢の一意性・解説を確認（公式解答照合なし）',sources=sources)])
 manifest_bytes=encode(manifest)
 # No manifest is installed until all questions pass. Evidence binds exact question bytes.
 (OUT/file).write_bytes(pack_bytes)
 (OUT/(stem+'-manifest.json')).write_bytes(manifest_bytes)
 report=dict(manifestSha256=sha(manifest_bytes),questions=len(rows),originalAnswers='pass',rationaleReview='pass',distinctCoverage='pass',answerMethod='Per-question methods recorded: execution, recalculation or reference-grounded knowledge review; source locators and unique answers checked',reviewLimit='Author agent reviewed wording and reasoning; no independent human review',checks=[dict(id=e['id'],**e['check']) for e in evidence])
 (OUT/(stem+'-verification.json')).write_bytes(encode(report))
 print(stem,len(rows),'verified original questions')
if __name__=='__main__':
 for path in sorted(OUT.glob('original-*-manifest.json')):
  raw=path.read_bytes();m=json.loads(raw)
  report=json.loads(path.with_name(path.name.replace('-manifest','-verification')).read_bytes())
  assert report['manifestSha256']==sha(raw)
  source_bytes(m['sources']['terms'],{s['file']:s for s in [m['sources']['terms'],*m['sources']['sources']]})
  for pack in m['packs']:
   data=(OUT/pack['file']).read_bytes();assert sha(data)==pack['sha256']
   rows=json.loads(data);by_id={r['id']:r for r in rows}
   for e in m['questions']:
    row=by_id[e['id']];assert sha(encode(row))==e['questionSha256']
    ref=e['reference'];s=next(s for s in pack['sources'] if s['file']==ref['file'])
    source=source_bytes(s,{s['file']:s for s in pack['sources']});assert ref['locator'] in source.decode('utf-8')
    assert e['review']['rationale']==row['explanation']
    if e['check']['method']=='knowledge-reference-review':
     result=check(dict(slug=row['id'],questionKind='knowledge',referenceExcerpt=e['check']['referenceExcerpt'],optionReviews=e['check']['optionReviews'],correct=row['options'][row['answer']],options=row['options']),source)
     assert result==e['check']
    else:check(dict(slug=row['id'],code=e['check']['program'],correct=row['options'][row['answer']],options=row['options']))
  print('PASS',path.name,report['questions'])
