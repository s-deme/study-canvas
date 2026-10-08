"""Import the visually reviewed official class B 1/2/3/5/6 paper for local study."""
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('hazmat_base', ROOT/'scripts/prepare-nonit-material.py')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
SRC, OUT = base.SRC, base.OUT
URL = 'https://www.shoubo-shiken.or.jp/content/kikenbutsu_otsu.pdf'


def main():
    from PIL import Image
    review = json.loads((SRC/'hazmat-review.json').read_bytes())
    source = SRC/review['sourceFile']
    assert base.ipa.sha(source.read_bytes()) == review['sha256'], 'Official PDF changed; review again'
    doc = base.fitz.open(source)
    assert len(doc) == 46 and set(review['classes']) == {'1','2','3','5','6'}
    assert len(review['commonAnswers']) == len(review['commonPages']) == 25
    cache, packs = {}, []
    for kind, detail in review['classes'].items():
        assert len(detail['answers']) == len(detail['pages']) == 10
        rows, evidence = [], []
        stem = 'hazmat-official-b'+kind
        answers = review['commonAnswers'] + detail['answers']
        pages = review['commonPages'] + detail['pages']
        for number, (answer, page) in enumerate(zip(answers, pages), 1):
            assert 1 <= answer <= 5 and 1 <= page <= 43
            image, record = base.picture(doc, page-1, 'hazmat-otsu', cache)
            answer_page = 44 if number <= 25 else detail['answerPage']
            solution, solution_record = base.picture(doc, answer_page-1, 'hazmat-otsu', cache)
            subject = '危険物に関する法令' if number <= 15 else '基礎的な物理学及び基礎的な化学' if number <= 25 else '危険物の性質並びにその火災予防及び消火の方法'
            title = f'乙種第{kind}類 公式公開問題 問{number}'
            rows.append(dict(id=f'{stem}-q{number:03}', examId='hazmat-b'+kind, type='single',
                year='実施年度不明', term='2026年6月掲載更新・過去問抜粋', subject=subject,
                category='公式公開過去問', topic=title,
                prompt=title+'\n原本画像の該当問題番号を解答してください。'+('問1〜25は乙1・2・3・5・6共通です。' if number <= 25 else ''),
                options=list('12345'), answer=answer-1, images=[image], solutionImages=[solution],
                source='消防試験研究センター 公式公開過去問（本人用学習）', sourceUrl=URL,
                explanation=f'公式正答：{answer}。解答画像の'+('共通表' if number <= 25 else f'第{kind}類の表')+'を参照。理由解説は未収録です。公表当時の法令・制度が前提です。',
                explanationSource=f'公式PDF {answer_page}ページ'))
            evidence.append(dict(id=rows[-1]['id'], number=number, answer=answer-1,
                                 images=[record], solutionImages=[solution_record]))
        task=dict(provider='HAZMAT', examId='hazmat-b'+kind, file=stem+'.json', url=URL,
                  year=rows[0]['year'], term=rows[0]['term'], subject='乙種第'+kind+'類 公式公開問題',
                  localOnly=True, sources=[dict(file=source.name,url=URL,sha256=review['sha256'])],
                  verificationLabel='問題番号・類別・公式正答表を目視照合。原本画像の画素一致検査。理由解説・現行法令との全問照合は未実施')
        packs.append(base.finish(task, rows, evidence, []))
    # Check every emitted image against the original, including the answer tables.
    for image, record in cache.values():
        pix = doc[record['page']].get_pixmap(matrix=base.fitz.Matrix(1.5,1.5), alpha=False)
        with Image.open(OUT/'assets'/record['file']) as saved:
            assert saved.size == (pix.width,pix.height) and saved.convert('RGB').tobytes() == pix.samples
    raw = base.ipa.encode(dict(packs=packs,reviewSha256=base.ipa.sha((SRC/'hazmat-review.json').read_bytes())))
    assert sum(p['count'] for p in packs) == 175
    (OUT/'hazmat-report.json').write_bytes(raw)
    (OUT/'hazmat-verification.json').write_bytes(base.ipa.encode(dict(reportSha256=base.ipa.sha(raw),
        questions=175,uniqueQuestions=75,officialAnswers='pass',originalPixels='pass',
        method='SHA-bound visual review of 75 question numbers, class headings and official answers; all 46 page images pixel-checked.')))
    print('PASS: 175 registrations / 75 distinct official questions; 46 original page images')


if __name__ == '__main__':
    main()
