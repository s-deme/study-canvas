// Append verified food packs to the last successful local build while other imports are pending.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,cpSync,mkdirSync,readdirSync,statSync,openSync,closeSync,unlinkSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {loadGithubMaterial} from './github-material.mjs';
import {loadGithubCandidates} from './github-candidates.mjs';
import {recoverPrivateBuild,updatePrivateBuild} from './private-build-update.mjs';
import {DEFAULT_EXAMS,validateQuestions,questionKey} from '../web/core.mjs';
const root=fileURLToPath(new URL('../',import.meta.url)),out=resolve(root,'build/private');let web=join(out,'web');
const lock=join(root,'build/private-build.lock'),lockFd=openSync(lock,'wx');
process.on('exit',()=>{closeSync(lockFd);unlinkSync(lock);});
for(const signal of ['SIGINT','SIGTERM']) process.on(signal,()=>process.exit(1));
recoverPrivateBuild(out);
const {MATERIAL_INDEX,MATERIAL_PACKS,MATERIAL_EXAMS}=await import(pathToFileURL(join(out,'web/catalog.mjs')));
const hash=b=>createHash('sha256').update(b).digest('hex');
const manifest=JSON.parse(readFileSync(join(out,'manifest.json'))),existing=[];
assert.deepEqual(manifest.packs,MATERIAL_PACKS);
for(const pack of MATERIAL_PACKS) {
 const bytes=readFileSync(join(web,pack.url));assert.equal(hash(bytes),pack.sha256);
 const rows=validateQuestions(JSON.parse(bytes));assert.equal(rows.length,pack.count);existing.push(...rows);
}
assert.equal(existing.length,manifest.questions);
const keys=new Set(existing.map(questionKey));assert.equal(keys.size,existing.length);
const kind=process.argv[2] || 'food',kinds=kind.split(',');
assert.ok(kinds.every(k=>['food','safety','history','finance','construction','math','business','electricity','welfare','public-examples'].includes(k)));
const foodIds=new Set(MATERIAL_PACKS.filter(p=>kinds.some(k=>p.id.startsWith('archive-'+k+'-'))).map(p=>p.id));
const loaded={exams:[],packs:[],report:{added:0}},unaffected=existing.filter(q=>!kinds.some(k=>q.id.startsWith(k+'-')));
for(const k of kinds) {
 const part=loadGithubMaterial(root,[...unaffected,...loaded.packs.flatMap(p=>p.rows)],k+'-report.json',k+'-verification.json');
 loaded.exams.push(...part.exams);loaded.packs.push(...part.packs);loaded.report.added+=part.report.added;
}
const replacements=new Map(),removed=new Set();
if(process.argv.includes('--replace')) for(const p of loaded.packs.filter(p=>foodIds.has(p.id))) {
 const prior=validateQuestions(JSON.parse(readFileSync(join(web,MATERIAL_PACKS.find(old=>old.id===p.id).url))));
 const shape=q=>[questionKey(q),q.type,q.year,q.term,q.subject,q.options.length,q.images,q.solutionImages,q.audio || []];
 assert.deepEqual(p.rows.map(shape),prior.map(shape),'Replacement must preserve index fields, assets and order');
 replacements.set(p.id,p.rows);
}
if(kind==='construction') {
 const candidateKeys=new Set(MATERIAL_PACKS.filter(p=>p.id.startsWith('candidate-')).flatMap(p=>JSON.parse(readFileSync(join(web,p.url))).map(questionKey)));
 const candidates=loadGithubCandidates(root,[...existing.filter(q=>!candidateKeys.has(questionKey(q))),...loaded.packs.flatMap(p=>p.rows)]);
 for(const pack of MATERIAL_PACKS.filter(p=>p.examId==='architect1' && p.id.startsWith('candidate-'))) {
  const rows=candidates.packs.find(p=>p.id===pack.id)?.rows || [],kept=new Set(rows.map(questionKey));
  for(const q of JSON.parse(readFileSync(join(web,pack.url)))) if(!kept.has(questionKey(q))) removed.add(questionKey(q));
  replacements.set(pack.id,rows);
 }
}
const packs=MATERIAL_PACKS.filter(p=>!replacements.has(p.id) || replacements.get(p.id).length).map(p=>replacements.has(p.id)?{...p,count:replacements.get(p.id).length,sha256:hash(JSON.stringify(replacements.get(p.id)))}:p);
const index=MATERIAL_INDEX.filter(q=>!removed.has(questionKey(q))),exams=[...MATERIAL_EXAMS];
for(const exam of loaded.exams) if(![...DEFAULT_EXAMS,...exams].some(e=>e.id===exam.id)) exams.push(exam);
updatePrivateBuild(out,stage=>{
web=join(stage,'web');
mkdirSync(join(web,'assets/github-material'),{recursive:true});
const copiedAssets=new Set();
for(const pack of packs) if(replacements.has(pack.id)) writeFileSync(join(web,pack.url),JSON.stringify(replacements.get(pack.id)));
for(const {rows,...pack} of loaded.packs) {
 if(foodIds.has(pack.id)){assert.equal(packs.find(p=>p.id===pack.id).sha256,hash(JSON.stringify(rows)),'Registered food pack changed');continue;}
 assert.equal(pack.localOnly,true);
 for(const q of rows) {
  assert.ok(!keys.has(questionKey(q)));keys.add(questionKey(q));
  for(const image of [...q.images,...q.solutionImages]) if(!copiedAssets.has(image.src)) {cpSync(join(root,'private-data/github-material/prepared/assets',image.src.split('/').at(-1)),join(web,image.src));copiedAssets.add(image.src);}
  index.push({id:q.id,examId:q.examId,type:q.type,options:q.options.map((_,i)=>String(i)),catalogOnly:true,year:q.year,term:q.term,subject:q.subject});
 }
 const bytes=JSON.stringify(rows),url='material/'+pack.id+'.json';writeFileSync(join(web,url),bytes);
 packs.push({...pack,url,sha256:hash(bytes)});
}
let files=0;
function walk(dir){for(const n of readdirSync(dir)){const p=join(dir,n);statSync(p).isDirectory()?walk(p):files++;}}
walk(web);
cpSync(join(root,'web/exams.mjs'),join(web,'exams.mjs'));
writeFileSync(join(web,'catalog.mjs'),`// Generated private index.\nexport const BUILTIN_QUESTIONS=[];\nexport const MATERIAL_INDEX=${JSON.stringify(index)};\nexport const MATERIAL_PACKS=${JSON.stringify(packs)};\nexport const MATERIAL_EXAMS=${JSON.stringify(exams)};\n`);
writeFileSync(join(stage,'manifest.json'),JSON.stringify({...manifest,questions:index.length,files,packs,exams:[...DEFAULT_EXAMS,...exams].map(e=>({id:e.id,name:e.name,count:index.filter(q=>q.examId===e.id).length}))},null,2));
});
console.log(`Local ${kind} import: ${loaded.report.added} verified questions; ${index.length} total`);
