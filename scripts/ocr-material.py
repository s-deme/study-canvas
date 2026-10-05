"""Cache OCR layout for image-only source pages; original page images remain authoritative."""
import concurrent.futures, json, os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'build/python-deps'))
import pymupdf as fitz

def run(task):
    name,pn=task; out=ROOT/'private-data/ipa/ocr'/f'{name}-{pn}.json'
    doc=fitz.open(ROOT/'private-data/ipa'/name);page=doc[pn]
    if out.exists() and (not page.rotation or json.loads(out.read_text(encoding='utf-8')).get('rasterized')): return 0
    rotated=bool(page.rotation)
    if rotated:
        raster=page.get_pixmap(dpi=150,alpha=False)
        ocrdoc=fitz.open(stream=raster.pdfocr_tobytes(language='jpn+eng',tessdata=str(ROOT/'build/tessdata')),filetype='pdf')
        page=ocrdoc[0]
    tp=page.get_textpage() if page.get_text().strip() else page.get_textpage_ocr(language='jpn+eng',dpi=150,full=True,tessdata=str(ROOT/'build/tessdata'))
    data=page.get_text('dict',textpage=tp)
    data['rasterized']=rotated
    data['blocks']=[b for b in data['blocks'] if b.get('type')==0]
    out.write_text(json.dumps(data,ensure_ascii=False),encoding='utf-8')
    return 1

if __name__=='__main__':
    os.environ['OMP_THREAD_LIMIT']='1'
    (ROOT/'private-data/ipa/ocr').mkdir(exist_ok=True)
    sources=json.loads((ROOT/'private-data/ipa/sources.json').read_text(encoding='utf-8'))
    tasks=[]
    for s in sources:
        doc=fitz.open(ROOT/'private-data/ipa'/s['file'])
        tasks.extend((s['file'],i) for i in range(len(doc)))
    print('Pages',len(tasks),flush=True)
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as ex:
        for i,_ in enumerate(ex.map(run,tasks,chunksize=1)):
            if i%100==0: print('Processed',i,flush=True)
    print('OCR complete',flush=True)
