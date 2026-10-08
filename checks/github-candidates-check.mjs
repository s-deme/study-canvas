import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,mkdtempSync,rmSync} from 'node:fs';
import {join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {tmpdir} from 'node:os';
import {createHash} from 'node:crypto';
import {loadGithubCandidates,candidateFingerprint} from '../scripts/github-candidates.mjs';
import {validateQuestions,emptyState,newSession,submit,finish,questionKey} from '../build/private/web/core.mjs';
const root=new URL('../',import.meta.url),hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const manifest=JSON.parse(readFileSync(new URL('build/private/manifest.json',root))),existing=manifest.packs.filter(p=>!p.id.startsWith('candidate-')).flatMap(p=>JSON.parse(readFileSync(new URL('build/private/web/'+p.url,root))));
const result=loadGithubCandidates(fileURLToPath(root),existing);
assert.equal(result.report.repositoryCount,result.report.repositories.length);
assert.equal(new Set(result.report.repositories.map(r=>r.repo)).size,result.report.repositoryCount);
assert.ok(result.report.repositoryCount>=71);assert.ok(result.report.added>5000);
for(const [repo,count] of [['akiina999/otsu2-training',149],['M-HMMY/kikenbutsu_otsu4_exam_app',105],['tetsu0950120/otsu3',151],['tetsu0950120/otsu5',101],['hutatumekozou/kikenbutu-otsu1syu',100]]) {
  const packs=result.packs.filter(p=>p.repo===repo);
  assert.equal(packs.reduce((n,p)=>n+p.count,0),count);assert.ok(packs.every(p=>p.localOnly));
}
const before=JSON.parse(readFileSync(new URL('private-data/github-candidates/hazmat-baseline.json',root)));
for(const p of before.packs.filter(p=>p.repo!=='iamirtasam/AWS-AI-Practitioner-Exam-Mock'))assert.equal(manifest.packs.find(b=>b.id===p.id)?.sha256,p.sha256,'Previous pack changed: '+p.id);
const aif=result.packs.filter(p=>p.repo==='iamirtasam/AWS-AI-Practitioner-Exam-Mock').flatMap(p=>p.rows);
assert.equal(aif.length,528);
assert.equal(aif.filter(q=>q.type==='written').length,24);
assert.equal(aif.filter(q=>q.type==='single').length,417);
assert.equal(aif.filter(q=>q.type==='multiple').length,87);
for(const q of aif) {
  assert.equal(q.examId,'aws-aif');assert.ok(q.explanation.includes('Copyright (c) 2026 iamirtasam'));
  const path=decodeURIComponent(new URL(q.sourceUrl).pathname.split('/').slice(4).join('/'));
  const text=readFileSync(new URL('private-data/github-candidates/iamirtasam/AWS-AI-Practitioner-Exam-Mock/'+path,root),'utf8');
  const sourceId=[...text.matchAll(/\bid:\s*"([^"]+)"/g)].find(m=>'github-'+hash('iamirtasam/AWS-AI-Practitioner-Exam-Mock|'+m[1]).slice(0,24)===q.id);
  assert.ok(sourceId);
  const answer=JSON.parse(text.slice(sourceId.index).match(/answer:\s*(\[[\d,\s]+\])/)[1]);
  if(q.type==='written') assert.equal(q.modelAnswer.split('\n')[0],answer.map(i=>i+1).join(' → '));
  else assert.deepEqual(Array.isArray(q.answer)?q.answer:[q.answer],answer);
}
for(const [repo,exam,type] of [['keisks/j_bar_exam','shiho','written'],['stueja/lpic-1-102-500-anki-flashcards','lpic1','written'],['MCCMDave/linux-essentials-quiz','linux-essentials','single'],['CarbonRaven/AWS-Quiz-SAA-C03','aws-saa',null]]) {
  const rows=result.packs.filter(p=>p.repo===repo).flatMap(p=>p.rows);
  assert.ok(rows.length>200,repo);assert.ok(rows.every(q=>q.examId===exam && (!type || q.type===type)));
}
const aws=result.packs.filter(p=>p.repo==='CarbonRaven/AWS-Quiz-SAA-C03').flatMap(p=>p.rows);
for(const q of aws) {
  const path=decodeURIComponent(new URL(q.sourceUrl).pathname.split('/').slice(4).join('/'));
  const source=JSON.parse(readFileSync(new URL('private-data/github-candidates/CarbonRaven/AWS-Quiz-SAA-C03/'+path,root)));
  const indices=(Array.isArray(q.answer)?q.answer:[q.answer]);
  assert.equal(indices.map(i=>Object.keys(source.options)[i]).join(''),source.correct_answer);
}
assert.ok(aws.some(q=>q.type==='multiple'));
const lpic=result.packs.filter(p=>p.repo==='stueja/lpic-1-102-500-anki-flashcards').flatMap(p=>p.rows);
assert.equal(lpic.filter(q=>q.solutionImages.length).length,2);assert.ok(lpic.every(q=>!/<(?:div|img|br)\b/i.test(q.modelAnswer)));
assert.equal(result.report.repositories.find(r=>r.repo==='eulerex/jlpt-test').imported,0);
assert.equal(manifest.questions,existing.length+result.report.added);
for(const [repo,names] of [['shajime0909-bit/eisei2',['関係法令','労働衛生','労働生理']],['yuaoki08/kokunai-travel-exam',['旅行業法令','約款','国内旅行実務']]]) {
  const rows=result.packs.filter(p=>p.repo===repo).flatMap(p=>p.rows);assert.deepEqual([...new Set(rows.map(q=>q.subject))].sort(),names.sort());
}
assert.ok(result.packs.filter(p=>p.repo==='5150kouhei-rgb/fp2-drill').flatMap(p=>p.rows).every(q=>q.year && !/^[A-F]$/.test(q.category)));
assert.ok(result.packs.filter(p=>p.repo==='masatopapa/unkan-quiz').flatMap(p=>p.rows).every(q=>q.year && q.term && !/^\d+$/.test(q.category)));
assert.equal(result.report.repositories.filter(r=>r.imported>0).length,result.report.repositories.filter(r=>result.packs.some(p=>p.repo===r.repo)).length);
for(const pack of result.packs) {
  const built=validateQuestions(JSON.parse(readFileSync(new URL('build/private/web/material/'+pack.id+'.json',root))));
  assert.deepEqual(built,pack.rows);
  for(const q of built) {
    assert.ok(q.source.includes('未検証'));
    if(q.type==='single' || q.type==='multiple') {
      const state=emptyState();state.selectedExam=q.examId;state.session=newSession([q],1,'検査');state.session.pending=q.answer;
      submit(state,[q]);finish(state,[q]);assert.equal(state.stats[questionKey(q)].correct,1);
    } else assert.ok(q.modelAnswer);
  }
}
assert.equal(candidateFingerprint({prompt:'Ａ B',passage:'',options:['a','b']}),candidateFingerprint({prompt:'A\nB',passage:'',options:['a','b']}));
assert.notEqual(candidateFingerprint({prompt:'value 10',options:['a','b']}),candidateFingerprint({prompt:'value 20',options:['a','b']}));
const temporary=mkdtempSync(join(tmpdir(),'study-candidates-'));
try {
  const dir=join(temporary,'private-data/github-candidates'),prepared=join(dir,'prepared');mkdirSync(join(dir,'owner/exam'),{recursive:true});mkdirSync(prepared,{recursive:true});
  const source=join(dir,'owner/exam/data.json'),packFile=join(prepared,'candidate-000000000001-1.json'),url='https://raw.githubusercontent.com/owner/exam/'+'a'.repeat(40)+'/data.json';
  writeFileSync(source,'original');
  const q={id:'candidate',examId:'fp3',type:'single',prompt:'question',options:['a','b'],answer:0,source:'unverified',sourceUrl:url};
  const raw=JSON.stringify([q]);writeFileSync(packFile,raw);
  const report={version:1,notice:'unverified',exams:[],repositories:[{repo:'owner/exam'}],packs:[{id:'candidate-000000000001-1',repo:'owner/exam',examId:'fp3',file:'candidate-000000000001-1.json',sha256:hash(raw),count:1,sources:[{repo:'owner/exam',path:'data.json',url,sha256:hash('original')}]}]};
  const reportFile=join(prepared,'report.json');writeFileSync(reportFile,JSON.stringify(report));
  assert.equal(loadGithubCandidates(temporary,[]).report.added,1);
  assert.equal(loadGithubCandidates(temporary,[validateQuestions([q])[0]]).report.added,0);
  assert.equal(loadGithubCandidates(temporary,[validateQuestions([{...q,id:'other',examId:'fp2'}])[0]]).report.added,1);
  writeFileSync(source,'changed');assert.throws(()=>loadGithubCandidates(temporary,[]),/source changed/);writeFileSync(source,'original');
  writeFileSync(packFile,'[]');assert.throws(()=>loadGithubCandidates(temporary,[]),/pack changed/);writeFileSync(packFile,raw);
  report.packs[0].sources[0].path='../../../escape.json';writeFileSync(reportFile,JSON.stringify(report));assert.throws(()=>loadGithubCandidates(temporary,[]),/escapes/);
} finally {rmSync(temporary,{recursive:true,force:true});}
console.log(`PASS: ${result.report.repositoryCount} candidate repositories, ${result.report.added} imported questions, scoring, source/pack integrity, deduplication and path rejection`);
