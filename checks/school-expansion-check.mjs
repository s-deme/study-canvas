import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {loadSchoolMaterial} from '../scripts/school-material.mjs';
import {MaterialLibrary} from '../web/material.mjs';
import {emptyState,newSession,submit,selfEvaluate,validateState,questionKey} from '../web/core.mjs';

const root=fileURLToPath(new URL('../',import.meta.url));
const dir=join(root,'private-data/school');
if(!existsSync(join(dir,'expansion-manifest.json'))) {
  console.log('SKIP: optional local school expansion is not present');
} else {
  const read=name=>JSON.parse(readFileSync(join(dir,name)));
  const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
  const school=loadSchoolMaterial(root),added=school.packs.filter(p=>p.id.startsWith('school-extra-'));
  const report=read('expansion-report.json'),verification=read('expansion-verification.json');
  assert.equal(added.reduce((n,p)=>n+p.count,0),report.questions);
  assert.equal(report.numeric,verification.originalAnswersChecked);
  assert.equal(verification.externalAligned+verification.originalAnswersChecked,report.questions);
  assert.equal(verification.externalAnswersIndependentlyVerified,false);
  const prompts=new Set(),ids=new Set();
  const normalize=s=>s.normalize('NFKC').replace(/\s+/g,'');
  for(const p of school.packs.filter(p=>!p.id.startsWith('school-extra-'))) for(const q of p.rows) prompts.add(normalize(q.prompt));
  for(const p of added) for(const q of p.rows) {
    assert.ok(!ids.has(questionKey(q)));ids.add(questionKey(q));
    assert.ok(!prompts.has(normalize(q.prompt)));prompts.add(normalize(q.prompt));
    assert.equal(p.localOnly,true);
    if(p.origin!=='original') assert.ok(q.source.includes('正答未独立照合'));
  }
  assert.equal(new Set(added.map(p=>p.examId)).size,12);
  if(process.argv.includes('--built')) {
    const out=join(root,'build/private');
    const {MATERIAL_INDEX:index,MATERIAL_PACKS:packs,MATERIAL_EXAMS:exams}=await import(pathToFileURL(join(out,'web/catalog.mjs')));
    const manifest=JSON.parse(readFileSync(join(out,'manifest.json')));
    assert.equal(manifest.questions,index.length);assert.deepEqual(manifest.packs,packs);
    for(const p of read('expansion-baseline.json').packs) {
      assert.deepEqual(packs.find(x=>x.id===p.id),p,'Previous pack metadata changed');
      assert.equal(hash(readFileSync(join(out,'web',p.url))),p.sha256,'Previous pack content changed');
    }
    for(const p of added) {
      const built=packs.find(x=>x.id===p.id);assert.ok(built);
      const bytes=readFileSync(join(out,'web',built.url));assert.equal(hash(bytes),built.sha256);
      assert.deepEqual(JSON.parse(bytes),p.rows);
    }
    // Exercise one of every new source/type combination in each grade.
    const library=new MaterialLibrary(index,packs,async path=>new Response(readFileSync(join(out,'web',path))));
    let sessions=0;
    for(const exam of school.exams) {
      await library.load(exam.id);
      const choices=new Map();
      for(const p of added.filter(p=>p.examId===exam.id)) choices.set(p.origin+'::'+p.rows[0].type,p.rows[0]);
      for(const q of choices.values()) {
        const state=emptyState();state.exams.push(exam);state.selectedExam=exam.id;
        state.session=newSession([q],1,'追加教材の検査');
        state.session.pending=q.type==='single'?q.answer:q.modelAnswer;
        submit(state,library.base);
        if(q.type==='written') selfEvaluate(state,library.base,'done');
        assert.equal(q.type==='single'?state.stats[questionKey(q)].correct:state.stats[questionKey(q)].self.done,1);
        assert.deepEqual(validateState(JSON.parse(JSON.stringify(state)),index).stats,state.stats);
        sessions++;
      }
      assert.equal(library.base.filter(q=>q.examId===exam.id).length,manifest.exams.find(e=>e.id===exam.id).count);
    }
    console.log(`PASS: ${sessions} new-source sessions, twelve grades, lazy loading, scoring, self assessment, restore, existing packs unchanged`);
  }
  console.log(`PASS: ${report.questions} added questions, provenance, numeric evidence, global prompt deduplication`);
}
