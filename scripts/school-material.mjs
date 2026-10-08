// Original and licensed external school exercises stay with the private material.
import assert from 'node:assert/strict';
import {existsSync,readFileSync} from 'node:fs';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {validateExam,validateQuestions,questionKey} from '../web/core.mjs';

export function loadSchoolMaterial(root,existing=[]) {
  const dir=join(root,'private-data/school');
  const manifests=['manifest.json','high-manifest.json','expansion-manifest.json'].map(name=>join(dir,name)).filter(existsSync).map(file=>JSON.parse(readFileSync(file)));
  if(!manifests.length) return {exams:[],packs:[],report:{added:0}};
  for(const item of manifests) assert.equal(item.version,1);
  const manifest={exams:manifests.flatMap(m=>m.exams),packs:manifests.flatMap(m=>m.packs),questions:manifests.reduce((n,m)=>n+m.questions,0)};
  const hash=b=>createHash('sha256').update(b).digest('hex');
  const expansionFile=join(dir,'expansion-manifest.json');
  if(existsSync(expansionFile)) {
    const expansion=JSON.parse(readFileSync(expansionFile));
    const verification=JSON.parse(readFileSync(join(dir,'expansion-verification.json')));
    assert.equal(verification.manifestSha256,hash(readFileSync(expansionFile)),'Run school/check-expansion.py before building');
    assert.equal(verification.questions,expansion.questions);
    for(const [name,sha256] of Object.entries(expansion.files)) {
      assert.match(name,/^(?:external\/)?[a-zA-Z0-9_.-]+$/);
      assert.equal(hash(readFileSync(join(dir,name))),sha256,'School expansion input changed: '+name);
    }
  }
  const elementaryFile=join(dir,'manifest.json');
  if(existsSync(elementaryFile)) {
    const elementary=JSON.parse(readFileSync(elementaryFile));
    for(const name of ['author.py','knowledge.txt','practical.py','check.py']) assert.equal(hash(readFileSync(join(dir,name))),elementary.authors[name],'Regenerate school material: '+name);
    for(const source of elementary.curriculumSources) {
      assert.ok(['elementary.csv','junior.csv','kanjidic2.xml.gz','edrdg-licence.html'].includes(source.file));
      assert.equal(hash(readFileSync(join(dir,source.file))),source.sha256,'School reference changed');
    }
    const verification=JSON.parse(readFileSync(join(dir,'verification.json')));
    assert.equal(verification.manifestSha256,hash(readFileSync(elementaryFile)),'Run school/check.py before building');
    assert.equal(verification.questions,elementary.questions);
  }
  const exams=manifest.exams.map(validateExam),examIds=new Set(exams.map(e=>e.id));
  assert.equal(examIds.size,exams.length);
  const keys=new Set(existing.map(questionKey)),packIds=new Set(),texts=new Set();
  const packs=manifest.packs.map(pack=>{
    assert.match(pack.id,/^school-[a-z0-9-]+$/);assert.ok(!packIds.has(pack.id));packIds.add(pack.id);
    assert.ok(examIds.has(pack.examId));
    const bytes=readFileSync(join(dir,pack.id+'.json'));assert.equal(hash(bytes),pack.sha256);
    const rows=validateQuestions(JSON.parse(bytes),[],false,pack.examId);assert.equal(rows.length,pack.count);
    const exam=exams.find(e=>e.id===pack.examId);
    for(const q of rows) {
      const key=questionKey(q);assert.ok(!keys.has(key),'Duplicate school ID '+key);keys.add(key);
      const text=q.examId+'::'+q.subject+'::'+q.prompt;assert.ok(!texts.has(text),'Duplicate school prompt');texts.add(text);
      assert.ok(exam.subjects.includes(q.subject) && q.category && q.topic);
      assert.ok((q.modelAnswer || q.type==='single') && q.explanation && q.source);
      if(pack.id.startsWith('school-extra-')) assert.ok(q.sourceUrl.startsWith('https://') && pack.license && pack.verification);
      else assert.ok(q.source.includes('自作') && q.source.includes('AI生成'));
    }
    return {...pack,rows,localOnly:true};
  });
  const count=packs.reduce((n,p)=>n+p.count,0);assert.equal(count,manifest.questions);
  return {exams,packs,report:{added:count}};
}
