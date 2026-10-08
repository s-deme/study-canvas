import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {validateQuestions} from '../web/core.mjs';
const base='private-data/github-material/prepared/';
const {packs}=JSON.parse(readFileSync(base+'jlpt-report.json'));
const counts={};let total=0;
for(const pack of packs) {
  const rows=validateQuestions(JSON.parse(readFileSync(base+pack.file)));
  const key=pack.year+':'+pack.examId;counts[key]=(counts[key] || 0)+rows.length;
  for(const q of rows) {
    assert.ok(q.images.length);assert.ok(q.answer>=0 && q.answer<q.options.length);
    assert.equal((q.audio || []).length,pack.subject==='聴解'?1:0);
    for(const asset of [...q.images,...(q.audio || [])]) assert.ok(existsSync(base+'assets/'+asset.src.split('/').at(-1)));
    if(q.audio?.length) assert.throws(()=>validateQuestions([{...q,audio:[{src:'assets/../secret.mp3',label:'invalid'}]}]));
  }
  total+=rows.length;
}
for(const [year,expected] of Object.entries({2009:[44,40,37,34,29],2012:[105,106,99,97,89],2018:[107,107,102,98,91]})) {
  expected.forEach((count,i)=>assert.equal(counts[year+':jlpt-n'+(i+1)],count));
}
assert.equal(Object.keys(counts).length,15);
console.log(`PASS: JLPT N1–N5, all 15 official editions, ${total} questions, audio assets and unsafe path rejection`);
