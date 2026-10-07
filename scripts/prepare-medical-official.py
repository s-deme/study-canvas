"""Reuse the MHLW numeric-paper importer for four additional medical professions."""
import concurrent.futures, importlib.util, json, re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('expansion', ROOT / 'scripts/expand-github-material.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
EXAMS = {'06': ('radiological-tech', '診療放射線技師'), '08': ('physical-therapist', '理学療法士'),
         '09': ('occupational-therapist', '作業療法士'), '10': ('orthoptist', '視能訓練士')}
m.NAMES.update({exam: name + '国家試験' for exam, name in EXAMS.values()})

def main():
    topics = {'file': 'mhlw-topics.html', 'url': 'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/topics_150873_139_140.html'}
    selected = {}
    for url, label in m.fetch.links(topics):
        year = re.search(r'(20\d\d)年', label)
        if year and int(year[1]) >= 2017 and '問題' in label:
            for code, (exam, name) in EXAMS.items():
                if name in label: selected.setdefault((year[1], exam), url)
    tasks = {}
    for (year, exam), url in sorted(selected.items()):
        page = m.fetch.fetcher.fetch(url, f'medical-official-{exam}-{year}-index.html')
        pdfs = {u for u, label in m.fetch.links(page) if u.endswith('.pdf')}
        for qurl in sorted(pdfs):
            match = re.search(r'-(06|08|09|10)([ab])_01\.pdf$', qurl)
            if not match: continue
            code, section = match.groups()
            answer = re.sub(r'[ab]_01\.pdf$', 'seitou.pdf', qurl)
            if answer not in pdfs: continue
            stem = 'medical-official-' + Path(urlparse(qurl).path).stem
            tasks[stem] = dict(provider='MHLW-MEDICAL', examId=EXAMS[code][0], year=year, term=year+'年度',
                               subject='午前' if section == 'a' else '午後', section='AM' if section == 'a' else 'PM',
                               file=stem+'.json', sourceFile=stem+'.pdf', url=qurl, answerUrl=answer,
                               answerFile='medical-official-'+Path(urlparse(answer).path).name)
    def download(task):
        try:
            sources = [m.fetch.fetcher.fetch(task['url'], task['sourceFile']), m.fetch.fetcher.fetch(task['answerUrl'], task['answerFile'])]
            return {**task, 'sources': sources, 'status': 'downloaded'}
        except Exception as error: return {**task, 'status': 'pending-download', 'reason': str(error)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        acquired = list(pool.map(download, tasks.values()))
    (m.SRC/'medical-official-discovery.json').write_bytes(m.encode({'tasks': acquired}))
    packs = []
    for task in acquired:
        pack = m.prepare(task); packs.append(pack)
        print(pack['file'], pack['status'], pack.get('count', 0), pack.get('reason', ''), flush=True)
    (m.OUT/'medical-official-report.json').write_bytes(m.encode({'packs': packs}))

if __name__ == '__main__': main()
