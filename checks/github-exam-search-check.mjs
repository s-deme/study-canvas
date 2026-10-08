import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';

const read=name=>readFileSync(new URL('../docs/'+name,import.meta.url),'utf8');
const data=JSON.parse(read('github-exam-search.json'));
const inventory=read('exam-inventory.md'),document=read('github-exam-search.md');
const missing=inventory.split('\n').filter(l=>l.includes('| 0 | 問題未登録 |')).map(l=>l.split('|')[2].trim());
const records=new Map(data.exams.map(r=>[r.examId,r.history.at(-1)]));
assert.equal(records.size,data.exams.length,'Duplicate exam record');
const labels={'not-found':'検索済み・候補未発見',review:'検索済み・要精査',candidate:'候補あり・本文未確認',held:'既存候補保留',blocked:'検索未確認',confirmed:'問題本文確認済み'};
const queue=document.split('## 未調査・検索未確認\n')[1].split('## 現在の問題未登録試験')[0];
for(const id of missing) {
  const record=records.get(id),pending=!record||record.status==='blocked';
  assert.equal(queue.includes(`（${id}）`),pending,'Wrong search queue '+id);
  assert.ok(document.includes(`| ${id} | ${record?labels[record.status]:'未調査'} |`),'Missing search row '+id);
  if(record) {assert.ok(record.queries.length);assert.ok(document.includes(record.date));}
}
assert.equal(document.split('## 現在の問題未登録試験\n')[1].split('\n').filter(l=>/^\| .* \| [a-z0-9][a-z0-9-]* \|/.test(l)).length,missing.length);
console.log(`GitHub search ledger: ${missing.length} unregistered exams, queue and states verified`);
