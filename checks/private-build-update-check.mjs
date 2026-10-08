import assert from 'node:assert/strict';
import {existsSync,mkdirSync,mkdtempSync,readFileSync,renameSync,rmSync,writeFileSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {recoverPrivateBuild,updatePrivateBuild} from '../scripts/private-build-update.mjs';

const root=mkdtempSync(join(tmpdir(),'study-build-update-')),out=join(root,'build/private');
try {
  mkdirSync(join(root,'build'));
  updatePrivateBuild(out,stage=>writeFileSync(join(stage,'manifest.json'),'original'));
  assert.throws(()=>updatePrivateBuild(out,stage=>{
    writeFileSync(join(stage,'manifest.json'),'partial');throw new Error('copy failed');
  }),/copy failed/);
  assert.equal(readFileSync(join(out,'manifest.json'),'utf8'),'original');
  updatePrivateBuild(out,stage=>writeFileSync(join(stage,'manifest.json'),'complete'));
  assert.equal(readFileSync(join(out,'manifest.json'),'utf8'),'complete');
  assert.equal(existsSync(out+'.previous'),false);
  renameSync(out,out+'.previous');recoverPrivateBuild(out);
  assert.equal(readFileSync(join(out,'manifest.json'),'utf8'),'complete');
  mkdirSync(out+'.previous');writeFileSync(join(out+'.previous','manifest.json'),'old');
  recoverPrivateBuild(out);assert.equal(existsSync(out+'.previous'),false);
  assert.equal(readFileSync(join(out,'manifest.json'),'utf8'),'complete');
  assert.throws(()=>updatePrivateBuild(out,stage=>rmSync(stage,{recursive:true,force:true})),/ENOENT/);
  assert.equal(readFileSync(join(out,'manifest.json'),'utf8'),'complete');
  assert.throws(()=>recoverPrivateBuild(root));
  writeFileSync(join(out,'retired.json'),'old');
  updatePrivateBuild(out,stage=>{
    assert.equal(existsSync(join(stage,'retired.json')),false);
    writeFileSync(join(stage,'manifest.json'),'rebuilt');
  },false);
  assert.equal(readFileSync(join(out,'manifest.json'),'utf8'),'rebuilt');
  assert.equal(existsSync(join(out,'retired.json')),false);
  console.log('PASS: failed update preserves original, successful swap and interrupted-swap recovery');
} finally {rmSync(root,{recursive:true,force:true});}
