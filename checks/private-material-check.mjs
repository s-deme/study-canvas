import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {MATERIAL_INDEX,MATERIAL_PACKS,MATERIAL_EXAMS} from '../build/private/web/catalog.mjs';
import {AVAILABLE_EXAMS,emptyState,validateState,validateQuestions,newSession,submit,finish,questionKey} from '../build/private/web/core.mjs';
import {onRequestGet,onRequestPut} from '../build/private/functions/api/state.js';
import {authFixture} from './cloud-preview.mjs';

const all=[];
for(const pack of MATERIAL_PACKS) {
  const raw=readFileSync(new URL('../build/private/web/'+pack.url,import.meta.url),'utf8');
  assert.equal(createHash('sha256').update(raw).digest('hex'),pack.sha256);
  const rows=validateQuestions(JSON.parse(raw));assert.equal(rows.length,pack.count);
  for(const q of rows) for(const image of [...q.images,...q.solutionImages,...(q.audio || [])]) assert.ok(existsSync(new URL('../build/private/web/'+image.src,import.meta.url)),image.src);
  all.push(...rows);
}
assert.equal(all.length,MATERIAL_INDEX.length);assert.ok(all.length>2000);
assert.equal(new Set(all.map(questionKey)).size,all.length);
for(const id of ['sg','fe','boki3','gken','ap','st','sa','pm','nw','db','es','sm','au','sc']) assert.ok(all.some(q=>q.examId===id));
const state=emptyState();assert.equal(state.exams.length,AVAILABLE_EXAMS.length);assert.ok(MATERIAL_EXAMS.every(e=>state.exams.some(registered=>registered.id===e.id)));
for(const examId of ['ap','st','sa','pm','nw','db','es','sm','au','sc']) for(const year of ['2023','2024','2025']) assert.ok(all.some(q=>q.examId===examId && q.year===year),examId+year);
state.selectedExam='ap';const q=all.find(q=>q.examId==='ap' && q.type==='single');state.session=newSession([q],1,'検証');state.session.pending=q.answer;submit(state,all);finish(state,all);
assert.equal(validateState(state,MATERIAL_INDEX).stats[questionKey(q)].correct,1);
for(const examId of ['ap','st','sa','pm','nw','db','es','sm','au','sc']) for(const year of ['2023','2024','2025']) {
 const item=all.find(q=>q.examId===examId && q.year===year && q.type==='single');state.selectedExam=examId;state.session=newSession([item],1,'年度別検証');state.session.pending=item.answer;submit(state,all);finish(state,all);
}
const restored=validateState(JSON.parse(JSON.stringify(state)),MATERIAL_INDEX);assert.deepEqual(restored.stats,state.stats);assert.equal(restored.custom.length,0);
for(const examId of ['jlpt-n1','jlpt-n2','jlpt-n3','jlpt-n4','jlpt-n5']) {
 const item=all.find(q=>q.examId===examId && q.audio?.length);assert.ok(item,examId);
 state.selectedExam=examId;state.session=newSession([item],1,'聴解検証');state.session.pending=item.answer;submit(state,all);finish(state,all);
 assert.equal(validateState(state,MATERIAL_INDEX).stats[questionKey(item)].correct,1);
 state.custom=[item];assert.deepEqual(validateState(JSON.parse(JSON.stringify(state)),MATERIAL_INDEX).custom[0].audio,item.audio);state.custom=[];
}
const edited=structuredClone(all.find(q=>q.examId==='sg'));edited.prompt='利用者の編集';state.custom=[edited];assert.equal(validateState(state,MATERIAL_INDEX).custom[0].prompt,'利用者の編集');state.custom=[];
const fixture=await authFixture();
try {
 const response=await onRequestPut({env:fixture.env,request:new Request('https://test/api/state',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:0,mutationId:'private-material-00000001',state})})});assert.equal(response.status,200,await response.text());
 const remote=await (await onRequestGet({env:fixture.env})).json();assert.equal(remote.state.stats[questionKey(q)].correct,state.stats[questionKey(q)].correct);assert.equal(remote.state.custom.length,0);
 const old={...emptyState(),exams:emptyState().exams.slice(0,4)};assert.equal(validateState(old,MATERIAL_INDEX).exams.length,state.exams.length);
} finally {fixture.restore();fixture.env.DB.sqlite.close();}
console.log(`PASS: ${all.length} private questions, all years/exams/images/hash references, index-only synchronization, old exam lists`);
