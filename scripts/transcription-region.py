"""Extract a source region for review. Neither native extraction nor OCR approves text."""
import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build/python-deps'))
import pymupdf as fitz


def extract(file, page_number, rect, output, dpi=300, rotation=0, ocr=False):
    raw = file.read_bytes()
    with fitz.open(file) as original:
        pdf = raw if original.is_pdf else original.convert_to_pdf()
    with fitz.open(stream=pdf, filetype='pdf') as doc:
        if not 1 <= page_number <= len(doc):
            raise ValueError('Page must be inside the source document')
        if dpi <= 0 or rotation not in (0, 90, 180, 270):
            raise ValueError('Invalid resolution or rotation')
        page = doc[page_number - 1]
        region = fitz.Rect(rect) if rect else page.rect
        if region.is_empty or not page.rect.contains(region):
            raise ValueError('Region must be inside the source page')
        output.parent.mkdir(parents=True, exist_ok=True)
        pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72, dpi / 72).prerotate(rotation), clip=region, alpha=False)
        pix.set_dpi(dpi, dpi)
        pix.save(str(output.with_suffix('.png')))
        result = dict(sourceFile=str(file.relative_to(ROOT)), sourceSha256=hashlib.sha256(raw).hexdigest(),
                      page=page_number, rect=list(region), dpi=dpi, rotation=rotation, status='unreviewed',
                      native=page.get_text('text', clip=region, sort=True),
                      layout=page.get_text('dict', clip=region, flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES))
        if ocr:
            with fitz.open(stream=pix.pdfocr_tobytes(language='jpn+eng', tessdata=str(ROOT / 'build/tessdata')), filetype='pdf') as scanned:
                result['ocr'] = scanned[0].get_text(sort=True)
        output.with_suffix('.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
        return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path)
    parser.add_argument('page', type=int, help='1-based page (use 1 for an image)')
    parser.add_argument('output', type=Path)
    parser.add_argument('--rect', nargs=4, type=float)
    parser.add_argument('--dpi', type=int, default=300)
    parser.add_argument('--rotation', type=int, choices=[0, 90, 180, 270], default=0)
    parser.add_argument('--ocr', action='store_true')
    args = parser.parse_args()
    result = extract(args.file.resolve(), args.page, args.rect, args.output, args.dpi, args.rotation, args.ocr)
    print(json.dumps({k: result[k] for k in ['sourceFile', 'page', 'status']}, ensure_ascii=False))
