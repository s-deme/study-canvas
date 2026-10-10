// Compare every output row to the successful original build, independently of packaging.
import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {validateQuestions,questionKey,emptyState,newSession,validateState} from '../web/core.mjs';
import {loadCorrections,applyTextCorrection,applyQuestionImageText,applySolutionText,applyReviewedImages} from '../scripts/material-transcription.mjs';
const read=file=>JSON.parse(readFileSync(file)),hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const source=resolve('build/private'),{directory}=read('build/private-compact/current.json');
const before=read(join(source,'manifest.json')),after=read(join(directory,'manifest.json'));
const evidence=read(join(directory,'text-evidence.json')),assets=read(join(directory,'asset-evidence.json'));
const corrections=loadCorrections(join(directory,'text-corrections.json'));
assert.equal(after.questions,before.questions);assert.equal(after.packs.length,before.packs.length);
const originalCatalog=await import(pathToFileURL(join(source,'web/catalog.mjs')));
const compactCatalog=await import(pathToFileURL(join(directory,'web/catalog.mjs')));
assert.deepEqual(compactCatalog.MATERIAL_INDEX,originalCatalog.MATERIAL_INDEX);
assert.deepEqual(compactCatalog.MATERIAL_EXAMS,originalCatalog.MATERIAL_EXAMS);
const checkedAssets=new Set(),keys=new Set();let count=0,converted=0,solutionConverted=0;
for(const [i,pack] of before.packs.entries()) {
  const nextPack=after.packs[i];assert.equal(nextPack.id,pack.id);assert.equal(nextPack.url,pack.url);
  const original=validateQuestions(read(join(source,'web',pack.url)));
  const bytes=readFileSync(join(directory,'web',nextPack.url));assert.equal(hash(bytes),nextPack.sha256);
  const next=validateQuestions(JSON.parse(bytes));assert.equal(next.length,original.length);
  for(const [j,q] of original.entries()) {
    const actual=next[j],patch=evidence[`${q.examId}::${q.id}`];let expected=structuredClone(q);
    if(patch?.textSha256) {expected.images=[];expected.passage=patch.passage || '';expected.prompt=patch.mode==='passage'?patch.prompt:q.topic+'\n'+patch.prompt;expected.options=patch.options;converted++;}
    expected=applyTextCorrection(expected,corrections,q);
    expected=applyQuestionImageText(expected,patch?.question);
    expected=applySolutionText(expected,patch?.solution,corrections.get(questionKey(q)));solutionConverted+=patch?.solution?.removed.length || 0;
    expected=applyReviewedImages(expected,corrections);
    for(const field of ['images','solutionImages','audio']) for(const a of expected[field] || []) {
      if(!a.src.startsWith('assets/')) continue;
      const entry=assets[a.src];assert.ok(entry,a.src);a.src=entry.src;
      if(!checkedAssets.has(a.src)) {
        assert.equal(hash(readFileSync(join(directory,'web',a.src))),entry.sha256,a.src);
        checkedAssets.add(a.src);
      }
    }
    assert.deepEqual(actual,expected,questionKey(q));assert.ok(!keys.has(questionKey(actual)));keys.add(questionKey(actual));count++;
  }
}
assert.equal(count,before.questions);assert.equal(converted,Object.values(evidence).filter(p=>p.textSha256).length);
const {MATERIAL_MANIFESTS}=await import(pathToFileURL(join(directory,'web/library-catalog.mjs')));
for(const m of MATERIAL_MANIFESTS) {
  const bytes=readFileSync(join(directory,'web',m.url));assert.equal(hash(bytes),m.sha256);
  const data=JSON.parse(bytes);data.index=data.index.map(q=>({...data.defaults,...q}));assert.equal(data.index.length,m.count);
  assert.deepEqual(data.packs,after.packs.filter(p=>p.examId===m.examId));
  assert.ok(data.index.every(q=>keys.has(questionKey(q))));
}
const q=originalCatalog.MATERIAL_INDEX.find(q=>q.examId==='fe'&&q.type==='single');
const state=emptyState();state.selectedExam='fe';state.session=newSession([q],1,'resume');state.session.pending=0;
assert.deepEqual(validateState(state,originalCatalog.MATERIAL_INDEX),validateState(state,compactCatalog.MATERIAL_INDEX));
for(const name of ['private-data','text-evidence.json','review.json','asset-evidence.json']) assert.ok(!existsSync(join(directory,'web',name)),name);
console.log(`PASS: ${count} question identities/order/answers/content, ${converted} question replacements, ${solutionConverted} answer/explanation image replacements, ${checkedAssets.size} asset hashes, indexes and saved-session compatibility`);
