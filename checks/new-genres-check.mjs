// Current local 150-question session; deliberately independent of the older 10,000 target.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {MATERIAL_PACKS,MATERIAL_INDEX} from '../build/private/web/catalog.mjs';
import {validateQuestions,questionKey} from '../web/core.mjs';
import {materialFingerprint} from '../scripts/additional-material.mjs';
const read=path=>JSON.parse(readFileSync(new URL(path,import.meta.url),'utf8'));
const baseline=read('../private-data/additions/new-genres-baseline.json'),current=read('../build/private/manifest.json');
const all=MATERIAL_PACKS.flatMap(p=>validateQuestions(read('../build/private/web/'+p.url)));
for(const old of baseline.packs) assert.equal(MATERIAL_PACKS.find(p=>p.id===old.id)?.sha256,old.sha256,'Existing pack changed: '+old.id);
for(const exam of baseline.exams) assert.equal(current.exams.find(e=>e.id===exam.id)?.count,exam.count,'Existing exam changed');
assert.equal(baseline.questions,baseline.exams.reduce((n,e)=>n+e.count,0));
const fresh=MATERIAL_PACKS.filter(p=>p.id.startsWith('original-new-')),rows=all.filter(q=>q.id.startsWith('original-new-'));
assert.equal(fresh.length,9);assert.equal(rows.length,150);assert.equal(all.length,baseline.questions+150);
assert.equal(all.length,MATERIAL_INDEX.length);assert.equal(current.exams.length,baseline.exams.length+3);
const prior=new Set(all.filter(q=>!q.id.startsWith('original-new-')).map(materialFingerprint));
const keys=new Set(),fingerprints=new Set(),topics=new Set();
for(const q of rows) {
 assert.ok(!keys.has(questionKey(q)));keys.add(questionKey(q));
 const fp=materialFingerprint(q);assert.ok(!prior.has(fp)&&!fingerprints.has(fp),'Duplicate: '+q.id);fingerprints.add(fp);
 assert.ok(!topics.has(q.topic));topics.add(q.topic);
 assert.match(q.prompt,/自作対策問題 \/ 難易度: (基礎|標準|応用)/);assert.match(q.prompt,/2026-10-05/);
 assert.ok(q.subject&&q.category&&q.sourceUrl&&q.explanation.includes('根拠箇所:'));
 assert.match(q.source,/自作問題/);assert.ok(!q.source.includes('公式過去問'));
 assert.equal(q.options.length,3);assert.equal(new Set(q.options).size,3);
 for(const option of q.options) assert.ok(q.explanation.includes('選択肢「'+option+'」:'),'Missing distractor explanation');
}
const byExam=[];
for(const [id,field] of [['gyosei-original','法律・行政'],['health2-original','医療・健康'],['agri3-original','農業・食品']]) {
 const qs=rows.filter(q=>q.examId===id),packs=fresh.filter(p=>p.examId===id);
 assert.equal(qs.length,50);assert.deepEqual(packs.map(p=>p.count),[15,15,20]);assert.ok(packs.every(p=>p.kind==='original'&&p.field===field));
 const subjects={},categories={},difficulty={};for(const q of qs) {subjects[q.subject]=(subjects[q.subject]||0)+1;categories[q.category]=(categories[q.category]||0)+1;const d=q.prompt.match(/難易度: (\S+)/)[1];difficulty[d]=(difficulty[d]||0)+1;}
 assert.equal(Object.keys(subjects).length,3);assert.equal(Object.keys(difficulty).length,3);
 byExam.push({id,field,name:current.exams.find(e=>e.id===id).name,questions:50,official:0,original:50,subjects,categories,difficulty});
}
const report={session:'new-genres-2026-10-05',before:{questions:baseline.questions,exams:baseline.exams.length,packs:baseline.packs.length},after:{questions:all.length,exams:current.exams.length,packs:MATERIAL_PACKS.length},added:150,official:0,original:150,duplicateExclusions:0,qualityExclusions:0,unverifiedRegistered:0,byExam,existingPacksUnchanged:baseline.packs.length,contentSha256:createHash('sha256').update(JSON.stringify(rows)).digest('hex'),checks:'counts, baseline pack hashes, ids, conservative duplicates, all-option explanations, sources, dates, subjects, fields and difficulty',reviewLimit:'Knowledge checks are author-agent source-grounded review, not independent expert/human review.'};
for(const path of ['../private-data/additions/new-genres-report.json','../build/private/new-genres-report.json']) writeFileSync(new URL(path,import.meta.url),JSON.stringify(report,null,2));
console.log('PASS new genres: 150 original, 3 x 50, nine verified units; 164 existing pack hashes unchanged');
