import assert from 'node:assert/strict';
import {MaterialLibrary} from '../web/material.mjs';
import {emptyState,validateState,newSession,finish,questionKey} from '../web/core.mjs';
import {materialFingerprint} from '../scripts/additional-material.mjs';

// Synthetic fixtures measure capacity only; never count these as learning material.
const rows=Array.from({length:12000},(_,i)=>({id:'capacity-'+i,examId:'sg',type:'single',prompt:'capacity fixture '+i,options:['A','B'],answer:0}));
const index=rows.map(({id,examId,type,options})=>({id,examId,type,options,catalogOnly:true}));
const packs=Array.from({length:6},(_,i)=>({id:'p'+i,examId:'sg',url:String(i),count:2000}));
let calls=0;
const library=new MaterialLibrary(index,packs,async url=>{calls++;return Response.json(rows.slice(Number(url)*2000,(Number(url)+1)*2000));});
await Promise.all([library.load('sg'),library.load('sg')]);
assert.equal(calls,6);assert.equal(library.base.length,12000);assert.ok(library.base.every(q=>!q.catalogOnly));
const state=emptyState();state.selectedExam='sg';state.session=newSession(library.base,12000,'容量検証');
assert.equal(validateState(state,index).session.ids.length,12000);
finish(state,library.base);
assert.equal(validateState(JSON.parse(JSON.stringify(state)),index).history[0].total,12000);
const invalid=structuredClone(state);invalid.session.ids[1]=invalid.session.ids[0];assert.throws(()=>validateState(invalid,index),/演習の問題/);
assert.throws(()=>validateState({...state,custom:rows.slice(0,2001)},index),/バックアップ/);
assert.equal(new Set(library.base.map(questionKey)).size,12000);
assert.equal(materialFingerprint({prompt:'問1 価格100円の品物',options:['20','40']}),materialFingerprint({prompt:'問９　価格200円の品物',options:['80','60']}));
assert.notEqual(materialFingerprint({prompt:'面積を求める',options:[]}),materialFingerprint({prompt:'体積を求める',options:[]}));
console.log('PASS: 12,000-question loading, in-flight deduplication, resume/history restoration; custom limit preserved; conservative numeric-variant deduplication');
