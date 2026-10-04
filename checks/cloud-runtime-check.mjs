// Run the compiled production Worker and D1 on Cloudflare's local runtime.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {Miniflare,convertV4MiniflareOptions} from 'miniflare';
import {fileURLToPath} from 'node:url';
import {authFixture} from './cloud-preview.mjs';
import {emptyState} from '../web/core.mjs';

const fixture=await authFixture();
const {DB,...bindings}=fixture.env;
const runtime=new Miniflare(convertV4MiniflareOptions({modules:true,scriptPath:fileURLToPath(new URL('../build/cloud/index.js',import.meta.url)),compatibilityDate:'2026-10-03',bindings,d1Databases:['DB'],
  serviceBindings:{ASSETS:()=>new Response('protected static asset')},
  outboundService:request=>{
    if (request.url!==bindings.ACCESS_DOMAIN+'/cdn-cgi/access/certs') throw new Error('Unexpected outbound request');
    return fetch(request.url);
  }
}));
try {
  const database=await runtime.getD1Database('DB');
  for (const sql of readFileSync(new URL('../schema.sql',import.meta.url),'utf8').split(';').filter(s=>s.trim())) await database.prepare(sql).run();
  const token=await fixture.token();
  const call=(path,options={})=>runtime.dispatchFetch('https://study.example'+path,{...options,headers:{'Cf-Access-Jwt-Assertion':token,...options.headers}});
  assert.equal((await runtime.dispatchFetch('https://study.example/app.mjs')).status,401);
  assert.equal((await call('/app.mjs')).status,200);
  assert.equal((await call('/api/config')).status,200);
  const first=await (await call('/api/state')).json(); assert.equal(first.revision,0);
  const state=emptyState(); state.daily['2026-10-03']=10;
  const put=id=>call('/api/state',{method:'PUT',headers:{Origin:'https://study.example','Content-Type':'application/json'},body:JSON.stringify({revision:0,mutationId:id.repeat(32),state})});
  const responses=await Promise.all([put('a'),put('b')]);
  assert.deepEqual(responses.map(r=>r.status).sort(),[200,409]);
  const saved=await (await call('/api/state')).json(); assert.equal(saved.revision,1); assert.deepEqual(saved.state,state);
  assert.equal((await call('/api/state',{method:'PUT',headers:{Origin:'https://evil.example','Content-Type':'application/json'},body:'{}'})).status,403);
  console.log('PASS: compiled production Worker, actual local D1, protected static assets, JWT, concurrent atomic writes and CSRF');
} finally { await runtime.dispose(); fixture.restore(); }
