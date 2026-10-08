// Original practice stays private, including its authoring and answer-check scripts.
import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {validateQuestions,validateExam,questionKey,DEFAULT_EXAMS} from '../web/core.mjs';
import {EXAM_CATALOG} from '../web/exams.mjs';
import {materialFingerprint} from './additional-material.mjs';

const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
export function loadLocalPractice(root,existing) {
  const dir=join(root,'private-data/local-practice'),file=join(dir,'manifest.json');
  if(!existsSync(file)) return {exams:[],packs:[],duplicates:[]};
  const manifest=JSON.parse(readFileSync(file));assert.equal(manifest.version,1);
  assert.match(manifest.verification,/実行照合/);
  assert.equal(hash(readFileSync(join(dir,'author.py'))),manifest.authorSha256,'Practice author changed; regenerate and check');
  const evidence=readFileSync(join(dir,'evidence.json'));assert.equal(hash(evidence),manifest.evidenceSha256,'Practice evidence changed');
  const checks=JSON.parse(evidence).checks,answers=new Map(checks.map(c=>[questionKey(c),c]));
  assert.equal(answers.size,checks.length,'Duplicate practice evidence');
  const keys=new Set(existing.map(questionKey)),fingerprints=new Set(existing.map(materialFingerprint));
  const packs=[],duplicates=[],packIds=new Set(),known=new Set(existing.map(q=>q.examId));
  for(const pack of manifest.packs) {
    assert.match(pack.file,/^practice-[a-z0-9-]+\.json$/);
    assert.equal(pack.id,pack.file.slice(0,-5));assert.ok(!packIds.has(pack.id));packIds.add(pack.id);
    const definition=DEFAULT_EXAMS.find(e=>e.id===pack.examId) || EXAM_CATALOG.find(e=>e.id===pack.examId);
    assert.ok(definition,'Unknown practice exam '+pack.examId);
    const raw=readFileSync(join(dir,pack.file));assert.equal(hash(raw),pack.sha256,'Practice pack changed; regenerate and check');
    const rows=validateQuestions(JSON.parse(raw),[],false,pack.examId);assert.equal(rows.length,pack.count);
    const kept=[];
    for(const q of rows) {
      assert.ok(q.source.includes('自作') && q.source.includes('AI生成'));
      assert.ok(q.explanation && q.explanationSource.includes('独自'));
      const check=answers.get(questionKey(q));assert.ok(check?.code,'Missing execution evidence');
      assert.ok(['python-execution','sqlite-execution','formula-and-expected-value','enumeration-and-expected-count'].includes(check.method));
      assert.equal(q.modelAnswer,check.answer,'Practice answer differs from execution evidence');
      assert.ok(!keys.has(questionKey(q)),'Duplicate practice ID '+questionKey(q));keys.add(questionKey(q));
      const fp=materialFingerprint(q);
      if(fingerprints.has(fp)) {duplicates.push(questionKey(q));continue;}
      fingerprints.add(fp);kept.push(q);
    }
    if(kept.length) packs.push({id:pack.id,examId:pack.examId,count:kept.length,term:'自作・分野別演習',subject:pack.subject,
      verification:manifest.verification,rows:kept});
  }
  assert.equal(manifest.packs.reduce((n,p)=>n+p.count,0),answers.size,'Practice evidence count mismatch');
  const exams=[...new Set(packs.map(p=>p.examId))].filter(id=>!known.has(id))
    .map(id=>validateExam(DEFAULT_EXAMS.find(e=>e.id===id) || EXAM_CATALOG.find(e=>e.id===id)));
  return {exams,packs,duplicates};
}
