import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {KEY,emptyState,validateQuestions,validateState,newSession,submit} from '../web/core.mjs';
import {CloudSync} from '../web/sync.mjs';
import {onRequestGet,onRequestPut} from '../functions/api/state.js';
import {onRequest as middleware} from '../functions/_middleware.js';
import {database,authFixture} from './cloud-preview.mjs';

import {questions as fixtures} from './fixtures.mjs';
const base=[];
const env={DB:database()};
const transport=async (path,options={})=>{
  const response=options.method==='PUT' ? await onRequestPut({env,request:new Request('https://study.example/api/state',options)}) : await onRequestGet({env});
  const body=await response.json();
  if (!response.ok) { const error=new Error(body.error); error.status=response.status; throw error; }
  return body;
};
function device(storage=new Map()) {
  return new CloudSync({storage:{getItem:key=>storage.get(key) ?? null,setItem:(key,value)=>storage.set(key,value)},base,owner:'owner@example.com',request:transport});
}
const save=(client,state)=>{ client.save(state,client.raw); clearTimeout(client.timer); };
const one=device(); await one.refresh(); assert.equal(one.kind,'synced');
let state=emptyState(); state.custom=validateQuestions(fixtures); state.session=newSession(state.custom,2,'途中の演習'); state.session.pending=0; submit(state,state.custom);
state.stats[state.session.ids[0]].bookmark=true;
state.custom.push(...validateQuestions(JSON.parse(readFileSync(new URL('../web/sample-questions.json',import.meta.url),'utf8')),state.custom,true));
save(one,state); await one.refresh(); assert.equal(one.meta.revision,1); assert.equal(one.meta.dirty,false);
const two=device(); await two.refresh(); assert.deepEqual(two.state,one.state);
assert.equal(two.state.session.index,0); assert.equal(two.state.session.answers[0],0);

// A stale second device cannot overwrite changes from the first device.
state=structuredClone(one.state); state.stats[state.session.ids[0]].bookmark=false;
save(one,state); await one.refresh();
const dayBefore=one.state.daily['2026-10-03'];
state=structuredClone(two.state); state.daily['2026-10-03']=55;
save(two,state); await two.refresh(); assert.equal(two.kind,'conflict');
assert.equal((await transport('/api/state')).state.daily['2026-10-03'],dayBefore);
let backup;
await two.useRemote(local=>{ backup=structuredClone(local); });
assert.equal(backup.daily['2026-10-03'],55); assert.deepEqual(two.state,one.state);

// Offline writes persist across reload, then upload after reconnecting.
const store=new Map(), offline=device(store); await offline.refresh();
offline.request=async()=>{ throw new Error('offline'); };
state=structuredClone(offline.state); state.daily['2026-10-04']=9;
save(offline,state); await offline.refresh(); assert.equal(offline.kind,'error');
const reloaded=device(store); await reloaded.refresh();
assert.equal(reloaded.state.daily['2026-10-04'],9); assert.equal(reloaded.meta.dirty,false);

// Lost acknowledgement, with a newer local edit during the upload.
reloaded.request=async (path,options)=>{
  if (options?.method==='PUT') {
    await transport(path,options);
    const newer=structuredClone(reloaded.state); newer.daily['2026-10-05']=3; save(reloaded,newer);
    throw new Error('lost response');
  }
  return transport(path,options);
};
state=structuredClone(reloaded.state); state.daily['2026-10-05']=2; save(reloaded,state);
await reloaded.refresh(); assert.ok(reloaded.meta.flightId);
const recovered=device(store); await recovered.refresh(); assert.equal(recovered.kind,'synced');
assert.equal((await transport('/api/state')).state.daily['2026-10-05'],3);

// Edits made during a successful upload remain pending, then reach the server.
recovered.request=async (path,options)=>{
  if (options?.method==='PUT') {
    const result=await transport(path,options);
    const newer=structuredClone(recovered.state); newer.daily['2026-10-06']=2; save(recovered,newer);
    return result;
  }
  return transport(path,options);
};
state=structuredClone(recovered.state); state.daily['2026-10-06']=1; save(recovered,state);
await recovered.refresh(); clearTimeout(recovered.timer); assert.equal(recovered.meta.dirty,true);
recovered.request=transport; await recovered.refresh(); assert.equal(recovered.meta.dirty,false);
assert.equal((await transport('/api/state')).state.daily['2026-10-06'],2);

// Concurrent first writes use an atomic compare-and-swap transaction.
const current=await transport('/api/state');
const puts=await Promise.allSettled(['a','b'].map(c=>transport('/api/state',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:current.revision,mutationId:c.repeat(32),state:current.state})})));
assert.equal(puts.filter(r=>r.status==='fulfilled').length,1);
assert.equal(puts.find(r=>r.status==='rejected').reason.status,409);
assert.equal((await transport('/api/state')).revision,current.revision+1);

// Validation and a database failure cannot damage the previous snapshot.
const legacyQuestion={...fixtures[0],id:'original:legacy-check'};
const legacy=emptyState(); legacy.session=newSession([legacyQuestion],1,'旧演習');
legacy.session.pending=0; submit(legacy,[legacyQuestion]);
await transport('/api/state',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:current.revision+1,mutationId:'legacy-record-0000',state:legacy})});
assert.deepEqual((await transport('/api/state')).state,legacy);
const before=await transport('/api/state');
await assert.rejects(()=>transport('/api/state',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:before.revision,mutationId:'bad-data-00000000',state:{version:9}})}),e=>e.status===400);
assert.deepEqual(await transport('/api/state'),before);
env.DB.sqlite.exec("CREATE TRIGGER reject_save BEFORE UPDATE ON sync_head BEGIN SELECT RAISE(ABORT, 'disk failure'); END;");
await assert.rejects(()=>transport('/api/state',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:before.revision,mutationId:'disk-failure-0000',state:emptyState()})}),e=>e.status===503);
assert.deepEqual(await transport('/api/state'),before);
env.DB.sqlite.exec('DROP TRIGGER reject_save');

// Imported question sets exceed the D1 single-row limit without corrupting Unicode.
const large=emptyState(); large.custom=validateQuestions(Array.from({length:2000},(_,i)=>({...fixtures[0],id:'custom:large-'+i,prompt:'😀'.repeat(990)})));
await transport('/api/state',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision:before.revision,mutationId:'large-import-00000',state:large})});
assert.deepEqual((await transport('/api/state')).state,large);
assert.ok(env.DB.sqlite.prepare('SELECT COUNT(*) AS n FROM sync_chunks').get().n>1);

// Real signed JWTs: owner only, required claims, audience, expiry and CSRF.
const fixture=await authFixture();
try {
  const call=async (token,method='GET',origin='https://study.example',claimsEnv=fixture.env)=>{
    const request=new Request('https://study.example/app.mjs',{method,headers:{...(token?{'Cf-Access-Jwt-Assertion':token}:{}),...(origin?{Origin:origin}:{})}});
    return middleware({request,env:claimsEnv,data:{},functionPath:'',waitUntil:()=>{},passThroughOnException:()=>{},next:()=>Promise.resolve(new Response('protected'))});
  };
  assert.equal((await call(null)).status,401);
  assert.equal((await call(null,'GET',null,{})).status,503);
  const valid=await fixture.token(); assert.equal((await call(valid)).status,200);
  assert.equal((await call(valid)).headers.get('Cache-Control'),'private, no-store');
  assert.equal((await call(await fixture.token({email:'other@example.com'}))).status,403);
  assert.equal((await call(valid,'PUT','https://evil.example')).status,403);
  assert.equal((await call(valid,'PUT',null)).status,403);
  for (const claims of [{aud:['wrong']},{aud:undefined},{exp:undefined},{exp:1},{iss:undefined},{nbf:Date.now()/1000+999}]) {
    assert.notEqual((await call(await fixture.token(claims))).status,200);
  }
  assert.notEqual((await call(valid.slice(0,-5)+'wrong')).status,200);
} finally { fixture.restore(); }
for (const client of [one,two,offline,reloaded,recovered]) clearTimeout(client.timer);
console.log('PASS: two-device resume, conflict backup, offline/reload, lost acknowledgements, edits during upload, atomic concurrent writes, validation/rollback, large Unicode imports, owner JWT and CSRF');
