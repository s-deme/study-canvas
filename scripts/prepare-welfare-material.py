"""Import SSSC reading-accessible originals and match the official answer cells."""
import importlib.util
import json
import re
import sys
from pathlib import Path
from urllib.parse import urljoin

spec = importlib.util.spec_from_file_location('welfare_base', Path(__file__).with_name('prepare-finance-material.py'))
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
from bs4 import BeautifulSoup

SRC, OUT = b.SRC, b.OUT
EXAMS = {'shakai': 'social-worker', 'kaigo': 'care-worker', 'seishin': 'mental-social-worker'}


def acquire():
    baseline = SRC / 'welfare-baseline.json'
    if not baseline.exists():
        baseline.write_bytes((b.ipa.ROOT / 'build/private/manifest.json').read_bytes())
    tasks = []
    for area, exam in EXAMS.items():
        index = f'https://www.sssc.or.jp/{area}/past_exam/index.html'
        record = b.fetch.fetch(index, f'welfare-{area}-index.html')
        soup = BeautifulSoup((SRC / record['file']).read_bytes(), 'html.parser')
        links = [urljoin(index, a['href']) for a in soup.find_all('a', href=True)]
        for url in dict.fromkeys(u for u in links if '/listen_' in u):
            number = int(re.search(r'/no(\d+)/', url)[1])
            year = number + (1998 if area == 'seishin' else 1988)
            answer = next(u for u in links if f'/no{number}/' in u and 'kijun_seitou.pdf' in u)
            stem = f'welfare-{area}-{number}-' + ('am' if '_am_' in url else 'pm')
            sources = [b.fetch.fetch(url, stem + '.html'), b.fetch.fetch(answer, f'welfare-{area}-{number}-answers.pdf')]
            tasks.append(dict(file=stem+'.json', examId=exam, year=str(year), term=f'第{number}回（{year-1}年度）',
                              subject='過去問', url=url, localOnly=True, sources=sources))
    (SRC / 'welfare-discovery.json').write_bytes(b.ipa.encode(tasks))
    print('Fetched', len(tasks), 'papers')


def answers(file, common=None):
    result, checked = {}, set()
    common_started = False
    with b.fitz.open(SRC / file) as doc:
        for page in doc:
            clip = b.fitz.Rect(page.rect)
            if common is not None:
                boundary = page.search_for('社会福祉士・精神保健福祉士共通科目')
                if boundary:
                    if common:
                        clip.y0 = boundary[0].y0
                    else:
                        clip.y1 = boundary[0].y0
                elif common != common_started:
                    continue
                common_started = common_started or bool(boundary)
            words = page.get_text('words', clip=clip)
            for label in (w for w in words if w[4] == '問題番号'):
                numbers = sorted((w for w in words if abs(w[1]-label[1]) < 4 and w[0] > label[2] and re.fullmatch(r'\d+', w[4])), key=lambda w: w[0])
                for w in numbers:
                    cells = [v for v in words if abs((v[0]+v[2]-w[0]-w[2])/2) < 9 and 8 < v[1]-w[1] < 25]
                    assert len(cells) == 1, (file, w, cells)
                    value = b.ipa.norm(cells[0][4]).replace(' ', '')
                    assert re.fullmatch(r'[1-5](?:,[1-5])*', value), (file, w[4], value)
                    n = int(w[4])
                    assert n not in result, (file, n)
                    result[n] = [int(x)-1 for x in value.split(',')]
            # Independent check using the PDF's reading-order table rows.
            text = b.ipa.norm(page.get_text(clip=clip))
            for match in re.finditer(r'問題番号\s+((?:\d+\s+)+)正\s*答\s+((?:[1-5](?:,[1-5])*\s+)+)', text):
                nums = list(map(int, match[1].split()))
                vals = match[2].split()
                assert len(nums) == len(vals), (file, nums, vals)
                for n, v in zip(nums, vals):
                    assert result[n] == [int(x)-1 for x in v.split(',')]
                    checked.add(n)
    assert sorted(result) == list(range(1, max(result)+1)), file
    assert checked == set(result), ('Unchecked answer cells', file, set(result)-checked)
    return result


def text(node):
    return node.get_text('\n', strip=True)


def prepare(task):
    soup = BeautifulSoup((SRC / task['sources'][0]['file']).read_bytes(), 'html.parser')
    keys = answers(task['sources'][1]['file'], '_am_' in task['url'] if task['examId']=='mental-social-worker' else None)
    rows, evidence, excluded, seen = [], [], [], []
    full = text(soup.select_one('.listen_exam'))
    starts = list(re.finditer(r'^問題\s*(\d+)\s', full, re.M))
    headings = [text(h) for h in soup.select('h2,h3')]
    cases = [p for p in soup.select('p') if re.match(r'次の(?:事例|文)', text(p))]
    for dt in soup.find_all('dt'):
        match = re.match(r'^問題\s*(\d+)\s', text(dt))
        if not match:
            continue
        n = int(match[1]); seen.append(n)
        block = dt.parent
        position = next(i for i, m in enumerate(starts) if int(m[1]) == n)
        body = full[starts[position].start():starts[position+1].start() if position+1 < len(starts) else len(full)]
        body = re.split(r'\n次の(?:事例|文)[^\n]*問題\d+', body)[0]
        for heading in headings:
            body = body.replace('\n'+heading+'\n', '\n').removesuffix('\n'+heading)
        note = re.search(r'\n[（(]注[）)]', body)
        notes = body[note.start():] if note else ''
        if note:
            body = body[:note.start()]
        candidates = list(re.finditer(r'\n([1-5１-５])\s+', body))
        runs = [candidates[i:i+5] for i in range(len(candidates)-4) if [b.ipa.norm(m[1]) for m in candidates[i:i+5]] == list('12345')]
        assert len(runs) == 1, (task['file'], n, 'Ambiguous option boundaries')
        labels = runs[0]
        assert [b.ipa.norm(m[1]) for m in labels] == list('12345'), (task['file'], n)
        options = [body[m.end():labels[i+1].start() if i < 4 else len(body)].strip() for i, m in enumerate(labels)]
        # A shared case before a group is carried to each question in that group.
        shared = []
        for x in cases:
            value = text(x)
            if not re.match(r'次の(?:事例|文)', value):
                continue
            header = value.split('答えなさい')[0]
            nums = list(map(int, re.findall(r'問題(\d+)', header)))
            assert nums, (task['file'], header)
            targets = range(nums[0], nums[-1]+1) if 'から' in header else nums
            if n in targets:
                shared.append(x)
        if any(x.find(['img', 'table']) for x in [block, *shared]):
            excluded.append(dict(number=n, reason='図表を伴うため原本との追加照合が必要')); continue
        prompt = body[:labels[0].start()] + notes
        answer = keys[n]
        count = re.search(r'([12１２])つ選び', prompt)
        if count and int(b.ipa.norm(count[1])) == 1 and len(answer) > 1:
            excluded.append(dict(number=n, reason='単一選択で複数の正答を許容する採点特例')); continue
        assert count and int(b.ipa.norm(count[1])) == len(answer), (task['file'], n, answer)
        value = answer[0] if len(answer) == 1 else answer
        q = dict(id=Path(task['file']).stem+f'-q{n}', examId=task['examId'], type='single' if len(answer)==1 else 'multiple',
                 year=task['year'], term=task['term'], subject=text(dt.find_previous('h2')), category='過去問', topic=f'{task["term"]} 問題{n}',
                 prompt=prompt, passage='\n'.join(text(x) for x in shared), options=options, answer=value, images=[],
                 source='社会福祉振興・試験センター 公式過去問（音声読み上げ用本文・本人用）', sourceUrl=task['url'],
                 explanation='公式正答：'+','.join(str(x+1) for x in answer)+'。理由解説は未収録。試験実施当時の制度を前提とします。',
                 explanationSource='社会福祉振興・試験センター 公式正答一覧')
        rows.append(q); evidence.append(dict(id=q['id'], number=n, answer=value, images=[]))
    assert seen and seen == list(range(min(seen), max(seen)+1)), (task['file'], seen)
    assert rows
    metadata = {**task, 'verificationLabel':'公式HTML本文・選択肢・問題番号と公式PDF正答セルを照合（全問目視・理由解説は未実施）'}
    raw = b.ipa.encode(rows)
    if '--verify' in sys.argv:
        assert (OUT / task['file']).read_bytes() == raw, task['file']
        return {**metadata, 'status':'prepared', 'count':len(rows), 'sha256':b.ipa.sha(raw), 'questions':evidence, 'excludedQuestions':excluded}
    return b.nonit.finish(metadata, rows, evidence, excluded)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    if '--fetch' in sys.argv:
        acquire(); return
    tasks = json.loads((SRC / 'welfare-discovery.json').read_bytes())
    packs = [prepare(t) for t in tasks]
    report = b.ipa.encode(dict(packs=packs))
    if '--verify' in sys.argv:
        assert (OUT / 'welfare-report.json').read_bytes() == report
        (OUT / 'welfare-verification.json').write_bytes(b.ipa.encode(dict(reportSha256=b.ipa.sha(report), officialAnswers='pass',
            originalPixels='pass', method='No raster assets. Reparsed archived HTML and official answer PDF; validated sequence, options and selection count.')))
    else:
        (OUT / 'welfare-report.json').write_bytes(report)
    for p in packs:
        print(p['file'], p['count'], 'excluded', len(p['excludedQuestions']))


if __name__ == '__main__':
    main()
