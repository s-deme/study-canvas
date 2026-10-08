import assert from 'node:assert/strict';
import {mkdtempSync,readFileSync,writeFileSync,mkdirSync,rmSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {MaterialLibrary} from '../web/material.mjs';
import {writeLibraryCatalog} from '../scripts/library-catalog.mjs';
import {emptyState,newSession,validateState,questionKey,indexQuestions,questionIndex} from '../web/core.mjs';
import {CloudSync} from '../web/sync.mjs';

const root=resolve('build');mkdirSync(root,{recursive:true});const dir=mkdtempSync(join(root,'staged-check-'));
assert.ok(dir.startsWith(root));
try {
  mkdirSync(join(dir,'material'));
  const packs=[],index=[],rows=[];
  for(let i=0;i<6;i++) {
    const examId=i<5?'sg':'fe',q={id:'stage-'+i,examId,type:'single',options:['a','b'],answer:0,prompt:'Synthetic fixture',category:'基礎',year:String(2020+i),subject:'科目A'};
    rows.push(q);const url=`material/p${i}.json`,raw=JSON.stringify([q]);writeFileSync(join(dir,url),raw);
    packs.push({examId,url,count:1,sha256:createHash('sha256').update(raw).digest('hex')});
    index.push({id:q.id,examId,type:q.type,options:['0','1'],catalogOnly:true,year:q.year,subject:q.subject});
  }
  writeLibraryCatalog(dir,index,packs,[]);
  const {MATERIAL_MANIFESTS}=await import(pathToFileURL(join(dir,'library-catalog.mjs')));
  let calls=[],active=0,peak=0,fail='';
  const request=async url=>{calls.push(url);active++;peak=Math.max(peak,active);await new Promise(ok=>setTimeout(ok,5));active--;return url===fail?new Response('',{status:503}):new Response(readFileSync(join(dir,url),'utf8'));};
  const library=new MaterialLibrary([],[],request,MATERIAL_MANIFESTS);
  assert.equal(library.base.length,0);assert.deepEqual({...library.counts()},{sg:5,fe:1});
  await Promise.all([library.loadIndex('sg'),library.loadIndex('sg')]);assert.equal(calls.length,1);assert.equal(library.base.length,5);
  await library.load('sg',{year:'2020'});assert.equal(calls.length,2);assert.equal(library.loaded.has('sg'),false);
  assert.equal(library.base.filter(q=>!q.catalogOnly).length,1);
  const state=emptyState();state.selectedExam='sg';state.session=newSession([rows[0]],1,'保存');state.session.pending=1;
  assert.equal(validateState(state,library.base).session.pending,1);
  fail='material/p2.json';await assert.rejects(library.load('sg'));assert.equal(library.loaded.has('sg'),false);
  const before=calls.length;fail='';await library.load('sg');assert.deepEqual(calls.slice(before),['material/p2.json']);assert.ok(peak<=4);
  assert.equal(library.loaded.has('sg'),true);
  const reopened=new MaterialLibrary([],[],request,MATERIAL_MANIFESTS);await reopened.prepareState(state);
  assert.equal(reopened.base.length,5);assert.ok(reopened.base.every(q=>q.catalogOnly));assert.equal(validateState(state,reopened.base).session.pending,1);
  state.custom=[{...rows[0],prompt:'Edited'}];assert.equal(reopened.counts(state.custom).sg,5);
  assert.equal(validateState(state,reopened.base).custom[0].prompt,'Edited');
  assert.throws(()=>validateState({...state,stats:{'sg::absent':{attempts:0,correct:0,bookmark:true}}},reopened.base));
  const map=questionIndex(reopened.base);validateState(state,reopened.base);assert.equal(questionIndex(reopened.base),map);
  reopened.base.push({...index[5]});indexQuestions(reopened.base);assert.notEqual(questionIndex(reopened.base),map);
  const tampered=new MaterialLibrary([],[],async url=>new Response(readFileSync(join(dir,url),'utf8')+' '),MATERIAL_MANIFESTS);
  await assert.rejects(tampered.loadIndex('sg'),/更新/);assert.equal(tampered.base.length,0);
  // Remote records hydrate their own exam before validation, without fetching bodies.
  const remoteState=emptyState();remoteState.selectedExam='fe';remoteState.session=newSession([rows[5]],1,'別端末');remoteState.session.pending=0;
  const cloudLibrary=new MaterialLibrary([],[],request,MATERIAL_MANIFESTS);let raw=null;
  const sync=new CloudSync({base:cloudLibrary.base,storage:{getItem:()=>raw,setItem:(_,v)=>raw=v},owner:'fixture',prepare:s=>cloudLibrary.prepareState(s),request:async()=>({revision:1,mutationId:null,state:remoteState})});
  await sync.refresh();assert.equal(sync.kind,'synced');assert.deepEqual(sync.state.session,remoteState.session);assert.ok(cloudLibrary.base.every(q=>q.catalogOnly));
  assert.equal(questionKey(cloudLibrary.base[0]),'fe::stage-5');
  console.log('PASS: split indexes, selected pack loading, four-request bound, retry, integrity, cached validation, edit counts, old-session and remote-state hydration');
} finally {rmSync(dir,{recursive:true,force:true});}
