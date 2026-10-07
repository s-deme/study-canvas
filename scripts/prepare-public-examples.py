"""Preserve official TCCI example blocks and answers for local self-assessment."""
import importlib.util
import sys
from pathlib import Path

spec = importlib.util.spec_from_file_location('examples_base', Path(__file__).with_name('prepare-welfare-material.py'))
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)


def prepare():
    packs = []
    targets = [(area, f'example_0{grade}.html', prefix+str(grade)) for area, prefix in [('houmu','business-law'), ('fukushi','welfare-housing')] for grade in [1,2,3]]
    targets += [('color','example_01.html','color-coordinator-advanced'), ('color','example_02.html','color-coordinator-standard'), ('eco','example.html','eco')]
    for area, page, exam in targets:
        url = f'https://kentei.tokyo-cci.or.jp/{area}/support/challenge/{page}'
        file = f'examples-{area}-{page}'
        if '--fetch' in sys.argv:
            w.b.fetch.fetch(url, file)
        raw = (w.SRC / file).read_bytes()
        soup = w.BeautifulSoup(raw, 'html.parser')
        blocks, solutions = soup.select('.example-block'), soup.select('.answer__textbox')
        assert len(blocks) == len(solutions) > 0, exam
        rows, evidence = [], []
        for i, (block, solution) in enumerate(zip(blocks, solutions), 1):
            for icon in solution.select('.answer__icon'):
                icon.decompose()
            answer = w.text(solution)
            for item in block.select('.answer-block,.example__icon,.example__option__title'):
                item.decompose()
            assert not block.find(['img','table']), exam
            # Keep compound exercises intact instead of inventing subquestion scoring.
            prompt = w.text(block)
            assert prompt and answer and '解答を表示' not in prompt
            q = dict(id=f'public-examples-{exam}-q{i}', examId=exam, type='written', year='', term='公式問題例（掲載年度不明）',
                     subject='公式問題例', category='公式問題例', topic=f'公式問題例 {i}', prompt=prompt+'\n\n公式解答と比較して自己採点してください。',
                     options=[], answer=None, modelAnswer=answer, images=[], sourceUrl=url,
                     source='東京商工会議所 公式試験問題例（本人用・転載許諾未確認のためローカル限定）',
                     explanation='掲載当時の制度・統計を前提とする公式問題例です。現行試験の全範囲を網羅する教材ではありません。',
                     explanationSource='東京商工会議所 公式解答')
            rows.append(q); evidence.append(dict(id=q['id'], number=i, answer=None, images=[]))
        metadata = dict(file=f'public-examples-{exam}.json', examId=exam, year='', term='公式問題例（掲載年度不明）', subject='公式問題例', url=url,
                        localOnly=True, sources=[dict(file=file,url=url,sha256=w.b.ipa.sha(raw),bytes=len(raw))],
                        verificationLabel='公式HTMLの問題ブロック・公式解答を保持（複合設問は分割せず自己採点）')
        data = w.b.ipa.encode(rows)
        if '--verify' in sys.argv:
            assert (w.OUT / metadata['file']).read_bytes() == data
            pack = {**metadata, 'status':'prepared', 'count':len(rows), 'sha256':w.b.ipa.sha(data), 'questions':evidence, 'excludedQuestions':[]}
        else:
            pack = w.b.nonit.finish(metadata, rows, evidence, [])
        packs.append(pack)
    assert len(packs) == 9 and sum(p['count'] for p in packs) == 12
    report = w.b.ipa.encode(dict(packs=packs))
    if '--verify' in sys.argv:
        assert (w.OUT / 'public-examples-report.json').read_bytes() == report
        (w.OUT / 'public-examples-verification.json').write_bytes(w.b.ipa.encode(dict(reportSha256=w.b.ipa.sha(report), officialAnswers='pass',
            originalPixels='pass', method='No raster assets; source HTML question blocks and answer text re-extracted and compared byte-for-byte.')))
    else:
        (w.OUT / 'public-examples-report.json').write_bytes(report)
    print('PASS: 9 exams, 12 complete official example blocks (self-assessment)')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    prepare()
