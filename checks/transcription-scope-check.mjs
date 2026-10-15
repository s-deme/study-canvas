// Shared page OCR must not become another question's passage or explanation.
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {join} from 'node:path';
import {validateQuestions,questionKey} from '../web/core.mjs';
import {loadAnswerCorrespondence,applyAnswerCorrespondence} from '../scripts/material-answer-correspondence.mjs';
const read=file=>JSON.parse(readFileSync(file));
const {directory}=read('build/material-transcription/current.json');
const report=read(join(directory,'transcription-report.json'));
const manifest=read(join(directory,'manifest.json'));
const answerCorrespondence=loadAnswerCorrespondence();
const reviewed=new Set(read(join(directory,'text-corrections.json')).map(r=>r.key));
const pending=new Map();
for(const r of report.supplementaryPending.filter(r=>r.reason.startsWith('question-range-not-established'))) {
  if(!pending.has(r.key)) pending.set(r.key,[]);
  pending.get(r.key).push(r);
}
let checked=0;
// The IPA advanced morning paper has identical question IDs in several exams.
for(const pack of manifest.packs) if(/2023r05a_koudo_am1-/.test(pack.id)) {
  for(const q of validateQuestions(read(join(directory,'web',pack.url)))) {
    assert.ok(!(pending.get(questionKey(q)) || []).some(r=>r.field==='images'),questionKey(q)+' same question in multiple exams');
  }
}
for(const pack of manifest.packs) {
  const baseline=new Map(validateQuestions(read(join(report.source,'web',pack.url))).map(q=>[questionKey(q),q]));
  for(const q of validateQuestions(read(join(directory,'web',pack.url)))) {
    const key=questionKey(q);if(reviewed.has(key)) continue;
    for(const item of pending.get(key) || []) {
      const prior=baseline.get(key),field=item.field==='images'?'passage':'explanation';
      if(prior[item.field].every(image=>(pending.get(key) || []).some(p=>p.field===item.field && p.src===image.src))) assert.equal(q[field],prior[field],key+' '+field);
      assert.ok(q[item.field].some(i=>i.src===item.src),key+' authoritative image');
      checked++;
    }
    assert.deepEqual(q.answer,applyAnswerCorrespondence(baseline.get(key),answerCorrespondence).answer,key+' answer');
  }
}
assert.ok(checked>0,'No real shared-page scope checks ran');
console.log(`PASS: ${checked} shared-image references retain authoritative pixels without adding other-question text; answer mappings match original-cover correspondence`);
