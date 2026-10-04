import assert from 'node:assert/strict';
import {existsSync,mkdtempSync,readFileSync,rmSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

const dir=mkdtempSync(join(tmpdir(),'study-canvas-config-'));
const script=fileURLToPath(new URL('../scripts/prepare-cloud-config.mjs',import.meta.url));
const run=()=>spawnSync(process.execPath,[script],{cwd:dir,encoding:'utf8'});
try {
  assert.notEqual(run().status,0);
  assert.equal(existsSync(join(dir,'.wrangler')),false);
  const original='{ "name": "local-test", "pages_build_output_dir": "./web" }\n';
  writeFileSync(join(dir,'wrangler.local.jsonc'),original);
  for (let i=0;i<2;i++) {
    const result=run(); assert.equal(result.status,0,result.stderr);
    const redirect=JSON.parse(readFileSync(join(dir,'.wrangler/deploy/config.json'),'utf8'));
    assert.equal(redirect.configPath,'../../wrangler.local.jsonc');
    assert.equal(readFileSync(join(dir,'wrangler.local.jsonc'),'utf8'),original);
    assert.equal(existsSync(join(dir,'wrangler.jsonc')),false);
  }
  console.log('PASS: Pages local config redirect, missing-config refusal, original preservation and repeatability');
} finally {
  assert.ok(dir.startsWith(join(tmpdir(),'study-canvas-config-')));
  rmSync(dir,{recursive:true,force:true});
}
