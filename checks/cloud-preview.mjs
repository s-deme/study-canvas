// Loopback-only test harness: real SQLite and JWT validation, no cloud account.
import {DatabaseSync} from 'node:sqlite';
import {createServer} from 'node:http';
import {readFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import {onRequest as middleware} from '../functions/_middleware.js';
import {onRequestGet as config} from '../functions/api/config.js';
import {onRequestGet,onRequestPut} from '../functions/api/state.js';

export function database() {
  const sqlite=new DatabaseSync(':memory:');
  sqlite.exec(readFileSync(new URL('../schema.sql',import.meta.url),'utf8'));
  return {
    sqlite,
    prepare(sql) { return {sql,args:[],bind(...args) { return {...this,args}; }}; },
    async batch(statements) {
      sqlite.exec('BEGIN');
      try {
        const results=statements.map(({sql,args})=>{
          const stmt=sqlite.prepare(sql);
          if (stmt.columns().length) return {results:stmt.all(...args),meta:{changes:0}};
          return {results:[],meta:{changes:Number(stmt.run(...args).changes)}};
        });
        sqlite.exec('COMMIT'); return results;
      } catch (error) { sqlite.exec('ROLLBACK'); throw error; }
    }
  };
}
export async function authFixture() {
  const pair=await crypto.subtle.generateKey({name:'RSASSA-PKCS1-v1_5',modulusLength:2048,publicExponent:new Uint8Array([1,0,1]),hash:'SHA-256'},true,['sign','verify']);
  const jwk={...await crypto.subtle.exportKey('jwk',pair.publicKey),kid:'local-test',alg:'RS256'};
  const env={DB:database(),OWNER_EMAIL:'owner@example.com',ACCESS_DOMAIN:'https://study-canvas-test.cloudflareaccess.com',ACCESS_AUD:'local-audience'};
  const realFetch=globalThis.fetch;
  globalThis.fetch=(url,options)=>String(url)===env.ACCESS_DOMAIN+'/cdn-cgi/access/certs' ? Promise.resolve(Response.json({keys:[jwk]})) : realFetch(url,options);
  return {env,restore:()=>{ globalThis.fetch=realFetch; }, async token(claims={}) {
    const encode=value=>Buffer.from(JSON.stringify(value)).toString('base64url');
    const data=encode({alg:'RS256',kid:jwk.kid})+'.'+encode({email:env.OWNER_EMAIL,iss:env.ACCESS_DOMAIN,aud:[env.ACCESS_AUD],exp:Math.floor(Date.now()/1000)+3600,...claims});
    const signature=await crypto.subtle.sign('RSASSA-PKCS1-v1_5',pair.privateKey,new TextEncoder().encode(data));
    return data+'.'+Buffer.from(signature).toString('base64url');
  }};
}
export async function servePreview(port=8767,{webRoot=new URL('../web/',import.meta.url),getState=onRequestGet,putState=onRequestPut,assetHandler=null}={}) {
  const fixture=await authFixture(), token=await fixture.token();
  fixture.env.ASSETS={fetch:async request=>{
    const path=new URL(request.url || request).pathname.slice(1);
    if(path.includes('..') || !/^(?:[a-zA-Z0-9_-]+\/)*[a-zA-Z0-9_.-]+$/.test(path)) return new Response('',{status:404});
    try {return new Response(readFileSync(new URL(path,webRoot)));} catch {return new Response('',{status:404});}
  }};
  const server=createServer(async (req,res)=>{
    try {
      const origin=`http://127.0.0.1:${server.address().port}`, url=new URL(req.url,origin);
      const parts=[]; for await (const part of req) parts.push(part);
      const headers=new Headers(req.headers); headers.set('Cf-Access-Jwt-Assertion',token);
      const request=new Request(url,{method:req.method,headers,...(!['GET','HEAD'].includes(req.method)?{body:Buffer.concat(parts)}:{})});
      const context={env:fixture.env,data:{},request,functionPath:'',waitUntil:()=>{},passThroughOnException:()=>{},next:async () => {
        if (url.pathname==='/api/config') return config(context);
        if (url.pathname==='/api/state') return req.method==='PUT'?putState(context):getState(context);
        if (assetHandler && url.pathname.startsWith('/assets/')) return assetHandler(context);
        const path=url.pathname==='/'?'index.html':url.pathname.slice(1);
        // Serve only flat, known web assets. Nothing outside web/ is reachable.
        if (path.includes('..') || !/^(?:[a-zA-Z0-9_-]+\/)*[a-zA-Z0-9_.-]+\.(html|css|mjs|json|csv|png|webp|mp3)$/.test(path)) return new Response('Not found',{status:404});
        try {
          const types={html:'text/html; charset=utf-8',css:'text/css; charset=utf-8',mjs:'text/javascript; charset=utf-8',json:'application/json',csv:'text/csv; charset=utf-8',png:'image/png',webp:'image/webp',mp3:'audio/mpeg'};
          return new Response(readFileSync(new URL(path,webRoot)),{headers:{'Content-Type':types[path.split('.').at(-1)]}});
        } catch { return new Response('Not found',{status:404}); }
      }};
      const response=await middleware(context);
      res.writeHead(response.status,Object.fromEntries(response.headers)); res.end(Buffer.from(await response.arrayBuffer()));
    } catch (error) { res.writeHead(500); res.end(error.message); }
  });
  await new Promise(resolve=>server.listen(port,'127.0.0.1',resolve));
  return {server,fixture};
}
if (process.argv[1]===fileURLToPath(import.meta.url)) {
  const {server}=await servePreview(); console.log(`Local authenticated sync preview: http://127.0.0.1:${server.address().port}`);
}
