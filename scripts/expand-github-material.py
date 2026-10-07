"""Archive and prepare unregistered nursing/laboratory exam originals found via GitHub."""
import concurrent.futures, importlib.util, json, re, sys
from pathlib import Path
from urllib.parse import urlparse, quote

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('nonit_fetch', ROOT / 'scripts/fetch-nonit-material.py')
fetch = importlib.util.module_from_spec(spec); spec.loader.exec_module(fetch)
spec = importlib.util.spec_from_file_location('nonit_prepare', ROOT / 'scripts/prepare-nonit-material.py')
material = importlib.util.module_from_spec(spec); spec.loader.exec_module(material)
SRC, OUT, fitz = material.SRC, material.OUT, material.fitz
NAMES = {'nurse': '看護師国家試験', 'public-health-nurse': '保健師国家試験',
         'midwife': '助産師国家試験', 'clinical-lab': '臨床検査技師国家試験'}
encode, sha, norm = material.ipa.encode, material.ipa.sha, material.norm

def acquire():
    discovery = [fetch.fetcher.fetch('https://raw.githubusercontent.com/seika759931-cloud/quiz-app_web/9170fb73d67b776a7a216a6129df2d74c87b2789/mondai.csv', 'nurse-github.csv')]
    for number in range(66, 70):
        for section in ('AM', 'PM'):
            path = f'({number}{section})臨床検査技師問題.jsonl'
            discovery.append(fetch.fetcher.fetch('https://raw.githubusercontent.com/bioinfo-tsukuba/KensagishiQA/7ad9c85b789193567f81b1a8431d33dba791223f/' + quote(path), f'clinical-lab-github-{number}-{section}.txt'))
    topics = {'file': 'mhlw-topics.html', 'url': 'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/topics_150873_139_140.html'}
    selected = {}
    for url, label in fetch.links(topics):
        if '問題' not in label or not any(n in label for n in ('看護師', '臨床検査技師')): continue
        year = re.search(r'(20\d\d)年', label)
        if year: selected.setdefault((year[1], 'nursing' if '看護師' in label else 'lab'), url)
    pages = []; tasks = []
    for (year, kind), url in sorted(selected.items()):
        page = fetch.fetcher.fetch(url, f'expansion-{kind}-{year}-index.html'); pages.append(page)
        def original_url(u):
            if '/stf/seisakunitsuite/bunya/dl/' in u:
                name=Path(urlparse(u).path).name
                base=f'https://www.mhlw.go.jp/topics/{year}/04/dl/' if name.startswith('tp_siken') else 'https://www.mhlw.go.jp/seisakunitsuite/bunya/kenkou_iryou/iryou/topics/dl/'
                return base+name
            return u
        pdfs = {original_url(u) for u, label in fetch.links(page) if u.endswith('.pdf')}
        print('Index', kind, year, len(pdfs), flush=True)
        pairs = []
        for qurl in sorted(pdfs):
            match = re.search(r'-(03|04|05|07)([ab])_01\.pdf$', qurl)
            if not match: continue
            code, section = match.groups()
            exam = {'03':'public-health-nurse', '04':'midwife', '05':'nurse', '07':'clinical-lab'}[code]
            answer = re.sub(r'[ab]_01\.pdf$', 'seitou.pdf', qurl)
            if answer not in pdfs: continue
            pairs.append((qurl,answer,exam,'AM' if section=='a' else 'PM'))
        if int(year)<2017:
            # Historical pages name files differently; their headings/anchor labels identify each paper.
            group=None; groups={}
            html=fetch.html(page)
            for token in re.finditer(r'<h[1-6]\b[^>]*>(.*?)</h[1-6]>|<a\b[^>]*href=["\']([^"\']+\.pdf)["\'][^>]*>(.*?)</a>',html,re.S|re.I):
                if token[1]:
                    label=norm(re.sub('<[^>]+>','',token[1]))
                    matches=[exam for exam,name in NAMES.items() if name.replace('国家試験','') in label]
                    if len(matches)==1: group=matches[0] if '追加試験' not in label else None
                elif group and token[2]:
                    label=norm(re.sub('<[^>]+>','',token[3])); u=original_url(fetch.urljoin(page['url'],token[2]))
                    if '別冊' not in label and 'ルビ' not in label:
                        key='AM' if '午前' in label else 'PM' if '午後' in label else 'answer' if '正答' in label else None
                        if key:groups.setdefault(group,{})[key]=u
            for exam,urls in groups.items():
                if 'answer' in urls:
                    pairs.extend((urls[s],urls['answer'],exam,s) for s in ('AM','PM') if s in urls)
            if not pairs:  # 2010–2012 links use generic PDF captions inside table cells.
                for qurl in sorted(pdfs):
                    m=re.search(r'(josan|hoken|kango|rinken)_(01|02|03|am1?|pm)\.pdf$',qurl)
                    if not m:continue
                    tag,s=m.groups();exam={'josan':'midwife','hoken':'public-health-nurse','kango':'nurse','rinken':'clinical-lab'}[tag]
                    if s in ('am','am1','pm'): section='PM' if s=='pm' else 'AM';answer=qurl[:m.start(2)-1]+'.pdf'
                    else:
                        pm='02' if tag=='hoken' else '03'
                        if s not in ('01',pm):continue
                        section='AM' if s=='01' else 'PM'
                        answer=qurl[:m.start(2)]+('03' if tag=='hoken' else '05' if tag=='rinken' else '04')+'.pdf'
                    if answer in pdfs:pairs.append((qurl,answer,exam,section))
        for qurl,answer,exam,section in pairs:
            stem = 'expansion-' + Path(urlparse(qurl).path).stem
            tasks.append(dict(provider='MHLW-NUMERIC', examId=exam, year=year, term=year+'年度',
                              subject='午前' if section=='AM' else '午後', section=section,
                              file=stem+'.json', sourceFile=stem+'.pdf', url=qurl, answerUrl=answer,
                              answerFile='expansion-'+Path(urlparse(answer).path).name))
    for task in tasks:
        try: fetch.fetcher.fetch(task['answerUrl'], task['answerFile'])
        except Exception: pass  # A broken historical link must not stop other exam years.
    def download(task):
        try:
            sources = [fetch.fetcher.fetch(task['url'], task['sourceFile']), fetch.fetcher.fetch(task['answerUrl'], task['answerFile'])]
            return {**task, 'sources': sources, 'status': 'downloaded'}
        except Exception as error: return {**task, 'status': 'pending-download', 'reason': str(error)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        acquired = []
        for task in pool.map(download, tasks):
            acquired.append(task); print('Archived', len(acquired), '/', len(tasks), task['status'], flush=True)
    (SRC/'expansion-discovery.json').write_bytes(encode(dict(discovery=discovery, pages=pages, tasks=acquired)))

def official_keys(doc, task):
    keys = {}
    for page in doc:
        words = page.get_text('words')
        labels = [w for w in words if re.fullmatch(r'(?:AM|PM|A|B)\d+', material.tidy(w[4]))]
        columns = sorted(set(round(w[0]) for w in labels))
        for w in labels:
            label = material.tidy(w[4])
            if label.startswith('A') and not label.startswith('AM'): label='AM'+label[1:]
            if label.startswith('B'): label='PM'+label[1:]
            right = next((x-3 for x in columns if x>w[0]+15), page.rect.width)
            cells = [material.tidy(c[4]) for c in material.at_row(words, w, right)]
            assert label not in keys, 'Repeated official question label'
            value = cells[0] if len(cells)==1 else ''
            # Other accepted answer columns and numeric-entry answers are excluded.
            keys[label] = [int(c)-1 for c in value] if re.fullmatch(r'[1-5]+', value) and len(set(value))==len(value) else None
    selected = {int(k[2:]):v for k,v in keys.items() if k.startswith(task['section'])}
    assert selected and sorted(selected)==list(range(1,max(selected)+1)), 'Incomplete official answer table'
    return {str(n):v for n,v in selected.items()}

def question_starts(doc, task):
    candidates = []
    for pn, page in enumerate(doc):
        if pn==0: continue  # Cover includes the exam edition in the same bold font.
        rows={}
        for line in material.ipa.lines(page.get_text('dict', flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)):
            for span in line['spans']:
                text = norm(span['text']).strip(); x,y = span['bbox'][:2]
                if re.fullmatch(r'\d{1,3}', text) and ('Bold' in span['font'] or 'Gothic' in span['font']) and 40<x<95 and 40<y<page.rect.height-40 and span['size']>=9.9:
                    rows.setdefault(round(y,1),[]).append((x,span['bbox'][2],text,y))
        for spans in rows.values():
            spans.sort(); value=''.join(s[2] for s in spans)
            if len(value)<=3: candidates.append((int(value),pn,spans[0][3],max(s[1] for s in spans),spans[0][0]))
    candidates.sort(key=lambda v:(v[1],v[2]))
    first=next((s for s in candidates if s[0]==1),None)
    if first is None:return []
    anchors=[first,next((s for s in candidates if s[0]==10),first)]
    return [(n,p,y) for n,p,y,right,left in candidates if min(min(abs(right-a[3]),abs(left-a[4]),abs((left+right-a[3]-a[4])/2)) for a in anchors)<1]

def segments(doc, starts, index):
    number,pn,y = starts[index]
    ep,ey = starts[index+1][1:] if index+1<len(starts) else (len(doc)-1,doc[-1].rect.height-40)
    data = []
    for p in range(pn,ep+1):
        for line in material.ipa.lines(doc[p].get_text('dict', flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)):
            if p==pn and line['bbox'][1]<y-1 or p==ep and line['bbox'][1]>=ey-1: continue
            data.append(norm(''.join(s['text'] for s in line['spans'])).strip())
    return data

def question_pages(doc, starts, index):
    number,pn,y = starts[index]
    ep,ey = starts[index+1][1:] if index+1<len(starts) else (len(doc)-1,doc[-1].rect.height)
    if ep>pn and index+1<len(starts): ep-=1
    context = pn
    # Include nearby shared clinical cases, even when their embedded numerals have broken character maps.
    for p in range(max(starts[0][1],pn-4),pn+1):
        for line in material.ipa.lines(doc[p].get_text('dict', flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)):
            text = material.tidy(''.join(s['text'] for s in line['spans']))
            if '次の文を読み' in text and (p<pn or line['bbox'][1]<y): context = p
    return list(range(context,ep+1))

def prepare(task):
    result = {**task, 'questions': []}
    if task['status']!='downloaded': return result
    try:
        for source in task['sources']: assert sha((SRC/source['file']).read_bytes())==source['sha256']
        doc = fitz.open(SRC/task['sourceFile']); keys = official_keys(fitz.open(SRC/task['answerFile']), task)
        starts = question_starts(doc,task)
        assert [n for n,p,y in starts]==list(range(1,len(keys)+1)), ('Question sequence', [n for n,p,y in starts], len(keys))
        rows=[]; evidence=[]; excluded=[]; cache={}; stem=Path(task['file']).stem
        for i,(number,pn,y) in enumerate(starts):
            answer=keys[str(number)]; text=segments(doc,starts,i); pages=question_pages(doc,starts,i)
            labels=sorted({int(m[1]) for line in text if (m:=re.match(r'^([1-5])\s*[.．]',line))})
            reason = None
            if answer is None: reason='deleted/alternative answer or numeric-entry question'
            elif not labels or labels!=list(range(1,max(labels)+1)) or not 2<=len(labels)<=5 or max(answer)>=len(labels): reason='option labels cannot be verified'
            elif any('別冊' in doc[p].get_text() for p in pages): reason='separate figure booklet needed'
            if reason:
                excluded.append(dict(number=str(number),reason=reason));continue
            images, records=zip(*(material.picture(doc,p,stem,cache) for p in pages))
            title=f'{task["year"]}年度 {NAMES[task["examId"]]} {task["subject"]} 問{number}'
            q=dict(id=stem+f'-q{number:03}',examId=task['examId'],year=task['year'],term=task['term'],subject=task['subject'],
                   type='multiple' if len(answer)>1 else 'single',category='過去問',topic=title,
                   prompt=title+'\n原本画像のこの問題番号に解答してください。共通症例も画像で確認できます。',
                   options=list(map(str,labels)),answer=answer if len(answer)>1 else answer[0],images=list(images),sourceUrl=task['url'],
                   source='出典：厚生労働省 '+title+'。公式PDFを原本ページ画像に加工（本文・図表変更なし、PDL1.0）。厚生労働省作成のアプリではありません。',
                   explanation='公式正答：'+','.join(str(a+1) for a in answer)+'。理由解説は未収録です。実施当時の医学・制度を前提とします。',
                   explanationSource='厚生労働省公式正答（理由解説なし）')
            rows.append(q); evidence.append(dict(id=q['id'],number=str(number),answer=q['answer'],images=list(records),optionCount=len(labels)))
        assert rows, 'No verified questions'
        return material.finish(result,rows,evidence,excluded)
    except Exception as error: return {**result,'status':'pending-review','reason':str(error)}

def prepare_all():
    (OUT/'assets').mkdir(parents=True,exist_ok=True)
    tasks=json.loads((SRC/'expansion-discovery.json').read_bytes())['tasks']
    report={'packs':[]}
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        for i,result in enumerate(pool.map(prepare,tasks)):
            report['packs'].append(result)
            print(i+1,'/',len(tasks),result['examId'],result['year'],result['subject'],result['status'],result.get('count',result.get('reason','')),flush=True)
            (OUT/'expansion-report.json').write_bytes(encode(report))

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    if sys.argv[1:] == ['fetch']: acquire()
    elif sys.argv[1:] == ['prepare']: prepare_all()
    else: raise SystemExit('Usage: expand-github-material.py fetch|prepare')
