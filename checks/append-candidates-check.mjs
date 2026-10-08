import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,cpSync,writeFileSync,readFileSync,rmSync} from 'node:fs';
import {join,resolve,sep} from 'node:path';
import {tmpdir} from 'node:os';
import {createHash} from 'node:crypto';
import {spawnSync} from 'node:child_process';
import {validateQuestions} from '../web/core.mjs';

const root=mkdtempSync(join(tmpdir(),'study-append-check-'));
const hash=x=>createHash('sha256').update(x).digest('hex');
const save=(p,data)=>writeFileSync(join(root,p),typeof data==='string'?data:JSON.stringify(data));
try {
  for(const dir of ['scripts','web','build/private/web/material','private-data/github-candidates/prepared','private-data/github-candidates/fixture/repo']) mkdirSync(join(root,dir),{recursive:true});
  for(const file of ['append-food-material.mjs','github-material.mjs','github-candidates.mjs','school-material.mjs','private-build-update.mjs']) cpSync(new URL('../scripts/'+file,import.meta.url),join(root,'scripts',file));
  for(const file of ['core.mjs','catalog.mjs','exams.mjs']) cpSync(new URL('../web/'+file,import.meta.url),join(root,'web',file));
  for(const [kind,examId] of [['github-hazmat','hazmat-b2'],['github-denken','denken2'],['github-candidates','hazmat-b2']]) {
    const notice='fixture',url='https://raw.githubusercontent.com/fixture/repo/'+'a'.repeat(40)+'/questions.json';
    const rows=validateQuestions(['old','new'].map(id=>({id,examId,type:'single',prompt:id+' prompt',options:['a','b'],answer:0,source:notice,sourceUrl:url})));
    const id='candidate-aaaaaaaaaaaa-1',oldRaw=JSON.stringify([rows[0]]),raw=JSON.stringify(rows);
    const pack={id,examId,count:1,url:'material/'+id+'.json',sha256:hash(oldRaw),localOnly:true};
    const manifest=JSON.stringify({questions:1,packs:[pack],exams:[],files:2});
    const catalog='export const MATERIAL_PACKS='+JSON.stringify([pack])+';export const MATERIAL_INDEX='+JSON.stringify([{...rows[0],catalogOnly:true}])+';export const MATERIAL_EXAMS=[];';
    save('build/private/web/'+pack.url,oldRaw);
    save('build/private/manifest.json',manifest);save('build/private/web/catalog.mjs',catalog);
    save('private-data/github-candidates/fixture/repo/questions.json',raw);
    const candidate={id,file:id+'.json',repo:'fixture/repo',examId,count:2,sha256:hash(raw),localOnly:true,sources:[{repo:'fixture/repo',path:'questions.json',url,sha256:hash(raw)}]};
    const report={version:1,notice,exams:[],repositories:[{repo:'fixture/repo'}],packs:[candidate]};
    save('private-data/github-candidates/prepared/'+candidate.file,raw);
    save('private-data/github-candidates/prepared/report.json',report);
    const run=()=>spawnSync(process.execPath,[join(root,'scripts/append-food-material.mjs'),kind],{encoding:'utf8',cwd:root});
    const rejected=run();assert.notEqual(rejected.status,0);assert.match(rejected.stderr,/Existing candidate pack requires full rebuild/);
    assert.equal(readFileSync(join(root,'build/private/manifest.json'),'utf8'),manifest);
    assert.equal(readFileSync(join(root,'build/private/web/catalog.mjs'),'utf8'),catalog);
    assert.equal(readFileSync(join(root,'build/private/web',pack.url),'utf8'),oldRaw);
    // A distinct new pack must still append successfully after the rejected update.
    const addedId='candidate-bbbbbbbbbbbb-1',addedRaw=JSON.stringify([rows[1]]);
    report.packs=[{...candidate,id:addedId,file:addedId+'.json',count:1,sha256:hash(addedRaw)}];
    save('private-data/github-candidates/prepared/'+addedId+'.json',addedRaw);
    save('private-data/github-candidates/prepared/report.json',report);
    const added=run();assert.equal(added.status,0,added.stderr);
    const built=JSON.parse(readFileSync(join(root,'build/private/manifest.json')));
    assert.equal(built.questions,2);assert.deepEqual(built.packs.map(p=>p.id),[id,addedId]);
    assert.equal(readFileSync(join(root,'build/private/web',pack.url),'utf8'),oldRaw);
  }
  console.log('PASS: all three candidate imports reject pack collisions without changing output; distinct packs still append');
} finally {
  assert.ok(resolve(root).startsWith(resolve(tmpdir())+sep));
  assert.ok(root.split(/[\\/]/).at(-1).startsWith('study-append-check-'));
  rmSync(root,{recursive:true,force:true});
}
