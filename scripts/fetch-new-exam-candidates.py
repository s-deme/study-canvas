"""Archive unresolved practice candidates without running their code."""
import hashlib, json, subprocess, sys
from pathlib import Path
from urllib.parse import quote

DEST = Path(__file__).resolve().parents[1] / 'private-data/github-candidates'
def get(url):
    return subprocess.check_output(['curl.exe', '-fsSL', '--connect-timeout', '20', '--max-time', '90', url])

def main():
    inventory = json.loads((DEST / 'inventory.json').read_bytes())
    acquired = json.loads((DEST / 'acquisition.json').read_bytes())
    candidates = [
        {'repo': 'shinki5301-art/-6', 'commit': '81e9198cfe5c0d097cc6ee633976aa91e58313c7', 'localOnly': True},
        {'repo': 'mitsugeek/shoubo-shiken', 'commit': '642ecb82c3aec477962236b7859514c2b894be5c', 'localOnly': True},
        {'repo': 'hkosu813-ux/shobo-quiz', 'commit': '2a9b0eb699a47990babbda38ef45d3f3ae3fe519', 'localOnly': True},
        {'repo': 'terukatsu58-hash/Shobo-quiz', 'commit': '09a53504eec4b8e379cb8eaa2a7393c94b4a007a', 'localOnly': True},
        {'repo': 'm3tk0616-lab/shobo-tokurui-quiz', 'commit': '04163315e22d508fd35f8f83e05ba9c545baf250', 'localOnly': True},
        {'repo': 'jiagyebo19891011/shoubou-otsu6', 'commit': 'e20c04dd84cea99d386d2978bffa313190b7225c', 'localOnly': True},
        {'repo': 'yousukeee/otsu6-cards', 'commit': '9b4720e6ef3716aa956b48aa1e7d82cecb94207a', 'localOnly': True},
        {'repo': 'tyaamarukusu-svg/study-os-shobo6', 'commit': '1679fb8d1e19b5783cf5080090d9402fd8e3c189', 'localOnly': True},
        {'repo': 'altxxxtla-lab/shoubou-setsubishi-drill', 'commit': 'f046c76a58551c0e4d87523883025bdb43de809c', 'localOnly': True},
        {'repo': 'kosukekkk-ops/fe-master-app', 'commit': '11eb4fe420dd194bb9773450801f5bcd759ec55e', 'localOnly': True},
        {'repo': 'AzFukami/Touhan-Quiz', 'commit': 'ca7ef538185cfeaad349a4fa7ac4979a0285cac2', 'localOnly': True},
        {'repo': 'ot6-shibainu/ot6-shibainu-pwa', 'commit': '350c85e96004e2e5f40d2dfe6a96897b0d44c90c', 'localOnly': True},
        {'repo': 'kids-jobai28/shoubou-quiz', 'commit': 'f777e0032b7ea97ce3c5c738d528535cba4ddbbc', 'localOnly': True},
        {'repo': 'kazuyan1004-a11y/fire-quiz-app', 'commit': 'b00c100a7a0a4da304b8c563e2462c89f4fabdbf', 'localOnly': True},
        {'repo': 'onokumao-png/gokaku-denki-quiz', 'commit': '8434af0dcba1b4a8f8aab13013dcc31ee20e671b', 'localOnly': True},
        {'repo': 'iamirtasam/AWS-AI-Practitioner-Exam-Mock', 'commit': 'ac64b85382987814f4d86c811af10b4c1e94047a'},
        {'repo': 'ikuma-hiroyuki/python_engineer_basic_demo', 'commit': '1dc6079993288065435dbcd714b2f96996836087'},
        {'repo': 'ThREE100/chosashi-app', 'commit': '22fbc96e5cb9886082ffc46e281dfa11c65ca413'},
    ]
    ledger = json.loads((DEST.parents[1] / 'docs/github-sources.json').read_bytes())
    finance = ('boki1-cards', 'bookkeeping-practice', 'boki-quise', 'fp-study-app', 'fp3-quiz-app', 'cpa-tantou-kakomon-drill')
    for source in ledger['sources']:
        if any(source['id'].endswith('/' + name) for name in finance):
            parts = source['resources'][0]['url'].split('/')
            candidates.append({'repo': '/'.join(parts[3:5]), 'commit': parts[5], 'localOnly': True})
    selected = sys.argv[sys.argv.index('--repos') + 1:] if '--repos' in sys.argv else []
    if selected: candidates = [row for row in candidates if row['repo'] in selected]
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
            practice = row.get('localOnly') and (path.endswith(('.json', '.js', '.xlsx')) or path in ('index.html', 'index (2).html', 'checklist.html', 'src/App.vue', '6') or path.startswith('images/'))
            diagram = path.startswith(('public/kijutsu/R07-tatemono/', 'public/kijutsu/R07-tochi/', 'public/kijutsu/R06-tatemono/', 'public/kijutsu/R06-tochi/')) and path.endswith('.png')
            if item['type'] != 'blob' or not (practice or diagram or path.startswith(('data/qb-', 'jsons/', 'src/data/')) or 'license' in path.lower() or path.lower() == 'readme.md'):
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
