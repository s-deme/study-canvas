"""Cache currently linked FP academic papers; never guess unpublished PDF URLs."""
import hashlib
import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'private-data' / 'fp'
INDEX = 'https://www.jafp.or.jp/exam/mohan/'
TERMS = urljoin(INDEX, 'files/exam_riyou.pdf')


def fetch(url, path):
    if not path.exists():
        with urllib.request.urlopen(url, timeout=60) as response:
            data = response.read()
        if path.suffix == '.pdf' and not data.startswith(b'%PDF-'):
            raise ValueError(f'Not a PDF: {url}')
        path.write_bytes(data)
    data = path.read_bytes()
    return dict(file=path.name, url=url, sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    # Terms reviewed before downloads: source attribution and identification of modifications.
    terms = fetch(TERMS, DEST / 'exam_riyou.pdf')
    with urllib.request.urlopen(INDEX, timeout=60) as response:
        html = response.read().decode('utf-8')
    (DEST / 'index.html').write_text(html, encoding='utf-8')
    rows = []
    for href in sorted(set(re.findall(r'href=["\']([^"\']+\.pdf)', html))):
        match = re.fullmatch(r'files/(g([23])_(20\d{2})(\d{2})_(q|a|qa)\.pdf)', href)
        if not match or not 2017 <= int(match[3]) <= 2026:
            continue
        row = fetch(urljoin(INDEX, href), DEST / match[1])
        row.update(examId='fp'+match[2], year=match[3], month=match[4], kind=match[5])
        rows.append(row)
        print(row['file'], flush=True)
    (DEST / 'sources.json').write_text(json.dumps(dict(terms=terms, sources=rows), ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
