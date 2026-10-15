"""Split verified official medical pages at the importer's question anchors."""
import concurrent.futures
import os
import importlib.util
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / file)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


images = module('image_text', 'extract-material-image-text.py')
numeric = module('numeric', 'expand-github-material.py')
fitz, read, sha = images.fitz, images.read, images.sha


def ruby_rows(lines):
    """Associate small kana above a body row; preserve exact pixels until readings are checked."""
    rows = {}
    for line in lines:
        if line['dir'] != (1.0, 0.0) or line.get('wmode'):
            continue
        size = max(s['size'] for s in line['spans'])
        if size >= 9:
            baseline = round(max(s['origin'][1] for s in line['spans'])*2)/2
            rows.setdefault(baseline, []).append(line)
    groups = []
    for owners in rows.values():
        box = fitz.Rect(owners[0]['bbox'])
        for line in owners[1:]: box |= fitz.Rect(line['bbox'])
        size = max(s['size'] for line in owners for s in line['spans'])
        ruby = [line for line in lines if line['dir'] == (1.0, 0.0) and not line.get('wmode')
                and max(s['size'] for s in line['spans']) <= size*.65
                and re.fullmatch(r'[ぁ-ゖーゝゞ\s]+', ''.join(s['text'] for s in line['spans']))
                and -.8 <= box.y0-line['bbox'][3] <= 3
                and box.x0-.5 <= line['bbox'][0] < line['bbox'][2] <= box.x1+.5]
        if ruby:
            annotation = fitz.Rect(box)
            for line in ruby: annotation |= fitz.Rect(line['bbox'])
            groups.append(dict(owners=owners, ruby=ruby, body=box, annotation=annotation))
    return groups


def question_top(page, top):
    lines=[l for b in page.get_text('dict',flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)['blocks'] for l in b.get('lines', []) if l['spans']]
    groups=[g for g in ruby_rows(lines) if abs(g['body'].y0-top)<3]
    return min([top]+[g['annotation'].y0 for g in groups])


def partial_unmapped(page, rect, cache, key, offset, layout=False):
    """Keep an unreadable line as original pixels, while transcribing known characters."""
    if images.compact.region_drawings(page, rect) or any(fitz.Rect(i['bbox']).intersects(rect) for i in page.get_image_info()):
        return None
    pix = page.get_pixmap(matrix=fitz.Matrix(1.5,1.5), clip=rect, alpha=False)
    raster = images.Image.frombytes('RGB', (pix.width,pix.height), pix.samples)
    lines = [l for b in page.get_text('dict',clip=rect,flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES & ~fitz.TEXT_USE_CID_FOR_UNKNOWN_UNICODE)['blocks'] for l in b.get('lines',[]) if any(s['text'].strip() for s in l['spans'])]
    groups = ruby_rows(lines) if layout else []
    ruby_by_owner = {id(g['owners'][0]):g for g in groups}
    skipped = {id(l) for g in groups for l in g['ruby']+g['owners'][1:]}
    lines = [l for l in lines if id(l) not in skipped]
    crops = []
    for line in lines:
        layout_error = None
        ruby = ruby_by_owner.get(id(line))
        known_ruby_body = None
        if layout:
            try:
                line_text = str(images.compact.native_text(page, ruby['body'] if ruby else fitz.Rect(line['bbox']), uniform_ink=True))
                if ruby:
                    known_ruby_body = line_text
                    layout_error = 'ruby reading association needs source review'
            except ValueError as error:
                layout_error = str(error)
                if layout_error not in ('styled, raised or clipped text', 'unsupported raised or lowered characters', 'Greek symbol font decodes to Latin letters', 'small numeral next to Greek symbol needs source typography review'):
                    return None
        if layout_error or any(images.unmapped(s['text']) for s in line['spans']):
            box = ((ruby['annotation'] if ruby else fitz.Rect(line['bbox']))+(-3,-3,3,3)) & rect
            pixel_rect = [max(0,int(box.x0*1.5)-pix.x),max(0,int(box.y0*1.5)-pix.y),min(pix.width,int(box.x1*1.5+.999999)-pix.x),min(pix.height,int(box.y1*1.5+.999999)-pix.y)]
            cropped = raster.crop(pixel_rect)
            ink = images.ImageChops.difference(cropped,images.Image.new('RGB',cropped.size,'white')).getbbox()
            if ink and (ink[0]==0 or ink[1]==0 or ink[2]==cropped.width or ink[3]==cropped.height):
                return None
            file=cache/(key+'-unmapped-'+str(len(crops)+1)+'.png');cropped.save(file)
            high_resolution=page.get_pixmap(dpi=300,clip=box,alpha=False)
            crops.append(dict(file=str(file.relative_to(ROOT)),sha256=sha(file.read_bytes()),pixelRect=pixel_rect,
                              reason=('Unsupported PDF text placement: '+layout_error+'; exact line retained for source comparison') if layout_error else 'Unreadable PDF character mapping; known text preserved; line retained for source comparison',
                              ocr=images.image_ocr(images.Image.frombytes('RGB',(high_resolution.width,high_resolution.height),high_resolution.samples),dpi=300),ocrDpi=300,status='unreviewed'))
            marker='［'+('組版照合待ち' if layout_error else '判読保留')+'：画像'+str(offset+len(crops))+'参照］'
            if layout_error:
                prefix = re.match(r'^\s*(?:\d+[．.]\s*|\d+\s+)', ''.join(s['text'] for s in line['spans']))
                line['spans']=[{**line['spans'][0], 'text':(known_ruby_body+' ' if known_ruby_body else prefix[0] if prefix else '')+marker, 'flags':0}]
                if ruby: line['bbox']=tuple(ruby['body'])
            else:
                for span in line['spans']:
                    span['text']=''.join(marker if images.unmapped(c) else c for c in span['text'])
        elif layout:
            line['spans']=[{**line['spans'][0], 'text':line_text, 'flags':0}]
        for span in line['spans']:
            if span['flags'] & 18 and span['text'].strip():
                style='太字・斜体' if span['flags'] & 18==18 else '太字' if span['flags'] & 16 else '斜体'
                span['text']='［'+style+'：'+span['text']+'］'
    if not crops:
        return None
    return dict(text=images.compact.prose_text(lines),crops=crops)


def clinical_contexts(doc, starts):
    contexts = []
    for page in doc:
        for block in page.get_text('dict',flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES & ~fitz.TEXT_USE_CID_FOR_UNKNOWN_UNICODE)['blocks']:
            for line in block.get('lines', []):
                text = ''.join(s['text'] for s in line['spans'])
                if '次の文を読み' not in text:
                    continue
                match = re.search(r'次の文を読み\s*(\d+)\s*([～〜~－-]|、|,)\s*(\d+)\s*の問いに答え', unicodedata.normalize('NFKC', text))
                first, last = ((int(match[1]), int(match[3])) if match else (None, None))
                if match and match[2] in ('、', ',') and last != first + 1:
                    first = last = None
                position = (page.number, line['bbox'][1])
                if first is not None and not (1 <= first <= last <= len(starts) and position < tuple(starts[first-1][1:]) and (first == 1 or tuple(starts[first-2][1:]) < position)):
                    first = last = None
                contexts.append(dict(first=first, last=last, page=page.number, top=line['bbox'][1]))
    return contexts


def prefix_has_content(page, stop):
    rect=fitz.Rect(0,35,page.rect.width,stop-1)
    return bool(page.get_text('text',clip=rect,flags=fitz.TEXTFLAGS_TEXT & ~fitz.TEXT_USE_CID_FOR_UNKNOWN_UNICODE).strip() or images.compact.region_drawings(page,rect) or any(fitz.Rect(i['bbox']).intersects(rect) for i in page.get_image_info()))


def footer_top(page):
    lines=[l for b in page.get_text('dict')['blocks'] for l in b.get('lines', [])]
    footers=[l['bbox'][1] for l in lines
             if re.match(r'(?:DK[I-X-]+|(?:HAP|TP)\d+[A-Za-z0-9-]+)', ''.join(s['text'] for s in l['spans']).strip())
             and l['bbox'][1] > page.rect.height*.8 and max(s['size'] for s in l['spans']) <= 9.2]
    if footers:
        for line in lines:
            box=fitz.Rect(line['bbox'])
            if not (box.y0 > page.rect.height*.85 and abs((box.x0+box.x1)/2-page.rect.width/2)<10
                    and re.fullmatch(r'\d{1,4}', ''.join(s['text'] for s in line['spans']).strip())):
                continue
            sides=set()
            for drawing in page.get_drawings():
                for item in drawing['items']:
                    if item[0]=='l' and abs(item[1].y-item[2].y)<.1 and box.y0 < item[1].y < box.y1:
                        lo,hi=sorted((item[1].x,item[2].x))
                        if box.x0-25 < lo < hi < box.x0:sides.add('left')
                        if box.x1 < lo < hi < box.x1+25:sides.add('right')
            if len(sides)==2:footers.append(box.y0)
    return min(footers)-3 if footers else page.rect.height


def extract_pack(task):
    source, cache, pack = task
    assets = read(source / 'asset-evidence.json')
    name = pack['sourceFile']; file = ROOT / 'private-data/github-material' / name
    digest = next(s['sha256'] for s in pack['sources'] if s['file'] == name)
    calibration=ROOT/'private-data/material-transcription/unicode-repairs.json'
    repairs=[r['id'] for r in read(calibration) if r['file'].replace('\\','/')==file.relative_to(ROOT).as_posix()] if calibration.exists() else []
    output, pending = {}, []
    if sha(file.read_bytes()) != digest:
        raise ValueError('Source PDF changed: ' + name)
    with fitz.open(stream=images.source_pdf(str(file.relative_to(ROOT)),digest),filetype='pdf') as doc:
        starts = numeric.question_starts(doc, pack)
        assert [s[0] for s in starts] == list(range(1, len(starts) + 1)), name
        starts = [(number, pn, question_top(doc[pn], top)) for number, pn, top in starts]
        contexts = clinical_contexts(doc, starts)
        checked = set()
        for record in pack['questions']:
            key = pack['examId'] + '::' + record['id']; number = int(record['number'])
            try:
                index = number - 1; _, pn, top = starts[index]
                ep, bottom = starts[index + 1][1:] if index + 1 < len(starts) else (len(doc)-1, doc[-1].rect.height-40)
                if ep > pn and index + 1 < len(starts) and bottom < 100:
                    if prefix_has_content(doc[ep],bottom):
                        raise ValueError('question continuation precedes next page anchor; registered page mapping needs source review')
                    ep -= 1; bottom = doc[ep].rect.height-40
                registered = {r['page']: r for r in record['images']}
                if any(c['first'] is None and c['page'] in registered for c in contexts):
                    raise ValueError('shared clinical question range is unreadable; source comparison required')
                following = [c for c in contexts if (pn, top) < (c['page'], c['top']) < (ep, bottom)]
                if following:
                    next_case = following[0]; ep, bottom = next_case['page'], next_case['top']
                shared = [c for c in contexts if c['first'] is not None and c['first'] <= number <= c['last']]
                if len(shared) > 1:
                    raise ValueError('overlapping shared clinical question ranges')
                sections = [('question', pn, top, ep, bottom)]
                if shared:
                    case = shared[0]; _, first_page, first_top = starts[case['first']-1]
                    sections.insert(0, ('passage', case['page'], case['top'], first_page, first_top))
                texts, passages, crops, evidence = [], [], [], []
                regions = [(role, page_number, begin-1 if page_number == begin_page else 35, stop-1 if page_number == end_page else doc[page_number].rect.height-40)
                           for role, begin_page, begin, end_page, stop in sections for page_number in range(begin_page, end_page+1)
                           if not (page_number == end_page and stop < 100 and page_number > begin_page and not prefix_has_content(doc[page_number],stop))]
                for role, page_number, begin, end in regions:
                    region = registered.get(page_number)
                    if not region:
                        raise ValueError('question crosses registered page boundary')
                    src = 'assets/github-material/' + region['file']; entry = assets.get(src)
                    if not entry:
                        raise ValueError('image already replaced by compact build')
                    delivered = source / 'web' / entry['src']
                    if sha(delivered.read_bytes()) != entry['sha256'] or entry['sourceSha256'] != region['sha256']:
                        raise ValueError('registered image changed')
                    if page_number not in checked:
                        images.compact.verified_pixels(doc[page_number], dict(region, sha256=entry['sha256']), delivered)
                        checked.add(page_number)
                    page = doc[page_number]
                    stop = min(end, footer_top(page))
                    rect = fitz.Rect(0, begin, page.rect.width, stop)
                    try:
                        text = images.compact.native_text(page, rect, uniform_ink=True)
                        text = str(text); method = 'native'
                    except ValueError as native_error:
                        fitz.TOOLS.store_shrink(100)
                        raw = page.get_pixmap(matrix=fitz.Matrix(1.5,1.5), clip=rect, alpha=False).tobytes('png')
                        crop_key = sha((key+role+str(page_number)+digest).encode())
                        line_layout = str(native_error) in ('styled, raised or clipped text', 'unsupported raised or lowered characters', 'Greek symbol font decodes to Latin letters', 'small numeral next to Greek symbol needs source typography review', 'columns, formula or overlapping lines')
                        split = partial_unmapped(page, rect, cache, crop_key, len(crops), layout=line_layout) if str(native_error)=='unmapped characters' or line_layout else None
                        partial = bool(split)
                        split = split or images.split_region(page, rect, raw, cache, crop_key)
                        if not split:
                            raise ValueError(str(native_error) + '; question text or figure boundary needs source review')
                        offset = len(crops)
                        text = re.sub(r'(文字化できない部分 )(\d+)', lambda m:m[1]+str(int(m[2])+offset), split['text'])
                        for crop in split['crops']:
                            crop.update(sourceFile=str(file.relative_to(ROOT)),sourceSha256=digest,page=page_number,sourceRect=list(rect),role=role)
                        crops.extend(split['crops']); method = ('partial-layout' if line_layout else 'partial-unmapped') if partial else 'split'
                    (passages if role == 'passage' else texts).append(text)
                    evidence.append(dict(sourceFile=str(file.relative_to(ROOT)), sourceSha256=digest, page=page_number, rect=list(rect), image=entry['src'], imageSha256=entry['sha256'], role=role, method=method, text=text, textSha256=sha(text.encode()),unicodeRepairIds=repairs,unicodeRepairSha256=sha(calibration.read_bytes()) if repairs else None))
                text = '\n\n'.join(texts)
                passage = '\n\n'.join(passages)
                if images.unmapped(text + passage) or len(text + passage) > 49000 or len(crops) > 30:
                    raise ValueError('unmapped or oversized question text')
                body = re.sub(r'^\s*(?:［太字：)?' + str(number) + r'(?:］)?\s*', '', text, count=1)
                labels = list(re.finditer(r'^\s*([1-5])[．.]\s*', body, re.M))
                if [int(m[1]) for m in labels] != list(range(1,record['optionCount']+1)):
                    raise ValueError('option sequence requires source review')
                prompt = body[:labels[0].start()].strip()
                options = [body[m.start():labels[i+1].start() if i+1<len(labels) else len(body)].strip() for i,m in enumerate(labels)]
                if not prompt or any(not o[m.end()-m.start():].strip() for o,m in zip(options,labels)):
                    raise ValueError('empty prompt or choice')
                output[key] = dict(prompt='問'+str(number)+'　'+prompt, options=options, passage=passage, crops=crops, evidence=evidence)
            except ValueError as error:
                pending.append(dict(key=key, reason=str(error)))
    return name, output, pending


def main(source):
    cache = ROOT / 'build/material-image-text/numeric'; cache.mkdir(parents=True, exist_ok=True)
    output, pending, seen, tasks = {}, [], set(), []
    for report in sorted((ROOT / 'private-data/github-material/prepared').glob('*report.json')):
        for pack in read(report).get('packs', []):
            if pack.get('status') != 'prepared' or pack.get('provider') not in ('MHLW-MEDICAL', 'MHLW-NUMERIC'):
                continue
            identity = (pack['sourceFile'], sha(json.dumps(pack['questions'],sort_keys=True).encode()))
            if identity not in seen:
                seen.add(identity); tasks.append((source, cache, pack))
    with concurrent.futures.ProcessPoolExecutor(max_workers=min(8, os.cpu_count() or 1)) as pool:
        for name, rows, review in pool.map(extract_pack, tasks):
            output.update(rows); pending.extend(review)
            print('Per-question text', name, len(output), 'pending', len(pending), flush=True)
    (cache.parent / 'numeric-text.json').write_text(json.dumps(output, ensure_ascii=False), encoding='utf-8')
    (cache.parent / 'numeric-review.json').write_text(json.dumps(pending, ensure_ascii=False), encoding='utf-8')
    print(json.dumps(dict(converted=len(output), retained=len(pending))), flush=True)


if __name__ == '__main__':
    os.environ['OMP_THREAD_LIMIT'] = '1'
    main(Path(sys.argv[1]))
