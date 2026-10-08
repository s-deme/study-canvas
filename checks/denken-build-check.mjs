import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {validateQuestions,emptyState,newSession,submit,selfEvaluate,finish,questionKey} from '../web/core.mjs';
const read=p=>JSON.parse(readFileSync(new URL('../'+p,import.meta.url)));
const manifest=read('build/private/manifest.json'),baseline=read('private-data/github-material/denken-baseline.json');
const report=read('private-data/github-material/prepared/denken-report.json');
const candidates=read('private-data/github-candidates/prepared/report.json');
const repos=['5garashi/denken2','nemi2nd-dot/denken2-app','nakasyo3519/denken3all'];
for(const prior of baseline.manifest.packs) assert.equal(manifest.packs.find(p=>p.id===prior.id)?.sha256,prior.sha256,'Existing pack changed: '+prior.id);
const packs=manifest.packs.filter(p=>p.id.startsWith('archive-denken-') || repos.includes(p.repo));
const rows=packs.flatMap(p=>{const bytes=readFileSync(new URL('../build/private/web/'+p.url,import.meta.url));assert.equal(createHash('sha256').update(bytes).digest('hex'),p.sha256);return validateQuestions(JSON.parse(bytes));});
assert.equal(rows.length,report.packs.filter(p=>p.status==='prepared').reduce((n,p)=>n+p.count,0)+candidates.packs.filter(p=>repos.includes(p.repo)).reduce((n,p)=>n+p.count,0));
assert.equal(new Set(rows.map(questionKey)).size,rows.length);assert.ok(packs.every(p=>p.localOnly));
const hashes=new Map(report.packs.filter(p=>p.status==='prepared').flatMap(p=>p.questions.flatMap(q=>[...q.images,...q.solutionImages])).map(i=>[i.file,i.sha256]));
for(const [file,hash] of hashes) assert.equal(createHash('sha256').update(readFileSync(new URL('../build/private/web/assets/github-material/'+file,import.meta.url))).digest('hex'),hash);
const community=rows.filter(q=>q.id.startsWith('github-'));
assert.ok(community.every(q=>q.source.includes('未検証')));
assert.equal(community.filter(q=>q.source.includes('nemi2nd-dot/denken2-app')).length,962);
assert.equal(community.filter(q=>q.source.includes('5garashi/denken2')).length,120);
assert.equal(community.filter(q=>q.source.includes('nakasyo3519/denken3all')).length,13);
assert.equal(community.find(q=>q.source.includes('q_theory.js#t001 ')).answer,1);
for(const q of [rows.find(q=>q.type==='single'),rows.find(q=>q.type==='written' && !q.solutionImages.length),rows.find(q=>q.solutionImages.length),community[0]]) {
 assert.ok(q);const state=emptyState();state.selectedExam=q.examId;state.session=newSession([q],1,'電験追加検証');state.session.pending=q.type==='single'?q.answer:q.modelAnswer;
 submit(state,rows);if(q.type==='written') selfEvaluate(state,rows,'done');finish(state,rows);
 assert.equal(q.type==='single'?state.stats[questionKey(q)].correct:state.stats[questionKey(q)].self.done,1);
}
console.log('PASS Denken: '+rows.length+' added; original packs preserved; hashes, source notices and grading verified');
