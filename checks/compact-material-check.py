"""Small synthetic checks: unsafe layouts never replace the authoritative image."""
import importlib.util
import json
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('compact', root / 'scripts/compact-material.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

doc = m.fitz.open()
page = doc.new_page()
page.insert_text((50, 50), 'Question: choose the correct statement.')
assert 'correct statement' in m.native_text(page, page.rect)
arithmetic = doc.new_page()
arithmetic.insert_text((50, 50), 'Calculate 1 + 2 = 3; 0.02 / 2 = 0.01.')
assert '0.02 / 2 = 0.01' in m.native_text(arithmetic, arithmetic.rect)
styled = doc.new_page();styled.insert_text((50, 50), 'Bold condition', fontname='hebo')
assert '［太字：Bold condition］' in m.native_text(styled, styled.rect)
indented = doc.new_page();indented.insert_text((50, 50), 'if ready:', fontname='cour');indented.insert_text((70, 70), 'execute()', fontname='cour')
try:
    m.native_text(indented, indented.rect)
    raise AssertionError('Code indentation must not be flattened')
except ValueError:
    pass
indented_prose = doc.new_page();indented_prose.insert_text((50,50),'Question 1. Choose one.',fontname='cour');indented_prose.insert_text((70,70),'Answer option.',fontname='cour')
assert 'Answer option.' in m.native_text(indented_prose,indented_prose.rect)
underline = doc.new_page()
underline.insert_text((50, 50), 'Do not omit the emphasis.')
underline.draw_line((50, 52), (150, 52))
try:
    m.native_text(underline, underline.rect)
    raise AssertionError('Zero-height underline must keep the image')
except ValueError:
    pass
page = doc[0]
page.draw_rect(m.fitz.Rect(40, 70, 200, 120))
try:
    m.native_text(page, page.rect)
    raise AssertionError('A table border must keep the image')
except ValueError:
    pass
columns = doc.new_page();columns.insert_text((50,50), 'Column A');columns.insert_text((300,50), 'Column B')
try:
    m.native_text(columns, columns.rect)
    raise AssertionError('Borderless columns must retain the image')
except ValueError:
    pass
choices_page = doc.new_page()
choices_page.insert_text((50, 50), 'Question: choose one.')
for x, label, value in [(50, 'ア', '0.12'), (170, 'イ', '0.55'), (290, 'ウ', '0.75'), (410, 'エ', '0.84')]:
    choices_page.insert_text((x, 90), label + ' ' + value, fontname='japan')
choice_text = m.native_text(choices_page, choices_page.rect)
assert m.split_choices(choice_text, list('アイウエ'))[1] == ['ア 0.12', 'イ 0.55', 'ウ 0.75', 'エ 0.84']
table_page = doc.new_page();table_number = table_page.number
table_page.insert_text((50, 50), 'Read the table, not a diagram.')
for x in [50, 150, 250]:
    table_page.draw_line((x, 80), (x, 160))
for y in [80, 120, 160]:
    table_page.draw_line((50, y), (250, y))
for x, y, text in [(60, 100, 'Item'), (160, 100, 'Value'), (60, 140, 'Mass'), (160, 140, '0.02 kg')]:
    table_page.insert_text((x, y), text)
table_text = m.native_text(table_page, table_page.rect)
assert '| Item | Value |\n| --- | --- |\n| Mass | 0.02 kg |' in table_text
white_cells=doc.new_page()
for y in [80,120]:
    for x in [50,150]:white_cells.draw_rect(m.fitz.Rect(x,y,x+100,y+40),color=(0,0,0),fill=(1,1,1))
for x,y,t in [(60,100,'Item'),(160,100,'Value'),(60,140,'Mass'),(160,140,'0.02 kg')]:white_cells.insert_text((x,y),t)
assert '| Mass | 0.02 kg |' in m.native_text(white_cells,white_cells.rect)
hidden=doc.new_page();hidden.insert_text((60,100),'Hidden answer')
hidden.draw_rect(m.fitz.Rect(50,80,250,120),color=(0,0,0),fill=(1,1,1));hidden.insert_text((60,100),'Visible answer')
try:m.native_text(hidden,hidden.rect);raise AssertionError('Hidden text in white cells accepted')
except ValueError:pass
table_question = {'topic':'Table', 'prompt':'Read the table.', 'options':['1','2'], 'passage':'Read the table, not a diagram. Item Value Mass 0.02 kg'}
assert m.text_patch(table_question, table_text)['passage'] == table_text
merged = doc.new_page()
merged.draw_rect(m.fitz.Rect(50,80,250,160));merged.draw_line((50,120),(250,120));merged.draw_line((150,120),(150,160))
merged.draw_rect(m.fitz.Rect(50,80,250,120),color=None,fill=(0.8,0.8,0.8))
merged.insert_text((60,100),'Merged title',fontname='hebo');merged.insert_text((60,140),'First');merged.insert_text((160,140),'Second')
merged_text=m.native_text(merged,merged.rect)
assert '行1〜1・列1〜2' in merged_text and '［網掛け：［太字：Merged title］］' in merged_text
table_page = doc[table_number]
table_page.draw_line((70, 180), (200, 210))
try:
    m.native_text(table_page, table_page.rect)
    raise AssertionError('A detected table must not hide another drawing')
except ValueError:
    pass
scan = doc.new_page();scan_number = scan.number
with tempfile.TemporaryDirectory(dir=root / 'build') as folder:
    source = Path(folder) / 'source'
    cache = Path(folder) / 'cache'
    (source / 'web/assets').mkdir(parents=True)
    cache.mkdir()
    plain = doc.new_page();plain.insert_text((50,50), 'Exact source region, 0.02 kg, not 002 kg.')
    crop = source / 'region.png';plain.get_pixmap(matrix=m.fitz.Matrix(1.5,1.5),alpha=False).save(crop)
    region = {'rect': list(plain.rect), 'sha256': m.sha(crop.read_bytes())}
    checked = {}
    assert '0.02 kg' in m.verified_region(plain,region,crop,'source-sha',checked)
    assert m.verified_region(plain,region,crop,'source-sha',checked) == next(iter(checked.values()))
    assert len(checked) == 1
    archive = Path(folder) / 'private-data/ipa';archive.mkdir(parents=True)
    material = Path(folder) / 'private-data/material/assets';material.mkdir(parents=True)
    pdf = archive / 'question.pdf';plain.parent.save(pdf)
    original_crop = material / 'region.png';original_crop.write_bytes(crop.read_bytes())
    original_crop.with_suffix('.geometry.json').write_text(json.dumps([plain.number,list(plain.rect)]))
    answer_crop = material / 'solution.png';answer_crop.write_bytes(crop.read_bytes())
    answer_crop.with_suffix('.geometry.json').write_text(json.dumps([plain.number,list(plain.rect)]))
    unsafe_crop = material / 'diagram.png';plain.parent[0].get_pixmap(matrix=m.fitz.Matrix(1.5,1.5),alpha=False).save(unsafe_crop)
    unsafe_crop.with_suffix('.geometry.json').write_text(json.dumps([0,list(plain.parent[0].rect)]))
    question = {'id':'q1','examId':'fixture','topic':'Question','prompt':'Read the source.',
                'options':list('アイウエ'),'passage':'','images':[{'src':'assets/region.png'}],
                'type':'written','modelAnswer':'Existing answer.','solutionImages':[{'src':'assets/solution.png'},{'src':'assets/diagram.png'}]}
    mixed = {**question, 'id':'q2', 'images':[{'src':'assets/region.png'},{'src':'assets/diagram.png'}], 'solutionImages':[]}
    (source / 'web/questions.json').write_text(json.dumps([question,mixed]))
    (source / 'manifest.json').write_text(json.dumps({'packs':[{'url':'questions.json','sources':[{'kind':kind,'file':'question.pdf','sha256':m.sha(pdf.read_bytes())} for kind in ['qs','ans']]}]}))
    saved_root = m.ROOT
    try:
        m.ROOT = Path(folder);m.extract(source,cache)
    finally:
        m.ROOT = saved_root
    patch = json.loads((cache / 'text.json').read_bytes())['fixture::q1']
    partial = json.loads((cache / 'text.json').read_bytes())['fixture::q2']['question']
    assert partial['retained'] == [{'src':'assets/diagram.png'}] and len(partial['removed']) == 1
    assert '0.02 kg' in partial['text'] and '0.02 kg' in partial['sourceText']
    assert patch['original']['solutionImages'] == question['solutionImages']
    assert patch['solution']['retained'] == [{'src':'assets/diagram.png'}]
    assert patch['solution']['field'] == 'modelAnswer' and 'Existing answer.' in patch['solution']['value']
    assert len(patch['solution']['removed']) == 1 and '0.02 kg' in patch['solution']['text']
    assert json.loads((cache / 'review.json').read_bytes())[0]['reason'] == 'solution layout needs review'
    wrong = dict(region,sha256='wrong-hash')
    try:
        m.verified_region(plain,wrong,crop,'source-sha',checked)
        raise AssertionError('Changed source image must be rejected')
    except ValueError:
        pass
    altered = source / 'altered.png';m.Image.new('RGB',m.Image.open(crop).size,'white').save(altered)
    wrong_pixels = dict(region,sha256=m.sha(altered.read_bytes()))
    for _ in range(2):
        try:
            m.verified_region(plain,wrong_pixels,altered,'source-sha',checked)
            raise AssertionError('Different crop pixels must be rejected, including cached failures')
        except ValueError:
            pass
    scan = doc[scan_number]
    image = m.Image.new('RGBA', (80, 80), (30, 50, 90, 150))
    file = source / 'web/assets/test.png'
    image.save(file)
    scan.insert_image(scan.rect, filename=file)
    m.fitz.TOOLS.store_shrink(100)
    scan_crop = source / 'scan-crop.png';scan.get_pixmap(matrix=m.fitz.Matrix(1.5,1.5),alpha=False).save(scan_crop)
    scan.get_pixmap(matrix=m.fitz.Matrix(0.5,0.5),alpha=False)
    m.verified_pixels(scan,{'rect':list(scan.rect),'sha256':m.sha(scan_crop.read_bytes())},scan_crop)
    try:
        m.native_text(scan, scan.rect)
        raise AssertionError('Scan must keep the image')
    except ValueError:
        pass
    asset, entry = m.compress((source, cache, 'assets/test.png'))
    assert entry['src'].endswith('.webp')
    decoded = m.Image.open(cache / entry['file']).convert('RGBA')
    assert decoded.tobytes() == image.tobytes()
    assert m.compress((source, cache, asset))[1] == entry
    metadata = cache / (entry['sourceSha256'] + '.json')
    old = dict(entry, method=1)
    metadata.write_text(json.dumps(old), encoding='utf-8')
    upgraded = m.compress((source, cache, asset))[1]
    assert upgraded['method'] == m.COMPRESSION_METHOD and upgraded['bytes'] <= entry['bytes']
    entry = upgraded
    (cache / entry['file']).write_bytes(b'corrupt cache')
    assert m.compress((source, cache, asset))[1] == entry
    duplicate = source / 'web/assets/duplicate.png';duplicate.write_bytes(file.read_bytes())
    audio = source / 'web/assets/audio.mp3';audio.write_bytes(b'byte-identical-audio-fixture')
    audio_copy = source / 'web/assets/audio-copy.mp3';audio_copy.write_bytes(audio.read_bytes())
    jobs = []
    class InlinePool:
        def __init__(self, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def map(self, fn, tasks, **kwargs):
            for task in tasks:
                jobs.append(task[2]);yield fn(task)
    pool = m.concurrent.futures.ProcessPoolExecutor
    try:
        m.concurrent.futures.ProcessPoolExecutor = InlinePool
        grouped = m.compress_assets(source,cache,[asset,'assets/duplicate.png','assets/audio.mp3','assets/audio-copy.mp3'])
    finally:
        m.concurrent.futures.ProcessPoolExecutor = pool
    assert len(jobs)==3 and len(grouped)==4
    assert grouped[asset] == grouped['assets/duplicate.png']
    for name in ['assets/audio.mp3','assets/audio-copy.mp3']:
        assert grouped[name]['src']==name and grouped[name]['sha256']==m.sha(audio.read_bytes())
    audio.write_bytes(file.read_bytes())
    untouched = m.compress((source,cache,'assets/audio.mp3'))[1]
    assert untouched['src']=='assets/audio.mp3' and untouched['sha256']==m.sha(audio.read_bytes())
prompt, choices = m.split_choices('問1 否定に注意。\nア 10 kg\nイ 20 kg\nウ 30 kg\nエ 40 kg', list('アイウエ'))
assert prompt == '問1 否定に注意。' and choices[2] == 'ウ 30 kg'
numeric = {'topic':'Question 1','prompt':'Keep the 2023-10-01 law instruction.','options':['1','2','3'],'passage':'0.02 kg is not 002 kg.'}
patch = m.text_patch(numeric,numeric['passage'])
assert patch['mode']=='passage' and patch['prompt']==numeric['prompt'] and patch['options']==numeric['options']
image_title={**numeric,'topic':'画像通信 問1','prompt':'画像通信 問1\n原本画像の問題番号に回答してください。画像で確認できます。'}
assert m.text_patch(image_title,image_title['passage'])['prompt']=='画像通信 問1\n原本資料の問題番号に回答してください。資料で確認できます。'
for unsafe in ['', '0.02 kg is 002 kg.', 'x'*50001]:
    try:
        m.text_patch(numeric,unsafe)
        raise AssertionError('Blank, mismatched and oversized text must retain images')
    except ValueError:
        pass
try:
    m.split_choices('問1\nア first\nウ missing second', list('アイウエ'))
    raise AssertionError('Missing option must retain the image')
except ValueError:
    pass
print('PASS: native prose, table/scan fallback, choice labels, alpha pixels, cache resume and corrupt-cache repair')
