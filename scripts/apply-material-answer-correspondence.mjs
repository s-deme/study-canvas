// Repair only the proven answer/section correspondence in a completed local derivative.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,copyFileSync,mkdirSync,existsSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {validateQuestions,questionKey} from '../web/core.mjs';
import {compactQuestionPack,writeLibraryCatalog} from './library-catalog.mjs';
import {loadAnswerCorrespondence,applyAnswerCorrespondence,answerCorrespondenceFile} from './material-answer-correspondence.mjs';
import {sha} from './material-transcription.mjs';
const read=p=>JSON.parse(readFileSync(p));
const directory=resolve(process.argv[2] || read('build/material-transcription/current.json').directory);
const manifest=read(join(directory,'manifest.json')),map=loadAnswerCorrespondence();
const history=join(directory,'answer-correspondence-history');assert.ok(!existsSync(history),'Correspondence repair already applied');mkdirSync(history);
for(const file of ['manifest.json','transcription-report.json','web/catalog.mjs','web/library-catalog.mjs']) {mkdirSync(join(history,file,'..'),{recursive:true});copyFileSync(join(directory,file),join(history,file));}
const {MATERIAL_INDEX,MATERIAL_EXAMS}=await import(pathToFileURL(join(directory,'web/catalog.mjs')));
const corrected=new Map(),changes=[];let answerChanges=0,typeChanges=0,alternatives=0,pending=0;
const packs=manifest.packs.map(pack=>{
  const file=join(directory,'web',pack.url),bytes=readFileSync(file);assert.equal(sha(bytes),pack.sha256);
  const before=validateQuestions(JSON.parse(bytes));if(!before.some(q=>map.has(questionKey(q)))) return pack;
  mkdirSync(join(history,'web',pack.url,'..'),{recursive:true});copyFileSync(file,join(history,'web',pack.url));
  const next=before.map(q=>{const result=applyAnswerCorrespondence(q,map);assert.equal(result.id,q.id);assert.deepEqual(result.options,q.options);
    if(map.has(questionKey(q))) {corrected.set(questionKey(q),result);changes.push({key:questionKey(q),before:{type:q.type,answer:q.answer,subject:q.subject,topic:q.topic,explanation:q.explanation},after:{type:result.type,answer:result.answer,subject:result.subject,topic:result.topic,explanation:result.explanation,acceptedAnswers:result.acceptedAnswers,answerPending:result.answerPending,previousType:result.previousType}});answerChanges+=JSON.stringify(q.answer)!==JSON.stringify(result.answer);typeChanges+=q.type!==result.type;alternatives+=!!result.acceptedAnswers;pending+=!!result.answerPending;}
    return result;});
  assert.deepEqual(validateQuestions(next),next);const text=JSON.stringify(compactQuestionPack(next));assert.deepEqual(validateQuestions(JSON.parse(text)),next);writeFileSync(file,text);
  return {...pack,subject:next[0].subject,sha256:sha(text)};
});
assert.equal(corrected.size,map.size);
const index=MATERIAL_INDEX.map(q=>{const result=corrected.get(questionKey(q));return result?{...q,type:result.type,subject:result.subject,topic:result.topic,...(result.previousType?{previousType:result.previousType}:{})}:q;});
writeFileSync(join(directory,'web/catalog.mjs'),`export const BUILTIN_QUESTIONS=[];\nexport const MATERIAL_INDEX=${JSON.stringify(index)};\nexport const MATERIAL_PACKS=${JSON.stringify(packs)};\nexport const MATERIAL_EXAMS=${JSON.stringify(MATERIAL_EXAMS)};\n`);
writeLibraryCatalog(join(directory,'web'),index,packs,MATERIAL_EXAMS);
copyFileSync(answerCorrespondenceFile,join(directory,'answer-correspondence.json'));
const proof={questions:corrected.size,packs:packs.filter((p,i)=>p.sha256!==manifest.packs[i].sha256).length,answerChanges,typeChanges,alternatives,pending,proofSha256:sha(readFileSync(answerCorrespondenceFile)),changes};
writeFileSync(join(directory,'answer-correspondence-changes.json'),JSON.stringify(proof,null,2));
writeFileSync(join(directory,'manifest.json'),JSON.stringify({...manifest,packs,answerCorrespondence:{report:'answer-correspondence-changes.json',proof:'answer-correspondence.json'}},null,2));
const report=read(join(directory,'transcription-report.json'));report.answerCorrespondence={...proof,changes:undefined};writeFileSync(join(directory,'transcription-report.json'),JSON.stringify(report,null,2));
for(const file of ['app.mjs','core.mjs','render.mjs']) copyFileSync(join('web',file),join(directory,'web',file));
console.log(JSON.stringify({...proof,changes:undefined}));
