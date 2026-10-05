import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {EXPANSION_FIELDS} from '../scripts/additional-material.mjs';
const report=JSON.parse(readFileSync(new URL('../build/private/web/material/expansion-report.json',import.meta.url),'utf8'));
console.log(JSON.stringify(report,null,2));
assert.ok(report.added>=10000,'追加1万問に未達です');
for(const field of EXPANSION_FIELDS) assert.ok(report.fields[field]>=200,field+'の追加200問に未達です');
assert.ok(report.complete,'追加教材の完了条件に未達です');
console.log('PASS: expansion quantity targets (content review and deployment must be checked separately)');
