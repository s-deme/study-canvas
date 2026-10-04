// Exercise the real publication check in a disposable repository; use dummy secrets only.
import assert from 'node:assert/strict';
import {cpSync,mkdirSync,mkdtempSync,readFileSync,rmSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {spawnSync} from 'node:child_process';
const dir=mkdtempSync(join(tmpdir(),'study-canvas-publication-'));
const git=(...args)=>{const r=spawnSync('git',args,{cwd:dir,encoding:'utf8'});assert.equal(r.status,0,r.stderr);};
const run=(env={})=>spawnSync(process.execPath,['checks/publication-check.mjs'],{cwd:dir,encoding:'utf8',env:{...process.env,...env}});
try {
  cpSync(new URL('../web/',import.meta.url),join(dir,'web'),{recursive:true});
  mkdirSync(join(dir,'checks'));
  cpSync(new URL('./publication-check.mjs',import.meta.url),join(dir,'checks/publication-check.mjs'));
  writeFileSync(join(dir,'.gitignore'),readFileSync(new URL('../.gitignore',import.meta.url)));
  git('init','--quiet');
  assert.equal(run().status,0);
  const failedGit=run({GIT_DIR:join(dir,'missing-git')});
  assert.notEqual(failedGit.status,0);assert.ok(failedGit.stderr.includes('Git公開候補を確認できません'));
  for(const file of ['private-data/dummy.json','wrangler.local.jsonc','.dev.vars','.dev.vars.backup','.env','node_modules/dummy.json','build/dummy.json','dist/dummy.json','ipa-material.mjs','ipa-manifest.json','scripts/build-ipa-material.py']) {
    const full=join(dir,file);mkdirSync(join(full,'..'),{recursive:true});writeFileSync(full,'{}');
    git('add','--force','--',file);
    const result=run();assert.notEqual(result.status,0,file);assert.ok(result.stderr.includes('Git公開候補に非公開教材・個人設定・生成物が含まれています'),file);
    git('rm','--cached','--quiet','--',file);rmSync(full);
  }
  writeFileSync(join(dir,'web/extra-questions.json'),'[]');
  assert.notEqual(run().status,0);rmSync(join(dir,'web/extra-questions.json'));
  writeFileSync(join(dir,'.dev.vars.example'),'OWNER_EMAIL=you@example.com\n');
  git('add','--','.dev.vars.example');assert.equal(run().status,0);
  console.log('PASS: publication refuses Git failures and staged private/retired material, extra problem files, local config/builds; allows safe examples');
} finally {
  assert.ok(dir.startsWith(join(tmpdir(),'study-canvas-publication-')));
  rmSync(dir,{recursive:true,force:true});
}
