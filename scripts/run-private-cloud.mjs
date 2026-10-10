import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolve,join,relative} from 'node:path';
import {spawnSync} from 'node:child_process';
import {gzipSync} from 'node:zlib';
const mode=process.argv[2];assert.ok(['build','deploy'].includes(mode));
const root=resolve('.'),{directory}=JSON.parse(readFileSync('build/private-cloud/current.json'));
assert.ok(!relative(join(root,'build/private-cloud'),directory).startsWith('..'));
const manifest=JSON.parse(readFileSync(join(directory,'manifest.json')));
assert.ok(manifest.questions>0 && manifest.files<=20000);
if(mode==='deploy') {
  const verification=JSON.parse(readFileSync(join(directory,'verification.json')));
  assert.equal(verification.packagedAt,manifest.packagedAt);assert.equal(verification.passed,true);
  const upload=spawnSync(process.execPath,[join(root,'scripts/upload-private-cloud.mjs'),directory],{cwd:root,stdio:'inherit'});
  if(upload.status!==0) process.exit(upload.status ?? 1);
}
const args=mode==='build'?['pages','functions','build','--outdir','worker']:['pages','deploy','web','--branch','main','--commit-dirty=true'];
const result=spawnSync(process.execPath,[join(root,'node_modules/wrangler/bin/wrangler.js'),...args],{cwd:directory,stdio:'inherit',env:{...process.env,WRANGLER_LOG_PATH:process.env.WRANGLER_LOG_PATH || join(directory,'.wrangler/logs')}});
if(mode==='build' && result.status===0) assert.ok(gzipSync(readFileSync(join(directory,'worker/index.js'))).length<=3*1024*1024,'Worker exceeds the Free plan compressed size limit');
process.exit(result.status ?? 1);
