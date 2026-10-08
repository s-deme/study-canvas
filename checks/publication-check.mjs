// Only application files and import-format samples may be published.
import assert from 'node:assert/strict';
import {existsSync,lstatSync,readFileSync,readdirSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {BUILTIN_QUESTIONS,MATERIAL_INDEX,MATERIAL_PACKS,MATERIAL_EXAMS} from '../web/catalog.mjs';
import {previewImport} from '../web/core.mjs';
import {MATERIAL_MANIFESTS,MATERIAL_EXAMS as overviewExams} from '../web/library-catalog.mjs';
assert.deepEqual([MATERIAL_MANIFESTS,overviewExams],[[],[]],'公開版の教材概要は空です');
const root=fileURLToPath(new URL('../',import.meta.url)),web=new URL('../web/',import.meta.url);
const allowed=['_routes.json','app.mjs','core.mjs','catalog.mjs','library-catalog.mjs','exams.mjs','render.mjs','material.mjs','index.html','sample-questions.json','sample-questions-v2.json','sample-questions.csv','styles.css','sync.mjs'];
assert.deepEqual(readdirSync(web).sort(),allowed.sort(),'web/に未承認のファイルがあります');
for(const name of allowed) assert.ok(lstatSync(new URL(name,web)).isFile());
assert.deepEqual(BUILTIN_QUESTIONS,[],'試験問題集は同梱しません');
assert.deepEqual([MATERIAL_INDEX,MATERIAL_PACKS,MATERIAL_EXAMS],[[],[],[]],'個人用教材索引は公開しません');
for(const [name,count] of [['sample-questions.json',1],['sample-questions-v2.json',2],['sample-questions.csv',1]]) {
  const text=readFileSync(new URL(name,web),'utf8'),sample=previewImport(name.endsWith('.csv')?text:JSON.parse(text),[],'sg');
  assert.equal(sample.length,count);
  assert.ok(sample.every(q=>q.source==='形式確認用の自作ダミーデータ'),'サンプル以外の教材は公開しません');
}
const git=spawnSync('git',['ls-files','--cached','--others','--exclude-standard','-z'],{cwd:root,encoding:'utf8'});
if(existsSync(new URL('../.git',import.meta.url))) assert.equal(git.status,0,'Git公開候補を確認できません：'+(git.stderr || git.error?.message || 'Gitの実行に失敗しました'));
const candidates=git.status===0?git.stdout.split('\0').filter(Boolean):allowed.map(name=>'web/'+name);
assert.ok(!candidates.some(path=>/^(?:private-data\/|tmp\/|dist\/|(?:.*\/)?build\/|node_modules\/|\.wrangler\/|\.npm-cache\/|screenshots\/|wrangler\.local\.jsonc$|web\/questions\.json$|web\/assets\/)|(?:^|\/)\.(?:dev\.vars|env)(?!\.example$)[^/]*$|(?:^|\/)(?:ipa-material\.mjs|ipa-manifest\.json|build-ipa-material\.py)$|\.(?:zip|log)$/i.test(path)),'Git公開候補に非公開教材・個人設定・生成物が含まれています');
const privateFiles=['private-data/questions.json','private-data/retired-material/questions-v2.json'];
const texts=candidates.filter(path=>/\.(?:mjs|js|json|jsonc|csv|md|py|ps1|yml|cmd)$/.test(path)).map(path=>({path,text:readFileSync(new URL('../'+path,import.meta.url),'utf8')}));
const worker=new URL('../build/cloud/index.js',import.meta.url);
if(existsSync(worker)) texts.push({path:'build/cloud/index.js',text:readFileSync(worker,'utf8')});
const packList=new URL('../private-data/material/packs.json',import.meta.url);
if(existsSync(packList)) for(const p of JSON.parse(readFileSync(packList,'utf8'))) privateFiles.push('private-data/material/'+p.file);
const additions=new URL('../private-data/additions/',import.meta.url);
if(existsSync(additions)) for(const file of readdirSync(additions).filter(n=>n.endsWith('-manifest.json'))) {
  for(const p of JSON.parse(readFileSync(new URL(file,additions),'utf8')).packs) privateFiles.push('private-data/additions/'+p.file);
}
for(const path of privateFiles) if(existsSync(new URL('../'+path,import.meta.url))) {
  const material=JSON.parse(readFileSync(new URL('../'+path,import.meta.url),'utf8'));
  for(const q of material) for(const value of (path.startsWith('private-data/material/')?[q.passage,q.modelAnswer,q.evaluationGuide]:[q.prompt,q.passage,q.explanation,q.modelAnswer]).filter(v=>typeof v==='string' && v.length>20)) {
    const escaped=JSON.stringify(value).slice(1,-1);
    for(const file of texts) assert.ok(!file.text.includes(value) && !file.text.includes(escaped),`非公開教材の文章が混入しています：${file.path}`);
  }
}
console.log('PASS: empty question catalog, format samples only, no retired/private material in public files, Worker or Git candidates');
