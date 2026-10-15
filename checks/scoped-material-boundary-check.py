"""Independently bind saved question/common rectangles to fresh numbered source anchors."""
import importlib.util,json,re,sys
from pathlib import Path

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('scope',root/'scripts/extract-scoped-solution-text.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
read=lambda p:json.loads(p.read_bytes())
directory=Path(sys.argv[1]) if len(sys.argv)>1 else Path(read(root/'build/material-transcription/current.json')['directory'])
docs={};ranges={};checked=0
solutions=read(directory/'scoped-solution-evidence.json');cases=read(directory/'scoped-case-evidence.json')
for key,entry in [*[(k,v) for k,v in solutions.items() if v['kind']=='official-intent'],*cases.items()]:
    name=entry['sourceFile'];number=int(re.search(r'-q(\d+)$',key)[1])
    if name not in docs:
        raw=(root/name).read_bytes();assert m.sha(raw)==entry['sourceSha256']
        docs[name]=m.fitz.open(stream=m.images.source_pdf(name,entry['sourceSha256']),filetype='pdf')
        numbers=[int(x) for page in docs[name] for x in re.findall(r'第\s*(\d+)\s*問',m.norm(page.get_text('text')))]
        ranges[name]=m.intent_regions(docs[name],list(range(1,max(numbers)+1)))
    expected=ranges[name][number]
    is_case=entry is cases.get(key)
    own=[(e['page'],e['rect']) for e in entry['evidence'] if not is_case or e['role']=='question']
    assert own==expected,key+' own question and every continuation up to next anchor'
    if is_case:
        first=ranges[name][1][0];doc=docs[name]
        common=[(pn,[0,0,doc[pn].rect.width,first[1][1] if pn==first[0] else doc[pn].rect.height]) for pn in range(first[0]+1) if pn<first[0] or first[1][1]>0]
        assert [(e['page'],e['rect']) for e in entry['evidence'] if e['role']=='common']==common,key+' common case excludes all child questions'
    checked+=1
for doc in docs.values():doc.close()
actual={}
for pack in read(directory/'manifest.json')['packs']:
    if pack['examId']!='sme-consultant':continue
    data=read(directory/'web'/pack['url']);defaults=data.get('defaults',{}) if isinstance(data,dict) else {}
    passages={p['id']:p['text'] for p in data.get('passages',[])} if isinstance(data,dict) else {}
    for row in data['questions'] if isinstance(data,dict) else data:
        q={**defaults,**row}
        if q.get('passageId'):q['passage']=passages[q['passageId']]
        actual[q['examId']+'::'+q['id']]=q
for key,entry in solutions.items():
    q=actual[key];prefix='公式出題趣旨（原文）\n' if entry['kind']=='official-intent' else '公式正解・配点（原文）\n'
    assert q[entry['field']]==prefix+entry['text'],key+' actual application solution field'
    assert q.get('solutionImages',[])==[],key+' solution page removal'
for key,entry in cases.items():
    q=actual[key];assert (q['prompt'],q.get('passage',''))==(entry['prompt'],entry['passage']),key+' actual question/common fields'
    assert [i['src'] for i in q['images']]==[i['src'] for i in entry['crops']],key+' only corresponding crops'
result=dict(passed=True,questions=checked,sourcePDFs=len(docs),solutionFieldsBound=len(solutions),caseFieldsBound=len(cases),ownNextQuestionContinuationAndCommonBoundaries=True,evidenceHashes={file:m.sha((directory/file).read_bytes()) for file in ['scoped-solution-evidence.json','scoped-case-evidence.json']},fullVisualProofreading=False)
(directory/'scoped-boundary-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('PASS:',json.dumps(result))
