"""Archive GitHub discovery data and the referenced official exam sources locally."""
import concurrent.futures, hashlib, json, re, subprocess, sys, threading
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'private-data/github-material'
REGISTRY = ROOT / 'docs/github-sources.json'
GITHUB_LOCK = threading.Lock()
sha = lambda data: hashlib.sha256(data).hexdigest()
sys.stdout.reconfigure(encoding='utf-8')

def download(url, name):
    result = subprocess.run(['curl.exe', '--fail', '--silent', '--show-error', '--location',
                                 '--retry', '2', '--connect-timeout', '20', '--max-time', '90', url],
                                capture_output=True, check=True)
    if name.endswith('.pdf'):
        assert result.stdout.startswith(b'%PDF-'), url
    return result.stdout

def github_source(url):
    parsed = urlparse(url)
    if parsed.hostname not in ('raw.githubusercontent.com', 'gist.githubusercontent.com'):
        return None
    parts = parsed.path.strip('/').split('/')
    assert parsed.scheme == 'https' and len(parts) >= 4 and all(parts), url
    owner, repo = parts[0].lower(), parts[1].lower()
    gist = parsed.hostname == 'gist.githubusercontent.com'
    return {'id': ('gist:' if gist else 'repo:') + owner + '/' + repo,
            'url': f'https://{"gist.github.com" if gist else "github.com"}/{owner}/{repo}',
            'resource': f'https://{parsed.hostname}/{owner}/{repo}/' + '/'.join(parts[2:])}

def fetch_github(url, name, adopt=False):
    source = github_source(url)
    path = DEST / name
    assert path.resolve().is_relative_to(DEST.resolve()), name
    # ponytail: one acquisition process at a time; use an interprocess lock if parallel CLI runs are needed.
    with GITHUB_LOCK:
        registry = json.loads(REGISTRY.read_text(encoding='utf-8')) if REGISTRY.exists() else {'version': 1, 'sources': []}
        assert registry['version'] == 1, 'Unsupported source registry'
        entry = next((s for s in registry['sources'] if s['id'] == source['id']), None)
        resource = next((r for r in entry['resources'] if r['url'] == source['resource']), None) if entry else None
        for saved in registry['sources']:
            for row in saved['resources']:
                if name in row['files'] and row is not resource:
                    raise ValueError(f'Archive filename already belongs to {row["url"]}: {name}')
        cached = next((DEST / f for f in resource['files'] if (DEST / f).exists()), None) if resource else None
        if cached:
            data = cached.read_bytes()
        elif path.exists():
            if not resource and not adopt:
                raise ValueError(f'Unregistered existing archive: {name}; register its discovery report first')
            data = path.read_bytes()
        else:
            if adopt:
                raise FileNotFoundError(path)
            data = download(url, name)
        if resource and (sha(data) != resource['sha256'] or len(data) != resource['bytes']):
            raise ValueError(f'Archived source changed: {url}; use a new commit URL for an update')
        if path.exists() and path.read_bytes() != data:
            raise ValueError(f'Archive destination has different contents: {name}')
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        if entry is None:
            entry = {'id': source['id'], 'url': source['url'], 'resources': []}
            registry['sources'].append(entry)
        if resource is None:
            resource = {'url': source['resource'], 'files': [], 'sha256': sha(data), 'bytes': len(data)}
            entry['resources'].append(resource)
        if name not in resource['files']:
            resource['files'].append(name)
            registry['sources'].sort(key=lambda s: s['id'])
            for saved in registry['sources']:
                saved['resources'].sort(key=lambda r: r['url'])
            REGISTRY.parent.mkdir(parents=True, exist_ok=True)
            temporary = REGISTRY.with_suffix('.json.tmp')
            temporary.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
            temporary.replace(REGISTRY)
        return {'file': name, 'url': url, 'sha256': sha(data), 'bytes': len(data)}

def register_existing():
    rows = [row for report in ('discovery.json', 'nonit-discovery.json', 'expansion-discovery.json')
            if (DEST / report).exists()
            for row in json.loads((DEST / report).read_text(encoding='utf-8'))['discovery']]
    for row in rows:
        data = (DEST / row['file']).read_bytes()
        assert sha(data) == row['sha256'] and len(data) == row['bytes'], row['file']
    for row in rows:
        fetch_github(row['url'], row['file'], adopt=True)
    print('Registered existing GitHub resources:', len(rows))

def fetch(url, name):
    if github_source(url):
        return fetch_github(url, name)
    path = DEST / name
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(download(url, name))
    data = path.read_bytes()
    return {'file': name, 'url': url, 'sha256': sha(data), 'bytes': len(data)}

def links(row):
    text = (DEST / row['file']).read_text(encoding='utf-8')
    return [urljoin(row['url'], href.replace('&amp;', '&')) for href in re.findall(r'href=["\']([^"\']+)["\']', text)]

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    discovery = [
        fetch('https://gist.githubusercontent.com/amapyon/477930159cb5b0c47f401b0d4a09b1aa/raw/de2f3767abeaca03a2b3cc1b11cdb2212b4b6468/gistfile1.txt', 'ipa-github-links.txt'),
        fetch('https://raw.githubusercontent.com/inamuu/ITPassportExams/main/site/data/questions.json', 'ip-github.json'),
        fetch('https://raw.githubusercontent.com/onochin/assistant-surveyor-pwa/main/data/2025_R07/exam.json', 'surveyor-github-2025.json'),
        fetch('https://raw.githubusercontent.com/kosukekkk-ops/fe-master-app/master/docs/qualifications/fe/questions_official.json', 'fe-github-official.json'),
        fetch('https://raw.githubusercontent.com/kosukekkk-ops/fe-master-app/master/docs/qualifications/fe/questions_b.json', 'fe-github-b.json'),
    ]
    fetch('https://www.gsi.go.jp/LAW/SHIKEN/past.html','gsi-past.html')
    fetch('https://www.ipa.go.jp/shiken/faq.html','ipa-terms.html')
    fetch('https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html','gsi-terms.html')
    index = fetch('https://www.ipa.go.jp/shiken/mondai-kaiotu/index.html', 'ipa-index.html')
    current = fetch('https://www.ipa.go.jp/shiken/mondai-kaiotu/sg_fe/koukai/index.html', 'ipa-sg-fe.html')
    ip = fetch('https://www3.jitec.ipa.go.jp/JitesCbt/html/openinfo/questions.html', 'ipa-ip.html')
    pages = [index, current, ip]
    archives = sorted(set(url for page in (index, current) for url in links(page) if re.search(r'/20\d{2}[^/]*\.html$', url)))
    def archive(url):
        return fetch(url, ('sg-fe-' if '/sg_fe/' in url else '') + Path(urlparse(url).path).name)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        pages.extend(pool.map(archive, archives))
    sources = {Path(urlparse(url).path).name: url for page in pages for url in links(page) if urlparse(url).path.endswith('.pdf')}
    pairs = []
    for name, url in sorted(sources.items()):
        match = re.fullmatch(r'(20\d{2})(?:[hr]\d{2})([hao]?)_(ip|sg|fe|ap|st|sa|pm|nw|db|es|sm|au|sc)(?:_(am[12]?|kamoku_[ab]))?_qs\.pdf', name)
        if not match:
            continue
        answer = name.replace('_qs.pdf', '_ans.pdf')
        if answer not in sources:
            continue
        pairs.append({'file': name, 'url': url, 'answerFile': answer, 'answerUrl': sources[answer],
                      'year': match[1], 'term': {'h':'春期','a':'秋期','o':'公開問題','':'公開問題'}[match[2]],
                      'examId': match[3], 'subject': {'am':'午前','am1':'午前Ⅰ','am2':'午前Ⅱ','kamoku_a':'科目A','kamoku_b':'科目B',None:'公開問題'}[match[4]]})
    report = {'discovery': discovery, 'pages': pages, 'officialPdfLinks': sources, 'pairs': pairs}
    (DEST / 'discovery.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Archived GitHub sources:', len(discovery), 'official index pages:', len(pages), 'PDF links:', len(sources), flush=True)
    def download(pair):
        try:
            q = fetch(pair['url'], pair['file']); a = fetch(pair['answerUrl'], pair['answerFile'])
            return {**pair, 'question': q, 'answer': a, 'status': 'downloaded'}
        except Exception as error:
            return {**pair, 'status': 'failed', 'reason': str(error)}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        acquired = []
        for result in pool.map(download, pairs):
            acquired.append(result)
            if len(acquired) % 25 == 0:
                print('Downloaded pairs', len(acquired), '/', len(pairs), flush=True)
    report['pairs'] = acquired
    (DEST / 'discovery.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Completed pairs', sum(p['status']=='downloaded' for p in acquired), '/', len(pairs), flush=True)

if __name__ == '__main__':
    if sys.argv[1:] == ['--register-existing']:
        register_existing()
    elif sys.argv[1:]:
        raise SystemExit('Usage: fetch-github-material.py [--register-existing]')
    else:
        main()
