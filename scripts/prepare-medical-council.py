"""Import council PDF questions using the councils' native HTML answer cells."""
import concurrent.futures, importlib.util, json, re
from pathlib import Path
from urllib.parse import urljoin
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('expansion', ROOT/'scripts/expand-github-material.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
SRC, OUT, fitz, norm = m.SRC, m.OUT, m.fitz, m.norm

def official_keys(task):
    soup = BeautifulSoup((SRC/task['answerFile']).read_bytes(), 'html.parser')
    keys = {}
    if task['kind'] == 'ahaki':
        for tr in soup.find_all('tr'):
            cells = [norm(td.get_text('', strip=True)) for td in tr.find_all('td', recursive=False)]
            if len(cells) == 2 and (match := re.fullmatch(r'問(\d+)', cells[0])):
                assert match[1] not in keys
                keys[match[1]] = int(cells[1])-1 if re.fullmatch('[1-4]', cells[1]) else None
        assert sorted(map(int, keys)) == list(range(1, max(map(int, keys))+1))
    else:
        tables = []
        for table in soup.find_all('table'):
            rows = table.find_all('tr')
            if not rows or not any('問' in row.get_text() for row in rows): continue
            found = {}
            for i, tr in enumerate(rows[:-1]):
                labels = [norm(td.get_text('', strip=True)) for td in tr.find_all(['td', 'th'], recursive=False)]
                if labels and all(re.fullmatch(r'問\d+', label) for label in labels):
                    answers = [norm(td.get_text('', strip=True)) for td in rows[i+1].find_all(['td', 'th'], recursive=False)]
                    assert len(labels) == len(answers)
                    for label, value in zip(labels, answers):
                        assert label[1:] not in found
                        found[label[1:]] = int(value)-1 if re.fullmatch('[1-5]', value) else None
            if found: tables.append(found)
        assert len(tables) == 2 and all(set(t)==set(map(str, range(1,91))) for t in tables)
        keys = tables[0 if task['subject']=='午前' else 1]
    assert keys
    return keys

def question_starts(doc):
    starts=[]
    for pn, page in enumerate(doc):
        if pn == 0: continue
        lines = m.material.ipa.lines(page.get_text('dict', flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES))
        for i, line in enumerate(lines):
            text = norm(''.join(s['text'] for s in line['spans'])).strip()
            if text == '問題' and i+1<len(lines):
                text += norm(''.join(s['text'] for s in lines[i+1]['spans'])).strip()
            match = re.match(r'^問題\s*(\d+)(?:\s|$)', text)
            if match: starts.append((int(match[1]), pn, line['bbox'][1]))
    assert starts and len({n for n,p,y in starts})==len(starts)
    assert [n for n,p,y in starts] == list(range(starts[0][0], starts[-1][0]+1)), ('Question sequence', [n for n,p,y in starts])
    return starts

def prepare(task):
    result={**task,'questions':[]}
    try:
        doc=fitz.open(SRC/task['sourceFile']); keys=official_keys(task); starts=question_starts(doc)
        assert all(str(n) in keys for n,p,y in starts)
        if task['kind']=='jaame': assert [n for n,p,y in starts]==list(range(1,91))
        else:
            cover=re.sub(r'\s','',norm(doc[0].get_text()))
            bounds=re.search(r'試験問題は問題(\d+)[~〜～](\d+)',cover)
            count=re.search(r'試験問題は(\d+)問',cover) if task['subject']=='午前' else None
            assert bounds or count, 'Printed question range needs review'
            lo,hi=(int(bounds[1]),int(bounds[2])) if bounds else (1,int(count[1]))
            assert [n for n,p,y in starts]==list(range(lo,hi+1)), 'Question range differs from cover'
        rows=[]; evidence=[]; excluded=[]; cache={}; stem=Path(task['file']).stem
        maximum=max(map(int,keys)); common=maximum-20
        if task['kind']=='ahaki' and task['examId']!='massage-therapist' and task['subject']=='午後':
            assert str(common) in norm(doc[0].get_text()) and str(maximum-10) in norm(doc[0].get_text()), 'Specialty bounds need review'
        for i,(n,p,y) in enumerate(starts):
            if task['examId']=='acupuncturist' and n>maximum-10: continue
            if task['examId']=='moxibustion' and common<n<=maximum-10: continue
            answer=keys[str(n)]; text=m.segments(doc,starts,i)
            labels=sorted({int(match[1]) for line in text if (match:=re.match(r'^([1-5])\s*[.．]',line))})
            if answer is None or labels!=list(range(1,5 if task['kind']=='ahaki' else 6)):
                excluded.append({'number':str(n),'reason':'alternative/deleted answer or unverified options'});continue
            pages=m.question_pages(doc,starts,i)
            images,records=zip(*(m.material.picture(doc,p,stem,cache) for p in pages))
            title=f'{task["year"]} {task["examId"]} {task["subject"]} 問{n}'
            q={'id':stem+f'-q{n:03}','examId':task['examId'],'year':task['year'],'subject':task['subject'],
               'prompt':title+'\n原本画像のこの問題番号に解答してください。共通症例も画像で確認できます。',
               'options':list(map(str,labels)),'answer':answer,'images':list(images), 'sourceUrl':task['url'],
               'source':'公式試験機関公開の過去問。公式正答HTMLを照合。原本ページ画像、個人利用限定。',
               'explanation':'公式正答：'+str(answer+1)+'。理由解説未収録。','explanationSource':'公式正答（理由解説なし）'}
            rows.append(q);evidence.append({'id':q['id'],'number':str(n),'answer':answer,'images':list(records),'optionCount':len(labels)})
        assert rows
        return m.material.finish(result,rows,evidence,excluded)
    except Exception as error: return {**result,'status':'pending-review','reason':str(error)}

def main():
    soup=BeautifulSoup((SRC/'medical-ahaki.html').read_text(encoding='utf-8'),'html.parser');tasks=[]
    for tr in soup.find_all('tr'):
        links=[a['href'] for a in tr.find_all('a',href=True)]
        if len(links)!=3 or 'mondai_' not in links[0]:continue
        match=re.search(r'mondai_(\d+)_(anma|harikyu)_am',links[0]);assert match
        edition,kind=match.groups();year=str(1992+int(edition))
        for exam in (['massage-therapist'] if kind=='anma' else ['acupuncturist','moxibustion']):
            for section,url in zip(['午前','午後'],links[:2]):
                stem=f'medical-council-{exam}-{year}-'+('am' if section=='午前' else 'pm')
                tasks.append(dict(provider='MEDICAL-COUNCIL',kind='ahaki',examId=exam,year=year,subject=section,term='公開過去問',localOnly=True,
                                  file=stem+'.json',sourceFile=f'medical-ahaki-{edition}-{kind}-'+('am' if section=='午前' else 'pm')+'.pdf',
                                  url=urljoin('https://ahaki.or.jp',url),answerFile=f'medical-ahaki-{edition}-{kind}-answer.html',answerUrl=urljoin('https://ahaki.or.jp',links[2])))
    for section,tag in [('午前','am'),('午後','pm')]:
        stem='medical-council-clinical-engineer-2026-'+tag
        tasks.append(dict(provider='MEDICAL-COUNCIL',kind='jaame',examId='clinical-engineer',year='2026',subject=section,term='公開過去問',localOnly=True,
                          file=stem+'.json',sourceFile='medical-jaame-39'+tag+'.pdf',url=f'https://www.jaame.or.jp/ce/pdf/39{tag}.pdf',
                          answerFile='medical-jaame-39-answer.html',answerUrl='https://www.jaame.or.jp/ce/siken17/hpSEITO.html'))
    # Archive unique resources once: harikyu shared papers serve two different national examinations.
    pairs={n:u for t in tasks for u,n in [(t['url'],t['sourceFile']),(t['answerUrl'],t['answerFile'])]}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        sources=dict(zip(pairs,list(pool.map(lambda n:m.fetch.fetcher.fetch(pairs[n],n),pairs))))
    packs=[]
    for task in tasks:
        task.update(status='downloaded',sources=[sources[task['sourceFile']],sources[task['answerFile']]])
        pack=prepare(task);packs.append(pack);print(pack['file'],pack['status'],pack.get('count',0),pack.get('reason',''),flush=True)
    (OUT/'medical-council-report.json').write_bytes(m.encode({'packs':packs}))

if __name__=='__main__':main()
