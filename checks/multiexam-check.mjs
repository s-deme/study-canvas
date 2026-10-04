import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {emptyState,validateQuestions,validateState,validateExam,questionKey,allQuestions,newSession,submit,next,selfEvaluate,finish,correctAnswer,sessionSummary,parseCSV,previewImport,record,saveState,KEY} from '../web/core.mjs';
import {BUILTIN_QUESTIONS} from '../web/catalog.mjs';
import {richText} from '../web/render.mjs';
const make=(examId,id,type='single')=>validateQuestions([{id,examId,type,prompt:'問題',category:'任意の分野',options:['A','B','C'],answer:type==='multiple'?[0,2]:0,modelAnswer:'模範解答',source:'チェック用'}])[0];
let s=emptyState();s.exams.push(validateExam({id:'language',name:'語学',field:'語学'}));
const a=make('gken','same'),b=make('language','same'),m=make('language','multi','multiple'),w=make('language','written','written'),e=make('language','essay','essay');
s.custom=[a,b,m,w,e];
assert.deepEqual(BUILTIN_QUESTIONS,[]);assert.equal(allQuestions(BUILTIN_QUESTIONS,emptyState()).length,0);
assert.equal(allQuestions(BUILTIN_QUESTIONS,s).length,5);
assert.notEqual(questionKey(a),questionKey(b));
record(s,a,0,1000);record(s,b,1,1000);
assert.equal(s.stats.same.correct,1);assert.equal(s.stats['language::same'].correct,0);
assert.equal(Object.keys(s.daily).length,2);
assert.throws(()=>newSession([a,b],2,'混在'),/異なる試験/);
assert.equal(correctAnswer(m,[2,0]),true);assert.equal(correctAnswer(m,[0]),false);assert.equal(correctAnswer(m,[0,2,2]),false);assert.equal(correctAnswer(m,[0,1,2]),false);
for(const q of [m,w,e]) {
  s.session=newSession([q],1,q.type);
  s.session.pending=q.type==='multiple'?[2,0]:'自分の回答';submit(s,s.custom,false,2000);
  if(q.type!=='multiple') {
    assert.equal(s.stats[questionKey(q)],undefined);
    assert.throws(()=>next(s,s.custom),/自己評価/);
    assert.throws(()=>finish(s,s.custom),/自己評価/);
    // An unrated submitted answer survives a backup round trip.
    assert.deepEqual(validateState(JSON.parse(JSON.stringify(s)),BUILTIN_QUESTIONS),s);
    selfEvaluate(s,s.custom,'partial',3000);
    assert.throws(()=>selfEvaluate(s,s.custom,'done'),/自己評価/);
    assert.equal(s.stats[questionKey(q)].correct,0);assert.equal(s.stats[questionKey(q)].gradedAttempts,0);
  }
  next(s,s.custom,4000);assert.equal(s.session.ended,true);
}
assert.equal(s.history.length,3);
assert.equal(s.history[0].correct,1);assert.equal(s.history[1].gradedTotal,0);assert.equal(s.history[1].self.partial,1);
assert.deepEqual(validateState(JSON.parse(JSON.stringify(s)),BUILTIN_QUESTIONS),s);
// Histories for one exam do not evict another exam's recent sessions.
s.history=[];
for(let i=0;i<35;i++) {s.session=newSession([a],1,'G検');s.session.pending=0;submit(s,s.custom);next(s,s.custom);}
for(let i=0;i<35;i++) {s.session=newSession([b],1,'語学');s.session.pending=0;submit(s,s.custom);next(s,s.custom);}
assert.equal(s.history.filter(h=>h.examId==='gken').length,30);assert.equal(s.history.filter(h=>h.examId==='language').length,30);
// Literal v1 input, with an unavailable original question and pending selection.
const legacy={version:1,custom:[{id:'custom:old',category:0,topic:'旧問題',prompt:'旧問題文',options:['A','B','C','D'],answer:0,explanation:'旧解説',source:'旧出典'}],stats:{'original:missing':{attempts:2,correct:1,bookmark:true,lastCorrect:false,lastAt:1000}},daily:{'2026-10-03':2},history:[{title:'旧演習',correct:1,total:2,at:1000}],session:{ids:['original:missing'],answers:[-1],orders:[[3,2,1,0]],index:0,pending:2,title:'旧演習',mock:false,deadline:0,ended:false}};
const original=JSON.stringify(legacy),migrated=validateState(legacy,BUILTIN_QUESTIONS);
assert.equal(JSON.stringify(legacy),original);assert.equal(migrated.version,2);assert.equal(migrated.selectedExam,'gken');assert.equal(migrated.custom[0].id,'custom:old');assert.equal(migrated.session.pending,2);
assert.throws(()=>validateState({...migrated,session:{...migrated.session,examId:'fe'}},BUILTIN_QUESTIONS),/試験/);
assert.deepEqual(migrated.stats,legacy.stats);assert.deepEqual(migrated.daily,legacy.daily);assert.equal(migrated.history[0].examId,'gken');assert.deepEqual(validateState(migrated,BUILTIN_QUESTIONS),migrated);
const sample=JSON.parse(readFileSync(new URL('../web/sample-questions-v2.json',import.meta.url),'utf8'));
const imported=previewImport(sample,[],'language');assert.equal(imported[0].passage,imported[1].passage);
assert.ok(richText(imported[0].passage).includes('<table>'));
assert.throws(()=>previewImport(sample,imported,'language'),/重複/);
assert.throws(()=>previewImport({...sample,questions:[...sample.questions,{...sample.questions[0],id:'invalid',answer:99}]},[],'language'),/3問目/);
assert.throws(()=>previewImport([{...a,examId:'fe'}],[],'language'),/試験ID/);
const csv=readFileSync(new URL('../web/sample-questions.csv',import.meta.url),'utf8');const csvQuestions=previewImport(csv,[],'language');assert.deepEqual(csvQuestions[0].answer,[0,2]);assert.ok(csvQuestions[0].prompt.includes('\n'));
assert.equal(parseCSV('id,prompt\r\n1,"日本語,改行\n""引用"""')[0].prompt,'日本語,改行\n"引用"');
assert.throws(()=>parseCSV('id,prompt\n1,"未終了'),/引用符/);assert.throws(()=>parseCSV('id,prompt\n1,"a"x'),/引用符/);assert.throws(()=>parseCSV('id,prompt\n1,2,3'),/列数/);
assert.throws(()=>validateQuestions([{...b,id:'__proto__'}]),/ID/);
assert.throws(()=>validateQuestions([{...b,id:'toString'}]),/ID/);
assert.throws(()=>validateExam({id:'toString',name:'不正な試験'}),/ID/);
assert.throws(()=>validateQuestions([{...b,images:[{src:'javascript:alert(1)',alt:'危険'}]}]),/URL/);
assert.throws(()=>validateQuestions([{...b,images:[{src:'assets/../../private-data/a.png',alt:'危険'}]}]),/URL/);
assert.ok(!richText('<img src=x onerror=alert(1)>').includes('<img'));
assert.ok(richText('```js\n<x>\n```').includes('&lt;x&gt;'));
// Existing records remain usable when their built-in question is no longer shipped.
for(const [examId,id,type] of [['sg','2026r08_sg-q14','single'],['fe','2026r08_fe_kamoku_b-q06','single'],['boki3','boki3-original-19','multiple'],['boki3','boki3-original-20','essay']]) {
  const q=make(examId,id,type),old=emptyState();old.selectedExam=examId;
  old.session=newSession([q],1,'以前の教材');old.session.pending=type==='single'?2:type==='multiple'?[0,2]:'以前の記述回答';
  submit(old,[q],false,2000);if(type==='essay') selfEvaluate(old,[q],'partial',3000);
  assert.deepEqual(validateState(old,[]),old);
  assert.throws(()=>validateState({...old,session:{...old.session,examId:'gken'}},[]),/試験/);
  const restored=previewImport([q],[] ,examId);assert.deepEqual(validateState({...old,custom:restored},[]).stats,old.stats);
}
console.log('PASS: empty initial catalog, user question registration, exam isolation, multi-select, self assessment, migrations, CSV/JSON, safe rich text and retired catalog records');
