import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {validateExam,validateQuestions,questionKey,DEFAULT_EXAMS} from '../web/core.mjs';
import {EXAM_CATALOG} from '../web/exams.mjs';
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const paperUrl=url=>{const parsed=new URL(url);return parsed.pathname+parsed.hash;};
const name=value=>{assert.match(value,/^[a-zA-Z0-9_-]+\.(json|png|pdf|html|txt|mp3)$/);return value;};

export function loadGithubMaterial(root,existing,reportFile='report.json',verificationFile='verification.json') {
  name(reportFile);name(verificationFile);
  const dir=join(root,'private-data/github-material'),prepared=join(dir,'prepared'),file=join(prepared,reportFile);
  if(!existsSync(file)) return {exams:[],packs:[],report:{added:0}};
  const raw=readFileSync(file),report=JSON.parse(raw),verification=JSON.parse(readFileSync(join(prepared,verificationFile)));
  assert.equal(verification.reportSha256,hash(raw),'GitHub material needs verification');
  assert.equal(verification.officialAnswers,'pass');assert.equal(verification.originalPixels,'pass');
  const registered=new Map(existing.map(q=>[questionKey(q),q]));
  const keys=new Set(registered.keys()),papers=new Map(),packs=[],examIds=new Set(),imageHashes=new Map();
  for(const q of existing) {
    const number=q.id.match(/-q(\d+)$/)?.[1];
    if(q.sourceUrl && number) papers.set(q.examId+'|'+paperUrl(q.sourceUrl)+'|'+Number(number)+(q.examId==='cpa'?'|'+q.subject:''),questionKey(q));
  }
  for(const pack of report.packs.filter(p=>p.status==='prepared')) {
    const bytes=readFileSync(join(prepared,name(pack.file)));assert.equal(hash(bytes),pack.sha256,'GitHub pack changed');
    for(const source of pack.sources) {assert.match(source.url,/^https:\/\//);assert.equal(hash(readFileSync(join(dir,name(source.file)))),source.sha256,'GitHub source changed');}
    const rows=validateQuestions(JSON.parse(bytes)),kept=[];assert.equal(rows.length,pack.count);assert.equal(rows.length,pack.questions.length);
    for(const [i,q] of rows.entries()) {
      const evidence=pack.questions[i];assert.equal(q.id,evidence.id);assert.deepEqual(q.answer,evidence.answer);
      assert.equal(q.sourceUrl,evidence.sourceUrl || pack.url);assert.equal(q.examId,pack.examId);assert.equal(q.year,pack.year);
      const repeated=registered.has(questionKey(q));
      if(repeated) assert.deepEqual(q,registered.get(questionKey(q)),'Conflicting repeated official question');
      else {
        const identity=q.examId+'|'+paperUrl(q.sourceUrl)+'|'+evidence.number+(q.examId==='cpa'?'|'+q.subject:'');
        assert.ok(!papers.has(identity),'Previously registered official question '+identity);papers.set(identity,questionKey(q));
        assert.ok(!keys.has(questionKey(q)),'Duplicate GitHub question');keys.add(questionKey(q));
      }
      assert.deepEqual(q.audio || [],evidence.audio || []);
      for(const audio of q.audio || []) {
        const file=name(audio.src.replace('assets/github-material/',''));
        const source=pack.sources.find(s=>s.file===file);assert.ok(source,'Audio source missing');
        if(!imageHashes.has(file)) imageHashes.set(file,hash(readFileSync(join(prepared,'assets',file))));
        assert.equal(imageHashes.get(file),source.sha256,'Audio changed');
      }
      assert.equal(q.images.length,evidence.images.length);
      assert.equal(q.solutionImages.length,(evidence.solutionImages || []).length);
      for(const [j,image] of [...q.images,...q.solutionImages].entries()) {
        const record=[...evidence.images,...(evidence.solutionImages || [])][j];assert.equal(image.src,'assets/github-material/'+name(record.file));
        if(!imageHashes.has(record.file)) imageHashes.set(record.file,hash(readFileSync(join(prepared,'assets',record.file))));
        assert.equal(imageHashes.get(record.file),record.sha256,'GitHub image changed');
      }
      if(!repeated) kept.push(q);
    }
    if(!kept.length) continue;
    examIds.add(pack.examId);
    packs.push({id:'archive-'+pack.file.slice(0,-5),examId:pack.examId,year:pack.year,term:pack.term,subject:pack.subject,count:kept.length,
      sources:pack.sources,localOnly:['RBC','FOOD'].includes(pack.provider) || pack.localOnly || false,verification:pack.verificationLabel || (pack.provider==='RBC'?'公式正答印・問題番号・選択肢のOCR照合。問題画像は正答印除去・番号余白の淡色補正、解答画像は原本（全問目視・理由解説は未実施）':'公式解答照合・問題区切りの自動検査・原本画像の画素一致（全問の目視確認・理由解説は未実施）'),rows:kept});
  }
  const known=new Set(existing.map(q=>q.examId));
  const exams=[...examIds].filter(id=>!known.has(id)).map(id=>validateExam(DEFAULT_EXAMS.find(e=>e.id===id) || EXAM_CATALOG.find(e=>e.id===id)));
  return {exams,packs,report:{...report,added:packs.reduce((n,p)=>n+p.count,0)}};
}
