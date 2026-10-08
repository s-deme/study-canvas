import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {validateQuestions,correctAnswer,questionKey} from '../web/core.mjs';
import {loadGithubMaterial} from '../scripts/github-material.mjs';
import {assertPreservedPacks} from './preserved-packs.mjs';
const read=p=>JSON.parse(readFileSync(p));
const base='private-data/github-material/', manifest=read('build/private/manifest.json');
const baseline=read(base+'hazmat-baseline.json'), review=read(base+'hazmat-review.json');
assertPreservedPacks(manifest,baseline);
const loaded=loadGithubMaterial(process.cwd(),[],'hazmat-report.json','hazmat-verification.json');
assert.equal(loaded.report.added,175);
const keys=new Set(),unique=new Set();
for(const p of loaded.packs){
  const built=manifest.packs.find(b=>b.id===p.id);assert.ok(built?.localOnly);
  const rows=validateQuestions(read('build/private/web/'+built.url));assert.deepEqual(rows,p.rows);
  const kind=p.examId.slice(-1), detail=review.classes[kind];
  assert.equal(rows.length,35);
  assert.deepEqual(rows.map(q=>q.answer+1),[...review.commonAnswers,...detail.answers]);
  assert.equal(rows.filter(q=>q.subject==='危険物に関する法令').length,15);
  assert.equal(rows.filter(q=>q.subject==='基礎的な物理学及び基礎的な化学').length,10);
  for(const [i,q] of rows.entries()){
    assert.ok(!keys.has(questionKey(q)));keys.add(questionKey(q));
    unique.add((i<25?'common':kind)+'-'+(i+1));
    const page=[...review.commonPages,...detail.pages][i];
    assert.equal(q.images[0].src,`assets/github-material/hazmat-otsu-p${String(page).padStart(3,'0')}.png`);
    assert.equal(q.solutionImages[0].src,`assets/github-material/hazmat-otsu-p${i<25?'044':String(detail.answerPage).padStart(3,'0')}.png`);
    assert.ok(correctAnswer(q,q.answer));assert.ok(!correctAnswer(q,(q.answer+1)%5));
    for(const asset of [...q.images,...q.solutionImages]){
      const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
      assert.equal(hash('build/private/web/'+asset.src),hash(base+'prepared/assets/'+asset.src.split('/').at(-1)));
    }
  }
}
assert.equal(keys.size,175);assert.equal(unique.size,75);
assert.ok(manifest.questions>=baseline.questions+175);
for(const k of [1,2,3,4,5,6])assert.ok(manifest.exams.find(e=>e.id==='hazmat-b'+k)?.count>=35);
console.log('PASS: all six classes registered; 175 additions, 75 distinct questions; existing packs, answers, subjects and images preserved');
