import assert from 'node:assert/strict';
import {closeSync,openSync,readFileSync,unlinkSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';
import {join} from 'node:path';
const root=fileURLToPath(new URL('../',import.meta.url));
const manifest=join(root,'build/private/manifest.json'),before=readFileSync(manifest);
const lock=join(root,'build/private-build.lock'),fd=openSync(lock,'wx');
try {
  const result=spawnSync(process.execPath,['scripts/build-private.mjs'],{cwd:root,encoding:'utf8'});
  assert.notEqual(result.status,0);assert.match(result.stderr,/EEXIST/);
  assert.deepEqual(readFileSync(manifest),before,'Competing build must not remove or replace the existing output');
} finally {closeSync(fd);unlinkSync(lock);}
console.log('PASS: competing private build refused before output mutation');
