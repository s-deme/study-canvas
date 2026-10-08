import assert from 'node:assert/strict';
import {existsSync,mkdtempSync,mkdirSync,readFileSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,resolve,sep} from 'node:path';
import {createHash} from 'node:crypto';
import {loadSchoolMaterial} from '../scripts/school-material.mjs';
import {MaterialLibrary} from '../web/material.mjs';
import {emptyState,newSession,submit,finish,validateState,questionKey} from '../web/core.mjs';
const hash=b=>createHash('sha256').update(b).digest('hex');
const temporary=mkdtempSync(join(tmpdir(),'study-school-'));
try {
 assert.equal(loadSchoolMaterial(temporary).report.added,0);
 const dir=join(temporary,'private-data/school');mkdirSync(dir,{recursive:true});
 const q={id:'school-fixture',examId:'school-fixture',subject:'形式検査',category:'分類',topic:'fixture',type:'written',prompt:'検査用の入力',modelAnswer:'fixture',explanation:'検査用の説明',source:'自作 AI生成 テスト専用'};
 const raw=JSON.stringify([q]);writeFileSync(join(dir,'school-fixture.json'),raw);
 const manifest={version:1,questions:1,exams:[{id:q.examId,name:'形式検査',subjects:[q.subject]}],packs:[{id:q.id,examId:q.examId,count:1,sha256:hash(raw)}]};
 const save=m=>writeFileSync(join(dir,'high-manifest.json'),JSON.stringify(m));save(manifest);
 assert.equal(loadSchoolMaterial(temporary).report.added,1);
 assert.throws(()=>loadSchoolMaterial(temporary,[q]),/Duplicate school ID/);
 save({...manifest,packs:[{...manifest.packs[0],id:'../escape'}]});assert.throws(()=>loadSchoolMaterial(temporary));
 save(manifest);writeFileSync(join(dir,'school-fixture.json'),raw+' ');assert.throws(()=>loadSchoolMaterial(temporary));
 writeFileSync(join(dir,'school-fixture.json'),raw);
 const extra={...q,id:'school-extra-fixture',prompt:'外部形式の検査用入力',source:'External fixture',sourceUrl:'https://example.com/fixture'};
 const extraRaw=JSON.stringify([extra]);writeFileSync(join(dir,'school-extra-fixture.json'),extraRaw);
 writeFileSync(join(dir,'reference.txt'),'fixture');
 const expansion={version:1,exams:[],questions:1,files:{'reference.txt':hash('fixture')},packs:[{id:'school-extra-fixture',examId:q.examId,count:1,sha256:hash(extraRaw),license:'fixture',verification:'fixture'}]};
 const expansionRaw=JSON.stringify(expansion);writeFileSync(join(dir,'expansion-manifest.json'),expansionRaw);
 assert.throws(()=>loadSchoolMaterial(temporary),/expansion-verification/);
 const proof={manifestSha256:hash(expansionRaw),questions:1};
 writeFileSync(join(dir,'expansion-verification.json'),JSON.stringify(proof));
 assert.equal(loadSchoolMaterial(temporary).report.added,2);
 writeFileSync(join(dir,'reference.txt'),'changed');assert.throws(()=>loadSchoolMaterial(temporary),/input changed/);
 writeFileSync(join(dir,'reference.txt'),'fixture');
 writeFileSync(join(dir,'expansion-verification.json'),JSON.stringify({...proof,questions:2}));assert.throws(()=>loadSchoolMaterial(temporary));
 console.log('PASS: missing data, registration, duplicate ID, path traversal and changed pack rejection');
} finally {
 assert.ok(resolve(temporary).startsWith(resolve(tmpdir())+sep));
 assert.ok(temporary.split(/[\\/]/).at(-1).startsWith('study-school-'));
 rmSync(temporary,{recursive:true,force:true});
}

if(existsSync(new URL('../private-data/school/manifest.json',import.meta.url))) {
 const root=new URL('../',import.meta.url),{fileURLToPath}=await import('node:url');
 const loaded=loadSchoolMaterial(fileURLToPath(root)),school=loaded.packs.filter(p=>/^school-[1-9]$/.test(p.examId));
 const exams=loaded.exams.filter(e=>/^school-[1-9]$/.test(e.id));assert.equal(exams.length,9);
 const rows=school.flatMap(p=>p.rows),index=rows.map(q=>({...q,prompt:'',explanation:'',modelAnswer:'',catalogOnly:true}));
 const packs=school.map(p=>{const bytes=JSON.stringify(p.rows);return {...p,url:p.id+'.json',sha256:hash(bytes)};});
 const library=new MaterialLibrary(index,packs,async path=>new Response(JSON.stringify(school.find(p=>p.id+'.json'===path).rows)));
 const state=emptyState();state.exams.push(...exams);
 for(const exam of exams) {
  await library.load(exam.id);
  const questions=library.base.filter(q=>q.examId===exam.id);
  assert.ok(questions.every(q=>!q.catalogOnly && q.prompt && q.explanation));
  assert.deepEqual(new Set(questions.map(q=>q.subject)),new Set(exam.subjects));
  for(const subject of exam.subjects) assert.ok(questions.some(q=>q.subject===subject && q.category));
  const q=questions.find(q=>q.type==='single');assert.ok(q);
  state.selectedExam=exam.id;state.session=newSession([q],1,'検証');state.session.pending=q.answer;
  submit(state,library.base);finish(state,library.base);assert.equal(state.stats[questionKey(q)].correct,1);
 }
 assert.deepEqual(validateState(JSON.parse(JSON.stringify(state)),index).stats,state.stats);
 const {MATERIAL_PACKS,MATERIAL_INDEX}=await import('../build/private/web/catalog.mjs');
 const built=MATERIAL_PACKS.filter(p=>/^school-[1-9]$/.test(p.examId));
 if(built.length) {
  assert.equal(built.length,school.length);
  for(const pack of built) {
   const bytes=readFileSync(new URL('../build/private/web/'+pack.url,import.meta.url));assert.equal(hash(bytes),pack.sha256);
   assert.deepEqual(JSON.parse(bytes),school.find(p=>p.id===pack.id).rows);
  }
  assert.equal(MATERIAL_INDEX.filter(q=>/^school-[1-9]$/.test(q.examId)).length,rows.length);
  const baseline=JSON.parse(readFileSync(new URL('../private-data/school/baseline.json',import.meta.url)));
  for(const pack of baseline.packs) assert.deepEqual(MATERIAL_PACKS.find(p=>p.id===pack.id),pack,'Previous pack changed: '+pack.id);
  console.log(`PASS: registered ${rows.length} school questions; ${baseline.questions} prior questions and all pack metadata retained`);
 } else console.log('NOT REGISTERED: authored school packs have not been added to the running build yet');
 console.log(`PASS: ${rows.length} school questions, ${school.length} subject packs, nine grades, lazy loading, scoring and state restoration`);
}
