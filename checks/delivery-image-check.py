"""Verify every losslessly compressed crop against the actual delivery bundle."""
import hashlib
import json
import sys
from io import BytesIO
from pathlib import Path
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root/'build/python-deps'))
from PIL import Image
read = lambda p: json.loads(p.read_bytes())
sha = lambda raw: hashlib.sha256(raw).hexdigest()
directory = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(read(root/'build/private-cloud/current.json')['directory'])
directory.resolve().relative_to((root/'build/private-cloud').resolve())
manifest = read(directory/'manifest.json')
proof = read(directory/'delivery-asset-evidence.json')
source = Path(proof['source']); source.resolve().relative_to((root/'build').resolve())
entries = {}
for index in range(64): entries.update(read(directory/f'web/bundles/index-{index}.json'))
before_bytes = after_bytes = 0
bundles = {}
for path, record in proof['images'].items():
    assert path.startswith('assets/transcription/') and '..' not in Path(path).parts
    original = (source/'web'/path).read_bytes()
    assert sha(original) == record['sourceSha256'], path
    src = record['src']; assert manifest['assetAliases'][path] == src
    if src in entries:
        bundle, start, size, mime = entries[src]
        assert mime == 'image/webp'
        if bundle not in bundles: bundles[bundle] = (directory/'web'/bundle).read_bytes()
        actual = bundles[bundle][start:start+size]
        assert entries[path] == entries[src], path
    else:
        actual = (directory/'web'/src).read_bytes()
    assert sha(actual) == record['sha256'] == manifest['assetHashes'][path] == manifest['assetHashes'][src], path
    with Image.open(BytesIO(original)) as a, Image.open(BytesIO(actual)) as b:
        expected_mode = 'RGBA' if a.mode in ('RGBA','LA','P') and ('transparency' in a.info or a.mode in ('RGBA','LA')) else 'RGB'
        assert record['mode'] == expected_mode, path
        a, b = a.convert(record['mode']), b.convert(record['mode'])
        assert a.size == b.size == (record['width'], record['height']), path
        assert a.tobytes() == b.tobytes() and sha(a.tobytes()) == record['pixelSha256'], path
    assert len(actual) == record['bytes'] and len(actual) < len(original), path
    before_bytes += len(original); after_bytes += len(actual)
assert manifest['deliveryCompression']['converted'] == len(proof['images'])
result = dict(passed=True,images=len(proof['images']),beforeBytes=before_bytes,afterBytes=after_bytes,reductionBytes=before_bytes-after_bytes,exactDecodedPixels=True,evidenceSha256=sha((directory/'delivery-asset-evidence.json').read_bytes()))
(directory/'delivery-image-verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(f"PASS: {result['images']} delivery crops, exact decoded pixels and actual bundle hashes; saved {result['reductionBytes']} bytes")
