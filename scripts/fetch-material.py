"""Download the selected IPA releases into the private, git-ignored source archive."""
import concurrent.futures, hashlib, json, re, urllib.request
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'private-data' / 'ipa'
EXAMS = {'ap', 'st', 'sa', 'pm', 'nw', 'db', 'es', 'sm', 'au', 'sc', 'koudo'}

def fetch(url, path):
    if not path.exists():
        with urllib.request.urlopen(url, timeout=90) as response:
            data = response.read()
        if path.suffix == '.pdf' and not data.startswith(b'%PDF-'):
            raise ValueError(f'Not a PDF: {url}')
        path.write_bytes(data)
    return path.read_bytes()

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    sources = {}
    for year in (2023, 2024, 2025):
        url = f'https://www.ipa.go.jp/shiken/mondai-kaiotu/{year}r{year-2018:02}.html'
        html = fetch(url, DEST / f'{year}.html').decode('utf-8')
        for href in re.findall(r'href="([^"]+\.pdf)"', html):
            full = urljoin(url, href)
            name = Path(urlparse(full).path).name
            match = re.fullmatch(r'(20\d{2})r\d{2}([ha])_([a-z0-9]+)_(am[12]?|pm[12]?)_(qs|ans|cmnt)\.pdf', name)
            if match and match[3] in EXAMS:
                sources[name] = dict(file=name, url=full, year=int(match[1]), term='春期' if match[2]=='h' else '秋期', examId=match[3], subject=match[4], kind=match[5])
    def download(row):
        data = fetch(row['url'], DEST / row['file'])
        return {**row, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes':len(data)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        rows = list(executor.map(download, sources.values()))
    (DEST / 'sources.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Downloaded and hashed {len(rows)} official PDFs', flush=True)

if __name__ == '__main__':
    main()
