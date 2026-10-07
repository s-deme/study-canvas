import assert from 'node:assert/strict';
import {cpSync,existsSync,mkdtempSync,renameSync,rmSync} from 'node:fs';
import {basename,dirname,resolve} from 'node:path';

// Call only while holding private-build.lock. Keep the last successful build on failure.
export function recoverPrivateBuild(out) {
  assert.equal(out,resolve(out));
  assert.equal(basename(out),'private');assert.equal(basename(dirname(out)),'build');
  const backup=out+'.previous';
  if(existsSync(backup)) {
    if(!existsSync(out)) renameSync(backup,out);
    else rmSync(backup,{recursive:true,force:true});
  }
}

export function updatePrivateBuild(out,update,preserve=true) {
  recoverPrivateBuild(out);
  const stage=mkdtempSync(out+'-pending-'),backup=out+'.previous';
  const hadOutput=existsSync(out);
  try {
    // ponytail: copy the successful build; incremental storage if disk space becomes a constraint.
    if(hadOutput && preserve) cpSync(out,stage,{recursive:true});
    const result=update(stage);
    if(hadOutput) renameSync(out,backup);
    try {renameSync(stage,out);} catch(error) {if(hadOutput) renameSync(backup,out);throw error;}
    recoverPrivateBuild(out);
    return result;
  } finally {rmSync(stage,{recursive:true,force:true});}
}
