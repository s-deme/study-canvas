import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,existsSync} from 'node:fs';
import {resolve,join,relative} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {Miniflare,convertV4MiniflareOptions} from 'miniflare';
import {authFixture} from './cloud-preview.mjs';
import {loadAnswerCorrespondence} from '../scripts/material-answer-correspondence.mjs';
const {directory}=JSON.parse(readFileSync('build/private-cloud/current.json'));
assert.ok(!relative(resolve('build/private-cloud'),directory).startsWith('..'));
const web=join(directory,'web'),manifest=JSON.parse(readFileSync(join(directory,'manifest.json')));
const {emptyState,newSession,questionKey}=await import(pathToFileURL(join(web,'core.mjs')));
const {MATERIAL_INDEX}=await import(pathToFileURL(join(web,'state-catalog.mjs')));
assert.equal(MATERIAL_INDEX.size,manifest.questions);
const original=await import(pathToFileURL(resolve('build/private/web/catalog.mjs')));
const answerCorrespondence=loadAnswerCorrespondence();
const {MATERIAL_MANIFESTS}=await import(pathToFileURL(join(web,'library-catalog.mjs')));
let indexed=0;
for(const entry of MATERIAL_MANIFESTS) {
  const bytes=readFileSync(join(web,entry.url));
  assert.equal(createHash('sha256').update(bytes).digest('hex'),entry.sha256,entry.url);
  const data=JSON.parse(bytes);data.index=data.index.map(q=>({...data.defaults,...q}));assert.equal(data.index.length,entry.count);
  assert.deepEqual(data.packs,manifest.packs.filter(p=>p.examId===entry.examId));
  for(const q of data.index) {assert.equal(q.examId,entry.examId);assert.ok(MATERIAL_INDEX.has(questionKey(q)));}
  indexed+=data.index.length;
}
assert.equal(indexed,manifest.questions);
for(const q of original.MATERIAL_INDEX) {
  const compact=MATERIAL_INDEX.get(questionKey(q));
  const row=answerCorrespondence.get(questionKey(q));const expectedType=row?.sets.length?(row.sets[0].length===1?'single':'multiple'):q.type;
  assert.equal(compact.type,expectedType);assert.equal(compact.previousType,expectedType!==q.type?q.type:undefined);assert.equal(compact.options.length,q.options.length);assert.equal(compact.examId,q.examId);
}
// Retained assets keep aliases; retired assets require verified replacement evidence.
const before=JSON.parse(readFileSync('build/private/manifest.json'));
const retired=new Set(),removedByQuestion=new Map();
let imageText={},numericText={},compactAssets={};
const scopedSolutions=existsSync(join(directory,'scoped-solution-evidence.json'))?JSON.parse(readFileSync(join(directory,'scoped-solution-evidence.json'))):{};
const scopedCases=existsSync(join(directory,'scoped-case-evidence.json'))?JSON.parse(readFileSync(join(directory,'scoped-case-evidence.json'))):{};
const scopedVerification=existsSync(join(directory,'scoped-material-verification.json'))?JSON.parse(readFileSync(join(directory,'scoped-material-verification.json'))):null;
if(scopedVerification) for(const [file,hash] of Object.entries(scopedVerification.evidenceHashes)) assert.equal(createHash('sha256').update(readFileSync(join(directory,file))).digest('hex'),hash,'Changed scoped source verification');
if(manifest.compaction) {
  const compact=JSON.parse(readFileSync(join(directory,'compaction-report.json'))).target;
  assert.ok(!relative(resolve('build/private-compact'),compact).startsWith('..'));
  compactAssets=JSON.parse(readFileSync(join(compact,'asset-evidence.json')));
  for(const [old,asset] of Object.entries(compactAssets)) if(old!==asset.src) {
    assert.equal(manifest.assetAliases[old],asset.src,'Saved question image URL must remain available: '+old);
    assert.equal(manifest.assetHashes[old],asset.sha256,'Saved question image bytes must be preserved: '+old);
  }
  if(manifest.transcription) {
    imageText=JSON.parse(readFileSync(join(directory,'image-text-evidence.json')));
    if(existsSync(join(directory,'numeric-text-evidence.json'))) numericText=JSON.parse(readFileSync(join(directory,'numeric-text-evidence.json')));
  }
  for(const [key,p] of Object.entries(JSON.parse(readFileSync(join(compact,'text-evidence.json'))))) removedByQuestion.set(key,new Set([
    ...(p.textSha256?p.original.images:[]),...(p.question?.removed || []).map(r=>r.image),...(p.solution?.removed || []).map(r=>r.image)
  ].map(i=>i.src)));
  const correctionFile=existsSync(join(directory,'text-corrections.json'))?join(directory,'text-corrections.json'):join(compact,'text-corrections.json');
  for(const correction of existsSync(correctionFile)?JSON.parse(readFileSync(correctionFile)):[]) {
    const removed=removedByQuestion.get(correction.key) || new Set();
    for(const images of Object.values(correction.imageReplacement || {})) if(Array.isArray(images)) for(const image of images) removed.add(image.src);
    removedByQuestion.set(correction.key,removed);
  }
}
for(const pack of before.packs) for(const q of JSON.parse(readFileSync(resolve('build/private/web',pack.url)))) {
  for(const a of [...q.images,...(q.solutionImages || []),...(q.audio || [])]) if(a.src.startsWith('assets/') && !manifest.assetHashes[a.src]) {
    const asset=compactAssets[a.src],entry=imageText[asset?.src],numeric=numericText[questionKey(q)];
    const extracted=entry && (entry.nativeVerified && entry.nativeSafetyVersion===10 || entry.crops?.length);
    const segmented=numeric?.evidence.some(e=>e.image===asset?.src && e.imageSha256===asset?.sha256);
    const scopedSolution=scopedSolutions[questionKey(q)],scopedCase=scopedCases[questionKey(q)];
    const scoped=scopedVerification?.passed && (scopedSolution?.removed.includes(asset?.src) && scopedSolution.evidence.some(e=>e.image===asset?.src && e.imageSha256===asset?.sha256) || scopedCase?.originalImages.some(e=>e.src===asset?.src && e.sha256===asset?.sha256));
    if(extracted) assert.equal(entry.identity.imageSha256,asset.sha256,'Changed image replacement evidence');
    assert.ok(removedByQuestion.get(questionKey(q))?.has(a.src) || extracted || segmented || scoped,'Unverified image/audio removal: '+a.src);retired.add(a.src);
  }
}
const grouped=new Map(),checked=new Set();
for(let i=0;i<64;i++) for(const [path,entry] of Object.entries(JSON.parse(readFileSync(join(web,`bundles/index-${i}.json`))))) {
  assert.ok(!checked.has(path));checked.add(path);
  if(!grouped.has(entry[0])) grouped.set(entry[0],[]);grouped.get(entry[0]).push([path,...entry.slice(1)]);
}
for(const [file,entries] of grouped) {
  const bytes=readFileSync(join(web,file));
  for(const [path,start,length] of entries) assert.equal(createHash('sha256').update(bytes.subarray(start,start+length)).digest('hex'),manifest.assetHashes[path],path);
}
for(const [path,hash] of Object.entries(manifest.assetHashes)) if(!checked.has(path)) {assert.equal(createHash('sha256').update(readFileSync(join(web,path))).digest('hex'),hash);checked.add(path);}
assert.equal(checked.size,manifest.sourceAssets);
if(manifest.deliveryCompression) {
  const compression=spawnSync('python',['checks/delivery-image-check.py',directory],{stdio:'inherit'});
  assert.equal(compression.status,0,'Delivery crops differ from verified source pixels');
}
console.log(`PASS: all ${manifest.questions} index entries and ${checked.size} image/audio hashes preserved`);
const fixture=await authFixture(),{DB,...bindings}=fixture.env;
const assets=async request=>{
  let path=new URL(request.url).pathname;if(path==='/') path='/index.html';
  if(path.includes('..')) return new Response('',{status:404});
  try {
    const bytes=readFileSync(join(web,path.slice(1))),range=/^bytes=(\d+)-(\d+)$/.exec(request.headers.get('Range') || '');
    return range?new Response(bytes.subarray(+range[1],+range[2]+1),{status:206}):new Response(bytes);
  } catch {return new Response('',{status:404});}
};
const runtime=new Miniflare(convertV4MiniflareOptions({modules:true,scriptPath:join(directory,'worker/index.js'),compatibilityDate:'2026-10-03',bindings,d1Databases:['DB'],serviceBindings:{ASSETS:assets},outboundService:request=>{
  if(request.url!==bindings.ACCESS_DOMAIN+'/cdn-cgi/access/certs') throw new Error('Unexpected external request');return fetch(request.url);
}}));
try {
  const database=await runtime.getD1Database('DB');
  for(const sql of readFileSync('schema.sql','utf8').split(';').filter(s=>s.trim())) await database.prepare(sql).run();
  const token=await fixture.token(),call=(path,options={})=>runtime.dispatchFetch('https://study.example'+path,{...options,headers:{'Cf-Access-Jwt-Assertion':token,...options.headers}});
  const image=[...checked].find(p=>/\.(png|webp|jpg)$/.test(p)),audio=[...checked].find(p=>p.endsWith('.mp3'));
  for(const path of ['/','/api/state','/state-catalog.mjs','/bundles/index-0.json','/'+image,'/'+manifest.packs[0].url]) assert.equal((await runtime.dispatchFetch('https://study.example'+path)).status,401,path);
  for(const path of [image,audio].filter(Boolean)) {
    const result=await call('/'+path);assert.equal(result.status,200);assert.equal(result.headers.get('Cache-Control'),'private, no-store');
    assert.equal(createHash('sha256').update(new Uint8Array(await result.arrayBuffer())).digest('hex'),manifest.assetHashes[path]);
    const part=await call('/'+path,{headers:{Range:'bytes=1-3'}});assert.equal(part.status,206);assert.equal((await part.arrayBuffer()).byteLength,3);
  }
  const alias=Object.keys(manifest.assetAliases || {})[0];
  if(alias) {
    const r=await call('/'+alias);assert.equal(r.status,200);assert.equal(r.headers.get('Content-Type'),'image/webp');
    assert.equal(createHash('sha256').update(new Uint8Array(await r.arrayBuffer())).digest('hex'),manifest.assetHashes[manifest.assetAliases[alias]]);
  }
  const cropAlias=manifest.deliveryCompression && Object.keys(JSON.parse(readFileSync(join(directory,'delivery-asset-evidence.json'))).images)[0];
  if(cropAlias) {
    const r=await call('/'+cropAlias);assert.equal(r.status,200);assert.equal(r.headers.get('Content-Type'),'image/webp');
    assert.equal(createHash('sha256').update(new Uint8Array(await r.arrayBuffer())).digest('hex'),manifest.assetHashes[cropAlias]);
  }
  if(retired.size) assert.equal((await call('/'+retired.values().next().value)).status,404);
  const state=emptyState(),seen=new Set();
  for(const q of original.MATERIAL_INDEX) if(!seen.has(q.examId)) {seen.add(q.examId);state.stats[questionKey(q)]={attempts:0,correct:0,bookmark:true};}
  const q=original.MATERIAL_INDEX.find(q=>q.examId==='sg'&&q.type==='single');state.selectedExam='sg';state.session=newSession([q],1,'途中再開');state.session.pending=0;
  const put=(revision,id,next=state)=>call('/api/state',{method:'PUT',headers:{Origin:'https://study.example','Content-Type':'application/json'},body:JSON.stringify({revision,mutationId:id.repeat(32),state:next})});
  const results=await Promise.all([put(0,'a'),put(0,'b')]);assert.deepEqual(results.map(r=>r.status).sort(),[200,409]);
  const saved=await (await call('/api/state')).json();assert.deepEqual(saved.state,state);
  const invalid=structuredClone(state);invalid.stats['sg::missing']={attempts:0,correct:0,bookmark:true};assert.equal((await put(1,'c',invalid)).status,400);
  let compatibilityRevision=1;
  for(const previousType of ['single','multiple']) {
    const old=original.MATERIAL_INDEX.find(q=>MATERIAL_INDEX.get(questionKey(q)).previousType===previousType);assert.ok(old);
    const previous=emptyState();previous.selectedExam=old.examId;previous.session=newSession([old],1,'区分修正前の記録');previous.session.pending=previousType==='multiple'?[0]:0;
    assert.equal((await put(compatibilityRevision,previousType==='single'?'d':'e',previous)).status,200,'Old answer shape rejected by compiled Worker');
    assert.deepEqual((await (await call('/api/state')).json()).state,previous);compatibilityRevision++;
  }
  assert.equal((await call('/api/state',{method:'PUT',headers:{Origin:'https://evil.example','Content-Type':'application/json'},body:'{}'})).status,403);
  assert.equal((await call('/'+image,{headers:{'Cf-Access-Jwt-Assertion':await fixture.token({email:'other@example.com'})}})).status,403);
  writeFileSync(join(directory,'verification.json'),JSON.stringify({passed:true,packagedAt:manifest.packagedAt,at:new Date().toISOString(),questions:manifest.questions,assets:checked.size,retiredAssets:retired.size,exams:seen.size,previousAnswerTypeCompatibility:true},null,2));
  console.log(`PASS: compiled packed Worker, owner-only assets, Range/audio, ${seen.size}-exam sync, resume, conflicts, invalid IDs and CSRF`);
} finally {await runtime.dispose();fixture.restore();DB.sqlite.close();}
