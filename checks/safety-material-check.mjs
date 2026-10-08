import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {validateQuestions,correctAnswer,questionKey,isChoice} from '../web/core.mjs';
import {assertPreservedPacks} from './preserved-packs.mjs';
const read=p=>JSON.parse(readFileSync(p));
const report=read('private-data/github-material/prepared/safety-report.json');
const manifest=read('build/private/manifest.json');
const recovery=read('private-data/github-material/safety-recovery-baseline.json');
assertPreservedPacks(manifest,recovery);
assert.ok(manifest.questions>=recovery.questions+733);
assert.equal(report.packs.filter(p=>p.status==='prepared' && !recovery.packs.some(old=>old.id==='archive-'+p.file.slice(0,-5))).reduce((n,p)=>n+p.count,0),733);
const keys=new Set(),counts={};
for(const p of report.packs.filter(p=>p.status==='prepared')){
  const pack=manifest.packs.find(x=>x.id==='archive-'+p.file.slice(0,-5));assert.ok(pack,p.file);assert.equal(pack.localOnly,true);
  const rows=validateQuestions(read('build/private/web/'+pack.url));assert.equal(rows.length,p.count);
  assert.deepEqual(rows,validateQuestions(read('private-data/github-material/prepared/'+p.file)));
  for(const q of rows){
    assert.ok(!keys.has(questionKey(q)));keys.add(questionKey(q));
    if(isChoice(q)){assert.ok(correctAnswer(q,q.answer));assert.ok(!correctAnswer(q,(q.answer+1)%q.options.length));}
    else {assert.ok(correctAnswer(q,{review:'done'}));assert.ok(!correctAnswer(q,{review:'review'}));assert.ok(q.modelAnswer && q.solutionImages.length);}
    for(const image of [...q.images,...q.solutionImages])assert.ok(existsSync('build/private/web/'+image.src));
    if(!p.kind)assert.ok(q.solutionImages.length,'Original marked answer pages required');
  }
  counts[p.examId]=(counts[p.examId]||0)+rows.length;
}
assert.equal(keys.size,2307,'Safety import coverage changed');
for(const [exam,count] of Object.entries({'work-environment1':360,'work-environment2':160,'crane-derrick':80,'hazmat-a':45,'boiler-special':48}))assert.equal(counts[exam],count);
const scanned=read('private-data/github-material/prepared/safety-kikenbutsu-kou.json');
assert.equal(scanned[22].answer,1,'Reviewed hazmat question 23');
assert.equal(report.packs.filter(p=>p.status!=='prepared').length,2);
assert.ok(!report.packs.some(p=>p.file==='safety-external-0804.json'),'Duplicate official publication');
console.log('PASS: safety preservation, built packs, assets and grading',counts);
