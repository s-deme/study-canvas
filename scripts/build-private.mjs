import {writeLibraryCatalog} from './library-catalog.mjs';
import assert from 'node:assert/strict';
import {closeSync,cpSync,existsSync,mkdirSync,openSync,readFileSync,readdirSync,unlinkSync,writeFileSync,statSync} from 'node:fs';
import {resolve,join} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {validateQuestions,questionKey,DEFAULT_EXAMS} from '../web/core.mjs';
import {loadAdditionalMaterial} from './additional-material.mjs';
import {loadGithubMaterial} from './github-material.mjs';
import {loadGithubCandidates} from './github-candidates.mjs';
import {loadMedicalMaterial} from './medical-material.mjs';
import {loadLocalPractice} from './local-practice.mjs';
import {loadSchoolMaterial} from './school-material.mjs';
import {recoverPrivateBuild,updatePrivateBuild} from './private-build-update.mjs';

const root=fileURLToPath(new URL('../',import.meta.url)),out=resolve(root,'build/private');
assert.equal(out,join(resolve(root),'build','private'));
// ponytail: one shared output; use separate output directories if concurrent builds are needed.
mkdirSync(join(root,'build'),{recursive:true});
const lock=join(root,'build','private-build.lock'),lockFd=openSync(lock,'wx');
process.on('exit',()=>{closeSync(lockFd);unlinkSync(lock);});
for(const signal of ['SIGINT','SIGTERM']) process.on(signal,()=>process.exit(1));
recoverPrivateBuild(out);
const read=path=>JSON.parse(readFileSync(path,'utf8'));
const material=join(root,'private-data/material'), packsFile=join(material,'packs.json');
assert.ok(existsSync(packsFile),'Run fetch-material.py, ocr-material.py and prepare-material.py first');
assert.deepEqual(read(join(material,'errors.json')),[],'Unresolved material extraction errors; do not deploy');
const original=read(join(root,'private-data/questions.json'));
const restored=read(join(root,'private-data/retired-material/questions-v2.json'));
const existingPacks=read(packsFile).map(p=>({...p,rows:read(join(material,p.file))}));
const additions=loadAdditionalMaterial(root,[...original,...restored,...existingPacks.flatMap(p=>p.rows)]);
const github=loadGithubMaterial(root,[...original,...restored,...existingPacks.flatMap(p=>p.rows),...additions.packs.flatMap(p=>p.rows)]);
const safety=loadGithubMaterial(root,[...original,...restored,...existingPacks.flatMap(p=>p.rows),...additions.packs.flatMap(p=>p.rows),...github.packs.flatMap(p=>p.rows)],'safety-report.json','safety-verification.json');
github.exams.push(...safety.exams);github.packs.push(...safety.packs);
const history=loadGithubMaterial(root,[...original,...restored,...existingPacks.flatMap(p=>p.rows),...additions.packs.flatMap(p=>p.rows),...github.packs.flatMap(p=>p.rows)],'history-report.json','history-verification.json');
github.exams.push(...history.exams);github.packs.push(...history.packs);
const math=loadGithubMaterial(root,[...original,...restored,...existingPacks.flatMap(p=>p.rows),...additions.packs.flatMap(p=>p.rows),...github.packs.flatMap(p=>p.rows)],'math-report.json','math-verification.json');
github.exams.push(...math.exams);github.packs.push(...math.packs);
const medicalOfficial=loadGithubMaterial(root,[...original,...restored,...existingPacks.flatMap(p=>p.rows),...additions.packs.flatMap(p=>p.rows),...github.packs.flatMap(p=>p.rows)],'medical-verified-report.json','medical-verification.json');
github.exams.push(...medicalOfficial.exams);github.packs.push(...medicalOfficial.packs);
const finance=loadGithubMaterial(root,[...original,...restored,...existingPacks.flatMap(p=>p.rows),...additions.packs.flatMap(p=>p.rows),...github.packs.flatMap(p=>p.rows)],'finance-report.json','finance-verification.json');
github.exams.push(...finance.exams);github.packs.push(...finance.packs);
const kanken=loadGithubMaterial(root,[...original,...restored,...existingPacks.flatMap(p=>p.rows),...additions.packs.flatMap(p=>p.rows),...github.packs.flatMap(p=>p.rows)],'kanken-report.json','kanken-verification.json');
github.packs.push(...kanken.packs);github.exams.push(...kanken.exams);
const construction=loadGithubMaterial(root,[...original,...restored,...existingPacks.flatMap(p=>p.rows),...additions.packs.flatMap(p=>p.rows),...github.packs.flatMap(p=>p.rows)],'construction-report.json','construction-verification.json');
github.exams.push(...construction.exams);github.packs.push(...construction.packs);
const electricity=loadGithubMaterial(root,[...original,...restored,...existingPacks.flatMap(p=>p.rows),...additions.packs.flatMap(p=>p.rows),...github.packs.flatMap(p=>p.rows)],'electricity-report.json','electricity-verification.json');
github.exams.push(...electricity.exams);github.packs.push(...electricity.packs);
if(process.argv.includes('--cloud')) assert.ok(!github.packs.some(p=>p.localOnly),'個人利用限定の教材があります。クラウド配備には提供元の利用許諾を確認してください。');
const candidates=loadGithubCandidates(root,[...original,...restored,...existingPacks.flatMap(p=>p.rows),...additions.packs.flatMap(p=>p.rows),...github.packs.flatMap(p=>p.rows)]);
if(process.argv.includes('--cloud')) assert.ok(!candidates.packs.some(p=>p.localOnly),'ローカル学習限定のGitHub教材があります。');
const business=loadGithubMaterial(root,[...original,...restored,...existingPacks.flatMap(p=>p.rows),...additions.packs.flatMap(p=>p.rows),...github.packs.flatMap(p=>p.rows),...candidates.packs.flatMap(p=>p.rows)],'business-report.json','business-verification.json');
github.exams.push(...business.exams);github.packs.push(...business.packs);
if(process.argv.includes('--cloud')) assert.ok(!business.packs.some(p=>p.localOnly),'経営・事務・販売の個人学習用教材はローカル利用限定です。');
for(const kind of ['welfare','public-examples','hazmat','fire','denken']) {
const welfare=loadGithubMaterial(root,[...original,...restored,...existingPacks.flatMap(p=>p.rows),...additions.packs.flatMap(p=>p.rows),...github.packs.flatMap(p=>p.rows),...candidates.packs.flatMap(p=>p.rows)],kind+'-report.json',kind+'-verification.json');
github.exams.push(...welfare.exams);github.packs.push(...welfare.packs);
if(process.argv.includes('--cloud')) assert.ok(!welfare.packs.some(p=>p.localOnly),'追加の個人学習用教材はローカル利用限定です。');
}
const medical=loadMedicalMaterial(root,[...original,...restored,...existingPacks.flatMap(p=>p.rows),...additions.packs.flatMap(p=>p.rows),...github.packs.flatMap(p=>p.rows),...candidates.packs.flatMap(p=>p.rows)]);
github.exams.push(...medical.exams);github.packs.push(...medical.packs);
if(process.argv.includes('--cloud')) assert.ok(!medical.packs.some(p=>p.localOnly),'JMed48kは非商用利用限定です。クラウド配備には提供元の利用許諾を確認してください。');
const practice=loadLocalPractice(root,[...original,...restored,...existingPacks.flatMap(p=>p.rows),...additions.packs.flatMap(p=>p.rows),...github.packs.flatMap(p=>p.rows),...candidates.packs.flatMap(p=>p.rows)]);
github.exams.push(...practice.exams);github.packs.push(...practice.packs);
const school=loadSchoolMaterial(root,[...original,...restored,...existingPacks.flatMap(p=>p.rows),...additions.packs.flatMap(p=>p.rows),...github.packs.flatMap(p=>p.rows),...candidates.packs.flatMap(p=>p.rows)]);
if(process.argv.includes('--cloud')) assert.ok(!school.packs.some(p=>p.localOnly),'一般教材はローカル本人用教材として登録しています。');
github.exams.push(...school.exams);github.packs.push(...school.packs);
console.log(`Original practice: ${practice.packs.reduce((n,p)=>n+p.count,0)} questions; ${practice.duplicates.length} text/numeric duplicates excluded`);
console.log(updatePrivateBuild(out,stage=>{
const out=stage;
// Generate separately; replace the successful output only after all checks pass.
mkdirSync(join(out,'web/material'),{recursive:true});
cpSync(join(root,'web'),join(out,'web'),{recursive:true});
cpSync(join(root,'functions'),join(out,'functions'),{recursive:true});
cpSync(join(root,'schema.sql'),join(out,'schema.sql'));
mkdirSync(join(out,'web/assets/material'),{recursive:true});
cpSync(join(root,'private-data/retired-material/assets'),join(out,'web/assets'),{recursive:true});
const names={ap:'応用情報技術者',st:'ITストラテジスト',sa:'システムアーキテクト',pm:'プロジェクトマネージャ',nw:'ネットワークスペシャリスト',db:'データベーススペシャリスト',es:'エンベデッドシステムスペシャリスト',sm:'ITサービスマネージャ',au:'システム監査技術者',sc:'情報処理安全確保支援士'};
const exams=Object.entries(names).map(([id,name])=>({id,name,field:'IT',subjects:[],categories:[]}));
for(const exam of [...additions.exams,...github.exams,...candidates.exams]) {
 const prior=[...DEFAULT_EXAMS,...exams].find(e=>e.id===exam.id);
 if(prior) assert.deepEqual(exam,prior,'Conflicting added exam '+exam.id);
 else exams.push(exam);
}
const packs=[],index=[],keys=new Set(),copiedAssets=new Set();
function add(id,rows,metadata={}) {
  const checked=validateQuestions(rows);
  for(const q of checked) {
    assert.ok(!keys.has(questionKey(q)),`Duplicate ${questionKey(q)}`);keys.add(questionKey(q));
    for(const image of [...q.images,...q.solutionImages,...(q.audio || [])]) if(image.src.startsWith('assets/')) {
      if(copiedAssets.has(image.src)) continue;
      if(image.src.startsWith('assets/material/')) cpSync(join(material,'assets',image.src.slice('assets/material/'.length)),join(out,'web',image.src));
      if(image.src.startsWith('assets/additions/')) {mkdirSync(join(out,'web/assets/additions'),{recursive:true});cpSync(join(root,'private-data/additions/assets',image.src.slice('assets/additions/'.length)),join(out,'web',image.src));}
      if(image.src.startsWith('assets/github-material/') && !existsSync(join(out,'web',image.src))) {mkdirSync(join(out,'web/assets/github-material'),{recursive:true});cpSync(join(root,'private-data/github-material/prepared/assets',image.src.slice('assets/github-material/'.length)),join(out,'web',image.src));}
      if(image.src.startsWith('assets/github-candidates/') && !existsSync(join(out,'web',image.src))) {mkdirSync(join(out,'web/assets/github-candidates'),{recursive:true});cpSync(join(root,'private-data/github-candidates/prepared/assets',image.src.slice('assets/github-candidates/'.length)),join(out,'web',image.src));}
      assert.ok(existsSync(join(out,'web',image.src)),image.src);
      copiedAssets.add(image.src);
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
for(const {rows,...pack} of github.packs) add(pack.id,rows,pack);
for(const {rows,...pack} of candidates.packs) add(pack.id,rows,pack);
for(const exam of exams) assert.ok(index.some(q=>q.examId===exam.id),exam.id);
writeFileSync(join(out,'web/catalog.mjs'),`// Generated private index. Question bodies are loaded separately.\nexport const BUILTIN_QUESTIONS=[];\nexport const MATERIAL_INDEX=${JSON.stringify(index)};\nexport const MATERIAL_PACKS=${JSON.stringify(packs)};\nexport const MATERIAL_EXAMS=${JSON.stringify(exams)};\n`);
writeLibraryCatalog(join(out,'web'),index,packs,exams);
cpSync(join(material,'audit.json'),join(out,'web/material/audit.json'));
if(existsSync(join(material,'verification.json'))) cpSync(join(material,'verification.json'),join(out,'web/material/verification.json'));
writeFileSync(join(out,'web/material/expansion-report.json'),JSON.stringify(additions.report,null,2));
const files=[];
function walk(dir) {for(const name of readdirSync(dir)){const p=join(dir,name);if(statSync(p).isDirectory()) walk(p);else {if(process.argv.includes('--cloud')) assert.ok(statSync(p).size<25*1024*1024,`Pages asset too large: ${p}`);files.push(p);}}}
walk(join(out,'web'));if(process.argv.includes('--cloud')) assert.ok(files.length<=20000,'Pages file limit exceeded; the full collection is available locally');
writeFileSync(join(out,'manifest.json'),JSON.stringify({questions:index.length,files:files.length,exams:[...DEFAULT_EXAMS,...exams].map(e=>({id:e.id,name:e.name,count:index.filter(q=>q.examId===e.id).length})),packs},null,2));
return `Private build: ${index.length} questions, ${packs.length} packs, ${files.length} assets`;
},false));
