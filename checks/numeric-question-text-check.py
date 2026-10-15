"""A neighboring diagram must not keep a text-only question as a page image."""
import importlib.util
import json
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('numeric_text', root / 'scripts/extract-numeric-question-text.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
with tempfile.TemporaryDirectory(dir=root / 'private-data/github-material') as folder:
    path = Path(folder); (path / 'web/assets/github-material').mkdir(parents=True); cache = path / 'cache'; cache.mkdir()
    doc = m.fitz.open(); doc.new_page(); page = doc.new_page(width=519, height=725)
    for number, y in [(1,70),(2,200)]:
        page.insert_text((76,y),str(number),fontname='Times-Bold',fontsize=10)
        page.insert_text((90,y),'Which is not present?',fontname='Times-Roman',fontsize=10)
    for y in [100,350]:
        page.insert_text((95,y),'1. First',fontsize=10); page.insert_text((95,y+20),'2. Second',fontsize=10)
    page.draw_rect(m.fitz.Rect(120,240,220,300)); page.insert_text((130,270),'Diagram label')
    page.draw_line((220,270),(260,285))
    page.insert_text((330,680),'HAP05rn-amor-7',fontsize=8)
    source = path / 'source.pdf'; doc.save(source)
    image = path / 'web/assets/github-material/fixture.png'
    page.get_pixmap(matrix=m.fitz.Matrix(1.5,1.5),alpha=False).save(image)
    digest = m.sha(image.read_bytes()); name = str(source.relative_to(root / 'private-data/github-material'))
    region = dict(file='fixture.png',page=1,rect=list(page.rect),sha256=digest)
    pack = dict(sourceFile=name,examId='fixture',sources=[dict(file=name,sha256=m.sha(source.read_bytes()))],questions=[dict(id='fixture-q00'+str(n),number=str(n),optionCount=2,images=[region]) for n in [1,2]])
    (path / 'asset-evidence.json').write_text(json.dumps({'assets/github-material/fixture.png':dict(src='assets/github-material/fixture.png',sha256=digest,sourceSha256=digest)}))
    _, rows, pending = m.extract_pack((path,cache,pack))
    assert not pending, pending
    first = rows['fixture::fixture-q001']; second = rows['fixture::fixture-q002']
    assert first['options']==['1. First','2. Second'] and not first['crops']
    assert 'Diagram label' not in first['prompt']
    assert len(second['crops'])==1 and '画像参照' in second['prompt']
    assert all('HAP05' not in option for option in second['options']),'Publisher footer leaked into the final choice'
    crop = second['crops'][0]
    rect = second['evidence'][0]['rect']
    raster = page.get_pixmap(matrix=m.fitz.Matrix(1.5,1.5),clip=m.fitz.Rect(rect),alpha=False)
    with m.images.Image.open(root / crop['file']) as actual:
        expected = m.images.Image.frombytes('RGB',(raster.width,raster.height),raster.samples).crop(crop['pixelRect'])
        assert actual.tobytes()==expected.tobytes()
with tempfile.TemporaryDirectory(dir=root / 'private-data/github-material') as folder:
    path = Path(folder); (path / 'web/assets/github-material').mkdir(parents=True); cache = path / 'cache'; cache.mkdir()
    doc = m.fitz.open(); doc.new_page(); page = doc.new_page(width=519,height=725)
    for y, text in [(45,'次の文を読み1～2の問いに答えよ。'),(360,'次の文を読み3～4の問いに答えよ。')]:
        page.insert_text((50,y),text,fontname='japan',fontsize=10)
        page.insert_text((70,y+20),'Case A: 0.02 kg, not 002 kg.' if y==45 else 'Case B: 23 years.',fontsize=10)
    for number,y in [(1,100),(2,230),(3,420),(4,550)]:
        page.insert_text((76,y),str(number),fontname='Times-Bold',fontsize=10)
        page.insert_text((90,y),'Which is correct?',fontsize=10)
        for i in [1,2]:page.insert_text((95,y+i*25),str(i)+'. Choice '+str(i),fontsize=10)
    source = path / 'source.pdf'; doc.save(source)
    image = path / 'web/assets/github-material/shared.png'; page.get_pixmap(matrix=m.fitz.Matrix(1.5,1.5),alpha=False).save(image)
    digest=m.sha(image.read_bytes()); name=str(source.relative_to(root / 'private-data/github-material'))
    region=dict(file='shared.png',page=1,rect=list(page.rect),sha256=digest)
    pack=dict(sourceFile=name,examId='fixture',sources=[dict(file=name,sha256=m.sha(source.read_bytes()))],questions=[dict(id='q'+str(n),number=str(n),optionCount=2,images=[region]) for n in [1,2,3,4]])
    (path/'asset-evidence.json').write_text(json.dumps({'assets/github-material/shared.png':dict(src='assets/github-material/shared.png',sha256=digest,sourceSha256=digest)}))
    _,rows,pending=m.extract_pack((path,cache,pack));assert not pending,pending
    for number in [1,2,3,4]:
        row=rows['fixture::q'+str(number)]
        assert row['options']==['1. Choice 1','2. Choice 2']
        assert ('Case A: 0.02 kg, not 002 kg.' in row['passage'])==(number<=2)
        assert ('Case B: 23 years.' in row['passage'])==(number>=3)
        assert 'Case' not in row['prompt'] and all('Case' not in o for o in row['options'])
print('PASS: question boundaries, adjacent diagrams, choice order, exact crops and explicit shared-case ranges')
footer_doc=m.fitz.open();footer_page=footer_doc.new_page(width=400,height=600)
footer_page.insert_text((198,550),'7',fontsize=8)
footer_page.insert_text((300,585),'TP07ct-amor-5',fontsize=7)
assert m.footer_top(footer_page)>560, 'A bottom numeric answer without page-number rules must survive'
footer_page.draw_line((175,547),(185,547));footer_page.draw_line((215,547),(225,547))
assert m.footer_top(footer_page)<545
footer_doc.close()
medical = root/'private-data/github-material/expansion-tp150511-05am_01.pdf'
if medical.exists():
    with m.fitz.open(medical) as source:
        page=source[4]
        text=str(m.images.compact.native_text(page,m.fitz.Rect(0,244.52,page.rect.width,404.52),uniform_ink=True))
        assert '［太字：適切でない］' in text and '5．関節液' in text
        assert '栄養サポート' not in text and '血清成分' not in text
        assert m.footer_top(page)<670.71
        text=str(m.images.compact.native_text(page,m.fitz.Rect(0,404.52,page.rect.width,m.footer_top(page)),uniform_ink=True))
        assert text.endswith('5．総コレステロール') and 'TP07' not in text
    print('PASS: real sheet-edge marks do not block the complete negative medical question')
medical = root/'private-data/github-material/expansion-tp180511-07a_01.pdf'
if medical.exists():
    with m.fitz.open(medical) as source:
        page=source[7]
        assert m.footer_top(page)<660.32, 'DK publisher codes may contain Japanese suffixes'
        text=str(m.images.compact.native_text(page,m.fitz.Rect(0,397.4422,page.rect.width,m.footer_top(page)),uniform_ink=True))
        assert text.endswith('5．自己免疫性溶血性貧血') and 'DKIX' not in text
with tempfile.TemporaryDirectory(dir=root/'tmp') as folder:
    path=Path(folder);doc=m.fitz.open();page=doc.new_page()
    page.insert_text((50,100),'Known negation: not 0.02 kg.')
    page.insert_text((50,140),'1. Known value ',fontsize=12)
    page.insert_text((145,140),'4',fontsize=12)
    page.insert_text((50,180),'2. Second choice.')
    class BrokenMapping:
        def __getattr__(self,name):return getattr(page,name)
        def get_text(self,kind,**kwargs):
            data=page.get_text(kind,**kwargs)
            for block in data['blocks']:
                for line in block.get('lines',[]):
                    for span in line['spans']:
                        if kind=='dict' and span['text']=='4':span['text']='\x08'
                        if kind=='rawdict' and ''.join(c['c'] for c in span['chars'])=='4':span['chars'][0]['c']='\x08'
            return data
    broken=BrokenMapping()
    try:m.images.compact.native_text(broken,page.rect);raise AssertionError('Broken glyph accepted')
    except ValueError as error:assert str(error)=='unmapped characters',error
    partial=m.partial_unmapped(broken,page.rect,path,'fixture',0)
    assert partial and 'not 0.02 kg.' in partial['text'] and '2. Second choice.' in partial['text']
    assert '判読保留：画像1参照' in partial['text'] and not m.images.unmapped(partial['text'])
    assert len(partial['crops'])==1 and partial['crops'][0]['status']=='unreviewed'
    raster=page.get_pixmap(matrix=m.fitz.Matrix(1.5,1.5),alpha=False)
    with m.images.Image.open(root/partial['crops'][0]['file']) as actual:
        assert actual.tobytes()==m.images.Image.frombytes('RGB',(raster.width,raster.height),raster.samples).crop(partial['crops'][0]['pixelRect']).tobytes()
print('PASS: unknown characters explicit, numbers/negation retained, unreviewed OCR and exact line pixels')
record=next(r for r in m.read(root/'private-data/material-transcription/corrections.json') if r['key']=='orthoptist::medical-official-tp200414-10b_01-q003')
evidence=record['evidence'][0]
with m.fitz.open(root/evidence['file']) as doc:
    page=doc[evidence['page']-1];rect=m.fitz.Rect(evidence['rect'])
    assert '年.2018 年0' in page.get_text('text',clip=rect),'Real fallback-CID regression fixture changed'
    try:m.images.compact.native_text(page,rect,uniform_ink=True);raise AssertionError('Fallback CID punctuation accepted as original text')
    except ValueError as error:assert str(error)=='unmapped characters',error
    with tempfile.TemporaryDirectory(dir=root/'tmp') as folder:
        partial=m.partial_unmapped(page,rect,Path(folder),'real-cid',0)
        assert partial and '年.2018 年0' not in partial['text']
        assert '判読保留' in partial['text'] and len(partial['crops'])==2
print('PASS: real Japanese PDF fallback CIDs never masquerade as parentheses or digits')
name=Path(evidence['file']).as_posix();digest=m.sha((root/name).read_bytes())
with m.fitz.open(root/name) as original,m.fitz.open(stream=m.images.source_pdf(name,digest),filetype='pdf') as repaired:
    text=repaired[4].get_text('text',flags=m.fitz.TEXTFLAGS_TEXT & ~m.fitz.TEXT_USE_CID_FOR_UNKNOWN_UNICODE)
    assert '平成30 年(2018 年)' in text and '総人口は2億2600' in text
    assert '抗アクアポリン4抗体' in repaired[5].get_text() and '〈AZOOR〉' in repaired[5].get_text()
    assert '第1眼位' in repaired[10].get_text() and 'Parks の3step' in repaired[10].get_text()
    for a,b in zip(original,repaired):
        assert a.get_pixmap(matrix=m.fitz.Matrix(1.5,1.5),alpha=False).samples==b.get_pixmap(matrix=m.fitz.Matrix(1.5,1.5),alpha=False).samples,a.number
    assert m.sha((root/name).read_bytes())==digest
print('PASS: reviewed font-code repairs, all original PDF page pixels identical and original file unchanged')
doc=m.fitz.open();page=doc.new_page()
assert not m.prefix_has_content(page,95)
page.insert_text((50,65),'Continuation: 0.02 kg, not 002 kg.')
assert m.prefix_has_content(page,95),'Continuation above the next anchor was discarded'
picture=doc.new_page();picture.draw_rect(m.fitz.Rect(50,50,100,80))
assert m.prefix_has_content(picture,95),'A continued figure above the next anchor was discarded'
print('PASS: next-page text and figure continuations cannot be silently omitted')
doc=m.fitz.open();page=doc.new_page()
page.insert_text((50,50),'次の文を読み45、46の問いに答えよ。',fontname='japan')
assert m.clinical_contexts(doc,[(n,0,n/2 if n<45 else 100+n) for n in range(1,47)])[0]['last']==46
page.insert_text((50,80),'次の文を読み1、3の問いに答えよ。',fontname='japan')
assert m.clinical_contexts(doc,[(n,0,100+n*10) for n in range(1,47)])[1]['first'] is None,'A comma cannot imply an unlisted middle question'
with m.fitz.open(root/'private-data/github-material/expansion-tp150511-05am_01.pdf') as doc:
    text=str(m.images.compact.native_text(doc[8],m.fitz.Rect(0,240,doc[8].rect.width,375),uniform_ink=True))
    assert '1．Addison 病 — 副腎皮質刺激ホルモン' in text
    assert '5．副腎性Cushing 症候群 — アルドステロン' in text
    assert '溶血性' not in text and 'エリスロポエチン' not in text
with m.fitz.open(root/'private-data/github-material/expansion-tp150511-03-1pm.pdf') as doc:
    starts=m.numeric.question_starts(doc,{})
    case=next(c for c in m.clinical_contexts(doc,starts) if c['first']==45)
    assert case['last']==46 and case['page']==25
print('PASS: explicit comma-paired cases and original choice connector/term correspondence')
with tempfile.TemporaryDirectory(dir=root/'tmp') as folder:
    doc=m.fitz.open();page=doc.new_page()
    page.insert_text((50,60),'Which is not 0.02 kg?',fontsize=12)
    page.insert_text((50,100),'1. FEV',fontsize=12)
    page.insert_text((87,103),'1.0',fontsize=8)
    page.insert_text((50,140),'2. Plain option',fontsize=12)
    result=m.partial_unmapped(page,page.rect,Path(folder),'layout',0,layout=True)
    assert result and 'Which is not 0.02 kg?' in result['text'] and '2. Plain option' in result['text']
    assert '1. ［組版照合待ち：画像1参照］' in result['text'] and 'FEV1.0' not in result['text']
    assert len(result['crops'])==1 and result['crops'][0]['status']=='unreviewed'
    raster=page.get_pixmap(matrix=m.fitz.Matrix(1.5,1.5),alpha=False)
    with m.images.Image.open(root/result['crops'][0]['file']) as actual:
        assert actual.tobytes()==m.images.Image.frombytes('RGB',(raster.width,raster.height),raster.samples).crop(result['crops'][0]['pixelRect']).tobytes()
    page.draw_line((80,180),(200,180))
    assert m.partial_unmapped(page,page.rect,Path(folder),'layout-with-figure',0,layout=True) is None
print('PASS: unsupported placement stays in exact line pixels; ordinary choices and numbers remain text')

medical=root/'private-data/github-material/expansion-tp150511-05am_01.pdf'
digest=m.sha(medical.read_bytes());rect=m.fitz.Rect(60,380,475,535)
with m.fitz.open(medical) as original:
    assert 'b' in original[8].get_text('text',clip=rect)
    try:m.images.compact.native_text(original[8],rect,uniform_ink=True);raise AssertionError('Greek glyph decoded as Latin accepted')
    except ValueError as error:assert str(error)=='Greek symbol font decodes to Latin letters',error
with m.fitz.open(stream=m.images.source_pdf(medical.relative_to(root).as_posix(),digest),filetype='pdf') as repaired:
    page=repaired[8]
    assert 'β' in page.get_text('text',clip=rect)
    try:m.images.compact.native_text(page,rect,uniform_ink=True);raise AssertionError('Small subscript flattened')
    except ValueError as error:assert str(error)=='small numeral next to Greek symbol needs source typography review',error
    with tempfile.TemporaryDirectory(dir=root/'tmp') as folder:
        partial=m.partial_unmapped(page,rect,Path(folder),'greek-small-number',0,layout=True)
        assert partial and len(partial['crops'])==1 and '組版照合待ち' in partial['text']
        assert 'クレアチニンクリアランス' in partial['text'] and 'b 2' not in partial['text']
print('PASS: real Greek font calibration, Latin fallback rejected and unreviewed small subscript kept as exact source pixels')

medical=root/'private-data/github-material/expansion-tp170425-05b_01.pdf'
with m.fitz.open(medical) as doc:
    starts=m.numeric.question_starts(doc,{})
    _,pn,top=starts[4];_,ep,end=starts[5]
    assert m.prefix_has_content(doc[pn],top),'Real next-question ruby fixture changed'
    adjusted=m.question_top(doc[pn],top)
    assert adjusted<top and not m.prefix_has_content(doc[pn],adjusted),'Next-question ruby cannot be assigned to the previous question'
    rect=m.fitz.Rect(0,adjusted-1,doc[pn].rect.width,m.question_top(doc[ep],end)-1)
    with tempfile.TemporaryDirectory(dir=root/'tmp') as folder:
        partial=m.partial_unmapped(doc[pn],rect,Path(folder),'real-ruby-reading',0,layout=True)
        assert partial and len(partial['crops'])==5
        assert '看護師の業務従事者届の届出の間隔' in partial['text'] and 'かんご' not in partial['text']
        assert all(value in partial['text'] for value in ['1．1 年','2．2 年','3．5 年','4．10 年'])
        pix=doc[pn].get_pixmap(matrix=m.fitz.Matrix(1.5,1.5),clip=rect,alpha=False)
        raster=m.images.Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
        for crop in partial['crops']:
            assert crop['status']=='unreviewed' and 'ruby reading association' in crop['reason']
            with m.images.Image.open(root/crop['file']) as actual:assert actual.tobytes()==raster.crop(crop['pixelRect']).tobytes()
print('PASS: next-question ruby scope, known main text/numeric choices and exact annotation rows preserved separately')
