"""Archive pinned public Denken practice data without executing external code."""
import hashlib,importlib.util,json,re,sys
from pathlib import Path
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('fetch',ROOT/'scripts/fetch-github-material.py');fetch=importlib.util.module_from_spec(s);s.loader.exec_module(fetch)
DEST=ROOT/'private-data/github-candidates'
SOURCES={
 '5garashi/denken2':('a980ad6bb134ce68bc674f59d3e27278e26a6c94',['riron.html','denryoku.html','kikai.html','houki.html']),
 'nakasyo3519/denken3all':('bdeb66077002b6635b4a9832c0a5a0ac60b45a06',['denken3_'+s+'_ronsetsu_quiz.html' for s in ['riron','denryoku','kikai','hoki']]),
 'yamkenic/denken1-app':('ed75c7df87a015749e26ed1097027f7c469c199e',['data/extended_questions.js','data/questions_legacy.js','denken1_power.html']),
 'nemi2nd-dot/denken2-app':('319fb379e2c5ebed4d85347188d1d71972ce89bf',['q_theory.js','q_power.js','q_machine.js','q_law.js','index.html']),
 'ayatonikuman/denken3':('5d8b310e5aca86b5b7fc1910fb68fc865b218696',['index.html']),
}
def main():
 inventory=json.loads((DEST/'inventory.json').read_bytes());acquired=json.loads((DEST/'acquisition.json').read_bytes())
 for repo,(commit,paths) in SOURCES.items():
  folder=DEST/repo;folder.mkdir(parents=True,exist_ok=True)
  treefile=folder/'tree.json'
  if not treefile.exists():treefile.write_bytes(fetch.download(f'https://api.github.com/repos/{repo}/git/trees/{commit}?recursive=1','tree.json'))
  tree=json.loads(treefile.read_bytes());assert tree['sha']==commit and not tree.get('truncated')
  if repo=='5garashi/denken2':paths=paths+[t['path'] for t in tree['tree'] if re.match(r'0[1-4]_.*\.md$',t['path'])]
  for path in paths:
   item=next(t for t in tree['tree'] if t['path']==path);target=folder/path;assert target.resolve().is_relative_to(folder.resolve())
   url=f'https://raw.githubusercontent.com/{repo}/{commit}/'+quote(path)
   data=target.read_bytes() if target.exists() else fetch.download(url,path)
   assert hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()==item['sha']
   target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
   acquired=[r for r in acquired if (r['repo'],r['path'])!=(repo,path)]
   acquired.append(dict(repo=repo,path=path,url=url,sha256=fetch.sha(data),bytes=len(data),status='downloaded'))
  inventory=[r for r in inventory if r['repo']!=repo]+[dict(repo=repo,commit=commit,localOnly=True,tree=tree['tree'],status='indexed')]
  print(repo,flush=True)
 for name,data in [('inventory.json',inventory),('acquisition.json',acquired)]:
  (DEST/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
if __name__=='__main__':main()
