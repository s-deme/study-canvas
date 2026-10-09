// Keep the last successful imports and originals; publish only verified compact derivatives.
import assert from 'node:assert/strict';
import {cpSync,mkdirSync,readFileSync,readdirSync,writeFileSync,statSync,openSync,closeSync,unlinkSync,existsSync} from 'node:fs';
import {resolve,join,extname} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {validateQuestions,questionKey} from '../web/core.mjs';
import {writeLibraryCatalog,compactQuestionPack} from './library-catalog.mjs';

const root=resolve('.'),source=join(root,'build/private'),cache=join(root,'build/material-compact-cache');
const lock=join(root,'build/private-build.lock'),fd=openSync(lock,'wx');
process.on('exit',()=>{closeSync(fd);unlinkSync(lock);});
for(const signal of ['SIGINT','SIGTERM']) process.on(signal,()=>process.exit(1));
const run=spawnSync('python',[join(root,'scripts/compact-material.py'),source,cache],{stdio:'inherit'});
assert.equal(run.status,0,'Native extraction or lossless compression failed; original build retained');
const read=file=>JSON.parse(readFileSync(file));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const baseline=read(join(source,'manifest.json')),patches=read(join(cache,'text.json')),assets=read(join(cache,'assets.json'));
const {MATERIAL_INDEX,MATERIAL_EXAMS,MATERIAL_PACKS}=await import(pathToFileURL(join(source,'web/catalog.mjs')));
assert.deepEqual(MATERIAL_PACKS,baseline.packs);assert.equal(MATERIAL_INDEX.length,baseline.questions);
const out=join(root,'build/private-compact'),target=join(out,Date.now().toString());
mkdirSync(join(target,'web/material'),{recursive:true});
cpSync(join(root,'web'),join(target,'web'),{recursive:true});
cpSync(join(root,'functions'),join(target,'functions'),{recursive:true});
cpSync(join(root,'schema.sql'),join(target,'schema.sql'));
const packs=[],keys=new Set(),copied=new Set();let converted=0,referencedBytesBefore=0;
function copyAsset(src) {
  const entry=assets[src];assert.ok(entry,src);
  if(!copied.has(src)) {
    const originalBytes=readFileSync(join(source,'web',src));
    assert.equal(hash(originalBytes),entry.sourceSha256,src);referencedBytesBefore+=originalBytes.length;
    const bytes=entry.file?readFileSync(join(cache,entry.file)):originalBytes;
    assert.equal(hash(bytes),entry.sha256,src);
    const file=join(target,'web',entry.src);mkdirSync(resolve(file,'..'),{recursive:true});writeFileSync(file,bytes);
    copied.add(src);
  }
  return entry.src;
}
for(const pack of baseline.packs) {
  const raw=readFileSync(join(source,'web',pack.url));assert.equal(hash(raw),pack.sha256,pack.id);
  const original=validateQuestions(JSON.parse(raw)),rows=[];assert.equal(original.length,pack.count);
  for(const q of original) {
    const key=questionKey(q);assert.ok(!keys.has(key),key);keys.add(key);
    const patch=patches[`${q.examId}::${q.id}`],next=structuredClone(q);
    if(patch) {
      assert.deepEqual(q,validateQuestions([patch.original])[0],'Extraction evidence differs: '+key);
      next.prompt=patch.mode==='passage'?patch.prompt:q.topic+'\n'+patch.prompt;next.options=patch.options;next.passage=patch.passage || '';next.images=[];converted++;
    }
    for(const field of ['images','solutionImages','audio']) for(const a of next[field] || []) {
      if(!a.src.startsWith('assets/')) continue;
      a.src=copyAsset(a.src);
    }
    assert.equal(next.id,q.id);assert.equal(next.examId,q.examId);assert.equal(next.type,q.type);
    assert.deepEqual(next.answer,q.answer);assert.equal(next.options.length,q.options.length);
    for(const field of ['source','sourceUrl','year','term','subject','explanation','modelAnswer','evaluationGuide']) assert.deepEqual(next[field],q[field]);
    rows.push(next);
  }
  validateQuestions(rows);
  const compact=compactQuestionPack(rows);assert.deepEqual(validateQuestions(compact),rows,pack.id);
  const text=JSON.stringify(compact);writeFileSync(join(target,'web',pack.url),text);
  packs.push({...pack,sha256:hash(text)});
}
assert.equal(keys.size,baseline.questions);assert.ok(MATERIAL_INDEX.every(q=>keys.has(questionKey(q))));
assert.equal(converted,Object.keys(patches).length);
for(const patch of Object.values(patches)) for(const image of patch.original.images) copyAsset(image.src);
writeFileSync(join(target,'web/catalog.mjs'),`export const BUILTIN_QUESTIONS=[];\nexport const MATERIAL_INDEX=${JSON.stringify(MATERIAL_INDEX)};\nexport const MATERIAL_PACKS=${JSON.stringify(packs)};\nexport const MATERIAL_EXAMS=${JSON.stringify(MATERIAL_EXAMS)};\n`);
writeLibraryCatalog(join(target,'web'),MATERIAL_INDEX,packs,MATERIAL_EXAMS);
function inventory(dir) {
  const result={bytes:0,files:0,extensions:{},directories:{}};
  function walk(folder,group='.') {for(const f of readdirSync(folder,{withFileTypes:true})) {
    const p=join(folder,f.name);if(f.isDirectory()) walk(p,group==='.'?f.name:group);
    else {const n=statSync(p).size;result.bytes+=n;result.files++;const e=extname(p)||'(none)';result.extensions[e]=(result.extensions[e]||0)+n;result.directories[group]=(result.directories[group]||0)+n;}
  }}
  walk(dir);return result;
}
const before=inventory(join(source,'web')),after=inventory(join(target,'web'));
const report={at:new Date().toISOString(),source,target,sourceManifestSha256:hash(readFileSync(join(source,'manifest.json'))),questions:keys.size,packs:packs.length,converted,
  retainedForReview:read(join(cache,'review.json')).length,before,after,reduction:1-after.bytes/before.bytes,
  originalAssets:copied.size,distinctOutputAssets:new Set(Object.values(assets).map(a=>a.src)).size,
  exactDuplicateSourceFiles:copied.size-new Set(Object.values(assets).map(a=>a.sourceSha256)).size,
  referencedAssetBytesBefore:referencedBytesBefore,checks:{identityOrderAndAnswers:'pass',assetReferencesAndHashes:'pass',losslessPixels:'pass',nativeTextAndOriginalHashes:'pass'},
  limitations:['Complex tables, mathematics, drawings and scans retain their original pixels.','OCR is supplementary; no unreviewed OCR replaces an image.','Not every question has been visually reviewed.']};
writeFileSync(join(target,'manifest.json'),JSON.stringify({...baseline,packs,files:after.files,compaction:{report:'compaction-report.json',sourceManifestSha256:report.sourceManifestSha256}},null,2));
writeFileSync(join(target,'compaction-report.json'),JSON.stringify(report,null,2));
writeFileSync(join(target,'text-evidence.json'),JSON.stringify(patches));
writeFileSync(join(target,'review.json'),readFileSync(join(cache,'review.json')));
writeFileSync(join(target,'asset-evidence.json'),JSON.stringify(assets));
for(const file of ['ocr-representative.json','workspace-inventory.json','cloud-baseline.json']) if(existsSync(join(cache,file))) cpSync(join(cache,file),join(target,file));
writeFileSync(join(out,'current.json'),JSON.stringify({directory:target}));
console.log(JSON.stringify(report,null,2));
