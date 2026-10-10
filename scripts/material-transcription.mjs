import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {resolve,relative,isAbsolute} from 'node:path';
import {createHash} from 'node:crypto';
import {questionKey} from '../web/core.mjs';

export const textFields=['prompt','options','passage','modelAnswer','evaluationGuide','explanation'];
export const auditFields=[...textFields,'answer'];
export const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
export const correctionFile=resolve('private-data/material-transcription/corrections.json');
export function loadCorrections(file=correctionFile) {
  const records=existsSync(file)?JSON.parse(readFileSync(file)):[],map=new Map(),checked=new Map();
  assert.ok(Array.isArray(records));
  for(const record of records) {
    assert.equal(record.status,'source-verified','Unreviewed OCR cannot be installed');
    assert.ok(record.method && record.reviewer && record.reviewedOn && record.reason);
    assert.ok(!map.has(record.key),'Duplicate correction: '+record.key);
    assert.ok(record.evidence.length>0);
    for(const evidence of record.evidence) {
      const source=resolve(evidence.file),path=relative(resolve('private-data'),source);
      assert.ok(path && !path.startsWith('..') && !isAbsolute(path),'Source must be in private-data');
      if(!checked.has(source)) checked.set(source,sha(readFileSync(source)));
      assert.equal(checked.get(source),evidence.sha256,'Source changed: '+source);
      assert.ok(Number.isSafeInteger(evidence.page) && evidence.page>0);
      assert.ok(evidence.rect.length===4 && evidence.rect.every(Number.isFinite) && evidence.rect[2]>evidence.rect[0] && evidence.rect[3]>evidence.rect[1]);
      assert.ok(evidence.fields.length && evidence.fields.every(f=>textFields.includes(f) || f==='answer'));
    }
    for(const field of Object.keys(record.after)) {
      assert.ok([...textFields,'textReview','answerKind','explanationKind','explanationSource'].includes(field),'Forbidden correction field: '+field);
      assert.ok(Object.hasOwn(record.before,field),'Missing before value: '+field);
      if(textFields.includes(field)) assert.ok(record.evidence.some(e=>e.fields.includes(field)),'Missing field evidence: '+field);
    }
    for(const [field,status] of Object.entries(record.after.textReview || {})) {
      assert.equal(status,'source-verified');
      assert.ok(record.evidence.some(e=>e.fields.includes(field)),'Missing review evidence: '+field);
    }
    if(record.imageReplacement) {
      const replacement=record.imageReplacement;assert.ok(replacement.reason && replacement.reviewedOn);
      for(const field of ['images','solutionImages']) {
        assert.ok(Array.isArray(replacement[field]));
        if(replacement[field].length) {
          const required=field==='images'?['prompt','passage',...((record.before.options?.[0]?.length || 0)?['options']:[])]:['modelAnswer','evaluationGuide'];
          assert.ok(required.every(f=>record.after.textReview?.[f]==='source-verified'),'Image replacement requires complete source review');
        }
        for(const image of replacement[field]) {
          assert.ok(/^assets\/[a-zA-Z0-9_./-]+\.(png|webp|jpg)$/.test(image.src) && !image.src.includes('..'));
          assert.equal(sha(readFileSync(resolve('build/private/web',image.src))),image.sha256,'Reviewed image changed: '+image.src);
        }
      }
    }
    map.set(record.key,record);
  }
  return map;
}
export function applyTextCorrection(q,records,original=q) {
  const record=records.get(questionKey(q));if(!record) return q;
  assert.equal(questionKey(original),questionKey(q));
  for(const [field,value] of Object.entries(record.after)) {
    const prior=q[field] ?? null;
    assert.ok([...(record.before[field] || []),value].some(v=>JSON.stringify(v)===JSON.stringify(prior) || JSON.stringify(v)===JSON.stringify(original[field] ?? null)),`Stale correction: ${record.key} ${field}`);
  }
  if(record.after.options) assert.equal(record.after.options.length,q.options.length,'Option mapping must remain unchanged');
  return {...q,...record.after};
}

export function applySolutionText(q,solution,correction) {
  if(!solution) return q;
  assert.ok(['modelAnswer','evaluationGuide','explanation'].includes(solution.field));
  const removed=new Set(solution.removed.map(r=>r.image.src));
  const retained=q.solutionImages.filter(i=>!removed.has(i.src));
  assert.deepEqual(retained,solution.retained,'Solution image mapping changed');
  assert.equal(q.solutionImages.length-retained.length,removed.size);
  if(correction?.after.textReview?.[solution.field]==='source-verified') {
    assert.equal(correction.key,questionKey(q),'Correction belongs to another question');
    return {...q,solutionImages:retained};
  }
  const existing=(q[solution.field] || '').replace(/(標準解答|出題趣旨|公式正答)画像/g,'$1資料'),normalize=s=>s.normalize('NFKC').replace(/\s+/g,'');
  const value=normalize(existing).includes(normalize(solution.text))?existing:(existing?existing+'\n\n':'')+'原本の解答資料（文字化）\n'+solution.text;
  const textReview={...q.textReview};if(value!==q[solution.field]) delete textReview[solution.field];
  const result={...q,[solution.field]:value,solutionImages:retained};
  if(q.textReview) {if(Object.keys(textReview).length) result.textReview=textReview;else delete result.textReview;}
  if(solution.field==='explanation' && q.explanationKind==='absent-in-source' && value!==q.explanation) result.explanationKind='unknown';
  return result;
}

export function applyReviewedImages(q,records,assets={}) {
  const replacement=records.get(questionKey(q))?.imageReplacement;if(!replacement) return q;
  const result={...q};
  for(const field of ['images','solutionImages']) {
    const removed=new Set(replacement[field].flatMap(i=>{
      const entry=assets[i.src];
      if(entry && q[field].some(image=>image.src===entry.src)) assert.equal(entry.sourceSha256,i.sha256,'Reviewed source image mapping changed');
      return [i.src,...(entry?[entry.src]:[])];
    }));
    if(removed.size) {
      assert.ok(q[field].every(i=>removed.has(i.src)),'Reviewed image mapping changed');
      result[field]=[];
    }
  }
  return result;
}

export function applyQuestionImageText(q,part) {
  if(!part) return q;
  const removed=new Set(part.removed.map(r=>r.image.src)),images=q.images.filter(i=>!removed.has(i.src));
  assert.deepEqual(images,part.retained,'Question image mapping changed');
  assert.equal(q.images.length-images.length,removed.size);
  const result={...q,images},normalize=s=>s.normalize('NFKC').replace(/\s+/g,'');
  if(q.textReview?.prompt==='source-verified' && q.textReview?.passage==='source-verified' && (!q.options.length || q.textReview?.options==='source-verified')) return result;
  const field=images.length?'prompt':'passage',existing=q[field] || '';
  if(!images.length && (!existing || normalize(existing)===normalize(part.sourceText))) result.passage=part.text;
  else result[field]=existing+'\n\n原本資料（文字化済み領域）\n'+part.text;
  if(!images.length) result.prompt=result.prompt.replace(/原本画像|画像の該当/g,m=>m==='原本画像'?'原本資料':'資料の該当');
  if(result[field]!==existing && q.textReview) {result.textReview={...q.textReview};delete result.textReview[field];if(!Object.keys(result.textReview).length) delete result.textReview;}
  return result;
}

export function applySupplementaryImageText(q,assets) {
  const result={...q},pending=[];
  const normalize=s=>s.normalize('NFKC').replace(/\s+/g,'');
  for(const [images,field] of [['images','passage'],['solutionImages','explanation']]) {
    if(q.textReview?.[field]==='source-verified') continue;
    let text=q[field] || '';const replacement=[];
    const entries=q[images].map(image=>assets[image.src]);
    if(field==='passage' && entries.length && entries.every(e=>e?.crops && typeof e.sourceText==='string') && normalize(text)===normalize(entries.map(e=>e.sourceText).join('\n\n'))) text='';
    for(const [index,image] of q[images].entries()) {
      const entry=assets[image.src];assert.ok(entry,'Missing image extraction: '+image.src);
      assert.equal(entry.status,'unreviewed');assert.equal(sha(entry.text),entry.textSha256,'Changed extracted text');
      const value=entry.text.trim();if(!value) {replacement.push(image);continue;}
      if(normalize(text).includes(normalize(value))) {replacement.push(...(entry.crops?.map((c,i)=>({src:c.src,alt:image.alt+`（図・文字化できない部分 ${i+1}）`})) || [image]));continue;}
      const next=(text?text+'\n\n':'')+(images==='images'?'問題画像':'解答・解説画像')+` ${index+1} の補助テキスト（原本未照合・誤読や欠落の可能性あり）\n`+value;
      if(next.length>49000) {replacement.push(image);pending.push({src:image.src,field,reason:'field-length-limit'});continue;}
      text=next;
      replacement.push(...(entry.crops?.map((c,i)=>({src:c.src,alt:image.alt+`（図・文字化できない部分 ${i+1}）`})) || [image]));
    }
    if(replacement.length<=30) result[images]=replacement;
    else pending.push({field,reason:'image-count-limit'});
    if(text!==q[field] && text) {
      result[field]=text;
      if(field==='explanation' && q.explanationKind==='absent-in-source') result.explanationKind='unknown';
    }
  }
  return {question:result,pending};
}

// These are inventory flags, not proof of missing source content or OCR accuracy.
export function fieldStatus(q,field) {
  if(field==='explanation' && q.explanationKind==='absent-in-source') return 'absent-in-source';
  if(field==='passage' && !q.passage && q.textReview?.prompt==='source-verified' && q.textReview?.options==='source-verified') return 'not-applicable';
  if(q.textReview?.[field]==='source-verified') return 'source-verified';
  const choice=['single','multiple'].includes(q.type),value=q[field];
  if(field==='answer') return choice?'mapping-unreviewed':'not-applicable';
  if(field==='options') return !choice?'not-applicable':q.options.every(o=>/^[アイウエオカキクケコA-Z0-9①-⑳]$/.test(o))?'label-only':'unreviewed-text';
  if(field==='modelAnswer' && choice) return 'not-applicable';
  if(field==='evaluationGuide' && choice && !value) return 'not-applicable';
  if(field==='explanation' && /解説.{0,6}(ありません|なし|未収録|未登録)|理由解説は未収録/.test(value || '')) return 'declared-absent-unverified';
  if(field==='prompt' && /原本画像|問題文・図表・選択肢を確認|問題資料の設問|設問ア・イ・ウを含む論述/.test(value || '')) return 'placeholder';
  if(!value) return 'empty-availability-unknown';
  if(/[\uFFFD\uE000-\uF8FF]/.test(value)) return 'suspect-character';
  return 'unreviewed-text';
}
