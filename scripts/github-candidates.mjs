import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {join,resolve,sep} from 'node:path';
import {createHash} from 'node:crypto';
import {validateQuestions,validateExam,questionKey,DEFAULT_EXAMS} from '../web/core.mjs';
import {EXAM_CATALOG} from '../web/exams.mjs';
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
export const candidateFingerprint=q=>hash([q.prompt,q.passage || '',...q.options].join('\n').normalize('NFKC').replace(/\s+/gu,''));

export function loadGithubCandidates(root,existing) {
  const dir=join(root,'private-data/github-candidates'),prepared=join(dir,'prepared'),reportFile=join(prepared,'report.json');
  if(!existsSync(reportFile)) return {exams:[],packs:[],report:{added:0,repositories:[]}};
  const report=JSON.parse(readFileSync(reportFile)),keys=new Set(existing.map(questionKey));
  assert.equal(report.version,1);
  const fingerprints=new Set(existing.map(q=>q.examId+'|'+candidateFingerprint(q))),packs=[],verifiedSources=new Set(),assets=new Set();
  const architecture=new Set(existing.filter(q=>q.examId==='architect1' && q.id.startsWith('construction-')).map(q=>`${q.year}|${q.subject}|${Number(q.id.match(/-q(\d+)$/)[1])}`));
  const safe=(base,path)=>{const file=resolve(base,path);assert.ok(file.startsWith(resolve(base)+sep),'Archive path escapes its directory');return file;};
  for(const pack of report.packs) {
    assert.match(pack.file,/^candidate-[a-f0-9]{12}-\d+\.json$/);
    const raw=readFileSync(safe(prepared,pack.file));assert.equal(hash(raw),pack.sha256,'Candidate pack changed');
    for(const source of pack.sources) {
      const file=safe(dir,source.repo+'/'+(source.localPath || source.path));
      if(!verifiedSources.has(file)) {assert.equal(hash(readFileSync(file)),source.sha256,'Candidate source changed');verifiedSources.add(file);}
      assert.match(source.url,/^https:\/\/raw\.githubusercontent\.com\/[^/]+\/[^/]+\/[a-f0-9]{40}\//);
    }
    const rows=validateQuestions(JSON.parse(raw));assert.equal(rows.length,pack.count);
    const kept=[];
    for(const q of rows) {
      assert.equal(q.examId,pack.examId);
      assert.ok(q.source.includes(report.notice),'Candidate verification notice missing');
      assert.ok(pack.sources.some(s=>s.url===q.sourceUrl),'Candidate source reference missing');
      const fp=q.examId+'|'+candidateFingerprint(q);
      if(q.examId==='architect1') {
        const year=q.year.match(/^(H|R|平成|令和)(\d+)年?$/),number=q.source.match(/(\d+)\s—/);
        if(year && number && architecture.has(`${Number(year[2])+(['R','令和'].includes(year[1])?2018:1988)}|${q.subject}|${Number(number[1])}`)) continue;
      }
      if(fingerprints.has(fp)) continue;
      assert.ok(!keys.has(questionKey(q)),'Duplicate candidate ID');keys.add(questionKey(q));fingerprints.add(fp);
      for(const image of [...q.images,...q.solutionImages]) {
        assert.match(image.src,/^assets\/github-candidates\/[a-f0-9]{64}\.(png|jpe?g|webp)$/);
        const name=image.src.split('/').at(-1);
        if(!assets.has(name)) {assert.equal(hash(readFileSync(safe(join(prepared,'assets'),name))),name.slice(0,64));assets.add(name);}
      }
      kept.push(q);
    }
    if(kept.length) packs.push({id:pack.id,repo:pack.repo,examId:pack.examId,subject:pack.repo,count:kept.length,sources:pack.sources.map(s=>({...s,file:s.path})),
      verification:report.notice,rows:kept});
  }
  const registered=[...DEFAULT_EXAMS,...EXAM_CATALOG,...report.exams],used=new Set(packs.map(p=>p.examId));
  const exams=[...used].filter(id=>!existing.some(q=>q.examId===id)).map(id=>validateExam(registered.find(e=>e.id===id)));
  const repositories=report.repositories.map(r=>({...r,imported:packs.filter(p=>p.repo===r.repo).reduce((n,p)=>n+p.count,0)}));
  return {exams,packs,report:{...report,repositories,added:packs.reduce((n,p)=>n+p.count,0)}};
}
