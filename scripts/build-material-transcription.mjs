// Local derivative only. The existing successful build and original imports are read-only.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,readdirSync,cpSync,symlinkSync,openSync,closeSync,unlinkSync,renameSync,existsSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {spawnSync} from 'node:child_process';
import {validateQuestions,questionKey} from '../web/core.mjs';
import {compactQuestionPack,writeLibraryCatalog} from './library-catalog.mjs';
import {loadCorrections,applyTextCorrection,applySolutionText,applyReviewedImages,applySupplementaryImageText,sourceMarkerText,fieldStatus,textFields,auditFields,sha,correctionFile} from './material-transcription.mjs';
import {loadAnswerCorrespondence,applyAnswerCorrespondence,answerCorrespondenceFile} from './material-answer-correspondence.mjs';

const read=file=>JSON.parse(readFileSync(file));
const source=resolve(process.argv.slice(2).find(arg=>!arg.startsWith('--')) || read('build/private-compact/current.json').directory);
const lock=resolve('build/private-build.lock'),fd=openSync(lock,'wx');
process.on('exit',()=>{closeSync(fd);unlinkSync(lock);});
for(const signal of ['SIGINT','SIGTERM']) process.on(signal,()=>process.exit(1));
const previousPointer=resolve('build/material-transcription/current.json');
const progressBaseline=existsSync(previousPointer)?resolve(read(previousPointer).directory):null;
const manifestBytes=readFileSync(join(source,'manifest.json')),baseline=JSON.parse(manifestBytes),records=loadCorrections();
const answerCorrespondence=loadAnswerCorrespondence();
const assetEvidence=existsSync(join(source,'asset-evidence.json'))?read(join(source,'asset-evidence.json')):{};
const textEvidence=existsSync(join(source,'text-evidence.json'))?read(join(source,'text-evidence.json')):{};
const imageGeneratorHashes=Object.fromEntries(['scripts/extract-material-image-text.py','scripts/compact-material.py','private-data/material-transcription/unicode-repairs.json'].map(file=>[file,sha(readFileSync(file))]));
imageGeneratorHashes.sourceManifestSha256=sha(manifestBytes);
imageGeneratorHashes.preparedReports=Object.fromEntries(readdirSync('private-data/github-material/prepared').filter(file=>file.endsWith('report.json')).map(file=>[file,sha(readFileSync(join('private-data/github-material/prepared',file)))]));
const reusedImageExtraction=process.argv.includes('--reuse-image-extraction');
if(reusedImageExtraction) assert.deepEqual(read('build/material-image-text/generator-hashes.json'),imageGeneratorHashes,'Image extraction code/calibration changed; rerun extraction');
if(!process.argv.includes('--reuse-image-extraction')) {
  const extraction=spawnSync('python',['scripts/extract-material-image-text.py',source],{stdio:'inherit'});
  assert.equal(extraction.status,0,'Image text extraction failed; previous successful build retained');
  writeFileSync('build/material-image-text/generator-hashes.json',JSON.stringify(imageGeneratorHashes));
}
const imageText=read('build/material-image-text/text.json'),imageTextReport=read('build/material-image-text/report.json');
assert.equal(imageTextReport.allImagesAttempted,true);
assert.equal(Object.keys(imageText).length,imageTextReport.images);
const solutionInput=[];
for(const pack of baseline.packs) for(const q of validateQuestions(read(join(source,'web',pack.url)))) if(q.solutionImages.length || q.examId==='sme-consultant') solutionInput.push({...q,key:questionKey(q),packUrl:pack.url});
mkdirSync('build/material-solution-text',{recursive:true});
writeFileSync('build/material-solution-text/input.json',JSON.stringify(solutionInput));
const scopedGeneratorHashes={...imageGeneratorHashes,inputSha256:sha(readFileSync('build/material-solution-text/input.json')),scripts:Object.fromEntries(['scripts/extract-scoped-solution-text.py','scripts/extract-scoped-case-text.py'].map(file=>[file,sha(readFileSync(file))]))};
const scopedOutputFiles=['build/material-solution-text/text.json','build/material-solution-text/pending.json','build/material-case-text/text.json','build/material-case-text/pending.json'];
if(process.argv.includes('--reuse-scoped-extraction')) {
  const cached=read('build/material-solution-text/generator-hashes.json');assert.deepEqual(cached.generators,scopedGeneratorHashes,'Scoped extraction code/input changed');
  for(const [file,hash] of Object.entries(cached.outputs)) assert.equal(sha(readFileSync(file)),hash,'Scoped extraction cache changed');
} else {
  const solutionExtraction=spawnSync('python',['scripts/extract-scoped-solution-text.py',source,'build/material-solution-text/input.json','build/material-solution-text','build/material-image-text/text.json'],{stdio:'inherit'});
  assert.equal(solutionExtraction.status,0,'Scoped solution extraction failed; previous successful build retained');
  const caseExtraction=spawnSync('python',['scripts/extract-scoped-case-text.py',source,'build/material-solution-text/input.json','build/material-image-text/text.json','build/material-case-text'],{stdio:'inherit'});
  assert.equal(caseExtraction.status,0,'Scoped case extraction failed; previous successful build retained');
  writeFileSync('build/material-solution-text/generator-hashes.json',JSON.stringify({generators:scopedGeneratorHashes,outputs:Object.fromEntries(scopedOutputFiles.map(file=>[file,sha(readFileSync(file))]))}));
}
const scopedSolutions=read('build/material-solution-text/text.json');
const scopedCases=read('build/material-case-text/text.json');
const numericGeneratorHashes={...imageGeneratorHashes,'scripts/extract-numeric-question-text.py':sha(readFileSync('scripts/extract-numeric-question-text.py'))};
const reusedNumericExtraction=process.argv.includes('--reuse-numeric-extraction');
if(reusedNumericExtraction) {
  const cached=read('build/material-image-text/numeric-generator-hashes.json');
  assert.deepEqual(cached.generators,numericGeneratorHashes,'Numeric extraction code/source/calibration changed');
  for(const [file,hash] of Object.entries(cached.outputs)) assert.equal(sha(readFileSync(file)),hash,'Numeric extraction cache changed');
} else {
  const numericExtraction=spawnSync('python',['scripts/extract-numeric-question-text.py',source],{stdio:'inherit'});
  assert.equal(numericExtraction.status,0,'Per-question extraction failed; previous successful build retained');
  writeFileSync('build/material-image-text/numeric-generator-hashes.json',JSON.stringify({generators:numericGeneratorHashes,outputs:Object.fromEntries(['build/material-image-text/numeric-text.json','build/material-image-text/numeric-review.json'].map(file=>[file,sha(readFileSync(file))]))}));
}
const numericText=read('build/material-image-text/numeric-text.json'),numericPending=read('build/material-image-text/numeric-review.json');
const numericUnresolved=new Set(numericPending.map(r=>r.key));
const imageUsers=new Map();
for(const pack of baseline.packs) for(const q of validateQuestions(read(join(source,'web',pack.url)))) {
  for(const field of ['images','solutionImages']) for(const image of q[field]) {
    const id=field+'\0'+image.src;
    if(!imageUsers.has(id)) imageUsers.set(id,new Set());
    imageUsers.get(id).add(q.id.replace(/-s\d+$/,''));
  }
}
assert.equal(imageTextReport.sourceManifestSha256,sha(manifestBytes));
for(const [src,entry] of Object.entries(imageText)) assert.equal(sha(readFileSync(join(source,'web',src))),entry.identity.imageSha256,'Source image changed');
const out=resolve('build/material-transcription'),resumeArg=process.argv.find(arg=>arg.startsWith('--resume-generated='));
const target=resumeArg?resolve(resumeArg.slice('--resume-generated='.length)):join(out,Date.now().toString());
if(resumeArg) {assert.equal(resolve(target,'..'),out);assert.notEqual(target,progressBaseline);assert.ok(!existsSync(join(target,'manifest.json')),'Cannot resume a finished or historical build');}
mkdirSync(join(target,'web/material'),{recursive:true});
if(!resumeArg) for(const entry of readdirSync(join(source,'web'),{withFileTypes:true})) {
  if(entry.name==='material' || entry.name==='assets') continue;
  cpSync(join(source,'web',entry.name),join(target,'web',entry.name),{recursive:true});
}
// Share immutable folders; new crops live in this derivative's own asset folder.
mkdirSync(join(target,'web/assets'),{recursive:true});
if(!resumeArg) for(const entry of readdirSync(join(source,'web/assets'),{withFileTypes:true})) {
  if(entry.isDirectory()) symlinkSync(join(source,'web/assets',entry.name),join(target,'web/assets',entry.name),'junction');
  else cpSync(join(source,'web/assets',entry.name),join(target,'web/assets',entry.name));
}
for(const entry of [...Object.values(imageText),...Object.values(numericText),...Object.values(scopedCases),...Array.from(records.values(),r=>r.imageReplacement || {})]) for(const crop of entry.crops || []) {
  const bytes=readFileSync(resolve(crop.file));assert.equal(sha(bytes),crop.sha256,'Changed image crop');
  crop.src='assets/transcription/'+crop.sha256+'.png';
  const file=join(target,'web',crop.src);if(resumeArg) assert.equal(sha(readFileSync(file)),crop.sha256);else {mkdirSync(resolve(file,'..'),{recursive:true});writeFileSync(file,bytes);}
}
for(const file of ['app.mjs','core.mjs','render.mjs','styles.css']) cpSync(resolve('web',file),join(target,'web',file));
cpSync(join(source,'functions'),join(target,'functions'),{recursive:true});
cpSync(join(source,'schema.sql'),join(target,'schema.sql'));
const {MATERIAL_INDEX,MATERIAL_EXAMS}=await import(pathToFileURL(join(source,'web/catalog.mjs')));
const counts=()=>Object.fromEntries(auditFields.map(f=>[f,{}]));
const before=counts(),after=counts(),queue=[],changes=[],packs=[],seen=new Set(),supplementaryPending=[];let questions=0,originals=0,retainedImages=0,supplemented=0;
const imageInventory=[];
const numericAppliedKeys=new Set();
function count(counts,q) {for(const field of auditFields) {const status=fieldStatus(q,field);counts[field][status]=(counts[field][status] || 0)+1;}}
for(const pack of baseline.packs) {
  const raw=readFileSync(join(source,'web',pack.url));assert.equal(sha(raw),pack.sha256,pack.id);
  const rows=validateQuestions(JSON.parse(raw));assert.equal(rows.length,pack.count);
  const next=validateQuestions(rows.map(q=>{
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
    const caseText=scopedCases[key];
    if(caseText) {
      assert.deepEqual(result.images.map(i=>i.src),caseText.removed,'Scoped case image mapping changed');
      assert.equal(result.type,'written');
      for(const e of caseText.evidence) {assert.equal(sha(e.text),e.textSha256);assert.equal(sha(readFileSync(join(source,'web',e.image))),e.imageSha256);}
      result={...result,prompt:caseText.prompt,passage:caseText.passage,images:caseText.crops.map((c,i)=>({src:c.src,alt:`事例・設問の原本照合待ち ${i+1}`}))};
    }
    const solution=scopedSolutions[key];
    if(solution) {
      assert.equal(sha(solution.text),solution.textSha256);
      assert.deepEqual(result.solutionImages.map(i=>i.src),solution.removed,'Scoped solution image mapping changed');
      for(const e of solution.evidence) assert.equal(sha(readFileSync(e.imageFile || join(source,'web',e.image))),e.imageSha256);
      if(solution.previousField) {
        assert.equal(result[solution.previousField],solution.previousValue,'Prior whole-page solution text changed');
        result={...result,[solution.previousField]:solution.originalPreviousValue};
      }
      result={...result,[solution.field]:(solution.kind==='official-intent'?'公式出題趣旨（原文）\n':'公式正解・配点（原文）\n')+solution.text,solutionImages:[],explanationSource:solution.kind==='official-intent'?'公式出題趣旨（模範解答ではありません）':'公式正解・配点（原文文字化）'};
      if(solution.kind==='official-intent') result.modelAnswer='公式出題趣旨を解説欄で確認してください。模範解答・配点基準は未公表のため、自動採点できません。';
      // Automatic typography/pixel checks are not full visual proofreading.
      if(result.textReview?.[solution.field]) {result.textReview={...result.textReview};delete result.textReview[solution.field];}
    }
    const numeric=numericText[key];let numericApplied=false;
    if(numeric && /原本画像のこの問題番号/.test(result.prompt) && result.options.every((o,i)=>o===String(i+1))) {
      assert.equal(numeric.options.length,result.options.length);
      assert.ok(numeric.evidence.every(e=>result.images.some(i=>i.src===e.image)),'Per-question source mapping changed');
      result={...result,prompt:sourceMarkerText(numeric.prompt),options:numeric.options.map(sourceMarkerText),passage:sourceMarkerText(numeric.passage || ''),images:numeric.crops.map((c,i)=>({src:c.src,alt:`図・原本照合待ちの部分 ${i+1}`}))};
      numericApplied=true;
      numericAppliedKeys.add(key);
    }
    const scoped=Boolean(caseText) || numericApplied || numericUnresolved.has(key);
    const unscoped=new Set();
    const localText=Object.create(imageText);
    for(const field of ['images','solutionImages']) for(const image of result[field]) if(imageUsers.get(field+'\0'+image.src)?.size>1) {
      if(field==='images' && caseText) continue;
      unscoped.add(field+'\0'+image.src);
      localText[image.src]={...imageText[image.src],text:'',textSha256:sha(''),nativeVerified:false,crops:undefined};
      supplementaryPending.push({key,src:image.src,field,reason:'question-range-not-established: source image shared by distinct questions'});
    }
    const supplement=applySupplementaryImageText(scoped?{...result,images:[]}:result,localText);
    if(scoped) supplement.question.images=result.images;
    if(supplement.question.passage!==result.passage || supplement.question.explanation!==result.explanation) supplemented++;
    result=applyAnswerCorrespondence(supplement.question,answerCorrespondence);supplementaryPending.push(...supplement.pending.map(p=>({key,...p})));count(after,result);
    for(const field of ['images','solutionImages']) for(const image of q[field]) {
      const entry=imageText[image.src],retained=result[field].some(i=>i.src===image.src);
      const questionScoped=(numericApplied || caseText) && field==='images';
      imageInventory.push({key,field,src:image.src,method:questionScoped?'per-question':solution && field==='solutionImages'?'scoped-solution':entry?.method,action:retained?'retained':(questionScoped?result.images.length:entry?.crops)?'cropped':'text',reason:retained?(unscoped.has(field+'\0'+image.src)?'question range not established; shared source image':entry?.retainedReason || (entry?.method==='native'?'source review required':'OCR requires source comparison')):undefined});
    }
    if(result.images.length) retainedImages++;
    const expected=applyAnswerCorrespondence(q,answerCorrespondence);
    for(const field of ['id','examId','type','answer','audio','source','sourceUrl','year','term','subject','topic','category','acceptedAnswers','answerPending','previousType']) assert.deepEqual(result[field],expected[field],key+' '+field);
    assert.equal(result.options.length,q.options.length);
    if(records.has(key)) changes.push({key,fields:Object.keys(records.get(key).after).filter(f=>textFields.includes(f)),before:Object.fromEntries(textFields.map(f=>[f,fieldStatus(q,f)])),after:Object.fromEntries(textFields.map(f=>[f,fieldStatus(result,f)]))});
    const flags=Object.fromEntries(auditFields.map(f=>[f,fieldStatus(result,f)]));
    const remaining=records.get(key)?.remaining || [];
    if(remaining.length || Object.values(flags).some(s=>!['source-verified','not-applicable','absent-in-source'].includes(s))) queue.push({key,packUrl:pack.url,fields:flags,remaining,reason:remaining.length?'Known source regions still need transcription':'Source comparison still required; inventory flags do not establish absence or correctness',sourceUrl:q.sourceUrl});
    return result;
  }));
  assert.deepEqual(validateQuestions(next),next);const compact=compactQuestionPack(next);assert.deepEqual(validateQuestions(compact),next);
  const bytes=JSON.stringify(compact),packFile=join(target,'web',pack.url);
  if(resumeArg && existsSync(packFile)) assert.equal(sha(readFileSync(packFile)),sha(bytes),'Previously generated question pack changed');
  else writeFileSync(packFile,bytes);
  packs.push({...pack,...(next.some(q=>answerCorrespondence.has(questionKey(q)))?{subject:next[0].subject}:{}),sha256:sha(bytes)});
}
assert.equal(questions,baseline.questions);assert.equal(changes.length,records.size,'Correction target not present');
const correctedIndex=MATERIAL_INDEX.map(q=>{const row=answerCorrespondence.get(questionKey(q));if(!row) return q;const type=row.sets.length?(row.sets[0].length===1?'single':'multiple'):q.type;return {...q,type,subject:row.subject,...(q.topic?{topic:q.topic.replace(/(国家試験 )午後( 問\d+)$/,'$1'+row.subject+'$2')}:{}),...(q.type!==type?{previousType:q.type}:{})};});
writeFileSync(join(target,'web/catalog.mjs'),`export const BUILTIN_QUESTIONS=[];\nexport const MATERIAL_INDEX=${JSON.stringify(correctedIndex)};\nexport const MATERIAL_PACKS=${JSON.stringify(packs)};\nexport const MATERIAL_EXAMS=${JSON.stringify(MATERIAL_EXAMS)};\n`);
writeLibraryCatalog(join(target,'web'),correctedIndex,packs,MATERIAL_EXAMS);
const report={source,sourceManifestSha256:sha(manifestBytes),target,progressBaseline,progressReport:'retained-material/progress.json',progressMarkdown:'retained-material/progress.md',questions,packs:packs.length,excludedOriginalQuestions:originals,existingMaterialQuestions:questions-originals,retainedQuestionImages:retainedImages,before,after,changes,supplemented,imageText:imageTextReport,imageGeneratorHashes,reusedImageExtraction,numericQuestionsConverted:numericAppliedKeys.size,supplementaryPending,complete:false,
  limitations:['Inventory flags are not a source coverage audit. Unreviewed text may be correct or defective.','Empty passage/evaluation fields may be not applicable; availability is unknown until reviewed.','Only recorded regions have been visually compared. Remaining queue requires source review.','Local asset junction depends on the preserved source build; this candidate is for local review only.'],
  checks:{identityOrderSourceYearAnswers:'pass',reviewedImageReplacement:'pass',packValidationAndRoundtrip:'pass',sourceHashes:'pass',browser:'pending'}};
writeFileSync(join(target,'manifest.json'),JSON.stringify({...baseline,packs,transcription:{report:'transcription-report.json',sourceManifestSha256:sha(manifestBytes),cropMethod:imageTextReport.cropMethod,allImagesAttempted:imageTextReport.allImagesAttempted}},null,2));
cpSync(correctionFile,join(target,'text-corrections.json'));
if(existsSync(answerCorrespondenceFile)) cpSync(answerCorrespondenceFile,join(target,'answer-correspondence.json'));
const unicodeRepairs=resolve('private-data/material-transcription/unicode-repairs.json');
if(existsSync(unicodeRepairs)) cpSync(unicodeRepairs,join(target,'unicode-repairs.json'));
writeFileSync(join(target,'transcription-report.json'),JSON.stringify(report,null,2));
writeFileSync(join(target,'review-queue.json'),JSON.stringify(queue));
writeFileSync(join(target,'image-conversion-inventory.json'),JSON.stringify(imageInventory));
writeFileSync(join(target,'image-text-evidence.json'),JSON.stringify(imageText));
writeFileSync(join(target,'numeric-text-evidence.json'),JSON.stringify(numericText));
writeFileSync(join(target,'numeric-review.json'),JSON.stringify(numericPending));
writeFileSync(join(target,'scoped-solution-evidence.json'),JSON.stringify(scopedSolutions));
cpSync('build/material-solution-text/pending.json',join(target,'scoped-solution-pending.json'));
writeFileSync(join(target,'scoped-case-evidence.json'),JSON.stringify(scopedCases));
cpSync('build/material-case-text/pending.json',join(target,'scoped-case-pending.json'));
for(const file of ['asset-evidence.json','compaction-report.json']) cpSync(join(source,file),join(target,file));
assert.equal(sha(readFileSync(join(source,'manifest.json'))),sha(manifestBytes),'Source build changed during generation');
const inventory=spawnSync(process.execPath,['scripts/inventory-retained-material.mjs',target,join(target,'retained-material'),...(progressBaseline?[progressBaseline]:[])],{stdio:'inherit'});
assert.equal(inventory.status,0,'Remaining-image inventory failed; previous successful build retained');
const pointer=join(out,'current.json'),temporary=pointer+'.tmp';writeFileSync(temporary,JSON.stringify({directory:target}));renameSync(temporary,pointer);
console.log(JSON.stringify({directory:target,questions,corrected:changes.length,before,after},null,2));
