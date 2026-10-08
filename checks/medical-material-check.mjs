import assert from 'node:assert/strict';
import {readFileSync,existsSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {validateQuestions,correctAnswer,questionKey} from '../web/core.mjs';
import {loadMedicalMaterial} from '../scripts/medical-material.mjs';
const read=file=>JSON.parse(readFileSync(file)),hash=b=>createHash('sha256').update(b).digest('hex');
const manifest=read('build/private/manifest.json'),baseline=read('private-data/github-material/medical-baseline.json');
const changes=Object.entries(baseline).filter(([id,sha])=>manifest.packs.find(p=>p.id===id)?.sha256!==sha);
const prior=[],medical=[],counts={},keys=new Set();
for(const pack of manifest.packs) {
  const raw=readFileSync('build/private/web/'+pack.url);assert.equal(hash(raw),pack.sha256);
  const rows=validateQuestions(JSON.parse(raw));assert.equal(rows.length,pack.count);
  if(!pack.id.startsWith('medical-jmed-') && !pack.id.startsWith('archive-medical-')) {prior.push(...rows);continue;}
  medical.push(...rows);
  for(const q of rows) {
    assert.ok(!keys.has(questionKey(q)));keys.add(questionKey(q));assert.ok(correctAnswer(q,q.answer));
    assert.ok(!correctAnswer(q,q.type==='multiple'?[]:(q.answer+1)%q.options.length));
    for(const image of [...q.images,...q.solutionImages]) assert.ok(existsSync('build/private/web/'+image.src),image.src);
    if(pack.id.startsWith('medical-jmed-')) {
      assert.ok(pack.localOnly);assert.equal(q.solutionImages.length,0,'Visual choices must be shown before grading');
      assert.ok(![q.prompt,q.passage,...q.options].join('').includes('\ufffd'));
    }
  }
  counts[pack.examId]=(counts[pack.examId]||0)+rows.length;
}
// A concurrent architecture import replaces candidates by official year/subject/number; require unchanged archived gold.
const candidates=read('private-data/github-candidates/prepared/report.json'),byId=new Map(prior.map(q=>[questionKey(q),q]));
const architecture=new Map(prior.filter(q=>q.examId==='architect1' && q.id.startsWith('construction-'))
  .map(q=>[[q.year,q.subject,Number(q.id.match(/-q(\d+)$/)[1])].join('|'),q]));
for(const [id,sha] of changes) {
  assert.match(id,/^candidate-0a1c4990e588-[123]$/,'Unexpected previous pack change');
  const pack=candidates.packs.find(p=>p.id===id);assert.ok(pack);
  const original=validateQuestions(read('private-data/github-candidates/prepared/'+pack.file));
  assert.equal(hash(JSON.stringify(original)),sha,'Original candidate archive changed');
  for(const q of original) {
    const year=q.year.match(/^(H|R|平成|令和)(\d+)年?$/),number=q.source.match(/(\d+)\s—/);
    const match=byId.get(questionKey(q)) || (year && number && architecture.get(
      [Number(year[2])+(['R','令和'].includes(year[1])?2018:1988),q.subject,Number(number[1])].join('|')));
    assert.ok(match,'Previous architecture question missing');assert.ok(correctAnswer(q,match.answer),'Archived gold changed');
  }
}
const loaded=loadMedicalMaterial(process.cwd(),[...prior,...medical.filter(q=>!q.id.startsWith('jmed-'))]);
assert.deepEqual(medical.filter(q=>q.id.startsWith('jmed-')),loaded.packs.flatMap(p=>p.rows));
for(const pack of loaded.packs) {
  const source=pack.sources.find(s=>s.file.endsWith('.json')),original=read('private-data/github-material/'+source.file);
  for(const q of pack.rows) {
    const number=Number(q.id.match(/-q(\d+)$/)[1]);
    const src=original.questions.find(s=>s.question_number===number && String(s.section||'')===q.subject);assert.ok(src);
    assert.equal(q.prompt,src.question_text.trim());assert.equal(q.passage,(src.text_reference||'').trim());
    const choices=Object.values(src.options);
    assert.deepEqual(q.options,choices.every(s=>!s.trim())?choices.map((_,i)=>String(i+1)+'（図中の選択肢）'):choices.map(s=>s.trim()));
    const labels=Object.keys(src.options).map(s=>s.toUpperCase()),gold=src.correct_answer.map(s=>labels.indexOf(String(s).toUpperCase()));
    assert.deepEqual(q.answer,gold.length>1?gold:gold[0]);
    assert.equal(q.images.length,Object.values(src.img||{}).flat().filter(Boolean).length,'All supplied figures/visual choices must be visible');
  }
}
assert.ok(medical.length>0);
console.log('PASS: medical imports, source gold, visible figures, grading, uniqueness and previous packs',counts);
