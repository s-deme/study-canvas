// Local derivative only. The existing successful build and original imports are read-only.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync,cpSync,symlinkSync,openSync,closeSync,unlinkSync,renameSync,existsSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
import {validateQuestions,questionKey} from '../web/core.mjs';
import {compactQuestionPack,writeLibraryCatalog} from './library-catalog.mjs';
import {loadCorrections,applyTextCorrection,applySolutionText,applyReviewedImages,applySupplementaryImageText,fieldStatus,textFields,auditFields,sha,correctionFile} from './material-transcription.mjs';

const read=file=>JSON.parse(readFileSync(file));
const source=resolve(process.argv[2] || read('build/private-compact/current.json').directory);
const lock=resolve('build/private-build.lock'),fd=openSync(lock,'wx');
process.on('exit',()=>{closeSync(fd);unlinkSync(lock);});
for(const signal of ['SIGINT','SIGTERM']) process.on(signal,()=>process.exit(1));
const manifestBytes=readFileSync(join(source,'manifest.json')),baseline=JSON.parse(manifestBytes),records=loadCorrections();
const assetEvidence=existsSync(join(source,'asset-evidence.json'))?read(join(source,'asset-evidence.json')):{};
const textEvidence=existsSync(join(source,'text-evidence.json'))?read(join(source,'text-evidence.json')):{};
const extraction=spawnSync('python',['scripts/extract-material-image-text.py',source],{stdio:'inherit'});
assert.equal(extraction.status,0,'Image text extraction failed; previous successful build retained');
const imageText=read('build/material-image-text/text.json'),imageTextReport=read('build/material-image-text/report.json');
assert.equal(imageTextReport.sourceManifestSha256,sha(manifestBytes));
for(const [src,entry] of Object.entries(imageText)) assert.equal(sha(readFileSync(join(source,'web',src))),entry.identity.imageSha256,'Source image changed');
const out=resolve('build/material-transcription'),target=join(out,Date.now().toString());
mkdirSync(join(target,'web/material'),{recursive:true});
for(const entry of readdirSync(join(source,'web'),{withFileTypes:true})) {
  if(entry.name==='material' || entry.name==='assets') continue;
  cpSync(join(source,'web',entry.name),join(target,'web',entry.name),{recursive:true});
}
// Share immutable folders; new crops live in this derivative's own asset folder.
mkdirSync(join(target,'web/assets'),{recursive:true});
for(const entry of readdirSync(join(source,'web/assets'),{withFileTypes:true})) {
  if(entry.isDirectory()) symlinkSync(join(source,'web/assets',entry.name),join(target,'web/assets',entry.name),'junction');
  else cpSync(join(source,'web/assets',entry.name),join(target,'web/assets',entry.name));
}
for(const entry of Object.values(imageText)) for(const crop of entry.crops || []) {
  const bytes=readFileSync(resolve(crop.file));assert.equal(sha(bytes),crop.sha256,'Changed image crop');
  crop.src='assets/transcription/'+crop.sha256+'.png';
  const file=join(target,'web',crop.src);mkdirSync(resolve(file,'..'),{recursive:true});writeFileSync(file,bytes);
}
for(const file of ['app.mjs','core.mjs','render.mjs','styles.css']) cpSync(resolve('web',file),join(target,'web',file));
cpSync(join(source,'functions'),join(target,'functions'),{recursive:true});
cpSync(join(source,'schema.sql'),join(target,'schema.sql'));
const {MATERIAL_INDEX,MATERIAL_EXAMS}=await import(pathToFileURL(join(source,'web/catalog.mjs')));
const counts=()=>Object.fromEntries(auditFields.map(f=>[f,{}]));
const before=counts(),after=counts(),queue=[],changes=[],packs=[],seen=new Set(),supplementaryPending=[];let questions=0,originals=0,retainedImages=0,supplemented=0;
function count(counts,q) {for(const field of auditFields) {const status=fieldStatus(q,field);counts[field][status]=(counts[field][status] || 0)+1;}}
for(const pack of baseline.packs) {
  const raw=readFileSync(join(source,'web',pack.url));assert.equal(sha(raw),pack.sha256,pack.id);
  const rows=validateQuestions(JSON.parse(raw));assert.equal(rows.length,pack.count);
  const next=rows.map(q=>{
    const key=questionKey(q);assert.ok(!seen.has(key));seen.add(key);questions++;
    const original=pack.kind==='original' || /自作問題/.test(q.source);
    if(original) {originals++;if(q.images.length) retainedImages++;assert.ok(!records.has(key),'Original question outside scope');return q;}
    for(const image of [...q.images,...q.solutionImages]) {
      if(!records.has(key)) break;
      const entry=Object.values(assetEvidence).find(e=>e.src===image.src);
      if(entry) assert.equal(sha(readFileSync(join(source,'web',image.src))),entry.sha256,'Reviewed derivative image changed');
    }
    count(before,q);const evidence=textEvidence[key];let result=applyTextCorrection(q,records,evidence?.original || q);
    if(records.has(key) && evidence?.solution) {
      const solved=applySolutionText({...result,solutionImages:evidence.original.solutionImages},evidence.solution,records.get(key));
      result={...result,[evidence.solution.field]:solved[evidence.solution.field],textReview:solved.textReview};
    }
    result=applyReviewedImages(result,records,assetEvidence);
    const supplement=applySupplementaryImageText(result,imageText);
    if(supplement.question.passage!==result.passage || supplement.question.explanation!==result.explanation) supplemented++;
    result=supplement.question;supplementaryPending.push(...supplement.pending.map(p=>({key,...p})));count(after,result);
    if(result.images.length) retainedImages++;
    for(const field of ['id','examId','type','answer','audio','source','sourceUrl','year','term','subject','topic','category']) assert.deepEqual(result[field],q[field],key+' '+field);
    assert.equal(result.options.length,q.options.length);
    if(records.has(key)) changes.push({key,fields:Object.keys(records.get(key).after).filter(f=>textFields.includes(f)),before:Object.fromEntries(textFields.map(f=>[f,fieldStatus(q,f)])),after:Object.fromEntries(textFields.map(f=>[f,fieldStatus(result,f)]))});
    const flags=Object.fromEntries(auditFields.map(f=>[f,fieldStatus(result,f)]));
    const remaining=records.get(key)?.remaining || [];
    if(remaining.length || Object.values(flags).some(s=>!['source-verified','not-applicable','absent-in-source'].includes(s))) queue.push({key,packUrl:pack.url,fields:flags,remaining,reason:remaining.length?'Known source regions still need transcription':'Source comparison still required; inventory flags do not establish absence or correctness',sourceUrl:q.sourceUrl});
    return result;
  });
  assert.deepEqual(validateQuestions(next),next);const compact=compactQuestionPack(next);assert.deepEqual(validateQuestions(compact),next);
  const bytes=JSON.stringify(compact);writeFileSync(join(target,'web',pack.url),bytes);packs.push({...pack,sha256:sha(bytes)});
}
assert.equal(questions,baseline.questions);assert.equal(changes.length,records.size,'Correction target not present');
writeFileSync(join(target,'web/catalog.mjs'),`export const BUILTIN_QUESTIONS=[];\nexport const MATERIAL_INDEX=${JSON.stringify(MATERIAL_INDEX)};\nexport const MATERIAL_PACKS=${JSON.stringify(packs)};\nexport const MATERIAL_EXAMS=${JSON.stringify(MATERIAL_EXAMS)};\n`);
writeLibraryCatalog(join(target,'web'),MATERIAL_INDEX,packs,MATERIAL_EXAMS);
const report={source,sourceManifestSha256:sha(manifestBytes),target,questions,packs:packs.length,excludedOriginalQuestions:originals,existingMaterialQuestions:questions-originals,retainedQuestionImages:retainedImages,before,after,changes,supplemented,imageText:imageTextReport,supplementaryPending,complete:false,
  limitations:['Inventory flags are not a source coverage audit. Unreviewed text may be correct or defective.','Empty passage/evaluation fields may be not applicable; availability is unknown until reviewed.','Only recorded regions have been visually compared. Remaining queue requires source review.','Local asset junction depends on the preserved source build; this candidate is for local review only.'],
  checks:{identityOrderSourceYearAnswers:'pass',reviewedImageReplacement:'pass',packValidationAndRoundtrip:'pass',sourceHashes:'pass',browser:'pending'}};
writeFileSync(join(target,'manifest.json'),JSON.stringify({...baseline,packs,transcription:{report:'transcription-report.json',sourceManifestSha256:sha(manifestBytes),cropMethod:imageTextReport.cropMethod,allImagesAttempted:imageTextReport.allImagesAttempted}},null,2));
cpSync(correctionFile,join(target,'text-corrections.json'));
writeFileSync(join(target,'transcription-report.json'),JSON.stringify(report,null,2));
writeFileSync(join(target,'review-queue.json'),JSON.stringify(queue));
writeFileSync(join(target,'image-text-evidence.json'),JSON.stringify(imageText));
for(const file of ['asset-evidence.json','compaction-report.json']) cpSync(join(source,file),join(target,file));
assert.equal(sha(readFileSync(join(source,'manifest.json'))),sha(manifestBytes),'Source build changed during generation');
const pointer=join(out,'current.json'),temporary=pointer+'.tmp';writeFileSync(temporary,JSON.stringify({directory:target}));renameSync(temporary,pointer);
console.log(JSON.stringify({directory:target,questions,corrected:changes.length,before,after},null,2));
