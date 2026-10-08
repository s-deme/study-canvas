import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {loadSchoolMaterial} from '../scripts/school-material.mjs';
import {MaterialLibrary} from '../web/material.mjs';
import {questionKey,newSession,emptyState,submit,selfEvaluate,validateState} from '../web/core.mjs';

const root=fileURLToPath(new URL('../',import.meta.url));
const school=loadSchoolMaterial(root);
assert.ok(school.packs.length && school.report.added);
const rows=school.packs.flatMap(p=>p.rows);
assert.throws(()=>loadSchoolMaterial(root,[rows[0]]),/Duplicate school ID/);
const high=school.exams.filter(e=>e.id.startsWith('school-high-'));
assert.equal(high.length,3);
for(const e of high) for(const subject of e.subjects) assert.ok(rows.some(q=>q.examId===e.id && q.subject===subject));
if(process.argv.includes('--built')) {
  const catalog=await import(pathToFileURL(join(root,'build/private/web/catalog.mjs')));
  const {MATERIAL_INDEX:index,MATERIAL_PACKS:packs,MATERIAL_EXAMS:exams}=catalog;
  const library=new MaterialLibrary(index,packs,async path=>new Response(readFileSync(join(root,'build/private/web',path))));
  for(const exam of high) {
    assert.deepEqual(exams.find(e=>e.id===exam.id),exam);
    await library.load(exam.id);
    const actual=library.base.filter(q=>q.examId===exam.id);
    assert.deepEqual(new Map(actual.map(q=>[questionKey(q),q])),new Map(rows.filter(q=>q.examId===exam.id).map(q=>[questionKey(q),q])));
    for(const subject of exam.subjects) {
      const pool=actual.filter(q=>q.subject===subject);
      assert.ok(pool.length && pool.every(q=>(q.modelAnswer || q.type==='single') && q.explanation && q.topic));
      const session=newSession(pool.filter(q=>q.type==='written'),1,subject);
      assert.equal(session.examId,exam.id);
      const state=emptyState();
      state.exams.push(exam);state.selectedExam=exam.id;state.session=session;
      session.pending='確認用の記述回答';submit(state,pool);
      selfEvaluate(state,pool,'done');
      assert.equal(state.stats[session.ids[0]].self.done,1);
      const restored=validateState(JSON.parse(JSON.stringify(state)),actual);
      assert.equal(restored.stats[session.ids[0]].self.done,1);
    }
  }
  const baselinePath=join(root,'private-data/school/high-baseline.json');
  if(existsSync(baselinePath)) for(const p of JSON.parse(readFileSync(baselinePath)).packs) {
    assert.deepEqual(packs.find(q=>q.id===p.id),p,'Previous pack metadata changed');
    const bytes=readFileSync(join(root,'build/private/web',p.url));
    assert.equal(createHash('sha256').update(bytes).digest('hex'),p.sha256,'Previous pack content changed');
  }
}
console.log(`PASS: school classification, duplicate rejection${process.argv.includes('--built')?', lazy loading, sessions and previous pack preservation':''}: ${school.report.added} questions`);
