"""Follow GitHub discoveries to publicly released non-IT exam originals."""
import concurrent.futures, importlib.util, json, re, sys, unicodedata
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('archive_fetch',ROOT/'scripts/fetch-github-material.py')
fetcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(fetcher)
SRC=fetcher.DEST
norm=lambda s:unicodedata.normalize('NFKC',s)
def html(source):
    data=(SRC/source['file']).read_bytes()
    try:return data.decode('utf-8')
    except UnicodeDecodeError:return data.decode('cp932')
def links(source):
    return [(urljoin(source['url'],u.replace('&amp;','&')),norm(re.sub('<[^>]+>','',label)).strip())
            for u,label in re.findall(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)</a>',html(source),re.S)]

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    discovery=[]
    for repo,path,file in [('officeharukaze/denko2','config.js','denko2-github-config.txt'),
                           ('onokumao-png/gokaku-denki-quiz','src/data/questions.ts','denki-github-data.txt'),
                           ('Consuke/denken-with-llm','data/questions/riron.json','denken3-github.json'),
                           ('aistairc/medLLM_QA_benchmark','data/ja/IgakuQA/igakuqa.jsonl','doctor-github-data.txt'),
                           ('aistairc/medLLM_QA_benchmark','data/ja/DenQA/denqa.jsonl','dentist-github-data.txt'),
                           ('inumanma/Pharmacist-bench','data/exam-111/questions.jsonl','pharmacist-github-data.txt')]:
        discovery.append(fetcher.fetch(f'https://raw.githubusercontent.com/{repo}/main/{path}',file))
    terms=[fetcher.fetch('https://www.shiken.or.jp/shiken/faq/faq08/000082.html','ecee-terms.html'),
           fetcher.fetch('https://www.mhlw.go.jp/chosakuken/index.html','mhlw-terms.html')]
    pages=[];tasks=[]
    for kind,exam in [('construction/first','electrician1'),('construction/second','electrician2'),('chief/third','denken3')]:
        base='https://www.shiken.or.jp/'+kind+'/qa/';queue=[base];seen=set();found={}
        while queue:
            url=queue.pop(0)
            if url in seen:continue
            seen.add(url);name='ecee-'+exam+'-'+(Path(urlparse(url).path).name or 'index')+'.html'
            page=fetcher.fetch(url,name);pages.append(page)
            for u,label in links(page):
                if u.endswith('.pdf'):found[u]=label
                elif u.startswith(base) and re.search(r'index_\d+\.html$',u) and u not in seen:queue.append(u)
        for url,label in found.items():
            match=re.search(r'/(\d{8})_(?:co|ch)_(?:first|second|third)_q(\d+)\.pdf$',url)
            if not match or '出題例' in label or not ('筆記' in label or '学科' in label or '科目' in label):continue
            date,part=match.groups()
            if date>'20261006':continue
            answer=url.replace('_q'+part+'.pdf','_a'+('01' if exam=='denken3' else part)+'.pdf')
            if answer not in found:continue
            year=re.search(r'令和(\d+)年度|平成(\d+)年度|(20\d\d)年度',label.replace('令和元','令和1'))
            assert year,label
            year=str(int(year[1])+2018 if year[1] else int(year[2])+1988 if year[2] else int(year[3]))
            subject=({'01':'理論','02':'電力','03':'機械','04':'法規'}[part] if exam=='denken3' else '学科')
            term=('上期' if (int(date[4:6])>=7 if exam=='denken3' else int(date[4:6])<=6) else '下期')
            if '午前' in label:term+='・午前'
            if '午後' in label:term+='・午後'
            stem='ecee-'+Path(urlparse(url).path).stem
            tasks.append(dict(provider='ECEE',examId=exam,year=year,term=term,subject=subject,label=label,
                              file=stem+'.json',url=url,answerUrl=answer,sourceFile=stem+'.pdf',
                              answerFile='ecee-'+Path(urlparse(answer).path).name))
    topics=fetcher.fetch('https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/topics_150873_139_140.html','mhlw-topics.html')
    for url,label in links(topics):
        label=re.sub(r'\s+','',label);m=re.search(r'第(\d+)回(医師|歯科医師)国家試験.*(?:問題|訂正)',label)
        if not m:continue
        number=int(m[1]);exam='doctor' if m[2]=='医師' else 'dentist'
        if not (112<=number<=116 if exam=='doctor' else 116<=number<=117):continue
        name=f'mhlw-{exam}-{number}-index.html'
        page=fetcher.fetch(url,name)
        if any(p['file']==name for p in pages):continue
        pages.append(page);pdfs=[u for u,l in links(page) if u.endswith('.pdf')]
        answer=next(u for u in pdfs if 'seitou' in u)
        for qurl in pdfs:
            match=re.search(r'([a-f])_01\.pdf$',qurl)
            if not match:continue
            section=match[1].upper();stem=f'mhlw-{exam}-{number}-{section}'
            tasks.append(dict(provider='MHLW',examId=exam,year=str(number+(1906 if exam=='doctor' else 1907)),term=f'第{number}回',
                              subject=section,section=section,examNumber=number,file=stem+'.json',url=qurl,answerUrl=answer,
                              sourceFile=stem+'.pdf',answerFile=f'mhlw-{exam}-{number}-answers.pdf',
                              dataset='doctor-github-data.txt' if exam=='doctor' else 'dentist-github-data.txt'))
    page=fetcher.fetch('https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000198929.html','pharmacist-111-index.html');pages.append(page)
    pdfs=links(page);answer=next(u for u,l in pdfs if re.match(r'正答',l))
    for i,(url,label) in enumerate((u,l) for u,l in pdfs if '.pdf' in u and '問題' in l):
        stem=f'mhlw-pharmacist-111-{i+1}'
        tasks.append(dict(provider='MHLW-PHARM',examId='pharmacist',year='2026',term='第111回',subject=re.split(r'[\[［]',label)[0].strip(),
                          file=stem+'.json',url=url,answerUrl=answer,sourceFile=stem+'.pdf',answerFile='mhlw-pharmacist-111-answers.pdf'))
    def download(task):
        try:
            sources=[fetcher.fetch(task['url'],task['sourceFile']),fetcher.fetch(task['answerUrl'],task['answerFile'])]
            return {**task,'sources':sources,'status':'downloaded'}
        except Exception as e:return {**task,'status':'pending-download','reason':str(e)}
    # Shared answer PDFs are fetched once before concurrent question downloads.
    for url,file in dict((t['answerUrl'],t['answerFile']) for t in tasks).items():
        try:fetcher.fetch(url,file)
        except Exception:pass
    report=dict(discovery=discovery,terms=terms,pages=pages,tasks=[])
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,task in enumerate(pool.map(download,tasks)):
            report['tasks'].append(task)
            if (i+1)%20==0:print('Archived',i+1,'/',len(tasks),flush=True)
    (SRC/'nonit-discovery.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Non-IT papers:',len(tasks),'downloaded:',sum(t['status']=='downloaded' for t in report['tasks']),flush=True)

if __name__=='__main__':main()
