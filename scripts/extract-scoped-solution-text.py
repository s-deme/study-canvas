"""Scope shared SME source solutions by explicit question anchors, never by OCR guesses."""
import importlib.util
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('solution_images', ROOT/'scripts/extract-material-image-text.py')
images = importlib.util.module_from_spec(spec); spec.loader.exec_module(images)
fitz, sha = images.fitz, images.sha
norm = lambda s: unicodedata.normalize('NFKC', s).strip()


def intent_regions(doc, expected):
    anchors = []
    for pn, page in enumerate(doc):
        for block in page.get_text('dict')['blocks']:
            for line in block.get('lines', []):
                text = norm(''.join(s['text'] for s in line['spans']))
                match = re.match(r'^第\s*(\d+)\s*問(?:\s|[（(]|$)', text)
                if match:
                    anchors.append((int(match[1]), pn, line['bbox'][1]-2))
    if [a[0] for a in anchors] != expected:
        raise ValueError('explicit question anchors do not match pack sequence; combined cases or unreadable numbering')
    result = {}
    for i, (number, pn, top) in enumerate(anchors):
        end_page, end_y = (anchors[i+1][1:]) if i+1<len(anchors) else (len(doc)-1, doc[-1].rect.height)
        result[number] = [(page, [0, top if page==pn else 0, doc[page].rect.width,
                                  end_y if page==end_page else doc[page].rect.height])
                          for page in range(pn, end_page+1)
                          if (end_y if page==end_page else doc[page].rect.height) > (top if page==pn else 0)]
    return result


def table_rows(page):
    """Keep coordinates for each column, including explicitly empty merged question cells."""
    result = []
    for table in page.find_tables().tables:
        rows = table.extract()
        extra_column=bool(rows and [norm(v or '') for v in rows[0]]==['','問題','設問','正解','配点'])
        if extra_column:
            if any(norm(row[0] or '') not in ('','合計','合 計') for row in rows[1:]): raise ValueError('unrecognized extra answer table column')
            rows=[row[1:] for row in rows]
        if not rows or [norm(v or '') for v in rows[0]] != ['問題','設問','正解','配点']:
            continue
        # Keep the find_tables cell geometry; converting thick filled borders to lines
        # can accidentally merge the header with the first answer row.
        cells=[fitz.Rect(c) for c in table.cells]
        for drawing in images.compact.region_drawings(page,fitz.Rect(table.bbox)):
            if drawing['type']=='f' and drawing.get('fill')==(1,1,1):
                if any(t['seqno']<drawing['seqno'] and fitz.Rect(t['bbox']).intersects(drawing['rect']) for t in page.get_texttrace()):
                    raise ValueError('white answer table background hides earlier text')
                continue
            for item in drawing['items']:
                if item[0]=='re':
                    box=item[1]
                    if drawing['type']=='f' and drawing.get('fill')==(0,0,0) and min(box.width,box.height)<=3:
                        a,b=(fitz.Point(box.x0,(box.y0+box.y1)/2),fitz.Point(box.x1,(box.y0+box.y1)/2)) if box.height<=3 else (fitz.Point((box.x0+box.x1)/2,box.y0),fitz.Point((box.x0+box.x1)/2,box.y1))
                        segments=[(a,b)]
                    elif drawing['type']=='s' and drawing.get('color')==(0,0,0):
                        segments=[(box.tl,box.tr),(box.tr,box.br),(box.br,box.bl),(box.bl,box.tl)]
                    else: raise ValueError('answer table contains unverified fill or drawing')
                elif item[0]=='l' and drawing['type']=='s' and drawing.get('color')==(0,0,0): segments=[(item[1],item[2])]
                else: raise ValueError('answer table contains non-border graphics')
                for a,b in segments:
                    horizontal,vertical=abs(a.y-b.y)<.1,abs(a.x-b.x)<.1
                    if not (horizontal or vertical): raise ValueError('diagonal answer table graphics')
                    borders=[]
                    for cell in cells:
                        if horizontal and min(abs(a.y-cell.y0),abs(a.y-cell.y1))<=1.5: borders.append((cell.x0,cell.x1))
                        if vertical and min(abs(a.x-cell.x0),abs(a.x-cell.x1))<=1.5: borders.append((cell.y0,cell.y1))
                    start,end=sorted((a.x,b.x) if horizontal else (a.y,b.y));cursor=start
                    for lo,hi in sorted(borders):
                        if lo<=cursor+1.5 and hi>cursor:cursor=hi
                    if cursor<end-1.5:raise ValueError('graphics do not match answer table cell borders')
        class CellPage:
            def __getattr__(self, name): return getattr(page, name)
            def get_drawings(self): return []
        number = None
        for row, geometry in zip(rows[1:], table.rows[1:]):
            source_values=[(v or '').strip() for v in row]
            values = [norm(v or '') for v in row]
            if re.sub(r'\s+','',values[0])=='合計' and values[1:3]==['',''] and values[3].isdigit(): continue
            match = re.fullmatch(r'第\s*(\d+)\s*問', values[0])
            if match: number = int(match[1])
            elif values[0]: raise ValueError('unknown question cell')
            if number is None: raise ValueError('merged question cell lacks parent')
            child = re.fullmatch(r'設問\s*(\d+)', values[1])
            if not child and values[1] not in ('-', '－', '―', '—', ''):
                raise ValueError('unknown child question cell')
            # Validate every visible cell using the existing typography/character gate.
            for value, box in zip(values, geometry.cells[1:] if extra_column else geometry.cells):
                if value and box:
                    try: native = str(images.compact.native_text(CellPage(), fitz.Rect(box), uniform_ink=True))
                    except ValueError as error:
                        if str(error)!='styled, raised or clipped text': raise
                        native=str(images.compact.native_text(CellPage(),fitz.Rect(box)+(-.75,-.75,.75,.75),uniform_ink=True))
                    if re.sub(r'\s+', '', norm(native)) != re.sub(r'\s+', '', value):
                        raise ValueError('cell extraction and source typography disagree')
                    if images.unmapped(native): raise ValueError('unmapped table cell')
            result.append(dict(number=number, child=int(child[1]) if child else None,
                               values=values, sourceValues=source_values, rect=list(geometry.bbox)))
    return result


def main(source, input_file, output, evidence_file=None):
    questions = json.loads(input_file.read_bytes())
    # Include already-textual shared solution pages: their old whole-page text also needs scoping.
    by_key={q['key']:q for q in questions}
    for pack in json.loads((source/'manifest.json').read_bytes())['packs']:
        if pack['examId']!='sme-consultant':continue
        raw=json.loads((source/'web'/pack['url']).read_bytes())
        defaults=raw.get('defaults',{}) if isinstance(raw,dict) else {}
        for row in raw['questions'] if isinstance(raw,dict) else raw:
            q={**defaults,**row};key=q['examId']+'::'+q['id']
            if key not in by_key:
                q.update(key=key,packUrl=pack['url']);q.setdefault('solutionImages',[]);by_key[key]=q
    questions=list(by_key.values())
    evidence = json.loads((evidence_file or source/'image-text-evidence.json').read_bytes())
    prior_text=json.loads((source/'text-evidence.json').read_bytes()) if (source/'text-evidence.json').exists() else {}
    registered={}
    for q in questions:
        original=prior_text.get(q['key'],{}).get('solution',{})
        registered[q['key']]=list(q['solutionImages'])
        for removed in original.get('removed',[]):
            image,region=removed['image'],removed['region']
            if image['src'] not in evidence:
                evidence[image['src']]=dict(identity=dict(imageSha256=region['sha256'],region=dict(sourceFile='private-data/'+region['archive']+'/'+region['sourceFile'],sourceSha256=region['sourceSha256'],page=region['page'],rect=region['rect'])))
            if image['src'] not in [i['src'] for i in registered[q['key']]]:registered[q['key']].append(image)
    output.mkdir(parents=True, exist_ok=True)
    converted, pending, files = {}, [], {}
    groups = {}
    for q in questions:
        if registered[q['key']]:
            groups.setdefault(q['packUrl'], []).append(q)
    for pack, qs in groups.items():
        if qs[0]['examId'] != 'sme-consultant':
            pending.extend(dict(key=q['key'], reason='solution scope parser not implemented for this source layout') for q in qs)
            continue
        try:
            sources = {evidence[i['src']]['identity']['region']['sourceFile']
                       for q in qs for i in registered[q['key']]}
            if len(sources)!=1: raise ValueError('solution images map to multiple source documents')
            name = sources.pop(); raw = (ROOT/name).read_bytes(); digest = sha(raw)
            pages = {}
            for q in qs:
                for image in registered[q['key']]:
                    entry = evidence[image['src']]; region = entry['identity']['region']
                    if region['sourceSha256']!=digest: raise ValueError('source hash changed')
                    if image['src'] not in pages:
                        pages[image['src']] = region
            doc = fitz.open(stream=images.source_pdf(name,digest),filetype='pdf')
            image_paths={}
            for src, region in pages.items():
                path=source/'web'/src
                if not path.exists():path=ROOT/'build/private/web'/src
                images.compact.verified_pixels(doc[region['page']], dict(region,sha256=evidence[src]['identity']['imageSha256']), path)
                image_paths[src]=str(path.resolve())
            if '-intent.pdf' in name:
                expected = [int(re.search(r'-q(\d+)$', q['id'])[1]) for q in qs]
                regions = intent_regions(doc, expected)
                for q, number in zip(qs, expected):
                    try:
                        parts, proof = [], []
                        for pn, rect in regions[number]:
                            srcs = [i['src'] for i in registered[q['key']] if pages[i['src']]['page']==pn]
                            if not srcs: raise ValueError('continuation page is not registered')
                            text = str(images.compact.native_text(doc[pn],fitz.Rect(rect),uniform_ink=True))
                            if images.unmapped(text): raise ValueError('unmapped characters in question intent')
                            parts.append(text); proof.append(dict(page=pn,rect=rect,text=text,textSha256=sha(text.encode()),image=srcs[0],imageFile=image_paths[srcs[0]],imageSha256=evidence[srcs[0]]['identity']['imageSha256']))
                        text='\n\n'.join(parts)
                        converted[q['key']] = dict(field='evaluationGuide',text=text,textSha256=sha(text.encode()),sourceFile=name,sourceSha256=digest,kind='official-intent',evidence=proof,removed=[i['src'] for i in q['solutionImages']],fullVisualProofreading=False)
                    except ValueError as error: pending.append(dict(key=q['key'],reason=str(error)))
            elif '-answer.pdf' in name:
                all_rows = [(pn,row) for pn,page in enumerate(doc) for row in table_rows(page)]
                if not all_rows: raise ValueError('no supported explicit answer table')
                for q in qs:
                    try:
                        match = re.search(r'-q(\d+)(?:-s(\d+))?$',q['id'])
                        if not match: raise ValueError('question id lacks explicit number')
                        number, child = int(match[1]), int(match[2]) if match[2] else None
                        matches = [(pn,r) for pn,r in all_rows if r['number']==number and (q['type']=='written' and child is None or r['child']==child)]
                        if not matches or len({r['child'] for pn,r in matches})!=len(matches): raise ValueError('answer row/child mapping is not unique')
                        if q['type']!='written' and (len(matches)!=1 or q['type']!='single' or q['answer']!='アイウエオカキ'.index(matches[0][1]['values'][2])): raise ValueError('official answer differs from stored answer; separate answer audit required')
                        children=[r['child'] for pn,r in matches]
                        if any(not re.fullmatch(r'[アイウエオカキ]',r['values'][2]) or not re.fullmatch(r'\d+',r['values'][3]) for pn,r in matches): raise ValueError('special answer/footnote requires separate source comparison')
                        if q['type']=='written' and children!=[None] and children!=list(range(1,len(children)+1)): raise ValueError('child answer sequence is incomplete')
                        proof=[]; lines=['| 問題 | 設問 | 正解 | 配点 |','| --- | --- | --- | --- |']
                        for pn,row in matches:
                            srcs=[i['src'] for i in registered[q['key']] if pages[i['src']]['page']==pn]
                            if not srcs: raise ValueError('answer page is not registered')
                            lines.append('| '+ ' | '.join(row['sourceValues'])+' |')
                            proof.append(dict(page=pn,rect=row['rect'],row=row,image=srcs[0],imageFile=image_paths[srcs[0]],imageSha256=evidence[srcs[0]]['identity']['imageSha256']))
                        text='\n'.join(lines)
                        converted[q['key']]=dict(field='modelAnswer' if q['type']=='written' else 'explanation',text=text,textSha256=sha(text.encode()),sourceFile=name,sourceSha256=digest,kind='official-answer-table',evidence=proof,removed=[i['src'] for i in q['solutionImages']],fullVisualProofreading=False)
                    except ValueError as error: pending.append(dict(key=q['key'],reason=str(error)))
            else: raise ValueError('source is not an identified official intent/answer PDF')
            files[name]=digest; doc.close()
        except (ValueError, KeyError, TypeError) as error:
            pending.extend(dict(key=q['key'],reason=str(error)) for q in qs)
    for name,value in [('text.json',converted),('pending.json',pending),('sources.json',files)]:
        if name=='text.json':
            for key,entry in converted.items():
                prior=prior_text.get(key,{});old=prior.get('solution',{})
                if old.get('field') and old['field']!=entry['field']:
                    entry['previousField']=old['field'];entry['previousValue']=old['value'];entry['originalPreviousValue']=prior['original'].get(old['field'],'')
        (output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(dict(converted=len(converted),pending=len(pending),sources=len(files))),flush=True)


if __name__=='__main__':
    main(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]),Path(sys.argv[4]) if len(sys.argv)>4 else None)
