"""Expose released fire examination questions by class, including practicals."""
import copy
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('fire_base', ROOT/'scripts/prepare-safety-material.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
SRC, OUT = base.SRC, base.OUT


def classes(label):
    result = ['special'] if '特類' in label else []
    for first, last in re.findall(r'(\d+)(?:[~〜～](\d+))?', label):
        result.extend(str(n) for n in range(int(first), int(last or first)+1))
    return result


def main():
    from PIL import Image
    baseline = SRC/'fire-baseline.json'
    if not baseline.exists():
        baseline.write_bytes((ROOT/'build/private/manifest.json').read_bytes())
    report = json.loads((OUT/'safety-report.json').read_bytes())
    packs = []
    for kind, prefix, count, practical_start, answer_page in [('kou','a',34,15,25),('otsu','b',42,16,23)]:
        source = SRC/f'safety-shoubou_{kind}.pdf'
        old = next(p for p in report['packs'] if p['file'] == f'safety-shoubou_{kind}.json')
        assert base.base.ipa.sha(source.read_bytes()) == old['sources'][0]['sha256']
        doc = base.fitz.open(source)
        text = base.norm('\n'.join(p.get_text() for p in doc))
        labels = {int(n): label for label, n in re.findall(r'【([^】]+)】\s*\[問\s*(\d+)\]', text)}
        assert set(labels) == set(range(1,count+1)), labels
        answers = base.table_keys(doc,'fire')
        original = json.loads((OUT/old['file']).read_bytes())
        assert len(original) == count
        groups = {c: ([],[]) for c in (['special']+list('12345') if prefix=='a' else list('1234567'))}
        cache = {}
        solution, solution_record = base.base.picture(doc,answer_page-1,'fire-'+kind,cache)
        for row, evidence in zip(original,old['questions']):
            number = evidence['number']
            assert row['answer'] == answers[number] and row['id'] == evidence['id']
            for c in classes(labels[number]):
                if c not in groups:
                    continue  # The other booklet supplies the corresponding B classes.
                exam = 'fire-'+prefix+('-special' if c=='special' else c)
                q, e = copy.deepcopy(row), copy.deepcopy(evidence)
                q.update(id=f'fire-{kind}-{c}-q{number:03}',examId=exam,year='実施年度不明',
                         term='2026年6月掲載更新・過去問抜粋',subject='筆記',category=labels[number],
                         topic=f'公式筆記 問{number}',prompt=f'公式筆記 問{number}【{labels[number]}】\n原本画像の該当問題番号を解答してください。共通問題は対応する各類に収録しています。',
                         solutionImages=[solution],explanationSource=f'公式PDF {answer_page}ページの正答表')
                e.update(id=q['id'],solutionImages=[solution_record])
                groups[c][0].append(q);groups[c][1].append(e)
        practicals = [(str(c),practical_start+c-1,'鑑別等',26 if prefix=='a' else 24 if c<=4 else 25) for c in range(1,6 if prefix=='a' else 8)]
        if prefix=='a':
            practicals += [(str(c),19+c,'製図',27 if c<=3 else 28) for c in range(1,6)]
        for c, page, subject, solution_page in practicals:
            image, image_record = base.base.picture(doc,page-1,'fire-'+kind,cache)
            answer, answer_record = base.base.picture(doc,solution_page-1,'fire-'+kind,cache)
            title = f'{"甲種" if prefix=="a" else "乙種"}第{c}類 {subject}'
            q = dict(id=f'fire-{kind}-{c}-practical-p{page}',examId='fire-'+prefix+c,type='written',
                     year='実施年度不明',term='2026年6月掲載更新・過去問抜粋',subject=subject,category='公式実技公開問題',
                     topic=title,prompt=title+'\n原本画像の全設問を解答してください。作図は紙などに描き、公式解答画像と比較して自己採点してください。',
                     options=[],answer=None,modelAnswer=f'解答画像（公式PDF {solution_page}ページ）の第{c}類・{subject}を参照してください。',
                     images=[image],solutionImages=[answer],source='消防試験研究センター 公式公開過去問（本人用学習）',sourceUrl=old['url'],
                     explanation='小問一式を1題として収録。図面・解答例は原本のままです。公表当時の法令・制度を前提とします。理由解説は未収録です。',
                     explanationSource=f'公式PDF {solution_page}ページ')
            groups[c][0].append(q)
            groups[c][1].append(dict(id=q['id'],number=f'practical-{page}',answer=None,images=[image_record],solutionImages=[answer_record]))
        for c,(rows,evidence) in groups.items():
            task = dict(provider='FIRE',examId=rows[0]['examId'],file=f'fire-{kind}-{c}.json',url=old['url'],
                        year=rows[0]['year'],term=rows[0]['term'],subject='公式筆記・実技公開問題',localOnly=True,sources=old['sources'],
                        verificationLabel='原本の類別見出し・公式正答表と照合。実技17題のページ対応確認・画像の画素一致検査。現行法令の全問照合・理由解説は未実施')
            packs.append(base.base.finish(task,rows,evidence,[]))
        for _,record in cache.values():
            pix = doc[record['page']].get_pixmap(matrix=base.fitz.Matrix(1.5,1.5),alpha=False)
            with Image.open(OUT/'assets'/record['file']) as saved:
                assert saved.size == (pix.width,pix.height) and saved.convert('RGB').tobytes() == pix.samples
    raw = base.base.ipa.encode(dict(packs=packs,uniqueNewPracticals=17))
    (OUT/'fire-report.json').write_bytes(raw)
    (OUT/'fire-verification.json').write_bytes(base.base.ipa.encode(dict(reportSha256=base.base.ipa.sha(raw),
        officialAnswers='pass',originalPixels='pass',method='Class headings and existing written answers checked against source PDFs; practical page mapping reviewed; new page pixels checked.')))
    print('PASS:',sum(p['count'] for p in packs),'registrations in',len(packs),'classes; 17 new practicals')


if __name__ == '__main__':
    main()
