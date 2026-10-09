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
