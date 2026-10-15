import hashlib,importlib.util,json,re,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1];out=root/'build/material-answer-correspondence';out.mkdir(parents=True,exist_ok=True)
spec=importlib.util.spec_from_file_location('expansion',root/'scripts/expand-github-material.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
sha=lambda raw:hashlib.sha256(raw).hexdigest()
tasks={}
for p in (root/'private-data/github-material/prepared').glob('*report.json'):
    for task in json.loads(p.read_bytes()).get('packs',[]):
        if task.get('status')=='prepared' and task.get('provider') in ('MHLW-MEDICAL','MHLW-NUMERIC'):
            key=task['examId']+'::'+task['sourceFile'];tasks.setdefault(key,task)
records=[];corrections=[];unresolved=[]
for task in tasks.values():
    file=root/'private-data/github-material'/task['sourceFile'];raw=file.read_bytes()
    source=next(s for s in task['sources'] if s['file']==task['sourceFile']);assert sha(raw)==source['sha256']
    with m.fitz.open(stream=raw,filetype='pdf') as doc:text=doc[0].get_text()
    found={('AM' if v=='前' else 'PM') for v in re.findall(r'午(?:\s|ご)*([前後])',text)}
    record=dict(sourceFile=task['sourceFile'],sourceSha256=sha(raw),recordedSection=task.get('section'),detectedSections=sorted(found),coverText=text,coverTextSha256=sha(text.encode()),examId=task['examId'])
    records.append(record)
    if len(found)!=1:
        unresolved.append({**record,'reason':'Cover section requires direct visual comparison'});continue
    actual=next(iter(found))
    if actual==task.get('section'):continue
    assert task['provider']=='MHLW-NUMERIC',(task['sourceFile'],'Non-numeric answer table requires its own parser')
    answer=root/'private-data/github-material'/task['answerFile'];answer_sha=sha(answer.read_bytes());assert answer_sha==next(s['sha256'] for s in task['sources'] if s['file']==task['answerFile'])
    with m.fitz.open(answer) as doc:
        keys=m.official_keys(doc,{**task,'section':actual});table={}
        for page in doc:
            words=page.get_text('words');labels=[w for w in words if re.fullmatch(r'(?:AM|PM|A|B)\d+',m.material.tidy(w[4]))];columns=sorted(set(round(w[0]) for w in labels))
            for w in labels:
                label=m.material.tidy(w[4]);normalized=('AM'+label[1:] if label.startswith('A') and not label.startswith('AM') else 'PM'+label[1:] if label.startswith('B') else label)
                if not normalized.startswith(actual):continue
                right=next((x-3 for x in columns if x>w[0]+15),page.rect.width)
                cells=[m.material.tidy(c[4]) for c in m.material.at_row(words,w,right)]
                table[str(int(normalized[2:]))]=dict(label=label,cells=cells,page=page.number+1,rect=[w[0]-3,w[1]-3,right,w[3]+3])
    rows=[]
    for q in task['questions']:
        value=keys[q['number']]
        rows.append(dict(key=task['examId']+'::'+q['id'],number=q['number'],beforeAnswer=q['answer'],answer=value,optionCount=q['optionCount'],**table[q['number']]))
    corrections.append(dict(sourceFile=task['sourceFile'],sourceSha256=sha(raw),answerFile=task['answerFile'],answerSha256=answer_sha,beforeSection=task['section'],section=actual,subject='午前' if actual=='AM' else '午後',coverTextSha256=sha(text.encode()),questions=rows))
result=dict(sources=len(records),records=records,corrections=corrections,unresolved=unresolved)
(Path(sys.argv[1]) if len(sys.argv)>1 else out/'answer-correspondence-audit.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
changed=[q for p in corrections for q in p['questions'] if q['answer'] is not None and (q['answer'][0] if len(q['answer'])==1 else q['answer'])!=q['beforeAnswer']]
pending=[q for p in corrections for q in p['questions'] if q['answer'] is None or max(q['answer'])>=q['optionCount']]
print('Cover audit:',len(records),'sources;',len(corrections),'incorrect sections;',len(changed),'answer changes;',len(pending),'unresolved answers;',len(unresolved),'unresolved covers')
print('Mismatched files:',[p['sourceFile'] for p in corrections]);print('Unresolved answers:',pending)
