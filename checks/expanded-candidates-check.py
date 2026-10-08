"""Check source-to-answer mapping and unchanged packs for the October expansion."""
import hashlib, importlib.util, json, re, math
from pathlib import Path
from functools import lru_cache

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT/'private-data/github-candidates'
spec = importlib.util.spec_from_file_location('literal', ROOT/'scripts/github-literals.py')
literal = importlib.util.module_from_spec(spec); spec.loader.exec_module(literal)
@lru_cache(maxsize=None)
def read(file): return json.loads(file.read_bytes())
@lru_cache(maxsize=None)
def js(repo, file, name): return literal.assignment((SRC/repo/file).read_text(encoding='utf-8-sig'), name)

manifest = read(ROOT/'build/private/manifest.json')
before = read(SRC/'expansion-baseline.json')
assert before['questions'] == 100915
packs = {p['id']:p for p in manifest['packs']}
for pack in before['packs']:
    assert packs[pack['id']] == pack, 'Previous pack metadata changed: '+pack['id']
    assert hashlib.sha256((ROOT/'build/private/web'/pack['url']).read_bytes()).hexdigest() == pack['sha256']

expected = {'kosukekkk-ops/fe-master-app':2632, 'AzFukami/Touhan-Quiz':119,
            'ot6-shibainu/ot6-shibainu-pwa':240, 'kazuyan1004-a11y/fire-quiz-app':10,
            'onokumao-png/gokaku-denki-quiz':419}
checked = 0
for repo,count in expected.items():
    rows=[]
    for pack in manifest['packs']:
        if pack.get('repo') != repo: continue
        assert pack.get('localOnly') is True
        rows.extend(read(ROOT/'build/private/web'/pack['url']))
    assert len(rows)==count, (repo,len(rows),count)
    for q in rows:
        identity=q['source'].split(' / ',1)[1].split(' — ',1)[0]
        assert q['id']=='github-'+hashlib.sha256((repo+'|'+identity).encode()).hexdigest()[:24]
        assert '未検証' in q['source'] and q['term'] and q['explanation']
        assert re.search(r'/[a-f0-9]{40}/',q['sourceUrl'])
        if repo.startswith('kosukekkk'):
            path='/'.join(q['sourceUrl'].split('/')[6:])
            original=next(v for v in read(SRC/repo/path)['questions'] if v['questionId']==identity)
            assert not original.get('bodyHtml')
            assert q['prompt']==original['text'].strip() and q['passage']==original.get('program','')
            assert q['options']==original['choices'] and q['answer']==original['correctIndex']
            assert q['explanation'].startswith(original['explanation'])
        elif repo.startswith('AzFukami'):
            original=next(v for v in js(repo,'script.js','quizData') if str(v['questionNumber'])==identity)
            assert identity!='3' and q['prompt']==original['question'].strip()
            assert q['options']==original['options'] and q['answer']==original['answer']
        elif repo.startswith('ot6-'):
            original=next(v for v in read(SRC/repo/'questions.json') if str(v['no'])==identity)
            assert not original.get('visual') and q['prompt']==original['question'].strip()
            assert q['options']==list(original['choices'].values())
            assert q['answer']==list(original['choices']).index(original['answer'])
        elif repo.startswith('kazuyan'):
            original=next(v for v in js(repo,'index.html','initialQuestions') if v['id']==identity)
            assert q['examId']=='fire-b4' and q['prompt']==original['q'].strip()
            assert q['options']==original['choices'] and q['answer']==original['answer']
        else:
            original=next(v for v in js(repo,'src/data/questions.ts','questions') if str(v['id'])==identity)
            assert q['examId']=={'denki1':'electrician1','denki2':'electrician2'}[original['category']]
            assert q['prompt']==original['question'].strip()
            assert q['options']==[v.strip() for v in original['choices']] and q['answer']==original['answer']
            assert not re.search(r'図|写真|次の表|下表|表に示|表の',q['prompt']+'\n'+'\n'.join(q['options']))
        checked+=1
assert not any(p.get('repo')=='kids-jobai28/shoubou-quiz' for p in manifest['packs'])
assert manifest['questions']>=before['questions']+checked
# Independently recalculate every generated trace answer (never execute source code).
traces=read(SRC/'kosukekkk-ops/fe-master-app/docs/qualifications/fe/questions_b_generated.json')['questions']
families=set()
for q in traces:
    program=q['program']; family=q['questionId'].split('_')[1]; families.add(family)
    if family in ('asum','amax','cgt'):
        values=list(map(int,re.search(r'A ← \{([\d, ]+)\}',program)[1].split(',')))
        value=sum(values) if family=='asum' else max(values) if family=='amax' else sum(v>int(re.search(r'A\[i\] > (\d+)',program)[1]) for v in values)
    elif family in ('cdiv','srange','pow'):
        start,end=map(int,re.search(r'for \(i を (\d+) から (\d+) まで',program).groups())
        if family=='srange': value=sum(range(start,end+1))
        elif family=='cdiv': value=sum(i%int(re.search(r'i mod (\d+)',program)[1])==0 for i in range(start,end+1))
        else: value=int(re.search(r'r × (\d+)',program)[1])**(end-start+1)
    elif family=='halve':
        x=int(re.search(r'x ← (\d+)',program)[1]); value=0
        while x>1: x//=2; value+=1
    elif family=='gcd': value=math.gcd(int(re.search(r'a ← (\d+)',program)[1]),int(re.search(r'b ← (\d+)',program)[1]))
    else: raise AssertionError('Unchecked trace family: '+family)
    assert int(q['choices'][q['correctIndex']])==value, q['questionId']
assert len(traces)==102 and len(families)==8
print(f'PASS: {checked} source/answer mappings; all {before["questions"]} previous questions retained')
print('PASS: 102 generated pseudocode answers independently recalculated across 8 patterns')
