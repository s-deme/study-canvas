"""Acquire the pinned candidate files without executing repository code."""
import concurrent.futures, hashlib, importlib.util, json, re, sys
from collections import Counter
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'private-data/github-candidates'
spec = importlib.util.spec_from_file_location('fetch', ROOT / 'scripts/fetch-github-material.py')
fetch = importlib.util.module_from_spec(spec); spec.loader.exec_module(fetch)
sys.stdout.reconfigure(encoding='utf-8')

def candidates():
    text = (ROOT / 'docs/github-candidates.md').read_text(encoding='utf-8').split('## 既存の取得元')[0]
    rows = {}
    for repo, commit in re.findall(r'https://github.com/([^/]+/[^/]+)/(?:(?:blob|tree)/)([0-9a-f]{40})', text):
        rows.setdefault(repo, {'repo': repo, 'commit': commit})
    return list(rows.values())

def acquire(row):
    folder = DEST / row['repo']; folder.mkdir(parents=True, exist_ok=True)
    tree_file = folder / 'tree.json'
    try:
        if not tree_file.exists():
            tree_file.write_bytes(fetch.download(f"https://api.github.com/repos/{row['repo']}/git/trees/{row['commit']}?recursive=1", 'tree.json'))
        tree = json.loads(tree_file.read_bytes())
        assert tree['sha'] == row['commit'], 'Cached tree belongs to a different commit'
        assert not tree.get('truncated'), 'Incomplete GitHub file tree'
        return {**row, 'tree': tree['tree'], 'status': 'indexed'}
    except Exception as error:
        return {**row, 'status': 'failed', 'reason': str(error)}

def main():
    DEST.mkdir(parents=True, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        rows = []
        for row in pool.map(acquire, candidates()):
            rows.append(row); print(row['repo'], row['status'], len(row.get('tree', [])), flush=True)
    (DEST / 'inventory.json').write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding='utf-8')
    if '--download' in sys.argv:
        tasks = []
        for row in rows:
            paths = [x['path'] for x in row.get('tree', []) if x['type'] == 'blob']
            collisions = {path for path, count in Counter(p.casefold() for p in paths).items() if count > 1}
            for item in row.get('tree', []):
                path = item['path']; lower = path.lower()
                if item['type'] != 'blob' or item.get('size', 0) > 25 * 1024 * 1024: continue
                if row['repo'].lower() == 'renatusauctor/cpa-tantou-kakomon-drill' and path not in ('index.html', 'checklist.html'): continue
                if any(s in lower for s in ('node_modules/', 'vendor/', 'package-lock', 'yarn.lock', '.claude/', 'bootstrap', 'jquery', '__pycache__')): continue
                if row['repo'] == 'oga3999/kokushi' and not (lower.endswith(('.sql', '.csv', '.json', '.db')) or lower == 'index.html'): continue
                if row['repo'] == 'kyuuki/kanken-rails' and not (lower.startswith('db/') or lower == 'readme.md'): continue
                if lower.endswith(('.json', '.jsonl', '.csv', '.xlsx', '.db', '.sqlite', '.html', '.js', '.mjs', '.ts', '.tsx', '.py', '.txt', '.sql', '.pdf', '.png', '.jpg', '.jpeg', '.webp', '.svg', '.swift')) or 'license' in lower or lower.endswith('readme.md'):
                    local_path = 'case-distinct/' + item['sha'] + '/' + path if path.casefold() in collisions else path
                    tasks.append((row, path, item['sha'], local_path))
        def save(task):
            row, path, blob_sha, local_path = task; target = DEST / row['repo'] / local_path
            url = f"https://raw.githubusercontent.com/{row['repo']}/{row['commit']}/" + quote(path)
            try:
                assert target.resolve().is_relative_to(DEST.resolve()), 'Unsafe archive path: ' + path
                if not target.exists():
                    data = fetch.download(url, path); target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
                data = target.read_bytes()
                assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == blob_sha, 'File does not match the pinned Git blob: ' + path
                return {'repo': row['repo'], 'path': path, 'localPath': local_path, 'url': url, 'sha256': fetch.sha(data), 'bytes': len(data), 'status': 'downloaded'}
            except Exception as error:
                return {'repo': row['repo'], 'path': path, 'url': url, 'status': 'failed', 'reason': str(error)}
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            files = []
            for file in pool.map(save, tasks):
                files.append(file)
                if len(files) % 50 == 0: print('Downloaded', len(files), '/', len(tasks), flush=True)
        (DEST / 'acquisition.json').write_text(json.dumps(files, ensure_ascii=False, indent=2), encoding='utf-8')
        print('Acquired', len(files), 'files; failed', sum(f['status'] != 'downloaded' for f in files))

if __name__ == '__main__':
    main()
