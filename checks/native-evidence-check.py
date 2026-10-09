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
docs, regions = {}, {}
for key, patch in patches.items():
    texts = []
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
    text = '\n\n'.join(texts)
    assert m.sha(text.encode('utf-8')) == patch['textSha256'], key
    expected = m.text_patch(patch['original'], text)
    assert expected == {k: patch[k] for k in expected}, key
for doc, _ in docs.values():
    doc.close()
print(f'PASS: {len(patches)} native replacements, PDF hashes, crop pixels, current layout rules, labels and instructions')
