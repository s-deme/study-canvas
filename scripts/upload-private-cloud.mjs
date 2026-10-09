import assert from 'node:assert/strict';
import {existsSync,linkSync,mkdirSync,readFileSync,readdirSync,statSync,writeFileSync} from 'node:fs';
import {dirname,join,relative,resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {spawnSync} from 'node:child_process';

export function uploadBatches(files,limit=128*1024*1024) {
  const batches=[];let current=[],bytes=0;
  for(const file of files) {
    assert.ok(Number.isSafeInteger(file.size) && file.size>=0 && file.size<=limit);
    if(bytes+file.size>limit) {batches.push(current);current=[];bytes=0;}
    current.push(file);bytes+=file.size;
  }
  if(current.length) batches.push(current);
  return batches;
}

async function main(directory) {
  const root=resolve('.');directory=resolve(directory);
  assert.ok(!relative(join(root,'build/private-cloud'),directory).startsWith('..'));
  const config=JSON.parse(readFileSync(join(directory,'wrangler.jsonc'))),web=join(directory,'web');
  const cli=join(root,'node_modules/wrangler/bin/wrangler.js');
  const list=()=>{
    const r=spawnSync(process.execPath,[cli,'pages','deployment','list','--project-name',config.name,'--json'],{cwd:directory,encoding:'utf8'});
    assert.equal(r.status,0,'Cloudflare login or project lookup failed');return JSON.parse(r.stdout);
  };
  const deployments=list(),account=new URL(deployments[0].Build).pathname.split('/')[1];
  assert.match(account,/^[a-f0-9]{32}$/);
  async function api(path,token,body) {
    const response=await fetch('https://api.cloudflare.com/client/v4'+path,{method:body?'POST':'GET',headers:{Authorization:'Bearer '+token,'Content-Type':'application/json'},...(body?{body:JSON.stringify(body)}:{}),signal:AbortSignal.timeout(60000)});
    const data=await response.json();assert.ok(response.ok && data.success,`Cloudflare ${path}: ${response.status}`);return data.result;
  }
  async function freshJwt() {
    list(); // Wrangler refreshes the existing OAuth login without exposing its token.
    // ponytail: default Windows OAuth store; use an API token for other hosts or profiles.
    const token=process.env.CLOUDFLARE_API_TOKEN || /oauth_token\s*=\s*"([^"]+)"/.exec(readFileSync(join(process.env.APPDATA,'xdg.config/.wrangler/config/default.toml'),'utf8'))?.[1];
    assert.ok(token,'Wrangler OAuth login or CLOUDFLARE_API_TOKEN is required');
    return (await api(`/accounts/${account}/pages/projects/${config.name}/upload-token`,token)).jwt;
  }
  const files=[];
  function walk(dir) {for(const entry of readdirSync(dir,{withFileTypes:true})) {
    const path=join(dir,entry.name);
    if(entry.isDirectory()) walk(path);
    else if(path!==join(web,'_routes.json')) files.push({path,relative:relative(web,path),size:statSync(path).size});
  }}
  walk(web);
  const batches=uploadBatches(files),progress={directory,totalFiles:files.length,totalBytes:files.reduce((n,f)=>n+f.size,0),completedFiles:0,completedBytes:0,batches:[]};
  for(let i=0;i<batches.length;i++) {
    const batch=batches[i],out=join(directory,'upload-batches',String(i)),manifest=out+'.json';
    for(const file of batch) {const target=join(out,file.relative);mkdirSync(dirname(target),{recursive:true});if(!existsSync(target)) linkSync(file.path,target);}
    console.log(`Upload batch ${i+1}/${batches.length}: ${batch.length} files, ${Math.round(batch.reduce((n,f)=>n+f.size,0)/1024/1024)} MiB`);
    const jwt=await freshJwt();assert.ok(jwt);
    // Pages registers reusable hashes only after a complete upload; keep each upload short.
    const result=spawnSync(process.execPath,[cli,'pages','project','upload',out,'--output-manifest-path',manifest],{cwd:directory,stdio:'inherit',env:{...process.env,CF_PAGES_UPLOAD_JWT:jwt}});
    assert.equal(result.status,0,'Batch upload failed; completed batches remain reusable');
    const hashes=Object.values(JSON.parse(readFileSync(manifest)));
    await api('/pages/assets/upsert-hashes',jwt,{hashes});
    assert.deepEqual(await api('/pages/assets/check-missing',jwt,{hashes}),[],'Upload cache confirmation failed');
    progress.completedFiles+=batch.length;progress.completedBytes+=batch.reduce((n,f)=>n+f.size,0);
    progress.batches.push({batch:i+1,files:batch.length,verifiedAt:new Date().toISOString()});
    writeFileSync(join(directory,'upload-progress.json'),JSON.stringify(progress,null,2));
    console.log(`Confirmed ${progress.completedFiles}/${progress.totalFiles} files (${Math.round(progress.completedBytes/progress.totalBytes*100)}% of bytes)`);
  }
}

if(process.argv[1]===fileURLToPath(import.meta.url)) await main(process.argv[2]);
