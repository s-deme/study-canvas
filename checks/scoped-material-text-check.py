"""Re-extract scoped source content and verify exact page/crop pixels, without OCR trust."""
import importlib.util
import json
import re
import sys
import tempfile
from io import BytesIO
from pathlib import Path

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('scoped',root/'scripts/extract-scoped-solution-text.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
case_spec=importlib.util.spec_from_file_location('scoped_cases',root/'scripts/extract-scoped-case-text.py')
case_module=importlib.util.module_from_spec(case_spec);case_spec.loader.exec_module(case_module)
read=lambda p:json.loads(p.read_bytes())
directory=Path(sys.argv[1]) if len(sys.argv)>1 else Path(read(root/'build/material-transcription/current.json')['directory'])
solutions=read(directory/'scoped-solution-evidence.json')
cases=read(directory/'scoped-case-evidence.json')
docs={};tables={};checked=set();count=0;crops=0;split_cache={}
scratch=tempfile.TemporaryDirectory(dir=root/'tmp')
for key,entry in [*solutions.items(),*cases.items()]:
    name=entry['sourceFile'];raw=(root/name).read_bytes();assert m.sha(raw)==entry['sourceSha256'],key
    if name not in docs:docs[name]=m.fitz.open(stream=m.images.source_pdf(name,entry['sourceSha256']),filetype='pdf')
    doc=docs[name]
    number=int(re.search(r'-q(\d+)(?:-s\d+)?$',key)[1])
    for original in entry.get('originalImages',[]):
        image=directory/'web'/original['src'];assert m.sha(image.read_bytes())==original['sha256'],key
        if (name,original['src']) not in checked:
            m.images.compact.verified_pixels(doc[original['page']],dict(rect=list(doc[original['page']].rect),sha256=original['sha256']),image)
            checked.add((name,original['src']))
    for e in entry['evidence']:
        image=Path(e['imageFile']) if e.get('imageFile') else directory/'web'/e['image'];assert m.sha(image.read_bytes())==e['imageSha256'],key
        if (name,e['image']) not in checked:
            m.images.compact.verified_pixels(doc[e['page']],dict(rect=list(doc[e['page']].rect),sha256=e['imageSha256']),image)
            checked.add((name,e['image']))
        if entry.get('kind')=='official-answer-table':
            token=(name,e['page'])
            if token not in tables:tables[token]=m.table_rows(doc[e['page']])
            assert e['row'] in tables[token] and e['row']['number']==number,key
        elif e.get('method','native')=='native':
            assert m.sha(e['text'].encode())==e['textSha256'],key
            assert str(m.images.compact.native_text(doc[e['page']],m.fitz.Rect(e['rect']),uniform_ink=True))==e['text'],key
            count+=1
        elif e.get('method','').startswith('split-'):
            assert m.sha(e['text'].encode())==e['textSha256'],key
            token=(name,e['page'],tuple(e['rect']))
            if token not in split_cache:
                pix=doc[e['page']].get_pixmap(matrix=m.fitz.Matrix(1.5,1.5),clip=m.fitz.Rect(e['rect']),alpha=False)
                image=m.images.Image.frombytes('RGB',(pix.width,pix.height),pix.samples);buffer=BytesIO();image.save(buffer,format='PNG')
                split=m.images.split_region(doc[e['page']],m.fitz.Rect(e['rect']),buffer.getvalue(),Path(scratch.name),m.sha(str(token).encode()))
                split_cache[token]=case_module.drop_page_footers(split,doc[e['page']],pix) if split else None
            split=split_cache[token];assert split,key
            fresh=split['text'].replace('図・文字化できない部分','図・原本照合待ちの部分')
            marker=re.search(r'部分 (\d+)：画像参照',e['text']);offset=int(marker[1])-1 if marker else 0
            fresh=re.sub(r'部分 (\d+)：画像参照',lambda match:'部分 '+str(int(match[1])+offset)+'：画像参照',fresh)
            assert fresh==e['text'],key+' known common prose and unreviewed image text re-extraction'
    if entry.get('kind')=='official-answer-table':
        wanted=[r for pn,p in enumerate(doc) for r in (tables.get((name,pn)) or m.table_rows(p)) if r['number']==number]
        assert [e['row'] for e in entry['evidence']]==wanted,key+' all child answers retained'
    for crop in entry.get('crops',[]):
        path=directory/'web'/crop['src'];assert m.sha(path.read_bytes())==crop['sha256'],key
        pix=doc[crop['page']].get_pixmap(matrix=m.fitz.Matrix(1.5,1.5),alpha=False)
        expected=m.images.Image.frombytes('RGB',(pix.width,pix.height),pix.samples).crop(crop['pixelRect'])
        with m.images.Image.open(path) as actual:assert actual.convert('RGB').size==expected.size and actual.convert('RGB').tobytes()==expected.tobytes(),key
        crops+=1
# Real regression: q8 has two separate child answers, not their union or only the first.
with m.fitz.open(root/'private-data/github-material/business-sme-2012-A-answer.pdf') as doc:
    rows=m.table_rows(doc[0]);assert [r['values'][2:] for r in rows if r['number']==8]==[['エ','4'],['イ','4']]
# An extra repeated question anchor must be refused, including across pages.
with m.fitz.open(root/'private-data/github-material/business-sme-case-2021-1-intent.pdf') as source:
    duplicate=m.fitz.open();duplicate.insert_pdf(source);duplicate.insert_pdf(source)
    try:m.intent_regions(duplicate,[1,2,3,4,5]);raise AssertionError('Repeated anchors accepted')
    except ValueError:pass
    duplicate.close()
for doc in docs.values():doc.close()
scratch.cleanup()
result=dict(passed=True,solutions=len(solutions),cases=len(cases),sourcePDFs=len(docs),pageImages=len(checked),nativeRegions=count,exactCrops=crops,evidenceHashes={file:m.sha((directory/file).read_bytes()) for file in ['scoped-solution-evidence.json','scoped-case-evidence.json']},fullVisualProofreading=False)
(directory/'scoped-material-verification.json').write_text(json.dumps(result,indent=2),encoding='utf8')
print('PASS:',json.dumps(result))
