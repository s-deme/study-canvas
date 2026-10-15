"""Extract all retained images; replace only verified text or pixel-exact figure crops."""
import concurrent.futures
import hashlib
import json
import os
import re
import sys
import importlib.util
from functools import lru_cache
from io import BytesIO
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build/python-deps'))
import pymupdf as fitz
from PIL import Image, ImageChops

spec = importlib.util.spec_from_file_location('compact', ROOT / 'scripts/compact-material.py')
compact = importlib.util.module_from_spec(spec)
spec.loader.exec_module(compact)

METHOD = 4
CROP_METHOD = 9
sha = lambda raw: hashlib.sha256(raw).hexdigest()
read = lambda file: json.loads(file.read_bytes())
unmapped = lambda text: bool(re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\uFFFD\uE000-\uF8FF]', text))


def verify_native(saved, region, image):
    """Reuse the conservative layout gate, then compare the actual delivered pixels."""
    if saved['method'] != 'native' or saved.get('nativeSafetyVersion') == 10:
        return saved
    saved['nativeSafetyVersion'] = 10
    saved.pop('nativeVerified', None)
    saved.pop('retainedReason', None)
    try:
        if not region:
            raise ValueError('no source PDF region')
        with fitz.open(stream=source_pdf(region['sourceFile'], region['sourceSha256']), filetype='pdf') as doc:
            native = doc[region['page']].get_text('text',clip=fitz.Rect(region['rect']),flags=fitz.TEXTFLAGS_TEXT & ~fitz.TEXT_USE_CID_FOR_UNKNOWN_UNICODE)
            text = compact.native_text(doc[region['page']], fitz.Rect(region['rect']), uniform_ink=True)
            if unmapped(text):
                raise ValueError('unmapped or control characters')
            compact.verified_pixels(doc[region['page']], dict(region, sha256=sha(image.read_bytes())), image)
        saved.update(text=str(text), textSha256=sha(text.encode()), sourceText=text.source_text, nativeVerified=True)
    except ValueError as error:
        saved['retainedReason'] = str(error)
        if 'native' in locals():
            saved.update(text=native.strip(),textSha256=sha(native.strip().encode()))
    return saved


def regions():
    result = {}
    for report in sorted((ROOT / 'private-data/github-material/prepared').glob('*report.json')):
        for pack in read(report).get('packs', []):
            if pack.get('status') != 'prepared':
                continue
            hashes = {s['file']: s['sha256'] for s in pack.get('sources', [])}
            for q in pack.get('questions', []):
                for field in ['images', 'solutionImages']:
                    for region in q.get(field, []):
                        name = region.get('sourceFile') or (pack.get('answerFile') if field == 'solutionImages' else pack.get('sourceFile'))
                        if not name or not name.endswith('.pdf') or name not in hashes or region.get('removedMarks'):
                            continue
                        entry = dict(region, sourceFile='private-data/github-material/' + name, sourceSha256=hashes[name])
                        key = region['file']
                        # Conflicting source mappings use the actual image's OCR instead.
                        if key in result and result[key] != entry:
                            result[key] = None
                        else:
                            result[key] = entry
    manifest = read(ROOT / 'build/private/manifest.json')
    for pack in manifest['packs']:
        for kind, field in [('qs', 'images'), ('ans', 'solutionImages')]:
            evidence = next((s for s in pack.get('sources', []) if s.get('kind') == kind), None)
            if not evidence:
                continue
            for q in read(ROOT / 'build/private/web' / pack['url']):
                for image in q.get(field, []):
                    geometry = ROOT / 'private-data/material/assets' / Path(image['src']).name
                    if geometry.with_suffix('.geometry.json').exists():
                        page, rect = read(geometry.with_suffix('.geometry.json'))
                        result[geometry.name] = dict(page=page, rect=rect, sha256=sha(geometry.read_bytes()),
                            sourceFile='private-data/ipa/' + evidence['file'], sourceSha256=evidence['sha256'])
    return result


@lru_cache(maxsize=16)
def source_pdf(name, digest):
    raw = (ROOT / name).read_bytes()
    if sha(raw) != digest:
        raise ValueError('Source PDF changed: ' + name)
    calibration = ROOT / 'private-data/material-transcription/unicode-repairs.json'
    repairs = [r for r in read(calibration) if r['file'].replace('\\','/')==name.replace('\\','/')] if calibration.exists() else []
    if repairs:
        with fitz.open(stream=raw,filetype='pdf') as doc:
            for repair in repairs:
                if repair['status']!='source-verified' or repair['sourceSha256']!=digest:
                    raise ValueError('Unverified PDF Unicode repair')
                if repair.get('glyphReviewFile'):
                    proof=reviewed_glyphs(repair['glyphReviewFile'],repair['glyphReviewSha256'])
                    glyphs={g['index']:g for g in proof['glyphs']}
                    allowed={(f['fontXref'],str(g['code'])):(glyphs[g['glyphIndex']]['reviewedUnicode'],g['pixelSha256'])
                             for f in proof['fonts'] if f['sourceFile'].replace('\\','/')==name.replace('\\','/') and f['sourceSha256']==digest for g in f['glyphs']}
                    for font in repair['fonts']:
                        for code,character in font['mappings'].items():
                            assert allowed.get((font['xref'],code))==(character,font['glyphPixelSha256'][code]),'Glyph calibration differs from reviewed source evidence'
                for font in repair['fonts']:
                    assert doc.xref_get_key(font['xref'],'Subtype')==('name','/Type1')
                    key=doc.xref_get_key(font['xref'],'ToUnicode')
                    if key[0]=='xref':
                        cmap=doc.xref_stream(int(key[1].split()[0])).decode('ascii')
                    else:
                        assert key[0]=='null',key
                        cmap='/CIDInit /ProcSet findresource begin 12 dict begin begincmap /CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def /CMapName /Reviewed-Glyph-UCS def /CMapType 2 def 1 begincodespacerange <00> <ff> endcodespacerange endcmap CMapName currentdict /CMap defineresource pop end end'
                    # A shared original CMap must not receive another font's glyph corrections.
                    xref=doc.get_new_xref();doc.update_object(xref,'<<>>')
                    doc.xref_set_key(font['xref'],'ToUnicode',str(xref)+' 0 R')
                    pairs=[]
                    for code,character in font['mappings'].items():
                        assert 0<=int(code)<=255 and len(character)==1 and not unmapped(character)
                        pairs.append(f'<{int(code):02x}> <{character.encode("utf-16-be").hex()}>')
                    cmap=re.sub(r'\d+\s+begincodespacerange.*?endcodespacerange','1 begincodespacerange <00> <ff> endcodespacerange',cmap,flags=re.S)
                    cmap=cmap.replace('endcmap',str(len(pairs))+' beginbfchar\n'+'\n'.join(pairs)+'\nendbfchar\nendcmap')
                    doc.update_stream(xref,cmap.encode('ascii'))
            raw=doc.tobytes()
    return raw


@lru_cache(maxsize=4)
def reviewed_glyphs(name, digest):
    raw=(ROOT/name).read_bytes();assert sha(raw)==digest,'Glyph review record changed'
    proof=json.loads(raw)
    for glyph in proof['glyphs']:
        assert glyph.get('reviewedUnicode') and glyph.get('reviewer') and glyph.get('reviewedOn')
        with Image.open(ROOT/glyph['file']) as image:
            assert sha(image.convert('RGB').tobytes())==glyph['pixelSha256'],'Reviewed glyph pixels changed'
    return proof


def original_region_text(region):
    raw=(ROOT/region['sourceFile']).read_bytes();assert sha(raw)==region['sourceSha256'],'Source PDF changed'
    with fitz.open(stream=raw,filetype='pdf') as doc:
        return doc[region['page']].get_text('text',clip=fitz.Rect(region['rect'])).strip()


@lru_cache(maxsize=8192)
def existing_ocr(name, page_number, digest):
    original = ROOT / 'private-data/ipa' / Path(name).name
    file = ROOT / 'private-data/ipa/ocr' / (Path(name).name + '-' + str(page_number) + '.json')
    if not original.exists() or not file.exists() or sha(original.read_bytes()) != digest:
        return None
    raw = file.read_bytes();data = json.loads(raw)
    return dict(file=str(file.relative_to(ROOT)), sha256=sha(raw), width=data['width'], height=data['height'])


def cached_ocr(region, page):
    evidence = region.get('ocr')
    if not evidence:
        return None
    raw = (ROOT / evidence['file']).read_bytes()
    if sha(raw) != evidence['sha256']:
        raise ValueError('Existing OCR cache changed')
    rect=fitz.Rect(region['rect']);texts=[]
    sx,sy=page.rect.width/evidence['width'],page.rect.height/evidence['height']
    for block in json.loads(raw)['blocks']:
        for line in block.get('lines', []):
            box=fitz.Rect(line['bbox']);box=fitz.Rect(box.x0*sx,box.y0*sy,box.x1*sx,box.y1*sy)
            if not box.intersects(rect):
                continue
            if not (rect+(-1,-1,1,1)).contains(box):
                return None
            texts.append(''.join(s['text'] for s in line['spans']))
    return '\n'.join(texts).strip() or None


def image_ocr(image, dpi=150):
    pix = fitz.Pixmap(fitz.csRGB, image.width, image.height, image.tobytes(), False)
    pix.set_dpi(dpi, dpi)
    with fitz.open(stream=pix.pdfocr_tobytes(language='jpn+eng', tessdata=str(ROOT / 'build/tessdata')), filetype='pdf') as ocr:
        return ocr[0].get_text(sort=True).strip()


def split_region(page, rect, raw, cache, key):
    """Partition around non-text bands only when source pixels match exactly."""
    if page.rotation or list(page.annots() or []) or not page.get_text('text',clip=rect).strip():
        return None
    if any(fitz.Rect(s['bbox']).intersects(rect) and (s['type'] == 3 or s.get('opacity', 1) == 0) for s in page.get_texttrace()):
        return None
    bounds = [fitz.Rect(d['rect']) & rect for d in compact.region_drawings(page, rect)
              if (fitz.Rect(d['rect']) + (-0.5, -0.5, 0.5, 0.5)).intersects(rect)]
    bounds += [fitz.Rect(i['bbox']) & rect for i in page.get_image_info() if fitz.Rect(i['bbox']).intersects(rect)]
    if not bounds:
        return None
    with Image.open(BytesIO(raw)) as source:
        image = source.convert('RGB')
    fitz.TOOLS.store_shrink(100)
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), clip=rect, alpha=False)
    if image.size != (pix.width, pix.height) or image.tobytes() != pix.samples:
        return None
    data = page.get_text('rawdict', clip=rect, flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES & ~fitz.TEXT_USE_CID_FOR_UNKNOWN_UNICODE)
    lines = [line for block in data['blocks'] for line in block.get('lines', [])]
    colors = {s['color'] for line in lines for s in line['spans'] if any(c['c'].strip() for c in s['chars'])}
    dark_ink = len(colors) == 1 and all(max((c >> 16) & 255, (c >> 8) & 255, c & 255) <= 80 for c in colors)
    char_boxes = [fitz.Rect(char['bbox']) for line in lines for span in line['spans'] for char in span['chars']]
    groups = [(b+(-3,-3,3,3)) & rect for b in bounds]
    changed = True
    while changed:
        previous = [tuple(g) for g in groups]
        merged=[]
        for group in groups:
            owners=[i for i,g in enumerate(merged) if (g+(-3,-3,3,3)).intersects(group)]
            if owners:
                for i in reversed(owners):
                    group |= merged.pop(i)
            merged.append(group)
        groups=merged
        for i, group in enumerate(groups):
            expanded = group+(-3,-3,3,3)
            for box in char_boxes:
                if expanded.intersects(box):
                    group |= box
                    expanded = group+(-3,-3,3,3)
            groups[i] = group & rect
        changed=previous != [tuple(g) for g in groups]
    blocks,crops,outside=[],[],[]
    for group in sorted(groups,key=lambda g:(g.y0,g.x0)):
        try:
            text=str(compact.native_text(page,group))
            blocks.append((group.y0,group.x0,text));continue
        except ValueError:
            pass
        x0=max(0,int(group.x0*1.5)-pix.x);y0=max(0,int(group.y0*1.5)-pix.y)
        x1=min(image.width,int(group.x1*1.5+0.999999)-pix.x);y1=min(image.height,int(group.y1*1.5+0.999999)-pix.y)
        cropped=image.crop((x0,y0,x1,y1))
        box=ImageChops.difference(cropped,Image.new('RGB',cropped.size,'white')).getbbox()
        if not box:
            continue
        if box[0]==0 or box[1]==0 or box[2]==cropped.width or box[3]==cropped.height:
            return None
        box=(max(0,box[0]-2),max(0,box[1]-2),min(cropped.width,box[2]+2),min(cropped.height,box[3]+2))
        cropped=cropped.crop(box)
        file=cache/(key+'-crop-'+str(len(crops)+1)+'.png');cropped.save(file)
        crops.append(dict(file=str(file.relative_to(ROOT)),sha256=sha(file.read_bytes()),
                          pixelRect=[x0+box[0],y0+box[1],x0+box[2],y0+box[3]]))
        group_text = page.get_text('text',clip=group,sort=True,flags=fitz.TEXTFLAGS_TEXT & ~fitz.TEXT_USE_CID_FOR_UNKNOWN_UNICODE).strip()
        if not group_text or unmapped(group_text) or any(fitz.Rect(i['bbox']).intersects(group) for i in page.get_image_info()):
            ocr_text = image_ocr(cropped)
            if ocr_text and sha(ocr_text.encode()) != sha(group_text.encode()):
                group_text += ('\n\n' if group_text else '')+'画像OCR\n'+ocr_text
        marker = '［図・文字化できない部分 '+str(len(crops))+'：画像参照］'
        if group_text:
            marker += '\n\n画像内の補助文字（原本未照合・位置関係は画像参照）\n'+group_text
        blocks.append((group.y0,group.x0,marker))
    for line in lines:
        spans=[]
        for span in line['spans']:
            remaining=[c for c in span['chars'] if not any(g.contains(fitz.Point((c['bbox'][0]+c['bbox'][2])/2,(c['bbox'][1]+c['bbox'][3])/2)) for g in groups)]
            if not remaining:
                continue
            text = ''.join(c['c'] for c in remaining)
            if not text.strip():
                continue
            if ('Greek' in span['font'] and re.search('[A-Za-z]',text)) or span['flags'] & 1 or span['color'] != 0 and not dark_ink or span.get('alpha',255) != 255 or line['dir'] != (1.0,0.0) or line.get('wmode'):
                return None
            if span['flags'] & 18 and text.strip():
                style = '太字・斜体' if span['flags'] & 18 == 18 else '太字' if span['flags'] & 16 else '斜体'
                text = '［' + style + '：' + text + '］'
            spans.append({**span,'chars':remaining,'text':text})
        if spans:
            outside.append({**line,'spans':spans})
    if not crops or len(crops)>20 or not outside:
        return None
    try:
        compact.prose_text(outside)
    except ValueError:
        return None
    for line in outside:
        blocks.append((line['bbox'][1],line['bbox'][0],''.join(s['text'] for s in line['spans']).strip()))
    return dict(text='\n\n'.join(b[2] for b in sorted(blocks) if b[2]),crops=crops)


def extract(task):
    source, cache, src, digest, region = task
    raw = (source / 'web' / src).read_bytes()
    if sha(raw) != digest:
        raise ValueError('Source image changed: ' + src)
    identity = dict(method=METHOD, imageSha256=digest, region=region)
    key = sha(json.dumps(identity, sort_keys=True).encode())
    file = cache / (key + '.json')
    if file.exists():
        try:
            saved = read(file)
        except (json.JSONDecodeError, UnicodeDecodeError):
            saved = {}
        if saved.get('identity') == identity and saved.get('textSha256') == sha(saved['text'].encode()) and not (saved['method']=='native' and unmapped(saved['text']) and (saved.get('nativeVerified') or saved.get('nativeSafetyVersion') != 10)) and (not saved.get('crops') or saved.get('cropMethod')==CROP_METHOD) and all((ROOT/c['file']).exists() and sha((ROOT/c['file']).read_bytes())==c['sha256'] for c in saved.get('crops', [])):
            if region:
                pdf=source_pdf(region['sourceFile'], region['sourceSha256'])
                if saved.get('crops') and 'sourceText' not in saved:
                    with fitz.open(stream=pdf,filetype='pdf') as doc:
                        saved['sourceText']=doc[region['page']].get_text('text',clip=fitz.Rect(region['rect'])).strip()
                    temporary=file.with_suffix('.'+str(os.getpid())+'.tmp')
                    temporary.write_text(json.dumps(saved,ensure_ascii=False),encoding='utf-8');temporary.replace(file)
            if saved['method'] == 'native' and saved.get('nativeSafetyVersion') != 10:
                saved = verify_native(saved, region, source / 'web' / src)
                if region and not saved.get('nativeVerified'):
                    with fitz.open(stream=source_pdf(region['sourceFile'], region['sourceSha256']), filetype='pdf') as doc:
                        split = split_region(doc[region['page']], fitz.Rect(region['rect']), raw, cache, key)
                        if split:
                            saved.update(split, method='native+cropped-images', cropMethod=CROP_METHOD,
                                         sourceText=doc[region['page']].get_text('text', clip=fitz.Rect(region['rect'])).strip())
                            saved['textSha256'] = sha(saved['text'].encode())
                temporary=file.with_suffix('.'+str(os.getpid())+'.tmp')
                temporary.write_text(json.dumps(saved,ensure_ascii=False),encoding='utf-8');temporary.replace(file)
            if not saved['text'].strip() and not saved.get('highResolutionAttempted'):
                if region:
                    with fitz.open(stream=source_pdf(region['sourceFile'], region['sourceSha256']), filetype='pdf') as doc:
                        pix = doc[region['page']].get_pixmap(dpi=300, clip=fitz.Rect(region['rect']), alpha=False)
                        image = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
                else:
                    with Image.open(BytesIO(raw)) as original:
                        image = original.convert('RGB').resize((original.width*2, original.height*2), Image.Resampling.LANCZOS)
                retry = image_ocr(image, dpi=300)
                saved.update(text=retry, textSha256=sha(retry.encode()), highResolutionAttempted=True,
                             highResolution=dict(dpi=300, pixelSha256=sha(image.tobytes()), width=image.width, height=image.height, status='unreviewed'))
                if retry:
                    saved['method'] = 'ocr'
                temporary=file.with_suffix('.'+str(os.getpid())+'.tmp')
                temporary.write_text(json.dumps(saved,ensure_ascii=False),encoding='utf-8');temporary.replace(file)
            return src, saved
    native = ''
    scan = True;split = None;previous_ocr = None;source_text = ''
    if region:
        with fitz.open(stream=source_pdf(region['sourceFile'], region['sourceSha256']), filetype='pdf') as doc:
            page = doc[region['page']]
            rect = fitz.Rect(region['rect'])
            if rect.is_empty or not (page.rect + (-1, -1, 1, 1)).contains(rect):
                raise ValueError('Invalid PDF crop: ' + src)
            native = page.get_text('text', clip=rect, sort=True, flags=fitz.TEXTFLAGS_TEXT & ~fitz.TEXT_USE_CID_FOR_UNKNOWN_UNICODE).strip()
            source_text = page.get_text('text', clip=rect, flags=fitz.TEXTFLAGS_TEXT & ~fitz.TEXT_USE_CID_FOR_UNKNOWN_UNICODE).strip()
            scan = not native or unmapped(native) or any(fitz.Rect(i['bbox']).intersects(rect) for i in page.get_image_info())
            split = split_region(page, rect, raw, cache, key)
            if scan and not split:
                previous_ocr = cached_ocr(region, page)
    text, method = native, 'native'
    if split:
        text, method = split['text'], 'native+cropped-images'
    elif previous_ocr:
        text,method=previous_ocr,'existing-ocr'
    elif scan:
        # shortcut: OCR uses existing image pixels; re-extract unclear regions at 300/400 dpi for review.
        with Image.open(BytesIO(raw)) as source_image:
            image = source_image.convert('RGB')
            text = image_ocr(image)
        method = 'ocr'
        if native and sha(native.encode()) != sha(text.encode()):
            text = 'PDF直接抽出\n' + native + '\n\n画像OCR\n' + text
            method = 'native+ocr'
    saved = dict(identity=identity, status='unreviewed', method=method, text=text, textSha256=sha(text.encode()))
    if split:
        saved['crops'] = split['crops']
        saved['cropMethod'] = CROP_METHOD
        saved['sourceText'] = source_text
    saved = verify_native(saved, region, source / 'web' / src)
    temporary = file.with_suffix('.' + str(os.getpid()) + '.tmp')
    temporary.write_text(json.dumps(saved, ensure_ascii=False), encoding='utf-8')
    temporary.replace(file)
    return src, saved


def main(source):
    cache = ROOT / 'build/material-image-text/cache'
    cache.mkdir(parents=True, exist_ok=True)
    calibration=ROOT/'private-data/material-transcription/unicode-repairs.json'
    repair_files={}
    for repair in read(calibration) if calibration.exists() else []:
        repair_files.setdefault(repair['file'].replace('\\','/'),[]).append(repair)
    mappings = regions()
    assets = read(source / 'asset-evidence.json')
    reverse = {}
    for src, entry in assets.items():
        region = mappings.get(Path(src).name)
        if region and region['sha256'] != entry['sourceSha256']:
            raise ValueError('PDF region/image mapping changed: ' + src)
        if region:
            ocr = existing_ocr(region['sourceFile'],region['page'],region['sourceSha256'])
            if ocr:
                region = dict(region,ocr=ocr)
            if region['sourceFile'].replace('\\','/') in repair_files:
                repairs=repair_files[region['sourceFile'].replace('\\','/')]
                assert all(r['sourceSha256']==region['sourceSha256'] and r['status']=='source-verified' for r in repairs)
                region=dict(region,unicodeRepairSha256=sha(calibration.read_bytes()),unicodeRepairIds=[r['id'] for r in repairs])
        if entry['src'] not in reverse or reverse[entry['src']] is None:
            reverse[entry['src']] = region
    tasks = [(source, cache, entry['src'], entry['sha256'], reverse[entry['src']])
             for entry in {e['src']: e for e in assets.values()}.values()
             if Path(entry['src']).suffix.lower() in ('.png', '.webp', '.jpg', '.jpeg')]
    output = ROOT / 'build/material-image-text/text.json'
    temporary = output.with_suffix('.tmp')
    counts = {}
    print('Retained images:', len(tasks), 'PDF-mapped:', sum(bool(t[4]) for t in tasks), flush=True)
    with temporary.open('w', encoding='utf-8') as stream, concurrent.futures.ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 1)) as pool:
        stream.write('{')
        for index, (src, data) in enumerate(pool.map(extract, tasks, chunksize=8)):
            region=data['identity'].get('region')
            if region and region.get('unicodeRepairSha256'):
                before=original_region_text(region)
                data.update(sourceTextBeforeUnicodeRepair=before,sourceTextBeforeUnicodeRepairSha256=sha(before.encode()))
            if index:
                stream.write(',')
            stream.write(json.dumps(src) + ':' + json.dumps(data, ensure_ascii=False))
            label = 'native-verified' if data.get('nativeVerified') else data['method']
            counts[label] = counts.get(label, 0) + 1
            if (index + 1) % 500 == 0:
                print('Extracted', index + 1, '/', len(tasks), counts, flush=True)
        stream.write('}')
    temporary.replace(output)
    report = dict(source=str(source), sourceManifestSha256=sha((source / 'manifest.json').read_bytes()),
                  images=len(tasks), methods=counts, cropMethod=CROP_METHOD, status='unreviewed', allImagesAttempted=True)
    (output.parent / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    os.environ['OMP_THREAD_LIMIT'] = '1'
    main(Path(sys.argv[1] if len(sys.argv) > 1 else read(ROOT / 'build/private-compact/current.json')['directory']).resolve())
