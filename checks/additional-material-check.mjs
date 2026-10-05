import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdtempSync,mkdirSync,writeFileSync,readFileSync,rmSync} from 'node:fs';
import {resolve,join,sep} from 'node:path';
import {loadAdditionalMaterial} from '../scripts/additional-material.mjs';
const build=resolve('build');mkdirSync(build,{recursive:true});const root=mkdtempSync(join(build,'additional-check-'));
assert.ok(root.startsWith(build+sep));
const hash=s=>createHash('sha256').update(s).digest('hex');
const folder=join(root,'private-data/additions'),archive=join(root,'private-data/test');mkdirSync(folder,{recursive:true});mkdirSync(archive,{recursive:true});
const q={id:'new',examId:'test',type:'single',prompt:'Synthetic capacity fixture',options:['one','two'],answer:1,explanation:'Fixture only',sourceUrl:'https://example.com/fixture'};
const bytes=JSON.stringify([q]);writeFileSync(join(folder,'pack.json'),bytes);writeFileSync(join(archive,'source.pdf'),'fixture');
const source={file:'source.pdf',url:'https://example.com/fixture',sha256:hash('fixture')};
const manifest={archive:'test',exams:[{id:'test',name:'Fixture'}],sources:{terms:source,sources:[source]},questions:[{...q,images:[]}],packs:[{id:'pack',file:'pack.json',examId:'test',field:'数学',kind:'official',count:1,sha256:hash(bytes),verification:'fixture',sources:[source]}]};
function verify() {
 const text=JSON.stringify(manifest);writeFileSync(join(folder,'test-manifest.json'),text);
 writeFileSync(join(folder,'test-verification.json'),JSON.stringify({manifestSha256:hash(text),officialAnswers:'pass',sourceCropPixels:'pass',answerLeakage:'pass'}));
}
try {
 verify();assert.equal(loadAdditionalMaterial(root,[]).report.added,1);
 const prior={...q,id:'prior',prompt:'Previously recorded fixture'};
 manifest.questions[0].duplicateReview={status:'excluded-duplicate',existingKey:'test::prior',existingQuestionSha256:hash(JSON.stringify(prior)),candidateQuestionSha256:hash(JSON.stringify(q)),reviewedOn:'2026-10-05',reviewer:'fixture',reason:'Semantic duplication reviewed against the exact earlier fixture'};
 verify();const excluded=loadAdditionalMaterial(root,[prior]);assert.equal(excluded.report.added,0);assert.equal(excluded.report.duplicateExcluded,1);
 assert.throws(()=>loadAdditionalMaterial(root,[]),/Invalid duplicate review/);
 manifest.questions[0].duplicateReview.existingQuestionSha256='0'.repeat(64);verify();assert.throws(()=>loadAdditionalMaterial(root,[prior]),/Stale duplicate target/);
 manifest.questions[0].duplicateReview.existingQuestionSha256=hash(JSON.stringify(prior));manifest.questions[0].duplicateReview.candidateQuestionSha256='0'.repeat(64);verify();assert.throws(()=>loadAdditionalMaterial(root,[prior]),/Stale duplicate candidate/);
 delete manifest.questions[0].duplicateReview;verify();
 assert.equal(loadAdditionalMaterial(root,[{...q,id:'old'}]).report.added,0);
 assert.throws(()=>loadAdditionalMaterial(root,[q]),/Duplicate added ID/);
 writeFileSync(join(archive,'source.pdf'),'changed');assert.throws(()=>loadAdditionalMaterial(root,[]),/Source changed/);writeFileSync(join(archive,'source.pdf'),'fixture');
 writeFileSync(join(folder,'pack.json'),bytes+' ');assert.throws(()=>loadAdditionalMaterial(root,[]),/Stale verification/);writeFileSync(join(folder,'pack.json'),bytes);
 manifest.questions[0].answer=0;verify();assert.throws(()=>loadAdditionalMaterial(root,[]),/Answer evidence mismatch/);manifest.questions[0].answer=1;verify();
 writeFileSync(join(folder,'test-manifest.json'),readFileSync(join(folder,'test-manifest.json'),'utf8')+' ');assert.throws(()=>loadAdditionalMaterial(root,[]),/needs verification/);
 // Original exercises require their own evidence, never official answer/crop flags.
 const original={...q,source:'自作問題',explanationSource:'独自作成の解説'};
 const originalBytes=JSON.stringify([original]);writeFileSync(join(folder,'pack.json'),originalBytes);
 manifest.packs[0]={...manifest.packs[0],kind:'original',sha256:hash(originalBytes)};
 const execution={method:'python-3.12-execution',program:'print("two")',stdout:'two',pythonVersion:'3.12'};
 manifest.questions=[{...original,images:[],check:execution,questionSha256:hash(JSON.stringify(original)),reference:{file:source.file,locator:'fixture'},review:{status:'pass',rationale:'Checked reasoning',uniqueness:'Distinct objective',distractors:'Other options fail'}}];
 function verifyOriginal(extra={}) {
  const raw=JSON.stringify(manifest);writeFileSync(join(folder,'test-manifest.json'),raw);
  writeFileSync(join(folder,'test-verification.json'),JSON.stringify({manifestSha256:hash(raw),questions:1,checks:[{id:q.id,...execution}],originalAnswers:'pass',rationaleReview:'pass',distinctCoverage:'pass',...extra}));
 }
 verifyOriginal();assert.equal(loadAdditionalMaterial(root,[]).report.original,1);
 verifyOriginal({officialAnswers:'pass'});assert.throws(()=>loadAdditionalMaterial(root,[]),/cannot claim official/);
 verifyOriginal({rationaleReview:'pending'});assert.throws(()=>loadAdditionalMaterial(root,[]));
 verifyOriginal({checks:[]});assert.throws(()=>loadAdditionalMaterial(root,[]));
 manifest.questions[0].reference.locator='absent';verifyOriginal();assert.throws(()=>loadAdditionalMaterial(root,[]),/source locator/);manifest.questions[0].reference.locator='fixture';
 manifest.questions[0].review.status='pending';verifyOriginal();assert.throws(()=>loadAdditionalMaterial(root,[]));manifest.questions[0].review.status='pass';
 manifest.questions[0].questionSha256='0'.repeat(64);verifyOriginal();assert.throws(()=>loadAdditionalMaterial(root,[]),/Stale original review/);
 manifest.questions[0].questionSha256=hash(JSON.stringify(original));verifyOriginal();
 const second=structuredClone(manifest),q2={...original,id:'second',prompt:'Another distinct fixture'};
 const b2=JSON.stringify([q2]);writeFileSync(join(folder,'second.json'),b2);
 second.packs[0]={...second.packs[0],id:'second',file:'second.json',sha256:hash(b2)};
 second.questions[0]={...second.questions[0],id:q2.id,questionSha256:hash(JSON.stringify(q2))};
 function verifySecond() {
  const raw=JSON.stringify(second);writeFileSync(join(folder,'second-manifest.json'),raw);
  writeFileSync(join(folder,'second-verification.json'),JSON.stringify({manifestSha256:hash(raw),questions:1,checks:[{id:q2.id,...execution}],originalAnswers:'pass',rationaleReview:'pass',distinctCoverage:'pass'}));
 }
 verifySecond();assert.equal(loadAdditionalMaterial(root,[]).report.original,2);
 const duplicateOf=row=>({status:'excluded-duplicate',existingKey:'test::'+row.id,existingQuestionSha256:hash(JSON.stringify(row)),candidateQuestionSha256:'',reviewedOn:'2026-10-05',reviewer:'fixture',reason:'Reviewed against an exactly bound, actually included addition'});
 second.questions[0].duplicateReview={...duplicateOf(original),candidateQuestionSha256:hash(JSON.stringify(q2))};verifySecond();
 assert.equal(loadAdditionalMaterial(root,[]).report.original,1); // Target is validated later in filename order.
 second.questions[0].duplicateReview.existingQuestionSha256='0'.repeat(64);verifySecond();assert.throws(()=>loadAdditionalMaterial(root,[]),/Stale duplicate target/);
 second.questions[0].duplicateReview.existingQuestionSha256=hash(JSON.stringify(original));verifySecond();
 manifest.questions[0].duplicateReview={...duplicateOf(q2),candidateQuestionSha256:hash(JSON.stringify(original))};verifyOriginal();
 assert.throws(()=>loadAdditionalMaterial(root,[]),/Invalid duplicate review/); // Neither side of a cycle is included.
 delete second.questions[0].duplicateReview;verifySecond();assert.equal(loadAdditionalMaterial(root,[]).report.original,1);
 delete manifest.questions[0].duplicateReview;verifyOriginal();assert.equal(loadAdditionalMaterial(root,[]).report.original,2);
 second.exams[0].name='Conflicting definition';verifySecond();assert.throws(()=>loadAdditionalMaterial(root,[]),/Conflicting added exam/);
 rmSync(join(folder,'second-manifest.json'));rmSync(join(folder,'second-verification.json'));
 const knowledgeSource='fixture source evidence';writeFileSync(join(archive,'source.pdf'),knowledgeSource);source.sha256=hash(knowledgeSource);
 const knowledge={method:'knowledge-reference-review',referenceExcerpt:knowledgeSource,correctOptionText:'two',optionReviews:['one is contradicted by the reviewed fixture','two is supported by the reviewed fixture'],sourceSha256:source.sha256,reviewer:'fixture author review',reviewedOn:'2026-10-05'};
 manifest.questions[0].check=knowledge;
 const knowledgeVerify=()=>verifyOriginal({checks:[{id:q.id,...knowledge}]});
 knowledgeVerify();assert.equal(loadAdditionalMaterial(root,[]).report.original,1);
 knowledge.stdout='two';knowledgeVerify();assert.throws(()=>loadAdditionalMaterial(root,[]),/cannot claim execution/);delete knowledge.stdout;
 knowledge.correctOptionText='one';knowledgeVerify();assert.throws(()=>loadAdditionalMaterial(root,[]),/Knowledge answer mismatch/);knowledge.correctOptionText='two';
 knowledge.sourceSha256='0'.repeat(64);knowledgeVerify();assert.throws(()=>loadAdditionalMaterial(root,[]),/Knowledge source mismatch/);knowledge.sourceSha256=source.sha256;
 knowledge.optionReviews=[];knowledgeVerify();assert.throws(()=>loadAdditionalMaterial(root,[]),/Missing option review/);
 knowledge.optionReviews=['one is contradicted by the reviewed fixture','two is supported by the reviewed fixture'];
 // Synthetic derivative fixture checks provenance; the Python verifier also regenerates actual PDF text.
 const transcript={file:'transcript.html',url:source.url,sha256:hash(knowledgeSource),derivation:{file:source.file,sha256:source.sha256,method:'pymupdf-text-to-html-v1'}};
 writeFileSync(join(archive,transcript.file),knowledgeSource);
 manifest.sources.sources=[source,transcript];manifest.packs[0].sources=[source,transcript];manifest.questions[0].reference.file=transcript.file;
 knowledge.sourceSha256=transcript.sha256;knowledgeVerify();assert.equal(loadAdditionalMaterial(root,[]).report.original,1);
 transcript.derivation.method='unchecked';knowledgeVerify();assert.throws(()=>loadAdditionalMaterial(root,[]),/Unsupported source derivation/);transcript.derivation.method='pymupdf-text-to-html-v1';
 transcript.derivation.sha256='0'.repeat(64);knowledgeVerify();assert.throws(()=>loadAdditionalMaterial(root,[]),/Derived source parent mismatch/);transcript.derivation.sha256=source.sha256;
 manifest.sources.sources=[transcript];knowledgeVerify();assert.throws(()=>loadAdditionalMaterial(root,[]),/Missing derived source PDF/);manifest.sources.sources=[source,transcript];
 transcript.url='https://example.com/other';knowledgeVerify();assert.throws(()=>loadAdditionalMaterial(root,[]),/Derived source URL mismatch/);transcript.url=source.url;
 manifest.packs[0].sources=[transcript];knowledgeVerify();assert.throws(()=>loadAdditionalMaterial(root,[]),/Missing pack derived source PDF/);
 console.log('PASS: added material validation, duplicate exclusion, tamper detection, official answer mismatch, original review evidence, false official claims and incomplete PDF provenance rejected');
} finally {rmSync(root,{recursive:true,force:true});}
