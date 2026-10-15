// Inventory the actual delivered rows; extraction success alone is not proofreading.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,statSync,existsSync,readdirSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {pathToFileURL} from 'node:url';
import {validateQuestions,questionKey} from '../web/core.mjs';
import {fieldStatus,sha} from './material-transcription.mjs';
import {questionProgress,summarizeImages,compareProgress,progressMarkdown} from './material-progress.mjs';

const read=file=>JSON.parse(readFileSync(file));
export function bindPreparedRegions(assetEvidence,packs) {
  const scopedRegions=new Map();
  for(const pack of packs) {
    if(pack.status!=='prepared') continue;
    const hashes=new Map((pack.sources || []).map(s=>[s.file,s.sha256]));
    for(const record of pack.questions || []) for(const field of ['images','solutionImages']) for(const region of record[field] || []) {
      const originalSrc='assets/github-material/'+region.file,asset=assetEvidence[originalSrc];
      const name=region.sourceFile || (field==='solutionImages'?pack.answerFile:null) || pack.sourceFile;
      if(!asset || !name || !hashes.has(name)) continue;
      assert.equal(asset.sourceSha256,region.sha256,'Prepared region/asset hash: '+originalSrc);
      const token=pack.examId+'::'+record.id+'\0'+field+'\0'+asset.src;
      const bound={...region,sourceFile:'private-data/github-material/'+name,sourceSha256:hashes.get(name),sourceMappingMethod:'prepared-question-region'};
      const prior=scopedRegions.get(token);
      scopedRegions.set(token,prior && (prior.page!==bound.page || JSON.stringify(prior.rect)!==JSON.stringify(bound.rect))?{sourceMappingMethod:'ambiguous-repeated-region'}:bound);
    }
  }
  return scopedRegions;
}
export function collectInventory(source) {
  source=resolve(source);
  const manifest=read(join(source,'manifest.json')),evidence=read(join(source,'image-text-evidence.json'));
  // Compacted blank images can be shared across unrelated PDFs. Bind each
  // reference through its prepared question record, rather than the first hash user.
  let scopedRegions=new Map();const assetFile=join(source,'asset-evidence.json');
  if(existsSync(assetFile)) {
    const assetEvidence=read(assetFile),prepared=resolve('private-data/github-material/prepared');
    scopedRegions=bindPreparedRegions(assetEvidence,readdirSync(prepared).filter(f=>f.endsWith('report.json')).flatMap(f=>read(join(prepared,f)).packs || []));
  }
  const cropSources=new Map();
  function addCrop(crop,region,parents) {
    const previous=cropSources.get(crop.src);
    cropSources.set(crop.src,{crop,region,parents:new Set([...(previous?.parents || []),...parents]),
      reasons:new Set([...(previous?.reasons || []),...(crop.reason?[crop.reason]:[])]),
      contentKinds:new Set([...(previous?.contentKinds || []),/Unreadable PDF character mapping|Unsupported PDF text placement/.test(crop.reason || '')?'unreadableText':'unspecified'])});
  }
  for(const [src,entry] of Object.entries(evidence)) for(const crop of entry.crops || []) addCrop(crop,entry.identity.region,[src]);
  for(const entry of Object.values(read(join(source,'numeric-text-evidence.json')))) for(const crop of entry.crops || []) {
    const parents=(entry.evidence || []).filter(e=>e.sourceFile===crop.sourceFile && e.page===crop.page && e.role===crop.role).map(e=>e.image);
    addCrop(crop,crop.sourceFile?{sourceFile:crop.sourceFile,sourceSha256:crop.sourceSha256,page:crop.page,rect:crop.sourceRect}:null,parents);
  }
  if(existsSync(join(source,'scoped-case-evidence.json'))) for(const entry of Object.values(read(join(source,'scoped-case-evidence.json')))) for(const crop of entry.crops || []) {
    const parents=entry.evidence.filter(e=>e.page===crop.page).map(e=>e.image);
    addCrop(crop,{sourceFile:crop.sourceFile,sourceSha256:crop.sourceSha256,page:crop.page,rect:crop.sourceRect},parents);
  }
  for(const entry of existsSync(join(source,'text-corrections.json'))?read(join(source,'text-corrections.json')):[]) for(const crop of entry.imageReplacement?.crops || []) {
    addCrop(crop,{sourceFile:crop.sourceFile,sourceSha256:crop.sourceSha256,page:crop.page,rect:crop.sourceRect},entry.imageReplacement[crop.field].map(i=>i.src));
  }
  const pending=new Map(read(join(source,'numeric-review.json')).map(r=>[r.key,r.reason]));
  if(existsSync(join(source,'scoped-case-pending.json'))) for(const r of read(join(source,'scoped-case-pending.json'))) pending.set(r.key,r.reason);
  const solutionPending=existsSync(join(source,'scoped-solution-pending.json'))?new Map(read(join(source,'scoped-solution-pending.json')).filter(r=>r.key.startsWith('sme-consultant::')).map(r=>[r.key,r.reason])):new Map();
  const mappingReasons=new Map(read(join(source,'image-conversion-inventory.json')).filter(r=>r.action==='retained' && /question range/.test(r.reason || '')).map(r=>[r.key+'\0'+r.field+'\0'+r.src,r.reason]));
  const assets=new Map(),rows=[],pdfs=new Map(),categories={},states=new Map(),assetHashes=new Map();let questions=0;
  const scopeUnresolved=reason=>/shared clinical|question crosses|option sequence|question range|question continuation|registered page mapping|explicit question anchors|merged question cell lacks parent|answer row\/child mapping|solution scope parser not implemented|continuation page is not registered/.test(reason);
  for(const pack of manifest.packs) for(const q of validateQuestions(read(join(source,'web',pack.url)))) {
    questions++;
    const key=questionKey(q);assert.ok(!states.has(key),'Duplicate question: '+key);
    states.set(key,questionProgress(q,pack.kind==='original' || /自作問題/.test(q.source)));
    for(const field of ['images','solutionImages']) for(const image of q[field]) {
      const entry=evidence[image.src],crop=cropSources.get(image.src),boundRegion=scopedRegions.get(key+'\0'+field+'\0'+image.src),region=boundRegion || entry?.identity?.region || crop?.region;
      const numericReason=field==='images'?pending.get(key):solutionPending.get(key);
      const reason=numericReason || mappingReasons.get(key+'\0'+field+'\0'+image.src) || crop?.crop.reason || entry?.retainedReason || (image.src.startsWith('assets/transcription/')?'Figure or unresolved source region preserved as an exact crop; full visual review still required':entry && !entry.text.trim()?'OCR returned no legible text after high-resolution retry; blank, header-only, graphical or unreadable region requires source comparison':entry?.method==='native'?'Native text extracted; source layout review still required':'OCR extracted; source comparison still required');
      const figureRequired=image.src.startsWith('assets/transcription/') && !crop?.crop.reason && fieldStatus(q,'prompt')!=='placeholder' && /図|写真|グラフ|別冊|地図|波形/.test(q.prompt+' '+q.options.join(' '));
      const category=crop?.crop.figureNeedEstablished?'図として必要':crop?.crop.reason?'OCR・原本照合待ち':image.src.startsWith('assets/transcription/')?figureRequired?'図として必要':'OCR・原本照合待ち':scopeUnresolved(reason)?'問題範囲・共通症例の対応未解決':entry?.method==='native' || /unmapped|styled|columns|shading|formula|non-horizontal|unsupported raised|no supported explicit answer table/.test(reason)?'文字抽出の不具合':'OCR・原本照合待ち';
      const origin=crop || image.src.startsWith('assets/transcription/')?'crop':'original';
      const purpose=origin==='original'?'original':crop?.contentKinds.size>1?'unknownCrop':crop?.contentKinds.has('unreadableText')?'unreadableText':figureRequired && crop?'figureCandidate':'unknownCrop';
      const reasons=[numericReason,mappingReasons.get(key+'\0'+field+'\0'+image.src),...(crop?.reasons || []),entry?.retainedReason].filter(Boolean).join('; ');
      const unresolved=[];
      if(/unmapped|character mapping|styled|columns|shading|formula|non-horizontal|superscript|subscript|layout/i.test(reasons) || category==='文字抽出の不具合') unresolved.push('文字コード・組版');
      if(category==='OCR・原本照合待ち' || purpose==='unreadableText' || /ocr/.test(entry?.method || '')) unresolved.push('OCR・原本照合待ち');
      if(scopeUnresolved(reasons)) unresolved.push('問題範囲未確定');
      if(!region?.sourceFile) unresolved.push('原本対応なし');
      let imageSha256=entry?.identity?.imageSha256 || crop?.crop.sha256 || assetHashes.get(image.src);
      if(!imageSha256) {imageSha256=sha(readFileSync(join(source,'web',image.src)));assetHashes.set(image.src,imageSha256);}
      const row={key,number:q.id.match(/-q(\d+)/)?.[1] || '',field,src:image.src,category,categoryProvisional:!crop?.crop.figureNeedEstablished,figureNeedEstablished:Boolean(crop?.crop.figureNeedEstablished),reason,origin,purpose,unresolved,method:entry?.method || 'exact-crop',imageSha256,sourceFile:region?.sourceFile || '',sourceUrl:q.sourceUrl || '',sourceMappingAvailable:Boolean(region?.sourceFile),page:region?region.page+1:null,rect:region?.rect || null,sourceSha256:region?.sourceSha256 || '',visualReview:crop?.crop.figureNeedEstablished?'Recorded direct source visual comparison in text-corrections.json':'not established by inventory',packUrl:pack.url};
      row.sourceMappingMethod=region?.sourceMappingMethod || (region?.sourceFile?'extraction-image-region':'unresolved');
      rows.push(row);categories[category]=(categories[category] || 0)+1;
      if(!assets.has(image.src)) assets.set(image.src,{src:image.src,bytes:statSync(join(source,'web',image.src)).size,references:[]});
      assets.get(image.src).references.push(rows.length-1);
      if(region?.sourceFile) {
        if(!pdfs.has(region.sourceFile)) pdfs.set(region.sourceFile,{file:region.sourceFile,sha256:region.sourceSha256,pages:new Set(),images:new Set()});
        const pdf=pdfs.get(region.sourceFile);assert.equal(pdf.sha256,region.sourceSha256);pdf.pages.add(region.page+1);pdf.images.add(image.src);
      }
    }
  }
  assert.equal(questions,manifest.questions);
  const summary={source,questions,questionsWithImages:new Set(rows.map(r=>r.key)).size,uniqueImages:assets.size,imageReferences:rows.length,uniquePDFs:pdfs.size,categories,complete:false,limitations:['Categories are processing queues, not proof that OCR is correct or a figure is necessary.','Exact crops may include unreadable text; consult each source and reason before removing them.']};
  summary.breakdown=summarizeImages(rows,assets,cropSources);
  assert.equal(Object.values(summary.breakdown.kinds).reduce((n,k)=>n+k.images,0),assets.size);
  return {summary,rows,assets,pdfs,states};
}

export function writeInventory(source,output,baseline=null) {
  const current=collectInventory(source),previous=baseline?collectInventory(baseline):null;
  const {summary,rows,assets,pdfs}=current;
  const report={current:summary,previous:previous?.summary || null,comparison:compareProgress(current,previous)};
  mkdirSync(output,{recursive:true});
  writeFileSync(join(output,'summary.json'),JSON.stringify(summary,null,2));
  writeFileSync(join(output,'references.json'),JSON.stringify(rows));
  writeFileSync(join(output,'images.json'),JSON.stringify([...assets.values()]));
  writeFileSync(join(output,'pdfs.json'),JSON.stringify([...pdfs.values()].map(p=>({...p,pages:[...p.pages].sort((a,b)=>a-b),images:[...p.images]}))));
  const fields=['key','number','field','src','category','categoryProvisional','figureNeedEstablished','reason','method','imageSha256','sourceFile','sourceUrl','sourceMappingAvailable','page','sourceSha256','packUrl','origin','purpose','unresolved','visualReview'];
  const cell=v=>'"'+String(v ?? '').replaceAll('"','""')+'"';
  writeFileSync(join(output,'references.csv'),'\ufeff'+[fields.join(','),...rows.map(r=>fields.map(f=>cell(r[f])).join(','))].join('\r\n'));
  writeFileSync(join(output,'progress.json'),JSON.stringify(report,null,2));
  writeFileSync(join(output,'progress.md'),progressMarkdown(report));
  return report;
}

if(process.argv[1] && import.meta.url===pathToFileURL(resolve(process.argv[1])).href) {
  const source=resolve(process.argv[2] || read('build/material-transcription/current.json').directory);
  const output=resolve(process.argv[3] || join(source,'retained-material'));
  const report=writeInventory(source,output,process.argv[4] || null);
  console.log(JSON.stringify({source,output,baseline:report.comparison.baseline,uniqueImages:report.current.uniqueImages}));
}
