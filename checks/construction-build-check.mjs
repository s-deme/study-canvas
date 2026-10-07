import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {validateQuestions,emptyState,newSession,submit,finish,questionKey} from '../web/core.mjs';
import {loadGithubCandidates} from '../scripts/github-candidates.mjs';
const root=new URL('../',import.meta.url),read=path=>JSON.parse(readFileSync(new URL(path,root)));
const manifest=read('build/private/manifest.json');
const construction=manifest.packs.filter(p=>p.id.startsWith('archive-construction-'));
const rows=construction.flatMap(p=>validateQuestions(read('build/private/web/'+p.url)));
const report=read('private-data/github-material/prepared/construction-report.json');
assert.equal(rows.length,report.packs.filter(p=>p.status==='prepared').reduce((n,p)=>n+p.count,0));
assert.equal(new Set(rows.map(questionKey)).size,rows.length);
for(const id of ['architect1','architect2','architect-wood','building-equipment','interior-planner','civil-management1','civil-management2','pipe-management1','pipe-management2','landscape-management1','landscape-management2','telecom-management1','telecom-management2']) assert.ok(rows.some(q=>q.examId===id),id);
for(const id of ['surveyor','surveyor-assistant']) assert.ok(manifest.exams.find(e=>e.id===id).count>=140);
assert.ok(construction.every(p=>p.localOnly));
const original=read('private-data/github-material/construction-baseline.json');
for(const p of manifest.packs.filter(p=>['surveyor','surveyor-assistant'].includes(p.examId))) if(original.packs[p.id]) assert.equal(p.sha256,original.packs[p.id]);
const state=emptyState();
for(const type of ['single','multiple']) {
 const q=rows.find(q=>q.type===type);assert.ok(q);
 state.selectedExam=q.examId;state.session=newSession([q],1,'検証');state.session.pending=q.answer;submit(state,rows);finish(state,rows);
 assert.equal(state.stats[questionKey(q)].correct,1);
}
const native=rows.filter(q=>q.examId==='architect1');
const candidates=loadGithubCandidates(fileURLToPath(root),rows).packs.filter(p=>p.examId==='architect1').flatMap(p=>p.rows);
for(const q of candidates) {
 const year=q.year.match(/^(H|R|平成|令和)(\d+)年?$/),number=q.source.match(/(\d+)\s—/);
 assert.ok(year && number,'Architecture candidate identity must be recognized');
 assert.ok(!native.some(n=>n.year===String(Number(year[2])+(['R','令和'].includes(year[1])?2018:1988)) && n.subject===q.subject && Number(n.id.match(/-q(\d+)$/)[1])===Number(number[1])));
}
console.log(`PASS: ${rows.length} construction questions, ${construction.length} packs, all destinations, grading, local-only flags and architecture deduplication`);
