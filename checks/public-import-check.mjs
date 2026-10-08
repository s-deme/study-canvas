import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {loadGithubMaterial} from '../scripts/github-material.mjs';
import {validateQuestions,emptyState,newSession,submit,questionKey} from '../web/core.mjs';

const root=fileURLToPath(new URL('../',import.meta.url));
const read=path=>JSON.parse(readFileSync(new URL('../'+path,import.meta.url)));
const before=read('private-data/github-material/welfare-baseline.json'),after=read('build/private/manifest.json');
const built=new Map(after.packs.map(p=>[p.id,p])),all=[];
for(const kind of ['welfare','public-examples']) {
 const loaded=loadGithubMaterial(root,[],kind+'-report.json',kind+'-verification.json');
 for(const p of loaded.packs) {
  assert.deepEqual(validateQuestions(read('build/private/web/'+built.get(p.id).url)),p.rows,'Built rows must match verified sources');
  all.push(...p.rows);
 }
}
assert.equal(all.length,1221);
const examIds=new Set(all.map(q=>q.examId));assert.equal(examIds.size,12);
for(const id of examIds) assert.equal(before.packs.filter(p=>p.examId===id).length,0);
assert.equal(after.questions,before.questions+all.length);
for(const p of before.packs) assert.deepEqual(built.get(p.id),p);
for(const q of all) {
 const state=emptyState();state.selectedExam=q.examId;state.session=newSession([q],1,'追加教材検査');
 state.session.pending=q.type==='written'?q.modelAnswer:q.answer;
 submit(state,[q]);
 if(q.type!=='written') assert.equal(state.stats[questionKey(q)].correct,1);
 else assert.equal(state.session.answers[0].text,q.modelAnswer);
}
console.log('PASS: 12 previously empty exams, 1221 source-matched questions, grading/submission and all previous packs preserved');
