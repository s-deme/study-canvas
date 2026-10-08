import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {validateQuestions} from '../web/core.mjs';
const dir='private-data/github-material/prepared/';
const {packs}=JSON.parse(readFileSync(dir+'kanken-report.json'));
assert.equal(packs.length,24);
const counts=new Map();
for(const pack of packs) {
  const rows=validateQuestions(JSON.parse(readFileSync(dir+pack.file)));
  assert.ok(pack.localOnly);
  assert.equal(rows.length,pack.count);
  assert.equal(new Set(pack.questions.map(e=>e.number)).size,rows.length);
  for(const [i,q] of rows.entries()) {
    assert.equal(q.type,'written');assert.equal(q.answer,null);
    assert.equal(q.topic,pack.questions[i].target);
    assert.ok(q.modelAnswer.includes(q.topic));
    assert.ok(q.images.length>=2 && q.solutionImages.length>=1);
    assert.ok(q.images.every(im=>!q.solutionImages.some(s=>s.src===im.src)));
  }
  counts.set(pack.examId,(counts.get(pack.examId)||0)+rows.length);
}
assert.equal(counts.size,12);
assert.equal([...counts.values()].reduce((a,b)=>a+b,0),2772);
console.log('PASS: Kanken 24 papers, 12 grades, 2,772 unique numbered items, written self grading and separate solutions');
