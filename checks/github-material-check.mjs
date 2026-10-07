import assert from 'node:assert/strict';
import {existsSync,mkdirSync,mkdtempSync,readFileSync,writeFileSync} from 'node:fs';
import {join,resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {loadGithubMaterial} from '../scripts/github-material.mjs';
import {emptyState,newSession,submit,finish,questionKey,validateState,validateQuestions} from '../web/core.mjs';
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
function checkImportedRows(current,packs) {
  for(const pack of packs) {
    const built=current.packs.find(p=>p.id==='archive-'+pack.file.slice(0,-5));
    assert.ok(built,'Missing imported pack '+pack.file);
    const rows=validateQuestions(JSON.parse(readFileSync(join('private-data/github-material/prepared',pack.file))));
    assert.deepEqual(validateQuestions(JSON.parse(readFileSync(join('build/private/web',built.url)))),rows,'Imported pack changed '+pack.file);
  }
}
mkdirSync('build',{recursive:true});const root=mkdtempSync(join(resolve('build'),'github-check-'));
assert.equal(loadGithubMaterial(root,[]).packs.length,0);
const dir=join(root,'private-data/github-material'),prepared=join(dir,'prepared');mkdirSync(join(prepared,'assets'),{recursive:true});
const q={id:'fixture-q001',examId:'ip',year:'2025',type:'single',prompt:'Synthetic archive fixture',options:['A','B'],answer:1,sourceUrl:'https://example.com/fixture_qs.pdf',images:[{src:'assets/github-material/fixture.png',alt:'Fixture only'}]};
writeFileSync(join(dir,'fixture.pdf'),'fixture source');writeFileSync(join(prepared,'assets/fixture.png'),'fixture pixels');
const bytes=JSON.stringify([q]);writeFileSync(join(prepared,'fixture.json'),bytes);
const report={packs:[{status:'prepared',file:'fixture.json',count:1,sha256:hash(bytes),examId:'ip',year:'2025',url:q.sourceUrl,
  sources:[{file:'fixture.pdf',url:q.sourceUrl,sha256:hash('fixture source')}],questions:[{id:q.id,number:1,answer:1,images:[{file:'fixture.png',sha256:hash('fixture pixels')}]}]}]};
const raw=JSON.stringify(report);writeFileSync(join(prepared,'report.json'),raw);
writeFileSync(join(prepared,'verification.json'),JSON.stringify({reportSha256:hash(raw),officialAnswers:'pass',originalPixels:'pass'}));
assert.equal(loadGithubMaterial(root,[]).report.added,1);
const registered=loadGithubMaterial(root,[]).packs[0].rows;
assert.equal(loadGithubMaterial(root,registered).report.added,0);
assert.throws(()=>loadGithubMaterial(root,[{...registered[0],answer:0}]),/Conflicting repeated/);
assert.throws(()=>loadGithubMaterial(root,[{...registered[0],id:'different-q001'}]),/Previously registered/);
writeFileSync(join(prepared,'assets/fixture.png'),'changed');assert.throws(()=>loadGithubMaterial(root,[]),/image changed/);assert.throws(()=>loadGithubMaterial(root,registered),/image changed/);writeFileSync(join(prepared,'assets/fixture.png'),'fixture pixels');
writeFileSync(join(dir,'fixture.pdf'),'changed');assert.throws(()=>loadGithubMaterial(root,[]),/source changed/);writeFileSync(join(dir,'fixture.pdf'),'fixture source');
writeFileSync(join(prepared,'fixture.json'),bytes+' ');assert.throws(()=>loadGithubMaterial(root,[]),/pack changed/);writeFileSync(join(prepared,'fixture.json'),bytes);
writeFileSync(join(prepared,'report.json'),raw+' ');assert.throws(()=>loadGithubMaterial(root,[]),/needs verification/);
if(process.argv.includes('--fixture-only')) {console.log('PASS: exact archive reuse, conflicting/renamed duplicate rejection and source/pack/image verification');process.exit(0);}
if(existsSync('private-data/github-material/baseline.json') && existsSync('build/private/manifest.json')) {
  const baseline=JSON.parse(readFileSync('private-data/github-material/baseline.json','utf8'));
  const current=JSON.parse(readFileSync('build/private/manifest.json','utf8'));
  for(const [id,prior] of Object.entries(baseline.packs)) {
    const pack=current.packs.find(p=>p.id===id);assert.ok(pack,id);
    assert.equal(hash(readFileSync(join('build/private/web',pack.url))),prior.sha256,'Existing pack changed '+id);
  }
  if(current.packs.some(p=>p.id.startsWith('archive-'))) {
    const existing=Object.values(baseline.packs).flatMap(p=>p.rows),loaded=loadGithubMaterial(resolve('.'),existing);
    assert.equal(current.questions,current.packs.reduce((n,p)=>n+p.count,0),'Manifest total differs from packs');
    for(const pack of loaded.packs) {
      const built=current.packs.find(p=>p.id===pack.id);assert.ok(built,'Missing imported pack '+pack.id);
      assert.equal(built.count,pack.rows.length);
      assert.deepEqual(validateQuestions(JSON.parse(readFileSync(join('build/private/web',built.url)))),pack.rows,'Imported pack changed '+pack.id);
    }
    const images=new Map(loaded.report.packs.filter(p=>p.status==='prepared').flatMap(p=>p.questions.flatMap(q=>q.images.map(i=>[i.file,i.sha256]))));
    for(const [file,sha] of images) assert.equal(hash(readFileSync(join('build/private/web/assets/github-material',file))),sha,'Copied image changed '+file);
    console.log(`PASS: ${loaded.report.added} archived questions, ${Object.keys(baseline.packs).length} old packs unchanged`);
  }
}
console.log('PASS: archive verification binding, sources, images, stale packs and official question deduplication');
if(existsSync('private-data/github-material/nonit-baseline.json')) {
  const baseline=JSON.parse(readFileSync('private-data/github-material/nonit-baseline.json','utf8'));
  const current=JSON.parse(readFileSync('build/private/manifest.json','utf8'));
  const report=JSON.parse(readFileSync('private-data/github-material/prepared/nonit-report.json','utf8'));
  const added=report.packs.filter(p=>p.status==='prepared');
  const expansion=existsSync('private-data/github-material/prepared/expansion-report.json')?JSON.parse(readFileSync('private-data/github-material/prepared/expansion-report.json','utf8')).packs.filter(p=>p.status==='prepared'):[];
  checkImportedRows(current,[...added,...expansion]);
  for(const [id,sha] of Object.entries(baseline.packs)) {
    const pack=current.packs.find(p=>p.id===id);assert.ok(pack,id);
    assert.equal(hash(readFileSync(join('build/private/web',pack.url))),sha,'Pre-existing pack changed '+id);
  }
  assert.deepEqual([...new Set(added.map(p=>p.examId))].sort(),['denken3','dentist','doctor','electrician1','electrician2','pharmacist']);
  const rows=[...added,...expansion].flatMap(p=>JSON.parse(readFileSync(join('private-data/github-material/prepared',p.file),'utf8')));
  const state=emptyState();
  for(const examId of [...new Set(rows.map(q=>q.examId))]) for(const q of [rows.find(q=>q.examId===examId),rows.find(q=>q.examId===examId && q.type==='multiple')].filter(Boolean)) {
    state.selectedExam=examId;state.session=newSession([q],1,'Non-IT import verification');state.session.pending=q.answer;
    submit(state,rows);finish(state,rows);assert.equal(state.stats[questionKey(q)].correct,1);
  }
  assert.deepEqual(validateState(JSON.parse(JSON.stringify(state)),rows).stats,state.stats);
  console.log(`PASS: ${rows.length} non-IT questions, single/multiple grading and ${Object.keys(baseline.packs).length} previous packs unchanged`);
}
if(existsSync('private-data/github-material/expansion-baseline.json')) {
  const baseline=JSON.parse(readFileSync('private-data/github-material/expansion-baseline.json','utf8'));
  const current=JSON.parse(readFileSync('build/private/manifest.json','utf8'));
  const added=JSON.parse(readFileSync('private-data/github-material/prepared/expansion-report.json','utf8')).packs.filter(p=>p.status==='prepared');
  checkImportedRows(current,added);
  for(const [id,sha] of Object.entries(baseline.packs)) assert.equal(hash(readFileSync(join('build/private/web',current.packs.find(p=>p.id===id).url))),sha,'Previous collection changed '+id);
  console.log(`PASS: ${added.reduce((n,p)=>n+p.count,0)} newly registered questions and ${Object.keys(baseline.packs).length} previous packs unchanged`);
}
