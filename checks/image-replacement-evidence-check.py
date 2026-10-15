"""Recheck delivered text replacements and figure crops against immutable sources."""
import importlib.util
import json
import re
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('image_text', root / 'scripts/extract-material-image-text.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
directory = Path(sys.argv[1]) if len(sys.argv)>1 else Path(m.read(root / 'build/material-transcription/current.json')['directory'])
directory.resolve().relative_to((root/'build/material-transcription').resolve())
native = crops = numeric_native = numeric_partial = 0
for src, entry in m.read(directory / 'image-text-evidence.json').items():
    image = directory / 'web' / src
    region=entry['identity'].get('region')
    if entry.get('sourceTextBeforeUnicodeRepair') is not None:
        assert m.sha(entry['sourceTextBeforeUnicodeRepair'].encode())==entry['sourceTextBeforeUnicodeRepairSha256'],src
        assert region and m.original_region_text(region)==entry['sourceTextBeforeUnicodeRepair'],src+' original decoded source text'
    if region and region.get('unicodeRepairSha256'):
        assert m.sha((directory/'unicode-repairs.json').read_bytes())==region['unicodeRepairSha256'],src
        assert m.sha((root/'private-data/material-transcription/unicode-repairs.json').read_bytes())==region['unicodeRepairSha256'],src
    if entry.get('nativeVerified') or entry.get('crops'):
        assert m.sha(image.read_bytes()) == entry['identity']['imageSha256'], src
    if entry.get('nativeVerified'):
        fresh = m.verify_native(dict(method='native'),entry['identity']['region'],image)
        assert fresh.get('nativeVerified') and fresh['text'] == entry['text'], src
        native += 1
    elif entry.get('crops'):
        assert region, src+' missing original PDF geometry'
        with m.fitz.open(stream=m.source_pdf(region['sourceFile'],region['sourceSha256']),filetype='pdf') as source:
            m.compact.verified_pixels(source[region['page']],dict(region,sha256=entry['identity']['imageSha256']),image)
    for crop in entry.get('crops', []):
        raw = (directory / 'web' / crop['src']).read_bytes()
        assert m.sha(raw) == crop['sha256'], src
        with m.Image.open(image) as original, m.Image.open(directory / 'web' / crop['src']) as actual:
            assert actual.convert('RGB').tobytes() == original.convert('RGB').crop(crop['pixelRect']).tobytes(), src
        crops += 1
print(f'Checked generic evidence: {native} native replacements, {crops} exact crops',flush=True)
spec = importlib.util.spec_from_file_location('numeric_text', root / 'scripts/extract-numeric-question-text.py')
partial = importlib.util.module_from_spec(spec);spec.loader.exec_module(partial)
partial.images.image_ocr=lambda image,dpi=150:'' # Recheck known text without rerunning unreviewed OCR.
scratch=tempfile.TemporaryDirectory(dir=root/'tmp')
docs, checked_pixels = {}, set()
for index,(key, entry) in enumerate(m.read(directory / 'numeric-text-evidence.json').items(),1):
    rasters = []
    for evidence in entry['evidence']:
        name = evidence['sourceFile']
        if evidence.get('unicodeRepairIds'):
            assert m.sha((directory/'unicode-repairs.json').read_bytes())==evidence['unicodeRepairSha256'],key
            assert m.sha((root/'private-data/material-transcription/unicode-repairs.json').read_bytes())==evidence['unicodeRepairSha256'],key
        if name not in docs:
            raw = (root / name).read_bytes(); assert m.sha(raw) == evidence['sourceSha256'], key
            docs[name] = m.fitz.open(stream=m.source_pdf(name,evidence['sourceSha256']),filetype='pdf')
        assert m.sha(evidence['text'].encode())==evidence['textSha256'],key
        page=docs[name][evidence['page']]
        if evidence['method']=='native':
            assert str(m.compact.native_text(page,m.fitz.Rect(evidence['rect']),uniform_ink=True))==evidence['text'],key
            numeric_native+=1
        elif evidence['method'] in ('partial-unmapped', 'partial-layout'):
            layout=evidence['method']=='partial-layout'
            if not layout:
                assert m.unmapped(page.get_text('text',clip=m.fitz.Rect(evidence['rect']),flags=m.fitz.TEXTFLAGS_TEXT & ~m.fitz.TEXT_USE_CID_FOR_UNKNOWN_UNICODE)) and '判読保留：画像' in evidence['text'],key
            assert any(c.get('reason') and c.get('status')=='unreviewed' for c in entry['crops']),key
            offset=min(map(int,re.findall(r'(?:判読保留|組版照合待ち)：画像(\d+)参照',evidence['text'])))-1
            fresh=partial.partial_unmapped(page,m.fitz.Rect(evidence['rect']),Path(scratch.name),'recheck-'+str(numeric_partial),offset,layout=layout)
            assert fresh and fresh['text']==evidence['text'],key+' known source text'
            assert [c['sha256'] for c in fresh['crops']]==[c['sha256'] for c in entry['crops'][offset:offset+len(fresh['crops'])]],key+' unresolved line mapping'
            numeric_partial+=1
        assert m.sha((directory / 'web' / evidence['image']).read_bytes()) == evidence['imageSha256'], key
        if evidence['image'] not in checked_pixels:
            page = docs[name][evidence['page']]
            m.compact.verified_pixels(page,dict(rect=list(page.rect),sha256=evidence['imageSha256']),directory / 'web' / evidence['image'])
            checked_pixels.add(evidence['image'])
        if entry['crops']:
            m.fitz.TOOLS.store_shrink(100)
            pix = docs[name][evidence['page']].get_pixmap(matrix=m.fitz.Matrix(1.5,1.5),clip=m.fitz.Rect(evidence['rect']),alpha=False)
            rasters.append(m.Image.frombytes('RGB',(pix.width,pix.height),pix.samples))
    for crop in entry['crops']:
        raw = (directory / 'web' / crop['src']).read_bytes(); assert m.sha(raw) == crop['sha256'], key
        with m.Image.open(directory / 'web' / crop['src']) as actual:
            assert any(actual.convert('RGB').tobytes() == raster.crop(crop['pixelRect']).tobytes() for raster in rasters), key
        crops += 1
    if index%1000==0:print(f'Checked {index} per-question records',flush=True)
for doc in docs.values(): doc.close()
scratch.cleanup()
print(f'PASS: {native} native image replacements, {crops} exact crops, {numeric_native} re-extracted question/case regions, {numeric_partial} explicit unresolved regions; source/image/text hashes')
(directory/'source-evidence-verification.json').write_text(json.dumps(dict(
    passed=True,nativeImageReplacements=native,exactCrops=crops,numericNativeRegions=numeric_native,partialRegions=numeric_partial,
    imageEvidenceSha256=m.sha((directory/'image-text-evidence.json').read_bytes()),
    numericEvidenceSha256=m.sha((directory/'numeric-text-evidence.json').read_bytes()),fullVisualProofreading=False),indent=2),encoding='utf-8')
