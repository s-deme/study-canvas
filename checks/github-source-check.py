"""Offline checks for acquired repository registration and download reuse."""
import importlib.util, json, subprocess, tempfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('archive_fetch', ROOT / 'scripts/fetch-github-material.py')
fetcher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fetcher)

def rejected(action, error=ValueError):
    try:
        action()
    except error:
        return
    raise AssertionError('Expected rejection')

with tempfile.TemporaryDirectory(prefix='study-github-sources-') as temporary:
    fetcher.DEST = Path(temporary) / 'private'
    fetcher.REGISTRY = Path(temporary) / 'docs/sources.json'
    url = 'https://raw.githubusercontent.com/Owner/Exam/main/2025.json'
    next_url = url.replace('2025', '2026')
    with patch.object(fetcher.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, b'old-year')) as network:
        original = fetcher.fetch(url, 'old.json')
        network.assert_called_once()
    with patch.object(fetcher.subprocess, 'run', side_effect=AssertionError('Unexpected download')):
        fetcher.fetch(url.replace('Owner/Exam', 'owner/exam'), 'alias.json')
        fetcher.fetch(url, 'old.json')
        registry = json.loads(fetcher.REGISTRY.read_text(encoding='utf-8'))
        assert len(registry['sources']) == 1
        assert registry['sources'][0]['id'] == 'repo:owner/exam'
        assert registry['sources'][0]['resources'][0]['files'] == ['old.json', 'alias.json']
        rejected(lambda: fetcher.fetch(next_url, 'old.json'))
        rejected(lambda: fetcher.fetch(url, '../escape.json'), AssertionError)
        (fetcher.DEST / 'old.json').write_bytes(b'tampered')
        rejected(lambda: fetcher.fetch(url, 'old.json'))
        (fetcher.DEST / 'old.json').write_bytes(b'old-year')
        (fetcher.DEST / 'old.json').unlink()
        fetcher.fetch(url, 'old.json')  # Restore from the other recorded filename, without network.
        (fetcher.DEST / 'discovery.json').write_text(json.dumps({'discovery': [original]}), encoding='utf-8')
        before = fetcher.REGISTRY.read_bytes()
        fetcher.register_existing()
        fetcher.register_existing()
        assert fetcher.REGISTRY.read_bytes() == before
        (fetcher.DEST / 'unregistered.json').write_bytes(b'unknown')
        rejected(lambda: fetcher.fetch(next_url, 'unregistered.json'))
    with patch.object(fetcher.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, b'new-year')) as network:
        fetcher.fetch(next_url, 'new.json')
        network.assert_called_once()
        assert len(json.loads(fetcher.REGISTRY.read_text())['sources'][0]['resources']) == 2
    before = fetcher.REGISTRY.read_bytes()
    with patch.object(fetcher.subprocess, 'run', side_effect=subprocess.CalledProcessError(22, 'curl')):
        rejected(lambda: fetcher.fetch(next_url.replace('2026', '2027'), 'failed.json'), subprocess.CalledProcessError)
        assert fetcher.REGISTRY.read_bytes() == before
    (fetcher.DEST / 'new.json').unlink()
    with patch.object(fetcher.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, b'changed-source')):
        rejected(lambda: fetcher.fetch(next_url, 'new.json'))
        assert not (fetcher.DEST / 'new.json').exists()
    with patch.object(fetcher.subprocess, 'run', return_value=subprocess.CompletedProcess([], 0, b'new-year')):
        fetcher.fetch(next_url, 'new.json')  # Missing archives may be repaired if the hash still matches.
    gist = fetcher.github_source('https://gist.githubusercontent.com/Owner/ABC/raw/commit/links.txt')
    assert gist['id'] == 'gist:owner/abc'
    assert fetcher.github_source('https://www.shiken.or.jp/exam.pdf') is None

registry = json.loads((ROOT / 'docs/github-sources.json').read_text(encoding='utf-8'))
assert len({s['id'] for s in registry['sources']}) == len(registry['sources'])
resources = [r for s in registry['sources'] for r in s['resources']]
assert len({r['url'] for r in resources}) == len(resources)
for report in ('discovery.json', 'nonit-discovery.json', 'expansion-discovery.json'):
    path = ROOT / 'private-data/github-material' / report
    if not path.exists():
        continue
    for row in json.loads(path.read_text(encoding='utf-8'))['discovery']:
        source = fetcher.github_source(row['url'])
        entry = next(s for s in registry['sources'] if s['id'] == source['id'])
        resource = next(r for r in entry['resources'] if r['url'] == source['resource'])
        assert row['file'] in resource['files']
        data = (path.parent / row['file']).read_bytes()
        assert fetcher.sha(data) == resource['sha256'] == row['sha256']
        assert len(data) == resource['bytes'] == row['bytes']
print('PASS: GitHub registry, reuse, new years, collisions, tampering, repair, failed downloads and existing sources')
