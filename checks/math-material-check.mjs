import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {validateQuestions,questionKey} from '../web/core.mjs';
import {loadGithubCandidates} from '../scripts/github-candidates.mjs';
const read=f=>JSON.parse(readFileSync(f)),hash=b=>createHash('sha256').update(b).digest('hex');
const manifest=read('build/private/manifest.json'),report=read('private-data/github-material/prepared/math-report.json');
const verification=read('private-data/github-material/prepared/math-verification.json');
assert.equal(verification.reportSha256,hash(readFileSync('private-data/github-material/prepared/math-report.json')));
const changed=[];
for(const [id,sha] of Object.entries(read('private-data/github-material/math-baseline.json')))if(manifest.packs.find(p=>p.id===id)?.sha256!==sha)changed.push(id);
if(changed.length){
 // A concurrent construction build replaced duplicate architect questions with official originals.
 assert.deepEqual(changed.sort(),['candidate-0a1c4990e588-1','candidate-0a1c4990e588-2','candidate-0a1c4990e588-3']);
 const existing=manifest.packs.filter(p=>!p.id.startsWith('candidate-')).flatMap(p=>validateQuestions(read('build/private/web/'+p.url)));
 const verified=loadGithubCandidates(process.cwd(),existing);
 for(const id of changed){const expected=verified.packs.find(p=>p.id===id);assert.equal(manifest.packs.find(p=>p.id===id)?.sha256,expected?hash(JSON.stringify(expected.rows)):undefined,'Concurrent replacement does not match frozen sources: '+id);}
}
const ready=report.packs.filter(p=>p.status==='prepared'),keys=new Set(),counts={};let samples=0;
assert.equal(ready.length,32);assert.equal(report.packs.filter(p=>p.status!=='prepared').length,1);
for(const p of ready){
 const built=manifest.packs.find(x=>x.id==='archive-'+p.file.slice(0,-5));assert.ok(built);assert.equal(built.localOnly,true);
 const raw=readFileSync('build/private/web/'+built.url);assert.equal(hash(raw),built.sha256);
 const rows=validateQuestions(JSON.parse(raw));assert.deepEqual(rows,validateQuestions(read('private-data/github-material/prepared/'+p.file)));
 counts[p.examId]=(counts[p.examId]||0)+rows.length;
 for(const [i,q]of rows.entries()){
  assert.ok(!keys.has(questionKey(q)));keys.add(questionKey(q));assert.equal(q.type,'essay');assert.ok(q.modelAnswer.includes('自己採点'));
  assert.equal(q.answer,null);assert.ok(q.images.length&&q.solutionImages.length);assert.equal(q.sourceUrl,p.url);
  if(p.kind==='sample'){samples++;assert.equal(q.category,'公式サンプル');}else assert.equal(q.category,'過去問');
  for(const [field,evidence]of [['images',p.questions[i].images],['solutionImages',p.questions[i].solutionImages]]){
   for(const [j,image]of q[field].entries()){assert.ok(existsSync('build/private/web/'+image.src));assert.equal(hash(readFileSync('build/private/web/'+image.src)),evidence[j].sha256);}
  }
  assert.ok(q.images.every(image=>!q.solutionImages.some(a=>a.src===image.src)),'Answer image leaked');
 }
}
assert.equal(keys.size,480);assert.equal(samples,10);assert.equal(Object.keys(counts).length,16);assert.equal(counts.statistics1,20);assert.equal(counts['suken-pre2'],50);
const advanced=read('private-data/github-material/prepared/math-statistics-ds-advanced-sample.json');assert.equal(advanced.length,8);
const applied=read('private-data/github-material/prepared/math-statistics1-202511-ouyo.json');
assert.equal(applied.length,15);assert.equal(applied.filter(q=>q.prompt.includes('問5')).length,1,'Shared application question duplicated');
console.log('PASS: 480 mathematics/statistics questions, 16 exams, 470 past + 10 samples; previous packs and original image hashes preserved',counts);
