"""Preserve common case pages and extract only the explicitly numbered written question."""
import importlib.util
import copy
import json
import re
import sys
from io import BytesIO
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('scoped_solutions',ROOT/'scripts/extract-scoped-solution-text.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
fitz,sha=m.fitz,m.sha


def drop_page_footers(split,page,pix):
    """Exclude only a centered page numeral with horizontal decoration below the body."""
    kept=[];omitted=[];text=split['text']
    class FooterPage:
        def __getattr__(self,name):return getattr(page,name)
        def get_drawings(self):return []
    for index,crop in enumerate(split['crops'],1):
        x0,y0,x1,y1=crop['pixelRect'];box=fitz.Rect((x0+pix.x)/1.5,(y0+pix.y)/1.5,(x1+pix.x)/1.5,(y1+pix.y)/1.5)
        numeral=page.get_text('text',clip=box).strip()
        drawings=m.images.compact.region_drawings(page,box)
        white=[d for d in drawings if d['type']=='f' and d.get('fill')==(1,1,1) and d.get('fill_opacity',1)==1 and all(i[0]=='re' for i in d['items'])]
        hidden=any(t['seqno']<d['seqno'] and fitz.Rect(t['bbox']).intersects(d['rect']) for d in white for t in page.get_texttrace())
        strokes=[d for d in drawings if d not in white]
        horizontal=not hidden and bool(strokes) and all(d['type']=='s' and d.get('stroke_opacity',1)==1 and d.get('color') and max(d['color'])<=.32 and all(i[0]=='l' and abs(i[1].y-i[2].y)<.1 for i in d['items']) for d in strokes)
        footer=box.y0>page.rect.height*.88 and box.width<page.rect.width*.25 and abs((box.x0+box.x1)/2-page.rect.width/2)<10 and re.fullmatch(r'\d{1,3}',numeral) and int(numeral)==page.number and horizontal
        if footer:
            native_box=fitz.Rect(box)
            for block in page.get_text('dict',clip=box)['blocks']:
                for line in block.get('lines',[]):
                    for span in line['spans']:native_box|=fitz.Rect(span['bbox'])
            try:footer=str(m.images.compact.native_text(FooterPage(),native_box+(-.1,-.1,.1,.1),uniform_ink=True)).strip()==numeral
            except ValueError:footer=False
        marker='［図・文字化できない部分 '+str(index)+'：画像参照］\n\n画像内の補助文字（原本未照合・位置関係は画像参照）\n'+numeral
        if footer and marker in text:
            text=text.replace(marker,'');omitted.append(dict(page=page.number,rect=list(box),text=numeral,reason='centered page numeral and horizontal decoration outside question/case body'))
        else:kept.append((index,crop))
    numbers={old:new for new,(old,crop) in enumerate(kept,1)}
    text=re.sub(r'部分 (\d+)：画像参照',lambda match:'部分 '+str(numbers[int(match[1])])+'：画像参照',text)
    return dict(text=text.strip(),crops=[crop for index,crop in kept],omittedFooters=omitted)


def main(source,input_file,evidence_file,output):
    output=output.resolve()
    qs=json.loads(input_file.read_bytes());images=json.loads(evidence_file.read_bytes());groups={}
    for q in qs:
        if q['examId']=='sme-consultant' and re.fullmatch(r'business-sme-case-\d+-\d+-q\d+',q['id']):groups.setdefault(q['packUrl'],[]).append(q)
    output.mkdir(parents=True,exist_ok=True);converted={};pending=[]
    for pack,rows in groups.items():
        try:
            files={images[i['src']]['identity']['region']['sourceFile'] for q in rows for i in q['images']}
            if len(files)!=1:raise ValueError('case source file mapping is not unique')
            name=files.pop();digest=sha((ROOT/name).read_bytes());doc=fitz.open(stream=m.images.source_pdf(name,digest),filetype='pdf')
            expected=[int(re.search(r'-q(\d+)$',q['id'])[1]) for q in rows];regions=m.intent_regions(doc,expected)
            first=regions[expected[0]][0];common=[(pn,[0,0,doc[pn].rect.width,first[1][1] if pn==first[0] else doc[pn].rect.height]) for pn in range(first[0]+1) if pn<first[0] or first[1][1]>0]
            page_images={}
            for q in rows:
                for image in q['images']:
                    entry=images[image['src']];region=entry['identity']['region']
                    if region['sourceSha256']!=digest or list(region['rect'])!=list(doc[region['page']].rect):raise ValueError('case image source is not an entire registered page')
                    page_images.setdefault(region['page'],image['src'])
            for pn,src in page_images.items():m.images.compact.verified_pixels(doc[pn],dict(rect=list(doc[pn].rect),sha256=images[src]['identity']['imageSha256']),source/'web'/src)
            split_cache={}
            for q,number in zip(rows,expected):
                try:
                    text_parts=[];passage=[];proof=[];crops=[]
                    for role,parts in [('common',common),('question',regions[number])]:
                        for pn,rect in parts:
                            src=page_images.get(pn)
                            if not src or src not in [i['src'] for i in q['images']]:raise ValueError('case continuation/common page not registered for this question')
                            try:
                                text=str(m.images.compact.native_text(doc[pn],fitz.Rect(rect),uniform_ink=True))
                                if m.images.unmapped(text):raise ValueError('unmapped case text')
                                (passage if role=='common' else text_parts).append(text)
                                method='native'
                            except ValueError as error:
                                # Reuse the existing text/figure partitioner before keeping a full region.
                                region_pix=doc[pn].get_pixmap(matrix=fitz.Matrix(1.5,1.5),clip=fitz.Rect(rect),alpha=False)
                                region_raster=m.images.Image.frombytes('RGB',(region_pix.width,region_pix.height),region_pix.samples)
                                buffer=BytesIO();region_raster.save(buffer,format='PNG')
                                token=(pn,tuple(rect))
                                if token not in split_cache:split_cache[token]=m.images.split_region(doc[pn],fitz.Rect(rect),buffer.getvalue(),output,sha((name+str(pn)+str(rect)).encode()))
                                split=copy.deepcopy(split_cache[token])
                                if split:split=drop_page_footers(split,doc[pn],region_pix)
                                if split:
                                    text=split['text'].replace('図・文字化できない部分','図・原本照合待ちの部分')
                                    offset=len(crops)
                                    text=re.sub(r'部分 (\d+)：画像参照',lambda match:'部分 '+str(int(match[1])+offset)+'：画像参照',text)
                                    for crop in split['crops']:
                                        x0,y0,x1,y1=crop['pixelRect']
                                        crop.update(sourceFile=name,sourceSha256=digest,page=pn,sourceRect=rect,pixelRect=[x0+region_pix.x,y0+region_pix.y,x1+region_pix.x,y1+region_pix.y],reason='Scoped case/question figure or unreviewed source region; native surrounding text retained')
                                        crops.append(crop)
                                    (passage if role=='common' else text_parts).append(text);method='split-'+role
                                    proof.append(dict(role=role,page=pn,rect=rect,text=text,textSha256=sha(text.encode()),method=method,image=src,imageSha256=images[src]['identity']['imageSha256'],omittedFooters=split.get('omittedFooters',[])))
                                    continue
                                if role=='question':raise ValueError('question region needs layout/source comparison: '+str(error))
                                # Retain the exact common region, excluding all later questions.
                                pix=doc[pn].get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False)
                                raster=m.images.Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
                                pixels=[max(0,int(rect[0]*1.5)),max(0,int(rect[1]*1.5)),min(pix.width,int(rect[2]*1.5+.999999)),min(pix.height,int(rect[3]*1.5+.999999))]
                                crop=raster.crop(pixels);file=output/(sha((name+str(pn)+str(rect)).encode())+'.png');crop.save(file)
                                crops.append(dict(file=str(file.relative_to(ROOT)),sha256=sha(file.read_bytes()),sourceFile=name,sourceSha256=digest,page=pn,sourceRect=rect,pixelRect=pixels,reason='Common case region needs layout/source comparison: '+str(error)))
                                text='［共通事例の原本照合待ち：画像'+str(len(crops))+'参照］';passage.append(text);method='exact-common-crop'
                            proof.append(dict(role=role,page=pn,rect=rect,text=text,textSha256=sha(text.encode()),method=method,image=src,imageSha256=images[src]['identity']['imageSha256']))
                    prompt='\n\n'.join(text_parts);body='\n\n'.join(passage)
                    if len(prompt)>49000 or len(body)>49000 or len(crops)>30:raise ValueError('case field/image limits')
                    converted[q['key']]=dict(prompt=prompt,passage=body,crops=crops,evidence=proof,sourceFile=name,sourceSha256=digest,removed=[i['src'] for i in q['images']],originalImages=[dict(src=i['src'],sha256=images[i['src']]['identity']['imageSha256'],page=images[i['src']]['identity']['region']['page']) for i in q['images']],fullVisualProofreading=False)
                except ValueError as error:pending.append(dict(key=q['key'],reason=str(error)))
            doc.close()
        except (ValueError,KeyError,TypeError) as error:pending.extend(dict(key=q['key'],reason=str(error)) for q in rows)
    for name,value in [('text.json',converted),('pending.json',pending)]: (output/name).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps(dict(converted=len(converted),pending=len(pending))),flush=True)


if __name__=='__main__':main(*map(Path,sys.argv[1:5]))
