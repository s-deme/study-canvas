import assert from 'node:assert/strict';
import {readFileSync,mkdtempSync,mkdirSync,writeFileSync,rmSync} from 'node:fs';
import {tmpdir} from 'node:os';
import {join,dirname,resolve} from 'node:path';
import {questionProgress,summarizeImages,compareProgress,progressMarkdown} from '../scripts/material-progress.mjs';
import {writeInventory,bindPreparedRegions} from '../scripts/inventory-retained-material.mjs';

const question=(id,images=[],extra={})=>({id,type:'single',prompt:'原本画像を確認',options:['1','2'],passage:'',modelAnswer:'',explanation:'',evaluationGuide:'',images:images.map(src=>({src,alt:'検証用画像'})),solutionImages:[],...extra});
const sharedAssets={'assets/github-material/one.png':{src:'shared-blank',sourceSha256:'blank hash'},'assets/github-material/two.png':{src:'shared-blank',sourceSha256:'blank hash'}};
const prepared=(id,file,page)=>({status:'prepared',examId:'fixture',sourceFile:file,sources:[{file,sha256:file+' hash'}],questions:[{id,images:[{file:id+'.png',sha256:'blank hash',page,rect:[0,0,10,10]}]}]});
const bindings=bindPreparedRegions(sharedAssets,[prepared('one','one.pdf',1),prepared('two','two.pdf',8)]);
assert.equal(bindings.get('fixture::one\0images\0shared-blank').sourceFile,'private-data/github-material/one.pdf');
assert.equal(bindings.get('fixture::two\0images\0shared-blank').page,8,'Identical blank pixels do not imply the same source question/page');
const repeated=prepared('one','one.pdf',1);repeated.questions[0].images.push({...repeated.questions[0].images[0],page:2});
assert.equal(bindPreparedRegions(sharedAssets,[repeated]).get('fixture::one\0images\0shared-blank').sourceFile,undefined,'Repeated identical images retain source ambiguity');
assert.throws(()=>bindPreparedRegions({...sharedAssets,'assets/github-material/one.png':{src:'shared-blank',sourceSha256:'wrong'}},[prepared('one','one.pdf',1)]),/region\/asset hash/);
const state=(q,excluded=false)=>questionProgress(q,excluded);
const inventory=(states,urls)=>({summary:{source:'fixture'},states:new Map(states),assets:new Map(urls.map(src=>[src,{}]))});
const before=inventory([
  ['full',state(question('full',['full.png']))],['partial',state(question('partial',['partial.png']))],
  ['restore',state(question('restore',[],{prompt:'以前の本文',options:['選択肢一','選択肢二']}))],
  ['removed',state(question('removed'))],['solution',state(question('solution',[],{solutionImages:[{src:'answer.png'}]}))],
  ['original',state(question('original',['original.png']),true)]
],['full.png','partial.png','answer.png','original.png']);
const text={prompt:'問題の本文',options:['選択肢一','選択肢二']};
const crops=['assets/transcription/a.png','assets/transcription/b.png','assets/transcription/c.png'];
const after=inventory([
  ['full',state(question('full',[],text))],['partial',state(question('partial',crops,text))],
  ['restore',state(question('restore',['restored.png'],{prompt:'修正した本文',options:['選択肢一','選択肢二']}))],
  ['added',state(question('added',[],text))],['solution',state(question('solution',[],{explanation:'回答理由の本文'}))],
  ['original',state(question('original',[],text),true)]
],[...crops,'restored.png']);
const diff=compareProgress(after,before);
assert.deepEqual(diff.changes.fullyText,['full']);
assert.deepEqual(diff.changes.partialText,['partial']);
assert.deepEqual(diff.changes.restored,['restore']);
assert.deepEqual(diff.changes.addedQuestions,['added']);
assert.deepEqual(diff.changes.removedQuestions,['removed']);
assert.deepEqual(diff.changes.solutionUpdated,['solution']);
assert.deepEqual(diff.changes.solutionImagesRemoved,['solution']);
assert.deepEqual(diff.changes.solutionFullyText,['solution']);
assert.equal(diff.quality.sourceVerified,0,'Unreviewed text must not become source-verified');
assert.equal(state(question('pending',crops,{...text,prompt:'本文［判読保留：画像1参照］'})).textReady,false);
assert.equal(state(question('layout',crops,{...text,prompt:'本文［組版照合待ち：画像1参照］'})).textReady,false);
assert.equal(state(question('reviewed',[],{...text,textReview:{prompt:'source-verified',options:'source-verified'}})).sourceVerified,true);
for(const changed of Object.values(compareProgress(after,after).changes)) assert.equal(changed.length,0);
assert.equal(compareProgress(after,after).images.net,0);
assert.equal(compareProgress(after).comparable,false);
assert.equal(compareProgress(after).changes,null);
const more=inventory([...after.states],[...after.assets.keys(),'assets/transcription/d.png']);
assert.ok(compareProgress(more,before).images.net>0);
assert.deepEqual(compareProgress(more,before).changes.fullyText,['full'],'Image growth can coexist with transcription progress');

const rows=[
  {key:'one',src:'original',origin:'original',purpose:'original',unresolved:['問題範囲未確定']},
  {key:'two',src:'original',origin:'original',purpose:'original',unresolved:['問題範囲未確定']},
  {key:'one',src:'figure',origin:'crop',purpose:'figureCandidate',unresolved:[]},
  {key:'one',src:'line',origin:'crop',purpose:'unreadableText',unresolved:['文字コード・組版','OCR・原本照合待ち']},
  {key:'two',src:'unknown',origin:'crop',purpose:'unknownCrop',unresolved:['原本対応なし']},
  {key:'one',src:'mixed',origin:'crop',purpose:'figureCandidate',unresolved:[]},
  {key:'two',src:'mixed',origin:'crop',purpose:'unreadableText',unresolved:['OCR・原本照合待ち']}
];
const assets=new Map();
rows.forEach((r,i)=>{if(!assets.has(r.src)) assets.set(r.src,{src:r.src,bytes:10,references:[]});assets.get(r.src).references.push(i);});
const summary=summarizeImages(rows,assets,new Map(['figure','line','unknown','mixed','unused'].map(src=>[src,{parents:new Set(['original'])}])));
assert.deepEqual(summary.kinds.original,{images:1,references:2,bytes:10});
assert.equal(summary.kinds.figureCandidate.images,1);
assert.equal(summary.kinds.unreadableText.images,1);
assert.equal(summary.kinds.unknownCrop.images,2);
assert.equal(summary.unresolved['問題範囲未確定'].questions,2);
assert.equal(summary.unresolved['問題範囲未確定'].images,1);
assert.equal(summary.unusedGeneratedCrops,1);
assert.equal(summary.coexistingParentImages,1);
assert.deepEqual(assets.get('figure').parentImages,['original']);
assert.equal(summary.storage.archivePDFs,null);
const current={source:'fixture',breakdown:summary,uniqueImages:5,imageReferences:7,uniquePDFs:1};
assert.match(progressMarkdown({current,previous:null,comparison:compareProgress(after)}),/比較不可/);

const directory=mkdtempSync(join(tmpdir(),'material-progress-'));
try {
  const json=(name,value)=>writeFileSync(join(directory,name),JSON.stringify(value));
  mkdirSync(join(directory,'web/assets/transcription'),{recursive:true});
  const original='assets/original.png',crop='assets/transcription/line.png',unknown='assets/transcription/unknown.png';
  for(const src of [original,crop,unknown]) writeFileSync(join(directory,'web',src),'fixture pixels');
  json('manifest.json',{questions:3,packs:[{url:'questions.json'}]});
  json('web/questions.json',[question('one',[original],{...text,examId:'fixture',answer:0}),question('two',[crop],{...text,examId:'fixture',answer:0}),question('three',[unknown],{...text,prompt:'図の問い',examId:'fixture',answer:0})]);
  json('image-text-evidence.json',{[original]:{identity:{region:null},method:'native+ocr',text:'OCR candidate',crops:[{src:crop,reason:'Unreadable PDF character mapping'}]}});
  json('numeric-text-evidence.json',{});json('numeric-review.json',[]);
  json('image-conversion-inventory.json',[{key:'fixture::one',field:'images',src:original,action:'retained',reason:'question range not established'}]);
  const output=join(directory,'report');
  const initial=writeInventory(directory,output);
  assert.equal(initial.comparison.comparable,false);
  assert.equal(initial.current.breakdown.kinds.unreadableText.images,1);
  assert.equal(initial.current.breakdown.kinds.unknownCrop.images,1,'A figure keyword without crop evidence is not a figure candidate');
  assert.equal(initial.current.breakdown.coexistingParentImages,1);
  assert.equal(initial.current.breakdown.unresolved['原本対応なし'].images,3);
  assert.equal(initial.current.breakdown.unresolved['OCR・原本照合待ち'].images,2);
  assert.equal(initial.current.breakdown.unresolved['問題範囲未確定'].images,1);
  const same=writeInventory(directory,output,directory);
  for(const ids of Object.values(same.comparison.changes)) assert.equal(ids.length,0);
  assert.equal(same.comparison.images.net,0);
  assert.match(readFileSync(join(output,'progress.md'),'utf8'),/未判読文字の切り抜き/);
  assert.equal(JSON.parse(readFileSync(join(output,'summary.json'))).uniqueImages,3);
  json('text-corrections.json',[{imageReplacement:{images:[{src:original}],crops:[{field:'images',src:unknown,sourceFile:'fixture.pdf',sourceSha256:'source hash',page:0,sourceRect:[0,0,10,10],reason:'Direct visual comparison: required graph',figureNeedEstablished:true}]}}]);
  writeInventory(directory,output);
  const reviewed=JSON.parse(readFileSync(join(output,'references.json'))).find(r=>r.src===unknown);
  assert.equal(reviewed.category,'図として必要');assert.equal(reviewed.figureNeedEstablished,true);assert.equal(reviewed.categoryProvisional,false);
  assert.equal(reviewed.sourceFile,'fixture.pdf');assert.equal(reviewed.page,1);assert.ok(!reviewed.unresolved.includes('OCR・原本照合待ち'));
} finally {
  assert.equal(dirname(resolve(directory)),resolve(tmpdir()));
  rmSync(directory,{recursive:true});
}

if(process.argv[2]) {
  const report=JSON.parse(readFileSync(process.argv[2]));
  assert.equal(report.current.uniqueImages,51834);
  assert.equal(report.current.breakdown.kinds.original.images,47355);
  assert.equal(report.previous.breakdown.kinds.original.images,47901);
  assert.equal(report.current.uniqueImages-report.current.breakdown.kinds.original.images,4479);
  assert.equal(report.previous.uniqueImages-report.previous.breakdown.kinds.original.images,4408);
  assert.equal(report.comparison.images.net,-475);
  assert.equal(report.current.breakdown.unresolved['原本対応なし'].images,3774);
}
console.log('PASS: progress units, shared/mixed images, source-review separation, restoration, exclusions, image growth and same-build comparisons');
