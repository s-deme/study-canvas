import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {validateQuestions,correctAnswer,questionKey} from '../web/core.mjs';
const read=p=>JSON.parse(readFileSync(p));
const report=read('private-data/github-material/prepared/safety-report.json');
const manifest=read('build/private/manifest.json');
const baseline=read('private-data/github-material/safety-baseline.json');
for(const [id,hash] of Object.entries(baseline))assert.equal(manifest.packs.find(p=>p.id===id)?.sha256,hash,'Existing pack changed: '+id);
const keys=new Set(),counts={};
for(const p of report.packs.filter(p=>p.status==='prepared')){
  const pack=manifest.packs.find(x=>x.id==='archive-'+p.file.slice(0,-5));assert.ok(pack,p.file);assert.equal(pack.localOnly,true);
  const rows=validateQuestions(read('build/private/web/'+pack.url));assert.equal(rows.length,p.count);
  assert.deepEqual(rows,validateQuestions(read('private-data/github-material/prepared/'+p.file)));
  for(const q of rows){
    assert.ok(!keys.has(questionKey(q)));keys.add(questionKey(q));
    assert.ok(correctAnswer(q,q.answer));assert.ok(!correctAnswer(q,(q.answer+1)%q.options.length));
    for(const image of [...q.images,...q.solutionImages])assert.ok(existsSync('build/private/web/'+image.src));
    if(!p.kind)assert.ok(q.solutionImages.length,'Original marked answer pages required');
  }
  counts[p.examId]=(counts[p.examId]||0)+rows.length;
}
assert.equal(keys.size,1574,'Safety import coverage changed');
assert.ok(!report.packs.some(p=>p.file==='safety-external-0804.json'),'Duplicate official publication');
console.log('PASS: safety preservation, built packs, assets and grading',counts);
