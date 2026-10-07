import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {validateQuestions,correctAnswer,questionKey} from '../web/core.mjs';
const read=file=>JSON.parse(readFileSync(file));
const report=read('private-data/github-material/prepared/tourism-report.json');
const manifest=read('build/private/manifest.json');
const baseline=read('private-data/github-material/tourism-baseline.json');
for(const [id,sha] of Object.entries(baseline)) assert.equal(manifest.packs.find(p=>p.id===id)?.sha256,sha,'Previous pack changed: '+id);
const keys=new Set(),counts={};
for(const pack of report.packs.filter(p=>p.status==='prepared')) {
  const built=manifest.packs.find(p=>p.id==='archive-'+pack.file.slice(0,-5));assert.ok(built,pack.file);
  assert.equal(built.localOnly,true);
  const bytes=readFileSync('build/private/web/'+built.url);assert.equal(createHash('sha256').update(bytes).digest('hex'),built.sha256);
  const rows=validateQuestions(JSON.parse(bytes));assert.equal(rows.length,pack.count);
  assert.deepEqual(rows,validateQuestions(read('private-data/github-material/prepared/'+pack.file)));
  for(const q of rows) {
    assert.ok(!keys.has(questionKey(q)));keys.add(questionKey(q));assert.ok(correctAnswer(q,q.answer));
    assert.ok(!correctAnswer(q,q.type==='multiple'?[]:(q.answer+1)%q.options.length));
    for(const image of q.images)assert.ok(existsSync('build/private/web/'+image.src),image.src);
  }
  counts[pack.examId]=(counts[pack.examId]||0)+rows.length;
}
for(const year of [2024,2025,2026]) {
  const rows=read(`private-data/github-material/prepared/tourism-anta-${year}-all.json`);
  const expected=year===2024?[1,3]:[0,3];assert.deepEqual(rows[0].answer,expected);
  assert.ok(!rows.some(q=>q.id.endsWith('-q'+({2024:'069',2025:'070',2026:'071'}[year]))),'Compound answer must stay excluded');
}
assert.equal(Object.keys(counts).length,5,'All five tourism/transport exams must receive questions');
console.log('PASS: tourism counts, previous packs, assets, reviewed keys, uniqueness and grading',counts);
