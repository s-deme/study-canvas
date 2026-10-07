"""Archive the pinned JMed48k public evaluation subset, preserving supplied gold and images."""
import concurrent.futures, hashlib, importlib.util, json, posixpath, re, shutil, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fetch', ROOT / 'scripts/fetch-github-material.py')
fetcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetcher)
SRC = fetcher.DEST
OUT = SRC / 'prepared'
COMMIT = '817f1879f63e1c91f9d01fd2ff60ac44559e3dfb'
BASE = f'https://huggingface.co/datasets/JMed48k/JMed48k/resolve/{COMMIT}/'
EXAMS = ['doctor', 'dentist', 'public-health-nurse', 'midwife', 'nurse', 'radiological-tech',
         'clinical-lab', 'physical-therapist', 'occupational-therapist', 'orthoptist', 'pharmacist']
NOTICE = 'JMed48k提供元の正答を使用（公式解答との独立照合・全問目視確認は未実施）。CC-BY-NC-4.0、個人・非商用利用限定。'
sha = lambda b: hashlib.sha256(b).hexdigest()
OFFICIAL = set()

def archive(path):
    assert path.startswith('JMed48k-eval/') and '..' not in path.split('/')
    name = 'medical-jmed-' + sha(path.encode())[:20] + Path(path).suffix
    return fetcher.fetch(BASE + path, name)

def prepare(path):
    source = archive(path)
    data = json.loads((SRC / source['file']).read_text(encoding='utf-8'))
    exam = EXAMS[int(path.split('/')[1][:2]) - 1]
    year = re.search(r'_(20\d\d)/', path)[1]
    rows, excluded, sources = [], [], [source]
    siblings = {s['rfilename'] for s in json.loads((SRC / 'medical-jmed-info.json').read_text(encoding='utf-8'))['siblings']}
    for q in data['questions']:
        number, section = q['question_number'], str(q.get('section') or '')
        canonical_section = {'AM': 'A', 'PM': 'B'}.get(section, section)
        if (exam, year, canonical_section, int(number)) in OFFICIAL:
            excluded.append({'section': section, 'number': number, 'reason': 'already registered official question'})
            continue
        options = q.get('options')
        gold = q.get('correct_answer')
        reason = None
        if not isinstance(options, dict) or len(options) < 2 or not isinstance(gold, list) or not gold:
            reason = 'unsupported answer/options'
        else:
            labels = [str(k).upper() for k in options]
            answers = [str(a).upper() for a in gold]
            if len(set(answers)) != len(answers) or any(a not in labels for a in answers):
                reason = 'numeric, deleted or alternative answer'
            elif len(answers) > 1 and not re.search(str(len(answers)) + r'\s*つ\s*選', unicodedata.normalize('NFKC', q['question_text'])):
                reason = 'multiple gold without explicit matching selection count'
            elif (selection := re.search(r'(\d+)\s*つ\s*選', unicodedata.normalize('NFKC', q['question_text']))) and int(selection[1]) != len(answers):
                reason = 'gold selection count mismatch'
        if '\ufffd' in json.dumps([q.get('question_text'), q.get('text_reference'), options], ensure_ascii=False):
            reason = 'corrupt text encoding'
        choices = list(options.values()) if isinstance(options, dict) else []
        visual_choices = bool(choices) and all(isinstance(o, str) and not o.strip() for o in choices)
        if visual_choices:
            refs = (q.get('img') or {}).get('answer_img') or []
            if not any(refs if isinstance(refs, list) else [refs]):
                reason = 'empty choices without visual option figure'
            choices = [str(i+1) + '（図中の選択肢）' for i in range(len(choices))]
        elif any(not isinstance(o, str) or not o.strip() for o in choices):
            reason = 'incomplete option text'
        elif len({o.strip() for o in choices}) != len(choices):
            reason = 'duplicate option text in supplied extraction'
        if reason:
            excluded.append({'section': section, 'number': number, 'reason': reason})
            continue
        images, solutions = [], []
        # answer_img contains visual answer OPTIONS, not worked solutions; it must be visible before grading.
        for key, target in [('content_img', images), ('answer_img', images)]:
            refs = (q.get('img') or {}).get(key) or []
            if isinstance(refs, str): refs = [refs]
            assert isinstance(refs, list), (path, number, refs)
            for ref in refs:
                if ref is None or ref == '': continue
                assert isinstance(ref, str)
                ref = ref.replace('\\', '/')
                candidates = [ref, posixpath.join(posixpath.dirname(path), ref),
                              posixpath.join(posixpath.dirname(path), f'{year}_images', posixpath.basename(ref))]
                image_path = next((p for p in candidates if p in siblings), None)
                assert image_path, (path, number, ref)
                image = archive(image_path)
                sources.append(image)
                shutil.copyfile(SRC / image['file'], OUT / 'assets' / image['file'])
                target.append({'src': 'assets/github-material/' + image['file'], 'alt': f'問題{section}{number}の' + ('参考図' if key == 'content_img' else '選択肢・別冊図')})
        # A declared visual question without its figure is not safe to present as text-only.
        if q.get('text_only') is False and not images:
            excluded.append({'section': section, 'number': number, 'reason': 'missing question figure'})
            continue
        passage = q.get('text_reference') or ''
        if not isinstance(passage, str):
            excluded.append({'section': section, 'number': number, 'reason': 'unsupported shared passage'})
            continue
        indexes = [labels.index(a) for a in answers]
        rows.append({'id': f'jmed-{exam}-{year}-{section or "all"}-q{number}', 'examId': exam,
                     'year': year, 'subject': section, 'type': 'multiple' if len(indexes) > 1 else 'single',
                     'prompt': q['question_text'], 'passage': passage, 'options': choices,
                     'answer': indexes if len(indexes) > 1 else indexes[0], 'images': images, 'solutionImages': solutions,
                     'source': f'JMed48k/JMed48k {year} {section} 問{number}。{NOTICE}', 'sourceUrl': source['url'],
                     'explanation': '', 'explanationSource': '理由解説未収録'})
    file = f'medical-jmed-{exam}-{year}.json'
    raw = json.dumps(rows, ensure_ascii=False, separators=(',', ':')).encode()
    (OUT / file).write_bytes(raw)
    return {'id': file[:-5], 'file': file, 'examId': exam, 'year': year, 'count': len(rows), 'sha256': sha(raw),
            'sources': list({s['file']: s for s in sources}.values()), 'excluded': excluded}

def main():
    info = json.loads((SRC / 'medical-jmed-info.json').read_text(encoding='utf-8'))
    assert info['sha'] == COMMIT
    paths = [s['rfilename'] for s in info['siblings'] if s['rfilename'].startswith('JMed48k-eval/') and s['rfilename'].endswith('.json')]
    assert len(paths) == 55
    (OUT / 'assets').mkdir(parents=True, exist_ok=True)
    for filename in ['nonit-report.json', 'expansion-report.json', 'medical-official-report.json']:
        for pack in json.loads((OUT / filename).read_bytes())['packs']:
            if pack.get('status') != 'prepared': continue
            section = {'AM': 'A', 'PM': 'B', '午前': 'A', '午後': 'B'}.get(pack.get('section', pack.get('subject')), pack.get('subject'))
            for q in pack['questions']:
                match = re.fullmatch(r'([A-F]?)(\d+)', str(q['number']))
                if match: OFFICIAL.add((pack['examId'], str(pack['year']), match[1] or section, int(match[2])))
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(archive, paths))
    print('Archived all 55 question JSON files', flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        packs = []
        for pack in pool.map(prepare, paths):
            packs.append(pack)
            print(pack['file'], pack['count'], 'excluded', len(pack['excluded']), flush=True)
    report = {'version': 1, 'commit': COMMIT, 'notice': NOTICE, 'license': 'CC-BY-NC-4.0', 'packs': packs}
    (OUT / 'medical-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'packs': len(packs), 'prepared': sum(p['count'] for p in packs), 'excluded': sum(len(p['excluded']) for p in packs)}))

if __name__ == '__main__': main()
