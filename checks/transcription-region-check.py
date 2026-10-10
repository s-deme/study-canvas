import importlib.util
import json
import tempfile
from pathlib import Path

root=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('region',root/'scripts/transcription-region.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
records=json.loads((root/'private-data/material-transcription/corrections.json').read_bytes())
for record in records:
    for evidence in record['evidence']:
        with m.fitz.open(root/evidence['file']) as doc:
            assert 0<evidence['page']<=len(doc)
            assert doc[evidence['page']-1].rect.contains(m.fitz.Rect(evidence['rect'])),evidence
with tempfile.TemporaryDirectory(dir=root/'tmp') as folder:
    path=Path(folder);doc=m.fitz.open();page=doc.new_page()
    page.insert_text((50,50),'0.02 kg, not 002 kg.');page.draw_rect(m.fitz.Rect(45,65,200,110))
    source=path/'source.pdf';doc.save(source);doc.close()
    data=m.extract(source,1,[40,30,220,120],path/'native',rotation=90)
    assert data['status']=='unreviewed' and '0.02 kg' in data['native']
    assert data['rotation']==90 and (path/'native.png').exists()
    assert m.fitz.Pixmap(str(path/'native.png')).xres==300
    with m.fitz.open(source) as original:
        original[0].get_pixmap(dpi=300).save(path/'upright.png')
    image=m.extract(path/'upright.png',1,None,path/'image',ocr=True)
    assert image['status']=='unreviewed' and '0.02' in image['ocr']
    assert not image['native']
    try:m.extract(source,1,[-1,0,200,100],path/'invalid');raise AssertionError('Outside crop accepted')
    except ValueError:pass
    for page,dpi in [(0,300),(2,300),(1,0)]:
        try:m.extract(source,page,None,path/'invalid',dpi=dpi);raise AssertionError('Invalid page/resolution accepted')
        except ValueError:pass
print('PASS: region bounds, rotated raster, native text with drawings, extraction remains unreviewed')

spec=importlib.util.spec_from_file_location('image_text',root/'scripts/extract-material-image-text.py')
batch=importlib.util.module_from_spec(spec);spec.loader.exec_module(batch)
with tempfile.TemporaryDirectory(dir=root/'tmp') as folder:
    path=Path(folder);(path/'web/assets').mkdir(parents=True);cache=path/'cache';cache.mkdir()
    doc=batch.fitz.open();page=doc.new_page(width=400,height=400)
    page.insert_text((30,40),'Question: follow the diagram.',fontsize=14)
    page.draw_rect(batch.fitz.Rect(70,100,180,180))
    page.draw_line((180,140),(260,220))
    page.insert_text((85,140),'Label A')
    page.insert_text((30,320),'Answer options: first, second.',fontsize=14)
    source=path/'source.pdf';doc.save(source)
    image=path/'web/assets/source.png';page.get_pixmap(matrix=batch.fitz.Matrix(1.5,1.5),alpha=False).save(image)
    raw=image.read_bytes();region=dict(page=0,rect=list(page.rect),sha256=batch.sha(raw),sourceFile=str(source.relative_to(root)),sourceSha256=batch.sha(source.read_bytes()))
    task=(path,cache,'assets/source.png',batch.sha(raw),region)
    src,result=batch.extract(task)
    assert result['status']=='unreviewed' and result['method']=='native+cropped-images'
    assert 'Question:' in result['text'] and 'Answer options:' in result['text'] and 'Label A' in result['text']
    assert '位置関係は画像参照' in result['text']
    assert len(result['crops'])==1
    crop=result['crops'][0]
    with batch.Image.open(root/crop['file']) as cropped,batch.Image.open(image) as original:
        assert cropped.tobytes()==original.convert('RGB').crop(crop['pixelRect']).tobytes()
        assert cropped.height<original.height/2 and cropped.width<original.width
    assert batch.extract(task)[1]==result,'Resume changed the extraction'
    (root/crop['file']).write_bytes(b'broken')
    assert batch.extract(task)[1]==result,'Corrupt crop was not rebuilt'
    try:batch.extract((path,cache,src,'changed',region));raise AssertionError('Changed image accepted')
    except ValueError:pass
    page.set_rotation(90)
    assert batch.split_region(page,page.rect,raw,cache,'rotated') is None
    page.set_rotation(0);page.insert_text((30,370),'Invisible answer',fill_opacity=0)
    assert batch.split_region(page,page.rect,raw,cache,'invisible') is None,'Invisible text must not replace visible source pixels'
    thick=batch.fitz.open();thick_page=thick.new_page(width=400,height=400)
    thick_page.insert_text((30,40),'Question: preserve the whole figure.')
    thick_page.draw_rect(batch.fitz.Rect(100,100,200,200),width=18)
    thick_raw=thick_page.get_pixmap(matrix=batch.fitz.Matrix(1.5,1.5),alpha=False).tobytes('png')
    assert batch.split_region(thick_page,thick_page.rect,thick_raw,cache,'thick') is None,'Ink crossing a crop boundary must retain the source image'
    thick.close()
    raster=batch.fitz.open();raster_page=raster.new_page(width=250,height=90)
    raster_page.insert_text((15,55),'RASTER WORDS',fontsize=24)
    picture=raster_page.get_pixmap(matrix=batch.fitz.Matrix(2,2),alpha=False).tobytes('png')
    mixed=batch.fitz.open();mixed_page=mixed.new_page(width=400,height=400)
    mixed_page.insert_text((30,40),'Question: read the figure.')
    mixed_page.insert_image(batch.fitz.Rect(60,110,340,210),stream=picture)
    mixed_page.insert_text((30,320),'Answer options: first, second.')
    mixed_raw=mixed_page.get_pixmap(matrix=batch.fitz.Matrix(1.5,1.5),alpha=False).tobytes('png')
    mixed_result=batch.split_region(mixed_page,mixed_page.rect,mixed_raw,cache,'raster')
    assert mixed_result and 'RASTER' in mixed_result['text'] and 'WORDS' in mixed_result['text'],'Embedded readable text must be OCRed while its figure is retained'
    assert len(mixed_result['crops'])==1
    mixed.close();raster.close()
print('PASS: diagram-only pixel-exact crops, surrounding prose, labels retained in crop, cache repair and hash rejection')
