"""Archive the three unresolved exam candidates without running their code."""
import hashlib, json, subprocess
from pathlib import Path
from urllib.parse import quote

DEST = Path(__file__).resolve().parents[1] / 'private-data/github-candidates'
def get(url):
    return subprocess.check_output(['curl.exe', '-fsSL', '--connect-timeout', '20', '--max-time', '90', url])

def main():
    inventory = json.loads((DEST / 'inventory.json').read_bytes())
    acquired = json.loads((DEST / 'acquisition.json').read_bytes())
    candidates = [
        {'repo': 'iamirtasam/AWS-AI-Practitioner-Exam-Mock', 'commit': 'ac64b85382987814f4d86c811af10b4c1e94047a'},
        {'repo': 'ikuma-hiroyuki/python_engineer_basic_demo', 'commit': '1dc6079993288065435dbcd714b2f96996836087'},
        {'repo': 'ThREE100/chosashi-app', 'commit': '22fbc96e5cb9886082ffc46e281dfa11c65ca413'},
    ]
    for row in candidates:
        repo, commit = row['repo'], row['commit']
        folder = DEST / repo
        folder.mkdir(parents=True, exist_ok=True)
        tree_file = folder / 'tree.json'
        if not tree_file.exists():
            tree_file.write_bytes(get(f'https://api.github.com/repos/{repo}/git/trees/{commit}?recursive=1'))
        tree = json.loads(tree_file.read_bytes())
        assert tree['sha'] == commit and not tree.get('truncated')
        for item in tree['tree']:
            path = item['path']
            if item['type'] != 'blob' or not (path.startswith(('data/qb-', 'jsons/')) or path == 'src/data/takuitsu.json' or 'license' in path.lower() or path.lower() == 'readme.md'):
                continue
            target = folder / path
            assert target.resolve().is_relative_to(folder.resolve())
            url = f'https://raw.githubusercontent.com/{repo}/{commit}/' + quote(path)
            data = target.read_bytes() if target.exists() else get(url)
            assert hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() == item['sha']
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            acquired = [r for r in acquired if (r['repo'], r['path']) != (repo, path)]
            acquired.append({'repo': repo, 'path': path, 'url': url, 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data), 'status': 'downloaded'})
        inventory = [r for r in inventory if r['repo'] != repo]
        inventory.append({**row, 'tree': tree['tree'], 'status': 'indexed'})
        print(repo, flush=True)
    for name, data in [('inventory.json', inventory), ('acquisition.json', acquired)]:
        (DEST / name).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
