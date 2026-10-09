"""Conservative native-PDF extraction and pixel-identical image compression.

Originals and prepared imports are read-only. Cache entries are content-addressed.
"""
import concurrent.futures
import hashlib
import json
import os
import re
import sys
import unicodedata
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build/python-deps'))
import pymupdf as fitz
from PIL import Image

sha = lambda data: hashlib.sha256(data).hexdigest()
encode = lambda value: json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
normalize = lambda value: re.sub(r'\s+', '', unicodedata.normalize('NFKC', value))
COMPRESSION_METHOD = 6


def native_text(page, rect):
    if page.rotation or any(a.rect.intersects(rect) for a in page.annots() or []):
        raise ValueError('rotation or annotations')
    if any((fitz.Rect(d['rect']) + (-0.5, -0.5, 0.5, 0.5)).intersects(rect) for d in page.get_drawings()):
        raise ValueError('table, formula, diagram or emphasis')
    if any(fitz.Rect(d['bbox']).intersects(rect) for d in page.get_image_info()):
        raise ValueError('scan or embedded picture')
    data = page.get_text('dict', clip=rect, flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)
    lines = [line for block in data['blocks'] for line in block.get('lines', [])]
    if not lines:
        raise ValueError('no native text; OCR requires review')
    for line in lines:
        if line['dir'] != (1.0, 0.0) or line.get('wmode'):
            raise ValueError('non-horizontal text')
        for span in line['spans']:
            if span['flags'] & 19 or span['color'] != 0 or span.get('alpha', 255) != 255 or not rect.contains(fitz.Rect(span['bbox'])):
                raise ValueError('styled, raised or clipped text')
        for left, right in zip(line['spans'], line['spans'][1:]):
            if right['bbox'][0] - left['bbox'][2] > max(left['size'], right['size']) * 1.5:
                raise ValueError('spaced columns need layout review')
    lines.sort(key=lambda line: (line['bbox'][1], line['bbox'][0]))
    for a, b in zip(lines, lines[1:]):
        if b['bbox'][1] < a['bbox'][3] - 2:
            raise ValueError('columns, formula or overlapping lines')
    text = '\n'.join(''.join(s['text'] for s in line['spans']).rstrip() for line in lines).strip()
    if not text or len(text) > 50000:
        raise ValueError('empty or oversized native text')
    if any(c == '\ufffd' or unicodedata.category(c) in ('Co', 'Cs') for c in text):
        raise ValueError('unmapped characters')
    if re.search(r'[=+*/^<>±−×÷√∑∫≤≥≠{}|`]|[₀-₉⁰-⁹]', text):
        raise ValueError('formula or code needs layout review')
    return text


def split_choices(text, labels):
    matches = list(re.finditer(r'^\s*([アイウエオカキクケコ])\s+', text, re.M))
    if [m[1] for m in matches] != labels:
        raise ValueError('ambiguous choice sequence')
    prompt = text[:matches[0].start()].strip()
    options = [text[m.start():matches[i+1].start() if i+1 < len(matches) else len(text)].strip()
               for i, m in enumerate(matches)]
    if not prompt or any(not value[len(label):].strip() for label, value in zip(labels, options)):
        raise ValueError('empty prompt or choice')
    return prompt, options


def verified_region(page, region, image_file, source_sha, results):
    original = image_file.read_bytes()
    if sha(original) != region['sha256']:
        raise ValueError('original image changed')
    key = (source_sha, page.number, tuple(region['rect']), region['sha256'])
    if key not in results:
        try:
            rect = fitz.Rect(region['rect'])
            text = native_text(page, rect)
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), clip=rect, alpha=False)
            with Image.open(BytesIO(original)) as image:
                im = image.convert('RGB')
                if im.size != (pix.width, pix.height) or im.tobytes() != pix.samples:
                    raise ValueError('source crop pixels differ')
            results[key] = text
        except ValueError as error:
            results[key] = ('error', str(error))
    result = results[key]
    if isinstance(result, tuple):
        raise ValueError(result[1])
    return result


def text_patch(q, text):
    if not text or len(text) > 50000:
        raise ValueError('empty or oversized native text')
    if q.get('passage') and normalize(text) != normalize(q['passage']):
        raise ValueError('native text differs from registered passage')
    if q['options'] == list('アイウエ') and q.get('passage'):
        prompt, options = split_choices(text, q['options'])
        return {'prompt': prompt, 'options': options}
    prompt = q['prompt']
    if prompt.startswith(q['topic'] + '\n原本画像'):
        prompt = q['topic'] + prompt[len(q['topic']):].replace('画像', '資料')
    return {'mode': 'passage', 'passage': text, 'prompt': prompt, 'options': q['options']}


def extract(source, cache):
    manifest = json.loads((source / 'manifest.json').read_bytes())
    patches, review, originals, regions_checked = {}, [], {}, {}
    for pack in manifest['packs']:
        rows = json.loads((source / 'web' / pack['url']).read_bytes())
        for q in rows:
            if q.get('images') or q.get('solutionImages'):
                originals[q['examId'] + '::' + q['id']] = q
                review.append({'key': q['examId'] + '::' + q['id'], 'reason': 'no verified native conversion',
                               'images': q.get('images', []), 'solutionImages': q.get('solutionImages', [])})
    reviewed = {r['key']: r for r in review}
    # The original IPA importer stores the exact PDF crop geometry separately.
    for pack in manifest['packs']:
        original_source = next((s for s in pack.get('sources', []) if s.get('kind') == 'qs'), None)
        if not original_source:
            continue
        file = ROOT / 'private-data/ipa' / original_source['file']
        original = file.read_bytes()
        if sha(original) != original_source['sha256']:
            raise ValueError('Original source changed: ' + str(file))
        doc = fitz.open(stream=original, filetype='pdf')
        for q in json.loads((source / 'web' / pack['url']).read_bytes()):
            key = q['examId'] + '::' + q['id']
            if key not in reviewed or q['options'] != list('アイウエ') or q.get('solutionImages'):
                continue
            try:
                texts, regions = [], []
                for image in q['images']:
                    image_file = ROOT / 'private-data/material/assets' / Path(image['src']).name
                    pn, coords = json.loads(image_file.with_suffix('.geometry.json').read_bytes())
                    region = {'file': image_file.name, 'page': pn, 'rect': coords, 'sha256': sha(image_file.read_bytes())}
                    texts.append(verified_region(doc[pn], region, image_file, original_source['sha256'], regions_checked))
                    regions.append(region)
                text = '\n\n'.join(texts)
                patches[key] = {'original': q, **text_patch(q, text),
                                'sourceFile': original_source['file'], 'sourceSha256': original_source['sha256'],
                                'regions': regions, 'textSha256': sha(text.encode('utf-8'))}
                del reviewed[key]
            except (ValueError, KeyError, FileNotFoundError) as error:
                reviewed[key]['reason'] = str(error)
        doc.close()
    reports = ROOT / 'private-data/github-material/prepared'
    for report_file in sorted(reports.glob('*report.json')):
        report = json.loads(report_file.read_bytes())
        for pack in report.get('packs', []):
            if pack.get('status') != 'prepared' or not pack.get('sourceFile', '').endswith('.pdf'):
                continue
            if not any(pack['examId'] + '::' + r['id'] in reviewed for r in pack['questions']):
                continue
            file = ROOT / 'private-data/github-material' / pack['sourceFile']
            original = file.read_bytes()
            evidence = next(s for s in pack['sources'] if s['file'] == pack['sourceFile'])
            if sha(original) != evidence['sha256']:
                raise ValueError('Original source changed: ' + str(file))
            doc = fitz.open(stream=original, filetype='pdf')
            source_hashes = {s['file']: s['sha256'] for s in pack['sources']}
            docs = {pack['sourceFile']: doc}
            for record in pack['questions']:
                key = pack['examId'] + '::' + record['id']
                if key not in reviewed:
                    continue
                q = originals[key]
                try:
                    if q.get('solutionImages'):
                        raise ValueError('solution layout needs review')
                    if [Path(i['src']).name for i in q['images']] != [i['file'] for i in record['images']]:
                        raise ValueError('registered image regions differ')
                    texts = []
                    for image in record['images']:
                        original_image = ROOT / 'private-data/github-material/prepared/assets' / image['file']
                        image_source = image.get('sourceFile', pack['sourceFile'])
                        if image_source not in docs:
                            data = (ROOT / 'private-data/github-material' / image_source).read_bytes()
                            if sha(data) != source_hashes[image_source]:
                                raise ValueError('original PDF changed')
                            docs[image_source] = fitz.open(stream=data, filetype='pdf')
                        texts.append(verified_region(docs[image_source][image['page']], image, original_image, source_hashes[image_source], regions_checked))
                    text = '\n\n'.join(texts)
                    patches[key] = {'original': q, **text_patch(q, text),
                                    'sourceFile': pack['sourceFile'], 'sourceSha256': evidence['sha256'],
                                    'regions': record['images'], 'textSha256': sha(text.encode('utf-8'))}
                    del reviewed[key]
                except (ValueError, KeyError) as error:
                    reviewed[key]['reason'] = str(error)
            for opened in docs.values():
                opened.close()
        print('Native review', report_file.name, len(patches), flush=True)
    # FP imports retain the exact per-question crop and the law-as-of instruction.
    fp = ROOT / 'private-data/additions/fp-manifest.json'
    if fp.exists():
        data = json.loads(fp.read_bytes())
        sources = {s['file']: s for s in data['sources']['sources']}
        docs = {}
        for record in data['questions']:
            key = record['examId'] + '::' + record['id']
            if key not in reviewed:
                continue
            q = originals[key]
            try:
                name = record['source']
                if name not in docs:
                    original = (ROOT / 'private-data/fp' / name).read_bytes()
                    if sha(original) != sources[name]['sha256']:
                        raise ValueError('original PDF changed')
                    docs[name] = fitz.open(stream=original, filetype='pdf')
                if [Path(i['src']).name for i in q['images']] != [i['file'] for i in record['images']]:
                    raise ValueError('registered image regions differ')
                texts = []
                for region in record['images']:
                    texts.append(verified_region(docs[name][region['page']-1], region,
                                 ROOT / 'private-data/additions/assets' / region['file'], sources[name]['sha256'], regions_checked))
                text = '\n\n'.join(texts)
                patches[key] = {'original': q, **text_patch(q, text),
                                'sourceFile': name, 'sourceSha256': sources[name]['sha256'], 'regions': record['images'],
                                'textSha256': sha(text.encode('utf-8'))}
                del reviewed[key]
            except (ValueError, KeyError, FileNotFoundError) as error:
                reviewed[key]['reason'] = str(error)
        for opened in docs.values():
            opened.close()
    (cache / 'text.json').write_bytes(encode(patches))
    (cache / 'review.json').write_bytes(encode(list(reviewed.values())))
    print(json.dumps({'nativeText': len(patches), 'retainedForReview': len(reviewed)}), flush=True)


def compress(task):
    source, cache, asset = task
    original = (source / 'web' / asset).read_bytes()
    digest = sha(original)
    cached = cache / (digest + '.json')
    previous = None
    if asset.endswith('.png') and cached.exists():
        entry = json.loads(cached.read_bytes())
        if entry['sourceSha256'] == digest and (cache / entry['file']).exists() and sha((cache / entry['file']).read_bytes()) == entry['sha256']:
            if entry.get('method') == COMPRESSION_METHOD:
                return asset, entry
            previous = entry
    if not asset.endswith('.png'):
        return asset, {'src': asset, 'sourceSha256': digest, 'sha256': digest, 'bytes': len(original)}
    with Image.open(BytesIO(original)) as image:
        # Do not flatten transparency or change dimensions, colors, labels, or pixels.
        if getattr(image, 'n_frames', 1) != 1 or image.mode not in ('RGB', 'RGBA', 'L', 'LA', 'P'):
            return asset, {'src': asset, 'sourceSha256': digest, 'sha256': digest, 'bytes': len(original)}
        mode = 'RGBA' if image.mode in ('RGBA', 'LA', 'P') and ('transparency' in image.info or image.mode in ('RGBA', 'LA')) else 'RGB'
        pixels = image.convert(mode)
        buffer = BytesIO()
        pixels.save(buffer, format='WEBP', lossless=True, exact=True, method=COMPRESSION_METHOD,
                    **{k: image.info[k] for k in ('icc_profile', 'exif') if k in image.info})
        data = buffer.getvalue()
        decoded = Image.open(BytesIO(data)).convert(mode)
        assert decoded.size == pixels.size and decoded.tobytes() == pixels.tobytes(), asset
        if previous and previous['bytes'] <= len(data):
            data = (cache / previous['file']).read_bytes()
            decoded = Image.open(BytesIO(data)).convert(mode)
            assert decoded.size == pixels.size and decoded.tobytes() == pixels.tobytes(), asset
        if len(data) >= len(original):
            return asset, {'src': asset, 'sourceSha256': digest, 'sha256': digest, 'bytes': len(original)}
        name = digest + '.webp'
        temporary = cache / (name + '.' + str(os.getpid()) + '.tmp')
        temporary.write_bytes(data)
        temporary.replace(cache / name)
        entry = {'src': 'assets/compact/' + name, 'file': name, 'sourceSha256': digest,
                 'sha256': sha(data), 'bytes': len(data), 'pixelSha256': sha(pixels.tobytes()),
                 'width': pixels.width, 'height': pixels.height, 'mode': mode, 'method': COMPRESSION_METHOD}
        temporary = cached.with_suffix('.' + str(os.getpid()) + '.tmp')
        temporary.write_bytes(encode(entry))
        temporary.replace(cached)
        return asset, entry


def compress_assets(source, cache, assets):
    groups = {}
    for asset in sorted(assets):
        key = sha((source / 'web' / asset).read_bytes()) if asset.endswith('.png') else asset
        groups.setdefault(key, []).append(asset)
    result, done = {}, 0
    with concurrent.futures.ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 1)) as pool:
        tasks = ((source, cache, names[0]) for names in groups.values())
        for (_, entry), names in zip(pool.map(compress, tasks, chunksize=8), groups.values()):
            for name in names:
                result[name] = entry if entry.get('file') else {**entry, 'src': name}
            previous = done
            done += len(names)
            if done // 1000 != previous // 1000:
                print('Verified image/audio', done, '/', len(assets), flush=True)
    return result


def main():
    source, cache = map(Path, sys.argv[1:3])
    cache.mkdir(parents=True, exist_ok=True)
    extract(source, cache)
    manifest = json.loads((source / 'manifest.json').read_bytes())
    assets = set()
    for pack in manifest['packs']:
        for q in json.loads((source / 'web' / pack['url']).read_bytes()):
            # Saved edits may still reference images removed from the text-only questions.
            for a in q.get('images', []) + q.get('solutionImages', []) + q.get('audio', []):
                if a['src'].startswith('assets/'):
                    assets.add(a['src'])
    result = compress_assets(source, cache, assets)
    (cache / 'assets.json').write_bytes(encode(result))
    print(json.dumps({'assets': len(result), 'bytes': sum(e['bytes'] for e in result.values())}), flush=True)


if __name__ == '__main__':
    main()
