import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {validateQuestions,correctAnswer,questionKey,isChoice} from '../web/core.mjs';
const read=file=>JSON.parse(readFileSync(file));
const manifest=read('build/private/manifest.json');
const report=read('private-data/github-material/prepared/history-report.json');
for(const [id,sha] of Object.entries(read('private-data/github-material/history-baseline.json'))) assert.equal(manifest.packs.find(p=>p.id===id)?.sha256,sha,'Previous pack changed: '+id);
assert.equal(report.packs.length,15);assert.ok(report.packs.every(p=>p.status==='prepared'));
const counts={},keys=new Set();let essays=0;
for(const pack of report.packs) {
  const built=manifest.packs.find(p=>p.id==='archive-'+pack.file.slice(0,-5));assert.ok(built);assert.equal(built.localOnly,true);
  const bytes=readFileSync('build/private/web/'+built.url);assert.equal(createHash('sha256').update(bytes).digest('hex'),built.sha256);
  const rows=validateQuestions(JSON.parse(bytes));assert.deepEqual(rows,validateQuestions(read('private-data/github-material/prepared/'+pack.file)));
  counts[pack.examId]=(counts[pack.examId]||0)+rows.length;
  for(const q of rows) {
    assert.ok(!keys.has(questionKey(q)));keys.add(questionKey(q));
    if(isChoice(q)) {assert.ok(correctAnswer(q,q.answer));assert.ok(!correctAnswer(q,(q.answer+1)%q.options.length));}
    else {essays++;assert.equal(q.type,'essay');assert.ok(q.solutionImages.length && q.modelAnswer.includes('自己採点'));}
    for(const image of [...q.images,...q.solutionImages]) assert.ok(existsSync('build/private/web/'+image.src));
    if(pack.kind==='practice') {assert.equal(q.category,'公式練習問題');assert.equal(q.year,'');assert.ok(q.passage && q.explanation);}
  }
}
assert.equal(keys.size,198);assert.equal(essays,27);assert.equal(Object.keys(counts).length,11);
assert.equal(counts['map-geography-basic'],60);assert.equal(counts['map-geography-specialist'],72);
const shared=read('private-data/github-material/prepared/history-jmc-43rd_s.json');
assert.deepEqual(read('private-data/github-material/prepared/history-jmc-45th_s.json').slice(0,15).map(q=>q.answer),[3,0,0,1,2,2,1,1,3,0,5,0,5,1,2],'Visually checked official answer table');
assert.ok(shared[3].images.some(i=>i.src.endsWith('-p006.png')),'Shared map preceding question 4 missing');
assert.ok(shared.filter(q=>q.type==='essay').every(q=>q.images.every(i=>!q.solutionImages.some(s=>s.src===i.src))),'Answers leaked into questions');
console.log('PASS: 198 history/geography questions, 11 exams, previous packs, grading, shared figures and 27 self-graded questions',counts);
