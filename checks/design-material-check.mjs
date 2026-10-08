import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {validateQuestions,emptyState,newSession,submit,finish,questionKey} from '../web/core.mjs';
const report=JSON.parse(readFileSync('private-data/github-material/prepared/design-report.json'));
const manifest=JSON.parse(readFileSync('build/private/manifest.json'));
const baseline=existsSync('private-data/github-material/design-baseline.json')?JSON.parse(readFileSync('private-data/github-material/design-baseline.json')):{};
for(const [id,sha] of Object.entries(baseline)) assert.equal(manifest.packs.find(p=>p.id===id)?.sha256,sha,'Previous pack changed '+id);
const keys=new Set();let count=0;
for(const pack of report.packs.filter(p=>p.status==='prepared')) {
  const built=manifest.packs.find(p=>p.id==='archive-'+pack.file.slice(0,-5));assert.ok(built);
  const rows=validateQuestions(JSON.parse(readFileSync('build/private/web/'+built.url)));
  assert.equal(rows.length,pack.count);assert.equal(built.localOnly,true);
  for(const q of rows) {
    assert.ok(!keys.has(questionKey(q)));keys.add(questionKey(q));assert.equal(q.options.length,4);
    assert.equal(q.images.length,q.solutionImages.length);
    for(const [i,image] of q.images.entries()) {
      assert.notEqual(image.src,q.solutionImages[i].src);
      for(const asset of [image,q.solutionImages[i]]) assert.ok(existsSync('build/private/web/'+asset.src));
    }
    const state=emptyState();state.selectedExam=q.examId;state.session=newSession([q],1,'取り込み確認');state.session.pending=q.answer;
    submit(state,[q]);finish(state,[q]);assert.equal(state.stats[questionKey(q)].correct,1);
  }
  count+=rows.length;
}
for(const file of ['rbc-54rhikki.json','rbc-54bhikki.json']) {
  const sample=validateQuestions(JSON.parse(readFileSync('private-data/github-material/prepared/'+file)));
  assert.deepEqual(sample.filter(q=>/-q[123]$/.test(q.id)).map(q=>q.answer),[2,3,2]);
}
assert.ok(count>0);console.log(`PASS: ${count} design/life questions, official sample keys, assets, deduplication and grading`);
