import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {loadGithubMaterial} from '../scripts/github-material.mjs';
import {MATERIAL_INDEX} from '../build/private/web/catalog.mjs';
import {emptyState,newSession,submit,finish,selfEvaluate,questionKey} from '../build/private/web/core.mjs';
// Existing index establishes catalog identity without loading unrelated question bodies.
const prior=MATERIAL_INDEX.filter(q=>!q.id.startsWith('business-'));
const result=loadGithubMaterial(process.cwd(),prior,'business-report.json','business-verification.json');
const rows=result.packs.flatMap(p=>p.rows);
assert.ok(rows.length>2900);assert.equal(new Set(rows.map(q=>q.examId)).size,18);
assert.ok(result.packs.every(p=>p.localOnly));
for(const examId of new Set(rows.map(q=>q.examId))) {
 const q=rows.find(q=>q.examId===examId),state=emptyState();state.selectedExam=examId;
 state.session=newSession([q],1,'経営・事務・販売検証');state.session.pending=q.type==='written'?'自己確認':q.answer;
 submit(state,rows);if(q.type==='written') selfEvaluate(state,rows,'done');
 finish(state,rows);assert.equal(q.type==='written'?state.stats[questionKey(q)].self.done:state.stats[questionKey(q)].correct,1);
}
console.log(`PASS: ${rows.length} verified business items across 18 exams; local-only material loads`);
const manifest=JSON.parse(readFileSync('build/private/manifest.json'));
if(manifest.packs.some(p=>p.id.startsWith('archive-business-'))) {
 assert.equal(manifest.packs.filter(p=>p.id.startsWith('archive-business-')).reduce((n,p)=>n+p.count,0),rows.length);
 const baseline='private-data/github-material/business-build-baseline.json';
 if(existsSync(baseline)) for(const p of JSON.parse(readFileSync(baseline)).packs) assert.equal(manifest.packs.find(q=>q.id===p.id)?.sha256,p.sha256,'Previous pack changed: '+p.id);
 console.log('PASS: registered business count and previous pack hashes preserved');
}
