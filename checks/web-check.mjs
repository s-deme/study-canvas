import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {CATEGORIES,KEY,validateQuestions,emptyState,newSession,makeDeck,remaining,expired,finish,submit,next,score,validateState,saveState} from '../web/core.mjs';

import {questions as fixtures} from './fixtures.mjs';
const base=validateQuestions(fixtures);
assert.equal(base.length,240);
assert.equal(new Set(base.map(q => q.prompt)).size,240);
for (let c=0;c<CATEGORIES.length;c++) assert.ok(base.filter(q => q.category===c).length>=20);
assert.deepEqual(makeDeck(base,-1),[]);
assert.equal(makeDeck(base,9999).length,240);
for (let seed=1;seed<=100;seed++) {
  let value=seed;
  const random=() => ((value=(Math.imul(value,1664525)+1013904223)>>>0)/4294967296);
  const deck=makeDeck(base,145,true,random);
  assert.equal(deck.length,145); assert.equal(new Set(deck.map(q => q.id)).size,145);
  for (let c=0;c<10;c++) assert.ok([14,15].includes(deck.filter(q => q.category===c).length));
}
assert.equal(makeDeck(base.slice(0,2),145,true).length,2);
assert.equal(remaining(1001,1000),1); assert.equal(remaining(1001,1001),0);
let state=emptyState(); state.session=newSession(base,10,'今日の10問',false,0,1000);
assert.throws(() => submit(state,base),/選択肢/);
state.session.pending=0;
const restored=validateState(JSON.parse(JSON.stringify(state)),base);
assert.deepEqual(restored.session.orders,state.session.orders); assert.equal(restored.session.pending,0);
for (const order of restored.session.orders) assert.deepEqual([...order].sort(),[0,1,2,3]);
submit(state,base,false,2000); submit(state,base,false,2000);
assert.equal(Object.values(state.stats).reduce((n,s) => n+s.attempts,0),1);
assert.equal(score(state.session,base),1);
next(state,base,3000); submit(state,base,true,4000);
assert.equal(state.session.answers[1],-2);
finish(state,base,5000); finish(state,base,6000);
assert.equal(state.history.length,1);
assert.equal(Object.values(state.stats).reduce((n,s) => n+s.attempts,0),2);
validateState(state,base);

state=emptyState(); state.session=newSession(base,20,'ミニ模試',true,15,1000);
state.session.pending=0; submit(state,base,false,2000);
assert.equal(Object.keys(state.stats).length,0); assert.equal(state.session.index,1);
assert.equal(expired(state.session,901000),true);
state.session.pending=0; submit(state,base,false,901000);
assert.equal(state.session.answers[1],-1); assert.equal(state.session.ended,true);
assert.equal(state.history[0].correct,1);
assert.equal(Object.values(state.stats).reduce((n,s) => n+s.attempts,0),20);
finish(state,base,902000); assert.equal(state.history.length,1); validateState(state,base);

state=emptyState(); state.session=newSession(base,2,'完了',true,15,1000);
for (let i=0;i<2;i++) { state.session.pending=0; submit(state,base,false,2000+i); }
assert.equal(state.session.ended,true); assert.equal(state.history[0].correct,2); validateState(state,base);

const sample=JSON.parse(readFileSync(new URL('../web/sample-questions.json',import.meta.url),'utf8'));
const custom=validateQuestions(sample,base,true);
assert.ok(custom.every(q => q.id.startsWith('custom:')));
state=emptyState(); state.custom=custom;
assert.deepEqual(validateState(JSON.parse(JSON.stringify(state)),base),state);
assert.throws(() => validateQuestions(sample,[...base,...custom],true),/重複/);
assert.throws(() => validateQuestions([{...sample[0],options:['same','same','a','b']}],base,true));
assert.throws(() => validateQuestions([{...sample[0],category:10}],base,true));
assert.throws(() => validateQuestions([{...sample[0],answer:'0'}],base,true));
assert.throws(() => validateState({...state,version:999},base));
assert.throws(() => validateState({...state,stats:{unknown:{attempts:1,correct:1,bookmark:false}}},base));
const active=emptyState(); active.session=newSession(base,2,'途中');
assert.throws(() => validateState({...active,session:{...active.session,ids:['missing']}},base));
assert.throws(() => validateState({...active,session:{...active.session,orders:[[0,0,2,3],[0,1,2,3]]}},base));
assert.throws(() => validateState({...active,session:{...active.session,index:1}},base));

let raw=null;
const storage={getItem:key => { assert.equal(key,KEY); return raw; },setItem:(key,value) => { assert.equal(key,KEY); raw=value; }};
const serialized=saveState(storage,state,null);
assert.equal(raw,serialized); assert.deepEqual(validateState(JSON.parse(raw),base),state);
assert.throws(() => saveState(storage,emptyState(),null),/別のタブ/);
const before=raw;
assert.throws(() => saveState({...storage,setItem:() => { throw new Error('quota'); }},emptyState(),before),/保存できません/);
assert.equal(raw,before);

// A clean installation needs no bundled material and imports through the normal path.
assert.deepEqual(validateState(emptyState(),[]),emptyState());
assert.throws(()=>newSession([],10,'未登録'),/対象の問題/);
assert.throws(()=>validateQuestions([],[],true));
const portable=emptyState(); portable.custom=validateQuestions(sample,[],true);
portable.session=newSession(portable.custom,10,'持込演習'); portable.session.pending=0;
submit(portable,portable.custom); finish(portable,portable.custom);
assert.equal(portable.history[0].correct,1);
assert.deepEqual(validateState(JSON.parse(JSON.stringify(portable)),[]),portable);

// Old records remain recoverable without distributing their question text.
const legacyQuestion={...base[0],id:'original:legacy-check'};
const legacy=emptyState(); legacy.session=newSession([legacyQuestion],1,'旧演習');
legacy.session.pending=0; submit(legacy,[legacyQuestion]);
const legacyRaw=JSON.stringify(legacy);
assert.deepEqual(validateState(JSON.parse(legacyRaw),[]),legacy);
legacy.custom=validateQuestions([legacyQuestion],[],true);
assert.equal(legacy.custom[0].id,legacyQuestion.id);
assert.equal(score(legacy.session,legacy.custom),1);
assert.equal(legacy.stats[legacyQuestion.id].attempts,1);
assert.deepEqual(validateState(legacy,[]),legacy);
assert.throws(()=>validateQuestions([legacyQuestion],legacy.custom,true),/重複/);
console.log('PASS: 240 synthetic fixtures, 100 balanced mock draws, resume, grading, skip, expiry, backup validation, atomic save and tab conflict');
