"""Recheck every accepted text replacement against source PDFs and crop pixels."""
import importlib.util
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('compact', root / 'scripts/compact-material.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
directory = Path(json.loads((root / 'build/private-compact/current.json').read_bytes())['directory'])
patches = json.loads((directory / 'text-evidence.json').read_bytes())
manifest = json.loads((root / 'build/private/manifest.json').read_bytes())
sources = {s['file']: s['sha256'] for p in manifest['packs'] for s in p.get('sources', [])}
docs, regions, marked_sources, marked_pages = {}, {}, {}, set()
safety_spec = importlib.util.spec_from_file_location('answer_marks', root / 'scripts/prepare-safety-material.py')
safety = importlib.util.module_from_spec(safety_spec);safety_spec.loader.exec_module(safety)
for key, patch in patches.items():
    texts = []
    question = patch.get('question')
    if question:
        question_texts = []
        for removed in question['removed']:
            region = removed['region'];name = region['sourceFile'];expected = region['sourceSha256']
            if (name, expected) not in docs:
                source = root / 'private-data' / region['archive'] / name
                assert m.sha(source.read_bytes()) == expected, key
                docs[name, expected] = (m.fitz.open(source), region['archive'])
            doc, _ = docs[name, expected]
            assert Path(removed['image']['src']).name == region['file'], key
            text = m.verified_region(doc[region['page']], region, root / 'build/private/web' / removed['image']['src'], expected, regions)
            assert m.sha(text.encode('utf-8')) == removed['textSha256'], key
            question_texts.append(text)
        assert '\n\n'.join(question_texts) == question['text'], key
        assert '\n\n'.join(t.source_text for t in question_texts) == question['sourceText'], key
    solution = patch.get('solution')
    if solution:
        solution_texts = []
        for removed in solution['removed']:
            region = removed['region'];name = region['sourceFile'];expected = region['sourceSha256']
            if (name, expected) not in docs:
                source = root / 'private-data' / region['archive'] / name
                assert m.sha(source.read_bytes()) == expected, key
                docs[name, expected] = (m.fitz.open(source), region['archive'])
            doc, _ = docs[name, expected]
            assert Path(removed['image']['src']).name == region['file'], key
            if solution.get('kind') == 'official-answer-mark':
                source_key = (name, expected)
                if source_key not in marked_sources:
                    marked_sources[source_key] = (safety.keys(doc), m.fitz.open(root / 'private-data' / region['archive'] / name), m.fitz.open(root / 'private-data' / region['archive'] / name))
                answers, exercise, calibration = marked_sources[source_key]
                assert answers[solution['questionNumber']] == patch['original']['answer'], key
                page_key = (name, expected, region['page'])
                if page_key not in marked_pages:
                    m.verified_pixels(doc[region['page']], region, root / 'build/private/web' / removed['image']['src'])
                    question = removed['exerciseRegion']
                    known_marks = safety.clean(calibration[region['page']])
                    for mark in question['removedMarks']:
                        assert any(max(abs(a-b) for a,b in zip(mark,known)) <= 1 for known in known_marks), key
                        exercise[region['page']].add_redact_annot(mark,fill=(1,1,1))
                    if question['removedMarks']:
                        exercise[region['page']].apply_redactions(images=0,graphics=2)
                    image = next(i for i in patch['original']['images'] if Path(i['src']).name == question['file'])
                    m.verified_pixels(exercise[region['page']], question, root / 'build/private/web' / image['src'])
                    marked_pages.add(page_key)
                continue
            text = m.verified_region(doc[region['page']], region, root / 'build/private/web' / removed['image']['src'], expected, regions)
            assert m.sha(text.encode('utf-8')) == removed['textSha256'], key
            solution_texts.append(text)
        if solution.get('kind') == 'official-answer-mark':
            assert solution['text'] == '公式正答：' + patch['original']['options'][patch['original']['answer']] + '。', key
        else:
            assert '\n\n'.join(solution_texts) == solution['text'], key
        field, value = m.solution_value(patch['original'], solution['text'])
        assert (field, value) == (solution['field'], solution['value']), key
    if not patch.get('textSha256'):
        continue
    assert len(patch['original']['images']) == len(patch['regions']), key
    for image, region in zip(patch['original']['images'], patch['regions']):
        name = region.get('sourceFile', patch['sourceFile'])
        expected = patch['sourceSha256'] if name == patch['sourceFile'] else sources[name]
        if (name, expected) not in docs:
            candidates = [root / 'private-data' / archive / name for archive in ['ipa', 'github-material', 'fp']]
            source = next(p for p in candidates if p.exists() and m.sha(p.read_bytes()) == expected)
            docs[name, expected] = (m.fitz.open(source), source.parent.name)
        doc, archive = docs[name, expected]
        pn = region['page'] - (1 if archive == 'fp' else 0)
        assert Path(image['src']).name == region['file'], key
        texts.append(m.verified_region(doc[pn], region, root / 'build/private/web' / image['src'], expected, regions))
    text = m.NativeText('\n\n'.join(texts), '\n\n'.join(t.source_text for t in texts))
    assert m.sha(text.encode('utf-8')) == patch['textSha256'], key
    expected = m.text_patch(patch['original'], text)
    assert expected == {k: patch[k] for k in expected}, key
for doc, _ in docs.values():
    doc.close()
for _, exercise, calibration in marked_sources.values():
    exercise.close();calibration.close()
print(f'PASS: {len(patches)} question/answer/explanation replacements, PDF hashes, crop pixels, layout, labels and official answer marks')
