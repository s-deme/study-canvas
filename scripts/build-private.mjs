import assert from 'node:assert/strict';
import {cpSync,existsSync,mkdirSync,readFileSync,readdirSync,rmSync,writeFileSync,statSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {validateQuestions,questionKey,DEFAULT_EXAMS} from '../web/core.mjs';
import {loadAdditionalMaterial} from './additional-material.mjs';

const root=fileURLToPath(new URL('../',import.meta.url)),out=resolve(root,'build/private');
assert.equal(out,join(resolve(root),'build','private'));
const read=path=>JSON.parse(readFileSync(path,'utf8'));
const material=join(root,'private-data/material'), packsFile=join(material,'packs.json');
assert.ok(existsSync(packsFile),'Run fetch-material.py, ocr-material.py and prepare-material.py first');
assert.deepEqual(read(join(material,'errors.json')),[],'Unresolved material extraction errors; do not deploy');
const original=read(join(root,'private-data/questions.json'));
const restored=read(join(root,'private-data/retired-material/questions-v2.json'));
const existingPacks=read(packsFile).map(p=>({...p,rows:read(join(material,p.file))}));
const additions=loadAdditionalMaterial(root,[...original,...restored,...existingPacks.flatMap(p=>p.rows)]);
// Keep the output root: a local preview process may hold it as its working directory on Windows.
if(existsSync(out)) for(const name of readdirSync(out)) {
 const target=resolve(out,name);assert.equal(target.startsWith(out+'\\') || target.startsWith(out+'/'),true);
 rmSync(target,{recursive:true,force:true});
}
mkdirSync(join(out,'web/material'),{recursive:true});
cpSync(join(root,'web'),join(out,'web'),{recursive:true});
cpSync(join(root,'functions'),join(out,'functions'),{recursive:true});
cpSync(join(root,'schema.sql'),join(out,'schema.sql'));
mkdirSync(join(out,'web/assets/material'),{recursive:true});
cpSync(join(root,'private-data/retired-material/assets'),join(out,'web/assets'),{recursive:true});
const names={ap:'応用情報技術者',st:'ITストラテジスト',sa:'システムアーキテクト',pm:'プロジェクトマネージャ',nw:'ネットワークスペシャリスト',db:'データベーススペシャリスト',es:'エンベデッドシステムスペシャリスト',sm:'ITサービスマネージャ',au:'システム監査技術者',sc:'情報処理安全確保支援士'};
const exams=Object.entries(names).map(([id,name])=>({id,name,field:'IT',subjects:[],categories:[]}));
for(const exam of additions.exams) {
 const prior=[...DEFAULT_EXAMS,...exams].find(e=>e.id===exam.id);
 if(prior) assert.deepEqual(exam,prior,'Conflicting added exam '+exam.id);
 else exams.push(exam);
}
const packs=[],index=[],keys=new Set();
function add(id,rows,metadata={}) {
  const checked=validateQuestions(rows);
  for(const q of checked) {
    assert.ok(!keys.has(questionKey(q)),`Duplicate ${questionKey(q)}`);keys.add(questionKey(q));
    for(const image of [...q.images,...q.solutionImages]) if(image.src.startsWith('assets/')) {
      if(image.src.startsWith('assets/material/')) cpSync(join(material,'assets',image.src.slice('assets/material/'.length)),join(out,'web',image.src));
      if(image.src.startsWith('assets/additions/')) {mkdirSync(join(out,'web/assets/additions'),{recursive:true});cpSync(join(root,'private-data/additions/assets',image.src.slice('assets/additions/'.length)),join(out,'web',image.src));}
      assert.ok(existsSync(join(out,'web',image.src)),image.src);
    }
    index.push({id:q.id,examId:q.examId,type:q.type,options:q.options.map((_,i)=>String(i)),catalogOnly:true,year:q.year,term:q.term,subject:q.subject});
  }
  const text=JSON.stringify(checked),file=id+'.json';writeFileSync(join(out,'web/material',file),text);
  packs.push({...metadata,id,examId:checked[0].examId,count:checked.length,url:'material/'+file,sha256:createHash('sha256').update(text).digest('hex')});
}
add('gken-restored',original);
for(const examId of ['sg','fe','boki3']) add(examId+'-restored',restored.filter(q=>q.examId===examId));
const audit=read(join(material,'audit.json'));
for(const pack of existingPacks) {
 const stem=pack.id.slice(0,-pack.examId.length-1);
 add(pack.id,pack.rows,{year:pack.year,term:pack.term,subject:pack.subject,sources:audit.sources.filter(s=>s.file.startsWith(stem+'_')),verification:'問題番号・公式解答対応・画像参照を検査済み'});
}
for(const {rows,...pack} of additions.packs) add(pack.id,rows,pack);
for(const exam of exams) assert.ok(index.some(q=>q.examId===exam.id),exam.id);
writeFileSync(join(out,'web/catalog.mjs'),`// Generated private index. Question bodies are loaded separately.\nexport const BUILTIN_QUESTIONS=[];\nexport const MATERIAL_INDEX=${JSON.stringify(index)};\nexport const MATERIAL_PACKS=${JSON.stringify(packs)};\nexport const MATERIAL_EXAMS=${JSON.stringify(exams)};\n`);
cpSync(join(material,'audit.json'),join(out,'web/material/audit.json'));
if(existsSync(join(material,'verification.json'))) cpSync(join(material,'verification.json'),join(out,'web/material/verification.json'));
writeFileSync(join(out,'web/material/expansion-report.json'),JSON.stringify(additions.report,null,2));
const files=[];
function walk(dir) {for(const name of readdirSync(dir)){const p=join(dir,name);if(statSync(p).isDirectory()) walk(p);else {assert.ok(statSync(p).size<25*1024*1024,`Pages asset too large: ${p}`);files.push(p);}}}
walk(join(out,'web'));assert.ok(files.length<=20000,'Pages file limit exceeded');
writeFileSync(join(out,'manifest.json'),JSON.stringify({questions:index.length,files:files.length,exams:[...DEFAULT_EXAMS,...exams].map(e=>({id:e.id,name:e.name,count:index.filter(q=>q.examId===e.id).length})),packs},null,2));
console.log(`Private build: ${index.length} questions, ${packs.length} packs, ${files.length} assets`);
