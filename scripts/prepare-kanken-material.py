"""Private, image-faithful Kanken papers; numbering is pinned after visual review."""
import importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('archive', ROOT/'scripts/prepare-github-material.py')
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
SRC, OUT, fitz = base.SRC, base.OUT, base.fitz


def reviewed(pack):
    record = json.loads((SRC/'kanken-reviewed-numbering.json').read_bytes())[pack['sourceFile']]
    for source in pack['sources']:
        assert base.sha((SRC/source['file']).read_bytes()) == record['hashes'][source['file']]
    return record


def targets(record):
    return [(f'{group}:{part}:{label}', f'大問（{group}）{part}・{label}')
            for group, part, labels in record['groups'] for label in labels]


def prepare():
    records = json.loads((SRC/'kanken-reviewed-numbering.json').read_bytes())
    sources = [s for file in ('kanken-discovery.json', 'kanken-external-discovery.json')
               for s in json.loads((SRC/file).read_bytes())['sources']]
    by_file = {s['file']: s for s in sources}; packs = []
    for file, record in records.items():
        answer_file = file.replace('m_3.pdf', 'k_3.pdf')
        pack = dict(provider='KANKEN', sourceFile=file, answerFile=answer_file,
                    sources=[by_file[file], by_file[answer_file]], url=by_file[file]['url'],
                    examId=record['examId'], year=record['year'], term=record['term'],
                    subject='漢字', localOnly=True, file=Path(file).stem+'.json',
                    verificationLabel='級・年度・設問番号を目視確認。原本画像の画素一致を検査。標準解答画像で自己採点（解答本文の転記・自動採点・理由解説なし）')
        assert reviewed(pack) == record
        images, solutions, image_records, solution_records = [], [], [], []
        for source, refs, evidence, kind in [(file, images, image_records, '問題'),
                                             (answer_file, solutions, solution_records, '標準解答')]:
            with fitz.open(SRC/source) as doc:
                assert len(doc) == record['pages'][source]
                for pn, page in enumerate(doc):
                    name = f'{Path(source).stem}-p{pn+1:02}.png'
                    path = OUT/'assets'/name
                    if not path.exists():
                        page.get_pixmap(matrix=fitz.Matrix(1.5,1.5), alpha=False).save(path)
                    refs.append(dict(src='assets/github-material/'+name, alt=f'{kind}原本 {pn+1}ページ'))
                    evidence.append(dict(file=name, sourceFile=source, page=pn,
                                         rect=list(page.rect), sha256=base.sha(path.read_bytes())))
        rows, evidence = [], []
        for index, (number, target) in enumerate(targets(record), 1):
            identity = f'kanken-{record["year"]}-{record["termId"]}-{record["examId"]}-item{index:03}'
            rows.append(dict(id=identity, examId=pack['examId'], type='written', year=pack['year'],
                             term=pack['term'], subject='漢字', category='過去問', topic=target,
                             prompt=f'{record["name"]} {pack["year"]}年度{pack["term"]}：{target}を解答してください。\n原本画像を拡大し、指定番号の設問を解いてください。記号を答える設問も原本の指示に従ってください。',
                             options=[], answer=None, modelAnswer=f'標準解答画像の{target}を参照し、自己採点してください。',
                             images=images, solutionImages=solutions, source='日本漢字能力検定協会・公式公開過去問（本人用ローカル教材）',
                             sourceUrl=pack['url'], explanation='', explanationSource='日本漢字能力検定協会の標準解答'))
            evidence.append(dict(id=identity, number=number, answer=None, target=target,
                                 images=image_records, solutionImages=solution_records))
        raw = base.encode(rows); (OUT/pack['file']).write_bytes(raw)
        packs.append({**pack, 'status':'prepared', 'count':len(rows), 'sha256':base.sha(raw), 'questions':evidence})
    (OUT/'kanken-report.json').write_bytes(base.encode({'packs':packs}))
    print('Kanken:', len(packs), 'papers,', sum(p['count'] for p in packs), 'numbered items')


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    prepare()
