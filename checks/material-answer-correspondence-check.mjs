import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {loadAnswerCorrespondence,applyAnswerCorrespondence} from '../scripts/material-answer-correspondence.mjs';
import {validateQuestions,correctAnswer,emptyState,newSession,record,sessionSummary,validateState,questionKey} from '../web/core.mjs';
import {CompactQuestionIndex} from '../scripts/cloud-runtime.mjs';
const read=p=>JSON.parse(readFileSync(p)),map=loadAnswerCorrespondence(),directory=read('build/material-transcription/current.json').directory;
const manifest=read(join(directory,'manifest.json')),questions=new Map();
const correctedFiles=new Set(read(join(directory,'answer-correspondence.json')).corrections.map(p=>p.sourceFile));
for(const pack of manifest.packs) if(pack.sources?.some(s=>correctedFiles.has(s.file))) {
  for(const q of validateQuestions(read(join(directory,'web',pack.url)))) {
    assert.deepEqual(applyAnswerCorrespondence(q,map),q,'Idempotent proven correction');questions.set(questionKey(q),q);
    if(q.acceptedAnswers) for(const answer of q.acceptedAnswers) assert.equal(correctAnswer(q,answer),true);
    if(q.previousType) {
      const old={...q,type:q.previousType,answer:map.get(questionKey(q)).beforeAnswer};delete old.previousType;delete old.acceptedAnswers;delete old.answerPending;
      const s=emptyState();s.selectedExam=q.examId;s.session=newSession([old],1,'既存記録');s.session.pending=old.answer;s.session.answers[0]=old.answer;s.session.pending=-1;
      validateState(s,[q]);
      const compact=new CompactQuestionIndex([[questionKey(q),['single','multiple'].indexOf(q.type)*32+q.options.length+128]]);assert.equal(compact.get(questionKey(q)).previousType,q.previousType);validateState(s,compact);
    }
  }
}
assert.equal(questions.size,map.size);
const {MATERIAL_INDEX}=await import(pathToFileURL(join(directory,'web/catalog.mjs')));
let catalogEntries=0;
for(const q of MATERIAL_INDEX) if(map.has(questionKey(q))) {
  const full=questions.get(questionKey(q));assert.equal(q.subject,full.subject);assert.equal(q.type,full.type);assert.equal(q.previousType,full.previousType);
  if(q.catalogOnly) assert.ok(!Object.hasOwn(q,'topic'),'Lightweight catalog must retain its omitted-topic format');
  catalogEntries++;
}
assert.equal(catalogEntries,map.size);
const get=id=>questions.get('nurse::'+id);
assert.equal(get('expansion-tp170425-05b_01-q005').answer,1);
const multi=get('expansion-tp210416-05b_01-q086');assert.deepEqual(multi.acceptedAnswers,[[3,4],[0,3],[0,4]]);assert.equal(correctAnswer(multi,[0,3,4]),false);
for(const q of questions.values()) if(q.answerPending) {const s=emptyState();s.selectedExam=q.examId;s.session=newSession([q],1,'保留');s.session.answers[0]=0;const before=structuredClone(s);record(s,q,0,1);assert.deepEqual(s,before);assert.deepEqual(sessionSummary(s.session,[q]),{correct:0,gradedTotal:0,self:{done:0,partial:0,review:0,pending:1}});assert.equal(correctAnswer(q,0),false);}
const base=get('expansion-tp190415-05b_01-q033');assert.throws(()=>validateQuestions([{...base,acceptedAnswers:[2,2]}]));assert.throws(()=>validateQuestions([{...base,answerPending:true,answer:null}]));
const summary={passed:true,covers:151,questions:questions.size,alternatives:[...questions.values()].filter(q=>q.acceptedAnswers).length,pending:[...questions.values()].filter(q=>q.answerPending).map(questionKey),oldSessionCompatibility:true};writeFileSync(join(directory,'answer-correspondence-verification.json'),JSON.stringify(summary,null,2));console.log('PASS: original-section grading, accepted answer sets, blank-answer hold, old saved sessions and compact state index',summary);
