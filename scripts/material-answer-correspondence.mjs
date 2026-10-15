// Answer changes have a separate authority: original cover + original official answer rows.
// OCR text corrections cannot alter grading.
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {join} from 'node:path';
import {sha} from './material-transcription.mjs';
import {questionKey} from '../web/core.mjs';
export const answerCorrespondenceFile='private-data/material-transcription/answer-correspondence.json';
export function loadAnswerCorrespondence(file=answerCorrespondenceFile,{verifySources=true}={}) {
  const map=new Map();if(!existsSync(file)) return map;
  const proof=JSON.parse(readFileSync(file));assert.equal(proof.unresolved.length,0,'Unresolved original cover');
  for(const pack of proof.corrections) {
    const cover=proof.records.find(r=>r.sourceFile===pack.sourceFile);
    assert.deepEqual(cover.detectedSections,[pack.section]);assert.equal(sha(cover.coverText),pack.coverTextSha256);
    assert.equal(cover.sourceSha256,pack.sourceSha256);
    if(verifySources) for(const [name,hash] of [[pack.sourceFile,pack.sourceSha256],[pack.answerFile,pack.answerSha256]]) {
      assert.ok(!/[\\/]/.test(name),'Unexpected source path');assert.equal(sha(readFileSync(join('private-data/github-material',name))),hash,'Changed original PDF');
    }
    for(const row of pack.questions) {
      assert.ok(!map.has(row.key));assert.equal(Number(row.key.match(/-q(\d+)$/)?.[1]),Number(row.number));
      const prefix=pack.section==='AM'?'(?:A|AM)':'(?:B|PM)';assert.match(row.label,new RegExp('^'+prefix+'0*'+Number(row.number)+'$'));
      assert.ok(Array.isArray(row.cells));
      const sets=row.cells.map(cell=>{assert.match(cell,/^[1-5]+$/);assert.equal(new Set(cell).size,cell.length);const set=[...cell].map(c=>Number(c)-1).sort();assert.ok(set.every(n=>n<row.optionCount));return set;});
      assert.ok(!sets.length || sets.every(s=>s.length===sets[0].length),'Mixed answer cardinalities');
      assert.equal(new Set(sets.map(s=>JSON.stringify(s))).size,sets.length);
      map.set(row.key,{...row,sets,subject:pack.subject,previousSubject:pack.beforeSection==='AM'?'午前':'午後',section:pack.section});
    }
  }
  return map;
}
export function applyAnswerCorrespondence(q,map) {
  const r=map.get(questionKey(q));if(!r) return q;
  assert.equal(q.options.length,r.optionCount,'Changed option count');
  const type=r.sets.length?(r.sets[0].length===1?'single':'multiple'):(Array.isArray(r.beforeAnswer)?'multiple':'single');
  const answer=r.sets.length?(type==='single'?r.sets[0][0]:r.sets[0]):null;
  assert.ok(JSON.stringify(q.answer)===JSON.stringify(r.beforeAnswer) || JSON.stringify(q.answer)===JSON.stringify(answer),'Stale answer correspondence');
  const topic=q.topic.replace(/(国家試験 )午後( 問\d+)$/,'$1'+r.subject+'$2');
  const result={...q,type,answer,subject:r.subject,topic};
  const previousTopic=topic.replace(/(国家試験 )(午前|午後)( 問\d+)$/,'$1'+r.previousSubject+'$3');
  const oldCaption='出典：厚生労働省 '+previousTopic+'。';
  if(q.source.startsWith(oldCaption)) result.source='出典：厚生労働省 '+topic+'。'+q.source.slice(oldCaption.length);
  if(q.prompt.startsWith(q.topic+'\n原本画像のこの問題番号')) result.prompt=topic+q.prompt.slice(q.topic.length);
  delete result.acceptedAnswers;delete result.answerPending;delete result.previousType;
  const previousType=Array.isArray(r.beforeAnswer)?'multiple':'single';if(previousType!==type) result.previousType=previousType;
  if(!r.sets.length) result.answerPending=true;
  else if(r.sets.length>1) result.acceptedAnswers=r.sets.map(s=>type==='single'?s[0]:s);
  assert.ok(q.explanation.startsWith('公式正答：') || q.explanation.startsWith('公式正答表の当該欄は空欄'),'Unexpected original explanation');
  result.explanation=r.sets.length?'公式正答：'+r.sets.map(s=>s.map(n=>n+1).join('、')).join(' または ')+'。理由解説は未収録です。実施当時の医学・制度を前提とします。':'公式正答表の当該欄は空欄です。正答を推測せず、採点を保留します。理由解説は未収録です。';
  if(result.textReview) {result.textReview={...result.textReview};delete result.textReview.answer;delete result.textReview.explanation;}
  return result;
}
