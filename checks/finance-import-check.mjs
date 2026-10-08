import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {resolve} from 'node:path';
import {loadGithubMaterial} from '../scripts/github-material.mjs';
import {MATERIAL_PACKS,MATERIAL_INDEX} from '../build/private/web/catalog.mjs';
import {emptyState,newSession,submit,finish,validateState,questionKey} from '../build/private/web/core.mjs';

const loaded=loadGithubMaterial(resolve('.'),[],'finance-report.json','finance-verification.json');
const rows=loaded.packs.flatMap(p=>p.rows);
assert.equal(rows.length,2331);
assert.equal(loadGithubMaterial(resolve('.'),rows,'finance-report.json','finance-verification.json').report.added,0);
const combined=rows.filter(q=>q.year==='2014' && q.term==='第Ⅱ回' && ['管理会計論','監査論'].includes(q.subject));
assert.equal(new Set(combined.map(q=>q.sourceUrl)).size,1);
assert.equal(new Set(combined.map(q=>q.subject)).size,2);
const baseline=JSON.parse(readFileSync('private-data/github-material/finance-baseline.json'));
for(const pack of baseline.packs.filter(p=>['boki3','fp2','fp3'].includes(p.examId)))
 assert.equal(MATERIAL_PACKS.find(p=>p.id===pack.id)?.sha256,pack.sha256,'Existing finance pack changed '+pack.id);
for(const pack of loaded.packs) assert.equal(MATERIAL_PACKS.find(p=>p.id===pack.id)?.count,pack.count);
assert.equal(MATERIAL_PACKS.filter(p=>p.id.startsWith('archive-finance-')).reduce((n,p)=>n+p.count,0),2331);
for(const examId of ['cpa','fp3']) {
 const q=rows.find(q=>q.examId===examId),state=emptyState();
 state.selectedExam=examId;state.session=newSession([q],1,'取り込み検証');
 state.session.pending=q.answer;submit(state,[q]);finish(state,[q]);
 assert.equal(validateState(state,MATERIAL_INDEX).stats[questionKey(q)].correct,1);
}
console.log('PASS: 2331 finance questions, combined-paper subjects, repeat-import deduplication, existing finance packs preserved and grading');
