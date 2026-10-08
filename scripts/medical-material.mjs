import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {validateQuestions,validateExam,questionKey,DEFAULT_EXAMS} from '../web/core.mjs';
import {EXAM_CATALOG} from '../web/exams.mjs';
import {candidateFingerprint} from './github-candidates.mjs';
const hash=b=>createHash('sha256').update(b).digest('hex');
const section=s=>({'午前':'A','午後':'B','AM':'A','PM':'B'}[s] || s);
const identity=(q,n)=>[q.examId,q.year,section(q.subject),Number(n)].join('|');

export function loadMedicalMaterial(root,existing) {
  const dir=join(root,'private-data/github-material'),prepared=join(dir,'prepared'),file=join(prepared,'medical-report.json');
  if(!existsSync(file)) return {exams:[],packs:[]};
  const report=JSON.parse(readFileSync(file));
  assert.equal(report.version,1);assert.match(report.commit,/^[a-f0-9]{40}$/);assert.equal(report.license,'CC-BY-NC-4.0');
  assert.equal(hash(readFileSync(join(dir,'medical-jmed-license.txt'))),'41003d4a74749c0220e33dd415042164b5a1093ed401f36277234f772d22d3d0');
  const fingerprints=new Set(existing.map(q=>q.examId+'|'+candidateFingerprint(q))),identities=new Set(),keys=new Set(existing.map(questionKey));
  for(const q of existing) {
    if(!q.sourceUrl?.startsWith('https://www.mhlw.go.jp/')) continue;
    const n=q.id.match(/-q[A-F]?(\d+)$/)?.[1];
    if(n) identities.add(identity(q,n));
  }
  const packs=[],checked=new Set(),skipped={duplicate:0};
  for(const pack of report.packs) {
    assert.match(pack.file,/^medical-jmed-[a-z-]+-20\d\d\.json$/);
    const raw=readFileSync(join(prepared,pack.file));assert.equal(hash(raw),pack.sha256);
    const sources=new Map();
    for(const s of pack.sources) {
      assert.match(s.file,/^medical-jmed-[a-f0-9]{20}\.(json|png|jpe?g|webp)$/);
      assert.ok(s.url.startsWith(`https://huggingface.co/datasets/JMed48k/JMed48k/resolve/${report.commit}/JMed48k-eval/`));
      if(!checked.has(s.file)) {assert.equal(hash(readFileSync(join(dir,s.file))),s.sha256);checked.add(s.file);}
      sources.set(s.file,s);
    }
    const input=JSON.parse(raw);assert.equal(input.length,pack.count);
    if(!input.length) continue;
    const rows=validateQuestions(input);
    const kept=[];
    for(const q of rows) {
      assert.equal(q.examId,pack.examId);assert.equal(q.year,pack.year);assert.ok(q.source.includes(report.notice));
      assert.ok(pack.sources.some(s=>s.url===q.sourceUrl && s.file.endsWith('.json')));
      const n=q.id.match(/-q(\d+)$/)?.[1];assert.ok(n);
      const fp=q.examId+'|'+candidateFingerprint(q),id=identity(q,n);
      if(identities.has(id) || fingerprints.has(fp)) {skipped.duplicate++;continue;}
      assert.ok(!keys.has(questionKey(q)));keys.add(questionKey(q));identities.add(id);fingerprints.add(fp);
      for(const image of [...q.images,...q.solutionImages]) {
        assert.match(image.src,/^assets\/github-material\/medical-jmed-[a-f0-9]{20}\.(png|jpe?g|webp)$/);
        const name=image.src.split('/').at(-1),source=sources.get(name);assert.ok(source);
        const asset='asset:'+name;
        if(!checked.has(asset)) {assert.equal(hash(readFileSync(join(prepared,'assets',name))),source.sha256);checked.add(asset);}
      }
      kept.push(q);
    }
    if(kept.length) packs.push({id:pack.id,examId:pack.examId,year:pack.year,subject:'JMed48k',count:kept.length,
      sources:pack.sources,localOnly:true,verification:report.notice,rows:kept});
  }
  const exams=[...new Set(packs.map(p=>p.examId))].filter(id=>!existing.some(q=>q.examId===id))
    .map(id=>validateExam([...DEFAULT_EXAMS,...EXAM_CATALOG].find(e=>e.id===id)));
  return {exams,packs,report:{...report,skipped,added:packs.reduce((n,p)=>n+p.count,0)}};
}
