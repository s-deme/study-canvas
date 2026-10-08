import assert from 'node:assert/strict';
import {existsSync,mkdtempSync,mkdirSync,readFileSync,rmSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve,sep} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {loadLocalPractice} from '../scripts/local-practice.mjs';
import {MaterialLibrary} from '../web/material.mjs';
import {questionKey} from '../web/core.mjs';
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const root=fileURLToPath(new URL('../',import.meta.url)),temporary=mkdtempSync(join(tmpdir(),'study-practice-check-'));
try {
  assert.deepEqual(loadLocalPractice(temporary,[]),{exams:[],packs:[],duplicates:[]});
  const dir=join(temporary,'private-data/local-practice');mkdirSync(dir,{recursive:true});
  const q={id:'practice-fixture',examId:'python-practical',type:'written',prompt:'形式検査専用のダミー入力',modelAnswer:'sample',
    explanation:'形式検査専用のダミー説明',source:'自作 AI生成（テスト専用）',explanationSource:'独自テスト'};
  const raw=JSON.stringify([q]),evidence=JSON.stringify({checks:[{id:q.id,examId:q.examId,answer:'sample',code:'fixture only',method:'python-execution'}]});
  writeFileSync(join(dir,'author.py'),'# fixture only');writeFileSync(join(dir,'evidence.json'),evidence);
  writeFileSync(join(dir,'practice-fixture.json'),raw);
  const pack={id:'practice-fixture',file:'practice-fixture.json',examId:q.examId,count:1,sha256:hash(raw)};
  const manifest={version:1,verification:'実行照合（テスト専用）',authorSha256:hash('# fixture only'),evidenceSha256:hash(evidence),packs:[pack]};
  const save=value=>writeFileSync(join(dir,'manifest.json'),JSON.stringify(value));save(manifest);
  const loaded=loadLocalPractice(temporary,[]);assert.equal(loaded.packs[0].rows[0].modelAnswer,'sample');assert.equal(loaded.exams[0].id,q.examId);
  const duplicate=loadLocalPractice(temporary,[{...q,id:'existing'}]);assert.equal(duplicate.packs.length,0);assert.equal(duplicate.duplicates.length,1);
  assert.throws(()=>loadLocalPractice(temporary,[q]),/Duplicate practice ID/);
  save({...manifest,packs:[{...pack,file:'../escape.json'}]});assert.throws(()=>loadLocalPractice(temporary,[]));save(manifest);
  writeFileSync(join(dir,'practice-fixture.json'),raw+' ');assert.throws(()=>loadLocalPractice(temporary,[]),/pack changed/);
  const changed=JSON.stringify([{...q,modelAnswer:'wrong'}]);writeFileSync(join(dir,'practice-fixture.json'),changed);
  save({...manifest,packs:[{...pack,sha256:hash(changed)}]});assert.throws(()=>loadLocalPractice(temporary,[]),/answer differs/);
  writeFileSync(join(dir,'practice-fixture.json'),raw);save({...manifest,packs:[{...pack,examId:'unknown-exam'}]});assert.throws(()=>loadLocalPractice(temporary,[]),/Unknown practice exam/);
  console.log('PASS: registration, deduplication, unknown exam, path traversal, tamper and answer-evidence rejection');
} finally {
  assert.ok(resolve(temporary).startsWith(resolve(tmpdir())+sep));
  assert.ok(temporary.split(/[\\/]/).at(-1).startsWith('study-practice-check-'));
  rmSync(temporary,{recursive:true,force:true});
}

if(existsSync(join(root,'private-data/local-practice/manifest.json'))) {
  const {MATERIAL_INDEX,MATERIAL_PACKS}=await import('../build/private/web/catalog.mjs');
  const all=MATERIAL_PACKS.flatMap(p=>JSON.parse(readFileSync(join(root,'build/private/web',p.url))));
  const old=all.filter(q=>!q.id.startsWith('practice-'));
  const practice=loadLocalPractice(root,old),built=all.filter(q=>q.id.startsWith('practice-'));
  assert.deepEqual(new Map(built.map(q=>[questionKey(q),q])),new Map(practice.packs.flatMap(p=>p.rows).map(q=>[questionKey(q),q])));
  const baseline=JSON.parse(readFileSync(join(root,'private-data/local-practice/baseline.json')));
  const oldKeys=new Set(old.map(q=>`${q.examId}::${q.id}`));
  assert.ok(Object.keys(baseline).every(key=>oldKeys.has(key)),'Previous material missing');
  const library=new MaterialLibrary(MATERIAL_INDEX,MATERIAL_PACKS,async path=>new Response(readFileSync(join(root,'build/private/web',path))));
  for(const id of new Set(practice.packs.map(p=>p.examId))) {
    await library.load(id);
    const rows=library.base.filter(q=>q.examId===id && q.id.startsWith('practice-'));
    assert.ok(rows.length && rows.every(q=>!q.catalogOnly && q.modelAnswer && q.explanation));
  }
  assert.equal(new Set(built.map(questionKey)).size,built.length);
  console.log(`PASS: ${built.length} new exercises loaded through MaterialLibrary across ${practice.packs.length} exams; ${old.length} previous questions retained`);
}
