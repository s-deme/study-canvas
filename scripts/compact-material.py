"""Conservative native-PDF extraction and pixel-identical image compression.

Originals and prepared imports are read-only. Cache entries are content-addressed.
"""
import concurrent.futures
import hashlib
import importlib.util
import json
import os
import re
import sys
import unicodedata
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build/python-deps'))
import pymupdf as fitz
from PIL import Image

sha = lambda data: hashlib.sha256(data).hexdigest()
encode = lambda value: json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')
normalize = lambda value: re.sub(r'\s+', '', unicodedata.normalize('NFKC', value))
COMPRESSION_METHOD = 6


class NativeText(str):
    def __new__(cls, text, source_text):
        value = super().__new__(cls, text)
        value.source_text = source_text
        return value


def native_text(page, rect):
    if page.rotation or any(a.rect.intersects(rect) for a in page.annots() or []):
        raise ValueError('rotation or annotations')
    drawings = [d for d in page.get_drawings() if (fitz.Rect(d['rect']) + (-0.5, -0.5, 0.5, 0.5)).intersects(rect)]
    if any(fitz.Rect(d['bbox']).intersects(rect) for d in page.get_image_info()):
        raise ValueError('scan or embedded picture')
    data = page.get_text('rawdict', clip=rect, flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)
    lines = [line for block in data['blocks'] for line in block.get('lines', [])]
    for line in lines:
        for span in line['spans']:
            span['text'] = ''.join(c['c'] for c in span['chars'])
    source_text = '\n'.join(''.join(s['text'] for s in line['spans']) for line in lines).strip()
    if not lines:
        raise ValueError('no native text; OCR requires review')
    for line in lines:
        if line['dir'] != (1.0, 0.0) or line.get('wmode'):
            raise ValueError('non-horizontal text')
        for span in line['spans']:
            footer = bool(re.fullmatch(r'(?:©|\d{4}|独立行政法人情報処理推進機構)\s*', span['text']))
            if span['flags'] & 1 or span['color'] != 0 or span.get('alpha', 255) != 255 or not (rect.contains(fitz.Rect(span['bbox'])) or footer and (rect+(-1,-1,1,1)).contains(fitz.Rect(span['bbox']))):
                raise ValueError('styled, raised or clipped text')
            if span['text'].strip() and span['flags'] & 18:
                style = '太字・斜体' if span['flags'] & 18 == 18 else '太字' if span['flags'] & 16 else '斜体'
                span['text'] = f'［{style}：' + span['text'] + '］'
                span['marks'] = [style]
        for left, right in zip(line['spans'], line['spans'][1:]):
            if not drawings and right['bbox'][0] - left['bbox'][2] > max(left['size'], right['size']) * 1.5:
                raise ValueError('spaced columns need layout review')
    normalized, shades = [], []
    traces = page.get_texttrace() if drawings else []
    for drawing in drawings:
        if (drawing['type'] == 'fs' and drawing.get('fill') == (1.0, 1.0, 1.0)
                and drawing.get('fill_opacity', 1) == 1 and len(drawing['items']) == 1
                and drawing['items'][0][0] == 're'):
            if any(s['seqno'] < drawing['seqno'] and fitz.Rect(s['bbox']).intersects(drawing['items'][0][1])
                   for s in traces):
                raise ValueError('white cell background hides earlier text')
            drawing = {**drawing, 'type':'s', 'fill':None}
        if drawing['type'] != 'f' or len(drawing['items']) != 1 or drawing['items'][0][0] != 're':
            normalized.append(drawing);continue
        box = drawing['items'][0][1];fill = drawing.get('fill')
        if fill == (0.0, 0.0, 0.0) and min(box.width, box.height) <= 1:
            a, b = (fitz.Point(box.x0, (box.y0+box.y1)/2), fitz.Point(box.x1, (box.y0+box.y1)/2)) if box.height <= 1 else (fitz.Point((box.x0+box.x1)/2, box.y0), fitz.Point((box.x0+box.x1)/2, box.y1))
            normalized.append({**drawing, 'type':'s', 'color':fill, 'items':[('l', a, b)], 'fill':None, 'width':min(box.width, box.height), 'stroke_opacity':1})
        elif fill and len(set(fill)) == 1 and 0 < fill[0] < 1 and drawing.get('fill_opacity', 1) == 1:
            marked = False
            for line in lines:
                for span in line['spans']:
                    bbox = fitz.Rect(span['bbox'])
                    if box.contains(fitz.Point((bbox.x0+bbox.x1)/2, (bbox.y0+bbox.y1)/2)) and span['text'].strip():
                        if not span['text'].startswith('［網掛け：'):
                            span['text'] = '［網掛け：' + span['text'] + '］'
                            span.setdefault('marks', []).append('網掛け')
                        marked = True
            if not marked:
                raise ValueError('non-text shading needs review')
            shades.append(box)
        else:
            normalized.append(drawing)
    drawings = normalized
    if drawings:
        return NativeText(table_text(page, rect, drawings, lines, shades), source_text)
    return NativeText(prose_text(lines), source_text)


def prose_text(lines):
    lines = sorted(lines, key=lambda line: (round(line['bbox'][1] / 2), line['bbox'][0]))
    code = any(re.search(r'^\s*(?:if|else|while|for|return|def|class)\b|←', ''.join(s['text'] for s in line['spans'])) for line in lines)
    if code and len(lines) > 1 and len({round(line['bbox'][0]) for line in lines}) > 1:
        raise ValueError('code indentation needs source review')
    labels = [re.match(r'^\s*([アイウエ])\s+\S', ''.join(s['text'] for s in line['spans'])) for line in lines]
    horizontal_choices = [m[1] for m in labels if m] == list('アイウエ')
    for i, (a, b) in enumerate(zip(lines, lines[1:])):
        if b['bbox'][1] < a['bbox'][3] - 2:
            if not (horizontal_choices and labels[i] and labels[i+1] and abs(a['bbox'][1] - b['bbox'][1]) < 2
                    and a['bbox'][2] < b['bbox'][0]):
                raise ValueError('columns, formula or overlapping lines')
    text = '\n'.join(''.join(s['text'] for s in line['spans']).rstrip() for line in lines).strip()
    if not text or len(text) > 50000:
        raise ValueError('empty or oversized native text')
    if any(c == '\ufffd' or unicodedata.category(c) in ('Co', 'Cs') for c in text):
        raise ValueError('unmapped characters')
    if re.search(r'[\^√∑∫{}|`]', text):
        raise ValueError('formula or code needs layout review')
    return text


def table_text(page, rect, drawings, lines, shades=()):
    text = '\n'.join(''.join(s['text'] for s in line['spans']) for line in lines)
    if re.search(r'平面図|間取り|回路図|配線図|グラフ|フローチャート|地図|座標軸|^\s*図\s*[0-9０-９]', text, re.M):
        raise ValueError('spatial diagram needs source review')
    vertical, horizontal = set(), set()
    for drawing in drawings:
        if drawing['type'] != 's' or drawing.get('color') != (0.0, 0.0, 0.0) or drawing.get('stroke_opacity', 1) != 1:
            raise ValueError('table shading or emphasis needs review')
        if any(item[0] not in ('l', 're') or item[0] == 'l' and abs(item[1].x-item[2].x) > 0.1 and abs(item[1].y-item[2].y) > 0.1 for item in drawing['items']):
            raise ValueError('diagram or curve needs review')
        for item in drawing['items']:
            if item[0] == 're':
                vertical.update((round(item[1].x0, 1), round(item[1].x1, 1)))
                horizontal.update((round(item[1].y0, 1), round(item[1].y1, 1)))
            elif abs(item[1].x-item[2].x) < 0.1:
                vertical.add(round(item[1].x, 1))
            else:
                horizontal.add(round(item[1].y, 1))
    if len(vertical) < 2 or len(horizontal) < 2:
        raise ValueError('table, formula, diagram or emphasis')
    finder = page.find_tables(clip=rect, paths=drawings)
    tables = list(finder.tables)
    known = {tuple(c) for table in tables for c in table.cells}
    for cell in finder.cells:
        if tuple(cell) not in known and any(fitz.Rect(cell).contains(fitz.Rect(s['bbox'])) and s['text'].strip() for line in lines for s in line['spans']):
            tables.append(SimpleNamespace(bbox=cell, cells=[cell], row_count=1, col_count=1))
    if not tables:
        raise ValueError('table, formula, diagram or emphasis')
    cells, grids = [], []
    for table in tables:
        if not rect.contains(fitz.Rect(table.bbox)):
            raise ValueError('incomplete table')
        table_cells = sorted(set(tuple(c) for c in table.cells), key=lambda c: (c[1], c[0]))
        xs = sorted({x for c in table_cells for x in (c[0], c[2])})
        ys = sorted({y for c in table_cells for y in (c[1], c[3])})
        for x0, x1 in zip(xs, xs[1:]):
            for y0, y1 in zip(ys, ys[1:]):
                if sum(fitz.Rect(c).contains(fitz.Point((x0+x1)/2, (y0+y1)/2)) for c in table_cells) != 1:
                    raise ValueError('incomplete or overlapping table cells')
        grids.append((table_cells, xs, ys));cells.extend(fitz.Rect(c) for c in table_cells)
    # Every vector must be a cell border; a detected grid alone does not prove that a diagram is a table.
    for drawing in drawings:
        for item in drawing['items']:
            if item[0] == 're':
                box = item[1]
                segments = [(box.tl, box.tr), (box.tr, box.br), (box.br, box.bl), (box.bl, box.tl)]
            elif item[0] == 'l':
                segments = [(item[1], item[2])]
            else:
                raise ValueError('diagram or curve needs review')
            for a, b in segments:
                horizontal, vertical = abs(a.y-b.y) < 0.1, abs(a.x-b.x) < 0.1
                if not (horizontal or vertical):
                    raise ValueError('diagonal table mark needs review')
                boundaries = []
                for c in [*cells, *shades]:
                    if horizontal and any(abs(a.y-y) < 1 for y in (c.y0, c.y1)):
                        boundaries.append((c.x0, c.x1))
                    if vertical and any(abs(a.x-x) < 1 for x in (c.x0, c.x1)):
                        boundaries.append((c.y0, c.y1))
                start, end = sorted((a.x, b.x) if horizontal else (a.y, b.y))
                cursor = start
                for lo, hi in sorted(boundaries):
                    if lo <= cursor + 1 and hi > cursor:
                        cursor = hi
                if not boundaries or cursor < end - 1:
                    raise ValueError(f'non-table drawing needs review: {tuple(a)}, {tuple(b)}')
    assigned = [[] for _ in cells];outside = []
    for line in lines:
        groups = {}
        for span in line['spans']:
            if not span['text'].strip():
                continue
            box = fitz.Rect(span['bbox'])
            owners = [i for i, c in enumerate(cells) if c.contains(box)]
            if len(owners) == 1:
                owner = owners[0]
            elif any(c.intersects(box) for c in cells):
                fragments = {}
                for char in span['chars']:
                    cb = fitz.Rect(char['bbox'])
                    choices = [i for i, c in enumerate(cells) if (c+(-0.75,-0.75,0.75,0.75)).contains(cb)]
                    if len(choices) != 1:
                        if char['c'].isspace():
                            continue
                        raise ValueError('character crossing a cell border needs review')
                    fragments.setdefault(choices[0], []).append(char)
                for owner, chars in fragments.items():
                    bbox = fitz.Rect(chars[0]['bbox'])
                    for char in chars[1:]:
                        bbox |= fitz.Rect(char['bbox'])
                    content = ''.join(c['c'] for c in chars)
                    for mark in span.get('marks', []):
                        content = f'［{mark}：' + content + '］'
                    groups.setdefault(owner, []).append({**span, 'text':content, 'bbox':list(bbox), 'chars':chars})
                continue
            else:
                owner = -1
            groups.setdefault(owner, []).append(span)
        for owner, spans in groups.items():
            box = fitz.Rect(spans[0]['bbox'])
            for span in spans[1:]:
                box |= fitz.Rect(span['bbox'])
            fragment = {**line, 'spans':spans, 'bbox':list(box)}
            (outside if owner == -1 else assigned[owner]).append(fragment)
    prose_text(outside) if outside else None
    blocks = [(line['bbox'][1], line['bbox'][3], ''.join(s['text'] for s in line['spans']).rstrip()) for line in outside]
    offset = 0
    for table, (table_cells, xs, ys) in zip(tables, grids):
        contents = [prose_text(assigned[i]) if assigned[i] else '' for i in range(offset, offset+len(table_cells))]
        offset += len(table_cells)
        regular = len(table_cells) == (len(xs)-1)*(len(ys)-1) and all('\n' not in c and '|' not in c for c in contents)
        if regular:
            values = [contents[i:i+len(xs)-1] for i in range(0, len(contents), len(xs)-1)]
            text = ['| ' + ' | '.join(row) + ' |' for row in values]
            text.insert(1, '| ' + ' | '.join(['---'] * (len(xs)-1)) + ' |')
        else:
            text = ['表（結合セルと改行の位置を保持）']
            for cell, content in zip(table_cells, contents):
                first_row, last_row = ys.index(cell[1])+1, ys.index(cell[3])
                first_col, last_col = xs.index(cell[0])+1, xs.index(cell[2])
                text.append(f'行{first_row}〜{last_row}・列{first_col}〜{last_col}：\n{content or "（空欄）"}')
        blocks.append((table.bbox[1], table.bbox[3], '\n'.join(text)))
    blocks.sort()
    if any(b[0] < a[1]-2 for a, b in zip(blocks, blocks[1:])):
        raise ValueError('side-by-side tables need review')
    return '\n\n'.join(b[2] for b in blocks)


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


def verified_pixels(page, region, image_file):
    original = image_file.read_bytes()
    if sha(original) != region['sha256']:
        raise ValueError('original image changed')
    # Shared raster caches can reuse an image decoded at another PDF's scale.
    fitz.TOOLS.store_shrink(100)
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), clip=fitz.Rect(region['rect']), alpha=False)
    with Image.open(BytesIO(original)) as image:
        im = image.convert('RGB')
        if im.size != (pix.width, pix.height) or im.tobytes() != pix.samples:
            raise ValueError('source crop pixels differ: ' + image_file.name)


def text_patch(q, text):
    if not text or len(text) > 50000:
        raise ValueError('empty or oversized native text')
    comparison = '\n'.join(line.replace('|', '') for line in text.splitlines() if not re.fullmatch(r'\s*\|(?:\s*---\s*\|)+\s*', line)) if '\n| ' in text else text
    comparison = re.sub(r'［網掛け：(.*?)］', r'\1', comparison)
    if q.get('passage') and normalize(q['passage']) not in [normalize(comparison), normalize(getattr(text, 'source_text', text))]:
        raise ValueError('native text differs from registered passage')
    if q['options'] == list('アイウエ') and q.get('passage') and '\n| ' not in text:
        try:
            prompt, options = split_choices(text, q['options'])
            return {'prompt': prompt, 'options': options}
        except ValueError:
            if not any(marker in text for marker in ('［太字', '［斜体', '［網掛け')):
                raise
    prompt = q['prompt']
    if prompt.startswith(q['topic'] + '\n原本画像'):
        prompt = q['topic'] + prompt[len(q['topic']):].replace('画像', '資料')
    return {'mode': 'passage', 'passage': text, 'prompt': prompt, 'options': q['options']}


def solution_value(q, text):
    field = 'evaluationGuide' if q.get('type') == 'essay' or '出題趣旨' in q.get('explanationSource', '') else 'modelAnswer' if q.get('type') == 'written' else 'explanation'
    existing = q.get(field, '')
    if normalize(text) in normalize(existing):
        return field, existing
    return field, (existing + '\n\n' if existing else '') + '原本の解答資料（文字化）\n' + text


def extract_image_parts(source, manifest, originals, patches, reviewed, checked):
    jobs = []
    for pack in manifest['packs']:
        answer = next((s for s in pack.get('sources', []) if s.get('kind') == 'ans'), None)
        question_source = next((s for s in pack.get('sources', []) if s.get('kind') == 'qs'), None)
        for q in json.loads((source / 'web' / pack['url']).read_bytes()):
            for field, evidence in [('images', question_source), ('solutionImages', answer)]:
                if not evidence or not q.get(field):
                    continue
                regions = []
                try:
                    for image in q[field]:
                        file = ROOT / 'private-data/material/assets' / Path(image['src']).name
                        pn, coords = json.loads(file.with_suffix('.geometry.json').read_bytes())
                        regions.append({'file': file.name, 'page': pn, 'rect': coords, 'sha256': sha(file.read_bytes())})
                except FileNotFoundError:
                    continue
                jobs.append((q, regions, evidence['file'], {evidence['file']: evidence['sha256']}, 'ipa', 'material/assets', field))
    for report_file in sorted((ROOT / 'private-data/github-material/prepared').glob('*report.json')):
        for pack in json.loads(report_file.read_bytes()).get('packs', []):
            if pack.get('status') != 'prepared':
                continue
            hashes = {s['file']: s['sha256'] for s in pack.get('sources', [])}
            for record in pack.get('questions', []):
                key = pack['examId'] + '::' + record['id']
                q = originals.get(key)
                for field in ['images', 'solutionImages']:
                    if not q or not q.get(field) or not record.get(field):
                        continue
                    source_file = (pack.get('answerFile') if field == 'solutionImages' else None) or pack.get('sourceFile')
                    if not source_file:
                        files = [file for file in hashes if file.endswith('.pdf')]
                        source_file = files[0] if len(files) == 1 else ''
                    jobs.append((q, record[field], source_file, hashes, 'github-material', 'github-material/prepared/assets', field))
    docs = {};converted = 0
    try:
        for q, regions, name, hashes, archive, image_folder, image_field in jobs:
            key = q['examId'] + '::' + q['id']
            part = 'question' if image_field == 'images' else 'solution'
            if patches.get(key, {}).get(part) or image_field == 'images' and patches.get(key, {}).get('textSha256'):
                continue
            if [Path(i['src']).name for i in q[image_field]] != [r['file'] for r in regions]:
                raise ValueError('registered solution image regions differ: ' + key)
            removed, retained, texts, failures = [], [], [], []
            for image, region in zip(q[image_field], regions):
                file = region.get('sourceFile', name)
                try:
                    if not file.endswith('.pdf'):
                        raise ValueError('no verified PDF source region')
                    digest = hashes[file]
                    doc_key = (archive, file, digest)
                    if doc_key not in docs:
                        data = (ROOT / 'private-data' / archive / file).read_bytes()
                        if sha(data) != digest:
                            raise ValueError('original answer PDF changed')
                        docs[doc_key] = fitz.open(stream=data, filetype='pdf')
                    text = verified_region(docs[doc_key][region['page']], region,
                                           ROOT / 'private-data' / image_folder / region['file'], digest, checked)
                    if image_field == 'images' and q.get('passage') and normalize(text.source_text) not in normalize(q['passage']):
                        raise ValueError('source region differs from registered passage')
                    texts.append(text)
                    removed.append({'image': image, 'region': {**region, 'sourceFile': file, 'sourceSha256': digest, 'archive': archive}, 'textSha256': sha(text.encode('utf-8'))})
                except (ValueError, KeyError, FileNotFoundError) as error:
                    retained.append(image);failures.append(str(error))
            if not removed:
                if key in reviewed:
                    reviewed[key][part+'Reasons'] = failures
                continue
            payload = {'text':'\n\n'.join(texts), 'sourceText':'\n\n'.join(t.source_text for t in texts), 'retained':retained, 'removed':removed}
            if len(payload['text']) + len(q.get('prompt' if retained and image_field == 'images' else 'passage' if image_field == 'images' else 'modelAnswer', '')) > 49000:
                if key in reviewed:
                    reviewed[key][part+'Reasons'] = ['text exceeds existing import field limit']
                continue
            if image_field == 'solutionImages':
                field, value = solution_value(q, payload['text'])
                payload.update(field=field, value=value)
            patches.setdefault(key, {'original': q, 'regions': []})[part] = payload
            converted += len(removed)
            if key in reviewed:
                question_images = [] if patches[key].get('textSha256') else patches[key].get('question', {}).get('retained', q.get('images', []))
                solution_images = patches[key].get('solution', {}).get('retained', q.get('solutionImages', []))
                if not question_images and not solution_images:
                    del reviewed[key]
                else:
                    reviewed[key][part+'Reasons'] = failures
                    reviewed[key][image_field] = retained
            if converted % 100 == 0:
                print('Question/answer/explanation images converted', converted, flush=True)
    finally:
        for doc in docs.values():
            doc.close()
    print('Question/answer/explanation images converted', converted, flush=True)


def marked_answer_replacements(originals, patches, reviewed):
    report = ROOT / 'private-data/github-material/prepared/safety-report.json'
    if not report.exists():
        return
    spec = importlib.util.spec_from_file_location('answer_marks', ROOT / 'scripts/prepare-safety-material.py')
    safety = importlib.util.module_from_spec(spec);spec.loader.exec_module(safety)
    count = 0
    for pack in json.loads(report.read_bytes()).get('packs', []):
        if pack.get('status') != 'prepared' or pack.get('kind'):
            continue
        evidence = next(s for s in pack['sources'] if s['file'] == pack['sourceFile'])
        file = ROOT / 'private-data/github-material' / pack['sourceFile']
        if sha(file.read_bytes()) != evidence['sha256']:
            raise ValueError('official answer source changed')
        with fitz.open(file) as original, fitz.open(file) as exercise, fitz.open(file) as calibration:
            answers = safety.keys(original);checked = set()
            for record in pack['questions']:
                key = pack['examId'] + '::' + record['id'];q = originals.get(key)
                if not q or not q.get('solutionImages') or q.get('type') != 'single' or patches.get(key, {}).get('solution'):
                    continue
                assert answers[record['number']] == record['answer'] == q['answer'], key
                assert len(record['images']) == len(record['solutionImages']) == len(q['solutionImages']), key
                removed = []
                for image, solution, question in zip(q['solutionImages'], record['solutionImages'], record['images']):
                    assert Path(image['src']).name == solution['file'], key
                    assert (solution['page'], solution['rect']) == (question['page'], question['rect']), key
                    assert 'removedMarks' in question, key
                    pn = solution['page']
                    if pn not in checked:
                        verified_pixels(original[pn], solution, ROOT / 'private-data/github-material/prepared/assets' / solution['file'])
                        known_marks = safety.clean(calibration[pn])
                        for mark in question['removedMarks']:
                            assert any(max(abs(a-b) for a,b in zip(mark,known)) <= 1 for known in known_marks), key
                            exercise[pn].add_redact_annot(mark, fill=(1,1,1))
                        if question['removedMarks']:
                            exercise[pn].apply_redactions(images=0, graphics=2)
                        verified_pixels(exercise[pn], question, ROOT / 'private-data/github-material/prepared/assets' / question['file'])
                        checked.add(pn)
                    removed.append({'image': image, 'region': {**solution, 'sourceFile':pack['sourceFile'], 'sourceSha256':evidence['sha256'], 'archive':'github-material'}, 'exerciseRegion':question})
                text = '公式正答：' + q['options'][q['answer']] + '。'
                field, value = solution_value(q, text)
                patches.setdefault(key, {'original':q, 'regions':[]})['solution'] = {
                    'kind':'official-answer-mark', 'questionNumber':record['number'], 'field':field, 'value':value, 'text':text, 'retained':[], 'removed':removed}
                count += 1
                if key in reviewed:
                    reviewed[key]['solutionImages'] = []
                    if not q.get('images') or patches[key].get('textSha256'):
                        del reviewed[key]
        print('Official marked answers in text', pack['sourceFile'], count, flush=True)


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
            if key not in reviewed or q['options'] != list('アイウエ'):
                continue
            try:
                texts, regions = [], []
                for image in q['images']:
                    image_file = ROOT / 'private-data/material/assets' / Path(image['src']).name
                    pn, coords = json.loads(image_file.with_suffix('.geometry.json').read_bytes())
                    region = {'file': image_file.name, 'page': pn, 'rect': coords, 'sha256': sha(image_file.read_bytes())}
                    texts.append(verified_region(doc[pn], region, image_file, original_source['sha256'], regions_checked))
                    regions.append(region)
                text = NativeText('\n\n'.join(texts), '\n\n'.join(t.source_text for t in texts))
                patches[key] = {'original': q, **text_patch(q, text),
                                'sourceFile': original_source['file'], 'sourceSha256': original_source['sha256'],
                                'regions': regions, 'textSha256': sha(text.encode('utf-8'))}
                if q.get('solutionImages'):
                    reviewed[key]['reason'] = 'solution layout needs review'
                else:
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
                    text = NativeText('\n\n'.join(texts), '\n\n'.join(t.source_text for t in texts))
                    patches[key] = {'original': q, **text_patch(q, text),
                                    'sourceFile': pack['sourceFile'], 'sourceSha256': evidence['sha256'],
                                    'regions': record['images'], 'textSha256': sha(text.encode('utf-8'))}
                    if q.get('solutionImages'):
                        reviewed[key]['reason'] = 'solution layout needs review'
                    else:
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
                text = NativeText('\n\n'.join(texts), '\n\n'.join(t.source_text for t in texts))
                patches[key] = {'original': q, **text_patch(q, text),
                                'sourceFile': name, 'sourceSha256': sources[name]['sha256'], 'regions': record['images'],
                                'textSha256': sha(text.encode('utf-8'))}
                if q.get('solutionImages'):
                    reviewed[key]['reason'] = 'solution layout needs review'
                else:
                    del reviewed[key]
            except (ValueError, KeyError, FileNotFoundError) as error:
                reviewed[key]['reason'] = str(error)
        for opened in docs.values():
            opened.close()
    extract_image_parts(source, manifest, originals, patches, reviewed, regions_checked)
    marked_answer_replacements(originals, patches, reviewed)
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
            # Cache source assets; packaging includes only assets still referenced after replacement.
            for a in q.get('images', []) + q.get('solutionImages', []) + q.get('audio', []):
                if a['src'].startswith('assets/'):
                    assets.add(a['src'])
    result = compress_assets(source, cache, assets)
    (cache / 'assets.json').write_bytes(encode(result))
    print(json.dumps({'assets': len(result), 'bytes': sum(e['bytes'] for e in result.values())}), flush=True)


if __name__ == '__main__':
    main()
