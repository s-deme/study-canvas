import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {loadGithubMaterial} from '../scripts/github-material.mjs';
import {correctAnswer} from '../web/core.mjs';
const read=p=>JSON.parse(readFileSync(p)),base='private-data/github-material/';
const manifest=read('build/private/manifest.json'),before=read(base+'fire-baseline.json');
for(const p of before.packs) assert.equal(manifest.packs.find(b=>b.id===p.id)?.sha256,p.sha256,'Existing pack changed: '+p.id);
const material=loadGithubMaterial(process.cwd(),[],'fire-report.json','fire-verification.json');
assert.equal(material.report.added,232);
const expected={'fire-a-special':4,'fire-a1':21,'fire-a2':22,'fire-a3':20,'fire-a4':15,'fire-a5':14,'fire-b1':23,'fire-b2':23,'fire-b3':23,'fire-b4':19,'fire-b5':16,'fire-b6':15,'fire-b7':17};
const unique=new Set();let practicals=0;
for(const p of material.packs){
  assert.equal(p.rows.length,expected[p.examId]);
  const built=manifest.packs.find(b=>b.id===p.id);assert.ok(built?.localOnly);
  assert.deepEqual(read('build/private/web/'+built.url),p.rows);
  const kind=p.examId.startsWith('fire-a')?'kou':'otsu';
  const original=read(base+'prepared/safety-shoubou_'+kind+'.json');
  for(const q of p.rows){
    unique.add(q.sourceUrl+'|'+(q.type==='single'?q.id.split('-q').at(-1):q.id));
    if(q.type==='single'){
      const n=Number(q.id.split('-q').at(-1));assert.equal(q.answer,original[n-1].answer);
      assert.deepEqual(q.images,original[n-1].images);assert.ok(correctAnswer(q,q.answer));
      assert.ok(!correctAnswer(q,(q.answer+1)%4));
    }else{
      practicals++;assert.equal(q.type,'written');assert.match(q.modelAnswer,/公式PDF/);
      const c=Number(q.examId.at(-1));
      const page=kind==='kou'?(q.subject==='製図'?19+c:14+c):15+c;
      const answer=kind==='kou'?(q.subject==='製図'?(c<=3?27:28):26):(c<=4?24:25);
      assert.match(q.images[0].src,new RegExp(`-p${String(page).padStart(3,'0')}\\.png$`));
      assert.match(q.solutionImages[0].src,new RegExp(`-p${String(answer).padStart(3,'0')}\\.png$`));
    }
    assert.equal(q.solutionImages.length,1);
    for(const image of [...q.images,...q.solutionImages]){
      const hash=p=>createHash('sha256').update(readFileSync(p)).digest('hex');
      assert.equal(hash('build/private/web/'+image.src),hash(base+'prepared/assets/'+image.src.split('/').at(-1)));
    }
  }
}
assert.equal(practicals,17);assert.equal(unique.size,93);
assert.ok(manifest.questions>=before.questions+232);
assert.ok(manifest.exams.find(e=>e.id==='github-fire-common').count>=before.exams.find(e=>e.id==='github-fire-common').count);
console.log('PASS: 13 classes / 232 registrations / 17 new practicals; original answers, images, existing packs and unofficial material preserved');
