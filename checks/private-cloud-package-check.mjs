import assert from 'node:assert/strict';
import {CompactQuestionIndex,bundledAsset} from '../scripts/cloud-runtime.mjs';
import {emptyState,validateState,newSession} from '../web/core.mjs';
import {uploadBatches} from '../scripts/upload-private-cloud.mjs';
assert.deepEqual(uploadBatches([2,3,4,7].map(size=>({size})),7).map(b=>b.map(f=>f.size)),[[2,3],[4],[7]]);
assert.deepEqual(uploadBatches([],7),[]);assert.throws(()=>uploadBatches([{size:8}],7));
const q={id:'fixture',examId:'sg',type:'single',options:['a','b'],answer:0};
const state=emptyState();state.selectedExam='sg';state.session=newSession([q],1,'test');state.session.pending=1;
const compact=new CompactQuestionIndex([['sg::fixture',2],['legacy',4],['fe::multiple',35],['fe::written',64],['fe::essay',96]]);
assert.deepEqual(validateState(state,compact),validateState(state,[q]));
assert.equal(compact.get('legacy').examId,'gken');assert.equal(compact.get('fe::multiple').type,'multiple');
assert.equal(compact.get('fe::written').options.length,0);assert.equal(compact.get('fe::essay').type,'essay');
state.session.pending=2;assert.throws(()=>validateState(state,compact));
state.session.ids=['sg::missing'];assert.throws(()=>validateState(state,compact));
const path='assets/test/a.png',payload=new Uint8Array([9,8,1,2,3,4,7]);
let honorRange=false,missing=false;
const env={ASSETS:{async fetch(req) {
  const url=new URL(typeof req==='string'?req:req.url || req);
  if(url.pathname.startsWith('/bundles/index-')) return Response.json({[path]:['bundles/0.bin',2,4,'image/png']});
  if(url.pathname==='/bundles/0.bin') {
    if(missing) return new Response('',{status:404});
    if(honorRange) {const [,start,end]=/bytes=(\d+)-(\d+)/.exec(req.headers.get('Range'));return new Response(payload.slice(+start,+end+1),{status:206});}
    return new Response(payload);
  }
  return new Response('',{status:404});
}}};
const call=(headers={},method='GET',file=path)=>bundledAsset({env,request:new Request('https://test/'+file,{headers,method})});
for(honorRange of [false,true]) {
  let r=await call();assert.equal(r.status,200);assert.deepEqual([...new Uint8Array(await r.arrayBuffer())],[1,2,3,4]);
  r=await call({Range:'bytes=1-2'});assert.equal(r.status,206);assert.equal(r.headers.get('Content-Range'),'bytes 1-2/4');assert.deepEqual([...new Uint8Array(await r.arrayBuffer())],[2,3]);
  r=await call({Range:'bytes=-2'});assert.deepEqual([...new Uint8Array(await r.arrayBuffer())],[3,4]);
}
assert.equal((await call({Range:'bytes=4-'})).status,416);
assert.equal((await call({Range:'bytes=0-1,2-3'})).status,416);
assert.equal((await call({},'HEAD')).headers.get('Content-Length'),'4');
assert.equal((await call({},'POST')).status,405);
assert.equal((await call({},'GET','assets/no.png')).status,404);
missing=true;assert.equal((await call()).status,503);
console.log('PASS: compact state validation, unknown IDs, image bytes, Range/HEAD, missing bundles and methods');
