import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {existsSync,readFileSync,readdirSync} from 'node:fs';
import {join} from 'node:path';
import {validateExam,validateQuestions,questionKey} from '../web/core.mjs';

export const EXPANSION_FIELDS=['IT・AI','統計','数学','英語','国語','日本史','世界史','地理','自然科学','金融・生活','会計・経営','電気・工学'];
// New local sessions have their own targets; keep the earlier 12-field plan unchanged.
export const ADDITIONAL_FIELDS=[...EXPANSION_FIELDS,'法律・行政','医療・健康','農業・食品'];
const hash=data=>createHash('sha256').update(data).digest('hex');
const read=path=>JSON.parse(readFileSync(path,'utf8'));
const filename=name=>{assert.match(name,/^[a-zA-Z0-9_-]+\.(json|png|pdf|html|txt)$/);return name;};

// Conservative text deduplication: layout, question labels and changed numerals do not add coverage.
// Diagrams can carry extra meaning; matching text is excluded rather than counted optimistically.
export function materialFingerprint(q) {
  const body=q.passage || q.prompt;
  return hash([body.normalize('NFKC').replace(/^問(?:題)?\s*\d+\s*/,'').replace(/[\s\p{P}\p{S}]/gu,'').replace(/[0-9]+/g,'#'),
    [...(q.options || [])].map(v=>v.normalize('NFKC').replace(/[\s\p{P}\p{S}]/gu,'').replace(/[0-9]+/g,'#')).sort().join('|')].join('\n'));
}

export function loadAdditionalMaterial(root,existing) {
  const dir=join(root,'private-data/additions'), exams=[], packs=[], fingerprints=new Set(existing.map(materialFingerprint));
  const keys=new Set(existing.map(questionKey)),examIds=new Set(),examDefinitions=new Map(),packIds=new Set(),duplicates=[];
  const existingByKey=new Map(existing.map(q=>[questionKey(q),q]));
  const reviewedDuplicates=[];
  const report={target:10000,minimumPerField:200,added:0,official:0,original:0,fields:Object.fromEntries(EXPANSION_FIELDS.map(f=>[f,0])),duplicates,complete:false,
    deduplication:'NFKC・空白・記号・設問番号・数値差の一致、および既存問題と候補のハッシュを対応付けた個別の意味重複レビュー。全件の意味照合を保証するものではない。'};
  if(!existsSync(dir)) return {exams,packs,report};
  for(const name of readdirSync(dir).filter(n=>n.endsWith('-manifest.json')).sort()) {
    const manifestBytes=readFileSync(join(dir,filename(name))),manifest=JSON.parse(manifestBytes);
    const verification=read(join(dir,name.replace('-manifest.json','-verification.json')));
    assert.equal(verification.manifestSha256,hash(manifestBytes),'Additional material needs verification: '+name);
    assert.ok(Array.isArray(manifest.exams) && Array.isArray(manifest.packs));
    assert.match(manifest.archive,/^[a-zA-Z0-9_-]+$/);
    const evidenceByKey=new Map(manifest.questions.map(q=>[questionKey(q),q]));
    assert.equal(evidenceByKey.size,manifest.questions.length,'Duplicate evidence');
    const sourceTextByFile=new Map();
    for(const source of [manifest.sources.terms,...manifest.sources.sources]) {
      assert.match(source.url,/^https:\/\//);
      const bytes=readFileSync(join(root,'private-data',manifest.archive,filename(source.file)));
      assert.equal(hash(bytes),source.sha256,'Source changed '+source.file);
      sourceTextByFile.set(source.file,bytes.toString('utf8'));
    }
    for(const source of manifest.sources.sources.filter(s=>s.derivation)) {
      assert.equal(source.derivation.method,'pymupdf-text-to-html-v1','Unsupported source derivation');
      const parent=manifest.sources.sources.find(s=>s.file===source.derivation.file);
      assert.ok(parent?.file.endsWith('.pdf'),'Missing derived source PDF');
      assert.equal(parent.sha256,source.derivation.sha256,'Derived source parent mismatch');
      assert.equal(parent.url,source.url,'Derived source URL mismatch');
      assert.ok(source.file.endsWith('.html'),'Derived source must be an HTML transcript');
    }
    for(const value of manifest.exams) {
      const exam=validateExam(value);
      if(examDefinitions.has(exam.id)) assert.deepEqual(exam,examDefinitions.get(exam.id),'Conflicting added exam '+exam.id);
      else {examIds.add(exam.id);examDefinitions.set(exam.id,exam);exams.push(exam);}
    }
    for(const pack of manifest.packs) {
      assert.match(pack.id,/^[a-zA-Z0-9_-]+$/);
      assert.ok(!packIds.has(pack.id),'Duplicate pack '+pack.id);packIds.add(pack.id);
      assert.ok(['official','original'].includes(pack.kind));
      if(pack.kind==='official') {
        assert.equal(verification.officialAnswers,'pass');
        assert.equal(verification.sourceCropPixels,'pass');
        assert.equal(verification.answerLeakage,'pass');
      } else {
        assert.equal(verification.originalAnswers,'pass');
        assert.equal(verification.rationaleReview,'pass');
        assert.equal(verification.distinctCoverage,'pass');
        assert.ok(!verification.officialAnswers,'Original material cannot claim official answer verification');
        assert.equal(verification.questions,manifest.questions.length);
        assert.equal(verification.checks?.length,manifest.questions.length);
      }
      assert.ok(ADDITIONAL_FIELDS.includes(pack.field) && examIds.has(pack.examId));
      assert.ok(pack.verification && pack.sources?.length,'Missing verification/source evidence');
      for(const source of pack.sources.filter(s=>s.derivation)) {
        const tracked=manifest.sources.sources.find(s=>s.file===source.file);
        assert.deepEqual(source,tracked,'Untracked derived source');
        assert.ok(pack.sources.some(s=>s.file===source.derivation.file && s.sha256===source.derivation.sha256),'Missing pack derived source PDF');
      }
      for(const source of pack.sources.filter(s=>s.derivation)) {
        const tracked=manifest.sources.sources.find(s=>s.file===source.file);
        assert.deepEqual(source,tracked,'Untracked derived source');
        assert.ok(pack.sources.some(s=>s.file===source.derivation.file && s.sha256===source.derivation.sha256),'Missing pack derived source PDF');
      }
      const raw=readFileSync(join(dir,filename(pack.file)));
      assert.equal(hash(raw),pack.sha256,'Stale verification: '+pack.id);
      const checked=validateQuestions(JSON.parse(raw),[],false,pack.examId);
      assert.equal(checked.length,pack.count);
      const rows=[];
      for(const q of checked) {
        assert.ok(!keys.has(questionKey(q)),'Duplicate added ID '+questionKey(q));keys.add(questionKey(q));
        assert.ok(q.sourceUrl && q.explanation,'Missing source or explanation '+q.id);
        const evidence=evidenceByKey.get(questionKey(q));
        assert.ok(evidence,'Missing question evidence '+q.id);
        assert.deepEqual(evidence.answer,q.answer,'Answer evidence mismatch '+q.id);
        if(pack.kind==='original') {
          assert.equal(evidence.questionSha256,hash(JSON.stringify(JSON.parse(raw).find(row=>questionKey(row)===questionKey(q)))),'Stale original review '+q.id);
          assert.equal(evidence.review?.status,'pass');
          assert.ok(evidence.review?.rationale && evidence.review?.uniqueness && evidence.review?.distractors);
          assert.ok(evidence.reference?.file && evidence.reference?.locator);
          assert.ok(pack.sources.some(s=>s.file===evidence.reference.file && s.url===q.sourceUrl),'Untracked original reference '+q.id);
          assert.ok(sourceTextByFile.get(evidence.reference.file)?.includes(evidence.reference.locator),'Missing original source locator '+q.id);
          assert.ok(['python-3.12-execution','independent-recalculation','knowledge-reference-review'].includes(evidence.check?.method),'Missing original check '+q.id);
          if(evidence.check.method==='knowledge-reference-review') {
            assert.ok(evidence.check.referenceExcerpt?.length>=15 && evidence.check.reviewer && evidence.check.reviewedOn,'Missing knowledge evidence '+q.id);
            assert.ok(evidence.check.optionReviews?.length===q.options.length && evidence.check.optionReviews.every(r=>typeof r==='string' && r.length>=12),'Missing option review '+q.id);
            assert.equal(evidence.check.correctOptionText,q.options[q.answer],'Knowledge answer mismatch '+q.id);
            assert.equal(evidence.check.sourceSha256,pack.sources.find(s=>s.file===evidence.reference.file).sha256,'Knowledge source mismatch '+q.id);
            assert.ok(!evidence.check.program && !evidence.check.stdout,'Knowledge review cannot claim execution '+q.id);
          } else {
            assert.ok(evidence.check.program && evidence.check.pythonVersion,'Missing execution evidence '+q.id);
            assert.equal(evidence.check.stdout,q.options[q.answer],'Original check output mismatch '+q.id);
          }
          const executed=verification.checks.find(c=>c.id===q.id);
          assert.deepEqual(executed,{id:q.id,...evidence.check},'Missing per-question verification '+q.id);
          assert.ok(q.source.includes('自作') && !q.source.includes('公式問題'),'Original attribution '+q.id);
          assert.ok(q.explanationSource.includes('独自'),'Original explanation attribution '+q.id);
        }
        for(const image of [...q.images,...q.solutionImages]) {
          assert.match(image.src,/^assets\/additions\/[a-zA-Z0-9_-]+\.png$/);
          const file=image.src.split('/').at(-1),record=evidence.images.find(r=>r.file===file);
          assert.ok(record,'Missing image evidence '+file);
          assert.equal(hash(readFileSync(join(dir,'assets',filename(file)))),record.sha256,'Image changed '+file);
        }
        if(evidence.duplicateReview) {
          const review=evidence.duplicateReview;
          assert.ok(review.status==='excluded-duplicate' && review.reviewedOn && review.reviewer && review.reason?.length>=20,'Invalid duplicate review '+q.id);
          assert.equal(review.candidateQuestionSha256,hash(JSON.stringify(JSON.parse(raw).find(row=>questionKey(row)===questionKey(q)))),'Stale duplicate candidate '+q.id);
          reviewedDuplicates.push({q,review});
          duplicates.push(questionKey(q));continue;
        }
        const fingerprint=materialFingerprint(q);
        if(fingerprints.has(fingerprint)) {duplicates.push(questionKey(q));continue;}
        fingerprints.add(fingerprint);rows.push(q);report.added++;report[pack.kind]++;
        report.fields[pack.field]=(report.fields[pack.field] || 0)+1;
        existingByKey.set(questionKey(q),JSON.parse(raw).find(row=>questionKey(row)===questionKey(q)));
      }
      if(rows.length) packs.push({...pack,count:rows.length,rows});
    }
  }
  for(const {q,review} of reviewedDuplicates) {
    const prior=existingByKey.get(review.existingKey);
    assert.ok(prior,'Invalid duplicate review '+q.id);
    assert.equal(review.existingQuestionSha256,hash(JSON.stringify(prior)),'Stale duplicate target '+q.id);
  }
  report.complete=report.added>=report.target && EXPANSION_FIELDS.every(f=>report.fields[f]>=report.minimumPerField);
  report.totalRecorded=existing.length+report.added;
  const baselineFile=join(dir,'expansion-baseline.json');
  if(existsSync(baselineFile)) {
    const baseline=read(baselineFile);
    report.baseline={startedOn:baseline.startedOn,added:baseline.baselineAdded,total:baseline.baselineTotal};
    report.netIncrease=report.added-baseline.baselineAdded;
  }
  report.remaining=Math.max(0,report.target-report.added);
  report.remainingPerField=Object.fromEntries(Object.entries(report.fields).map(([field,n])=>[field,Math.max(0,report.minimumPerField-n)]));
  report.duplicateExcluded=duplicates.length;
  report.unverifiedRegistered=0; // Every included manifest and question was checked above.
  report.deployment='local-only; this expansion has not been deployed';
  const reviewFile=join(dir,'source-review.json');
  if(existsSync(reviewFile)) {
    const review=read(reviewFile);
    report.pendingSources=(review.sources || []).filter(s=>/pending|excluded/.test(s.status)).map(s=>({provider:s.provider,status:s.status,reason:s.reason,questionCount:s.questionCount ?? null}));
    report.pendingSourceCount=report.pendingSources.length;
    report.pendingQuestionCount=report.pendingSources.some(s=>s.questionCount===null)?null:report.pendingSources.reduce((n,s)=>n+s.questionCount,0);
    report.unverifiedSources=(review.sources || []).filter(s=>s.status==='acquired-unverified').map(s=>({provider:s.provider,questionCount:s.questionCount ?? null,reason:s.reason}));
    report.unverifiedAcquiredQuestions=report.unverifiedSources.some(s=>s.questionCount===null)?null:report.unverifiedSources.reduce((n,s)=>n+s.questionCount,0);
    report.unverifiedAuthoredQuestions=review.unverifiedAuthoredQuestions ?? null;
    report.qualityExcludedQuestions=review.qualityExcludedQuestions ?? 0;
    report.qualityExclusions=review.qualityExclusions ?? [];
  }
  return {exams:exams.filter(e=>packs.some(p=>p.examId===e.id)),packs,report};
}
