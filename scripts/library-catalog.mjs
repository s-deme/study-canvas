import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {validateQuestions} from '../web/core.mjs';

function compactRows(rows) {
  const defaults={};
  for(const [key,value] of Object.entries(rows[0] || {})) if(key!=='id' && rows.every(row=>JSON.stringify(row[key])===JSON.stringify(value))) defaults[key]=value;
  return {defaults,rows:rows.map(row=>Object.fromEntries(Object.entries(row).filter(([key])=>!Object.hasOwn(defaults,key))))};
}

export function compactQuestionPack(rows) {
  const {defaults,rows:questions}=compactRows(rows),counts=new Map(),passages=[];
  for(const q of questions) if(q.passage) counts.set(q.passage,(counts.get(q.passage) || 0)+1);
  const shared=new Map([...counts].filter(([text,count])=>count>1 && text.length>120).map(([text],i)=>[text,'p'+i]));
  for(const [text,id] of shared) passages.push({id,text});
  for(const q of questions) if(shared.has(q.passage)) {q.passageId=shared.get(q.passage);delete q.passage;}
  const result={defaults,questions,...(passages.length?{passages}:{})};
  return JSON.stringify(result).length<JSON.stringify(rows).length?result:rows;
}

// Keep the complete catalog for server validation and existing inventory tools.
export function writeLibraryCatalog(web,index,packs,exams) {
  mkdirSync(join(web,'material'),{recursive:true});
  const grouped=new Map();
  for(const q of index) {if(!grouped.has(q.examId)) grouped.set(q.examId,[]);grouped.get(q.examId).push(q);}
  const manifests=[];
  const details=new Map();
  for(const pack of packs) for(const q of validateQuestions(JSON.parse(readFileSync(join(web,pack.url),'utf8')))) details.set(`${q.examId}::${q.id}`,{category:q.category,packUrl:pack.url});
  for(const [examId,rows] of grouped) {
    const compact=compactRows(rows.map(q=>({...q,...details.get(`${q.examId}::${q.id}`)})));
    const url=`material/index-${examId}.json`,text=JSON.stringify({defaults:compact.defaults,index:compact.rows,packs:packs.filter(p=>p.examId===examId)});
    writeFileSync(join(web,url),text);
    manifests.push({examId,count:rows.length,url,sha256:createHash('sha256').update(text).digest('hex')});
  }
  writeFileSync(join(web,'library-catalog.mjs'),`export const MATERIAL_EXAMS=${JSON.stringify(exams)};\nexport const MATERIAL_MANIFESTS=${JSON.stringify(manifests)};\n`);
}
