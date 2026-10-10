// Package the verified personal library without rebuilding or dropping incremental imports.
import assert from 'node:assert/strict';
import {cpSync,mkdirSync,readFileSync,readdirSync,writeFileSync,statSync,openSync,closeSync,unlinkSync} from 'node:fs';
import {resolve,join,extname,relative,isAbsolute} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {assetShard} from './cloud-runtime.mjs';
import {validateQuestions,questionKey} from '../web/core.mjs';

const root=resolve('.'),source=process.argv.includes('--compact')?JSON.parse(readFileSync(join(root,'build/material-transcription/current.json'))).directory:join(root,'build/private'),out=join(root,'build/private-cloud');
const sourcePath=relative(join(root,'build'),source);
assert.ok(!sourcePath.startsWith('..') && !isAbsolute(sourcePath),'Source must stay under build');
const lock=join(root,'build/private-build.lock'),fd=openSync(lock,'wx');
process.on('exit',()=>{closeSync(fd);unlinkSync(lock);});
for(const signal of ['SIGINT','SIGTERM']) process.on(signal,()=>process.exit(1));
const manifest=JSON.parse(readFileSync(join(source,'manifest.json')));
const {MATERIAL_INDEX,MATERIAL_PACKS,MATERIAL_EXAMS}=await import(pathToFileURL(join(source,'web/catalog.mjs')));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
if(process.argv.includes('--compact')) assert.equal(hash(readFileSync(join(root,'build/private/manifest.json'))),manifest.compaction.sourceManifestSha256,'Compact build is stale; regenerate it');
if(process.argv.includes('--compact')) {
  assert.equal(manifest.transcription.allImagesAttempted,true,'Image extraction is incomplete');
  assert.equal(manifest.transcription.cropMethod,4,'Image crop validation is stale; regenerate it');
  const compact=JSON.parse(readFileSync(join(root,'build/private-compact/current.json'))).directory;
  assert.equal(hash(readFileSync(join(compact,'manifest.json'))),manifest.transcription.sourceManifestSha256,'Transcription build is stale; regenerate it');
}
assert.equal(MATERIAL_INDEX.length,manifest.questions);
assert.deepEqual(MATERIAL_PACKS,manifest.packs);
const keys=new Set(),assets=new Set();
for(const pack of MATERIAL_PACKS) {
  const raw=readFileSync(join(source,'web',pack.url));
  assert.equal(hash(raw),pack.sha256,pack.url);
  const rows=validateQuestions(JSON.parse(raw));assert.equal(rows.length,pack.count);
  for(const q of rows) {
    const key=questionKey(q);assert.ok(!keys.has(key),key);keys.add(key);
    for(const a of [...q.images,...q.solutionImages,...(q.audio || [])]) if(a.src.startsWith('assets/')) assets.add(a.src);
  }
}
assert.equal(keys.size,manifest.questions);
assert.ok(MATERIAL_INDEX.every(q=>keys.has(questionKey(q))));
// Keep retained compact images and old URLs for previously edited questions.
const aliases={};
if(manifest.compaction) {
  for(const [old,entry] of Object.entries(JSON.parse(readFileSync(join(source,'asset-evidence.json'))))) {
    if(old!==entry.src) {aliases[old]=entry.src;assets.add(entry.src);}
  }
}
// Each run has a new directory, so interrupted packaging cannot be deployed as a complete build.
const target=join(out,Date.now().toString());mkdirSync(join(target,'web/bundles'),{recursive:true});
writeFileSync(join(target,'package.json'),JSON.stringify({private:true,type:'module'}));
cpSync(join(root,'web'),join(target,'web'),{recursive:true});
cpSync(join(root,'functions'),join(target,'functions'),{recursive:true});
cpSync(join(source,'web/material'),join(target,'web/material'),{recursive:true});
cpSync(join(source,'web/library-catalog.mjs'),join(target,'web/library-catalog.mjs'));
cpSync(join(root,'scripts/cloud-runtime.mjs'),join(target,'web/cloud-runtime.mjs'));
const entries=MATERIAL_INDEX.map(q=>[questionKey(q),['single','multiple','written','essay'].indexOf(q.type)*32+q.options.length]);
writeFileSync(join(target,'web/state-catalog.mjs'),`import {CompactQuestionIndex} from './cloud-runtime.mjs';\nexport const BUILTIN_QUESTIONS=[];\nexport const MATERIAL_INDEX=new CompactQuestionIndex(${JSON.stringify(entries)});\n`);
// The browser already uses per-exam manifests; never ship its obsolete 40 MB catalog.
writeFileSync(join(target,'web/catalog.mjs'),`export const BUILTIN_QUESTIONS=[];export const MATERIAL_INDEX=[];export const MATERIAL_PACKS=[];export const MATERIAL_EXAMS=${JSON.stringify(MATERIAL_EXAMS)};\n`);
mkdirSync(join(target,'functions/assets'),{recursive:true});
writeFileSync(join(target,'functions/assets/[[path]].js'),"export {bundledAsset as onRequest} from '../../web/cloud-runtime.mjs';\n");
const maps=Array.from({length:64},()=>Object.create(null)),assetHashes={};
const types={'.png':'image/png','.webp':'image/webp','.jpg':'image/jpeg','.mp3':'audio/mpeg'};
let chunks=[],size=0,number=0;
// ponytail: insertions can shift later bundles; use stable shard groups if future uploads become costly.
const flush=()=>{if(chunks.length) {writeFileSync(join(target,`web/bundles/${number}.bin`),Buffer.concat(chunks));number++;chunks=[];size=0;}};
for(const path of [...assets].sort()) {
  const bytes=readFileSync(join(source,'web',path));assert.ok(bytes.length<25*1024*1024,path);
  assetHashes[path]=hash(bytes);
  if(bytes.length>4*1024*1024) {mkdirSync(resolve(target,'web',path,'..'),{recursive:true});writeFileSync(join(target,'web',path),bytes);continue;}
  if(size+bytes.length>4*1024*1024) flush();
  maps[assetShard(path)][path]=[`bundles/${number}.bin`,size,bytes.length,types[extname(path)]];
  chunks.push(bytes);size+=bytes.length;
}
flush();
for(const [old,path] of Object.entries(aliases)) {
  const entry=maps[assetShard(path)][path] || [path,0,statSync(join(target,'web',path)).size,types[extname(path)]];
  maps[assetShard(old)][old]=entry;assetHashes[old]=assetHashes[path];
}
for(let i=0;i<maps.length;i++) writeFileSync(join(target,`web/bundles/index-${i}.json`),JSON.stringify(maps[i]));
const files=[];
function walk(dir) {for(const f of readdirSync(dir,{withFileTypes:true})) {const p=join(dir,f.name);if(f.isDirectory()) walk(p);else {assert.ok(statSync(p).size<25*1024*1024,p);files.push(p);}}}
walk(join(target,'web'));assert.ok(files.length<=20000,'Pages file count exceeds 20,000');
const config=JSON.parse(readFileSync(join(root,'wrangler.local.jsonc'),'utf8'));
assert.ok(config.name && config.d1_databases?.some(d=>d.binding==='DB'));
config.pages_build_output_dir='./web';writeFileSync(join(target,'wrangler.jsonc'),JSON.stringify(config,null,2));
mkdirSync(join(target,'.wrangler/deploy'),{recursive:true});
writeFileSync(join(target,'.wrangler/deploy/config.json'),JSON.stringify({configPath:'../../wrangler.jsonc'}));
if(manifest.compaction) cpSync(join(source,'compaction-report.json'),join(target,'compaction-report.json'));
if(manifest.transcription) for(const file of ['transcription-report.json','image-text-evidence.json']) cpSync(join(source,file),join(target,file));
writeFileSync(join(target,'manifest.json'),JSON.stringify({...manifest,files:files.length,sourceAssets:Object.keys(assetHashes).length,physicalAssets:assets.size,assetAliases:aliases,assetHashes,packagedAt:new Date().toISOString()},null,2));
writeFileSync(join(out,'current.json'),JSON.stringify({directory:target}));
console.log(JSON.stringify({directory:target,questions:manifest.questions,packs:MATERIAL_PACKS.length,assets:assets.size,files:files.length,bundles:number}));
