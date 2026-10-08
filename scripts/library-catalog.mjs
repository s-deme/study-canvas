import {writeFileSync,mkdirSync,readFileSync} from 'node:fs';
import {join} from 'node:path';
import {createHash} from 'node:crypto';

// Keep the complete catalog for server validation and existing inventory tools.
export function writeLibraryCatalog(web,index,packs,exams) {
  mkdirSync(join(web,'material'),{recursive:true});
  const grouped=new Map();
  for(const q of index) {if(!grouped.has(q.examId)) grouped.set(q.examId,[]);grouped.get(q.examId).push(q);}
  const manifests=[];
  const details=new Map();
  for(const pack of packs) for(const q of JSON.parse(readFileSync(join(web,pack.url),'utf8'))) details.set(`${q.examId}::${q.id}`,{category:q.category,packUrl:pack.url});
  for(const [examId,rows] of grouped) {
    const url=`material/index-${examId}.json`,text=JSON.stringify({index:rows.map(q=>({...q,...details.get(`${q.examId}::${q.id}`)})),packs:packs.filter(p=>p.examId===examId)});
    writeFileSync(join(web,url),text);
    manifests.push({examId,count:rows.length,url,sha256:createHash('sha256').update(text).digest('hex')});
  }
  writeFileSync(join(web,'library-catalog.mjs'),`export const MATERIAL_EXAMS=${JSON.stringify(exams)};\nexport const MATERIAL_MANIFESTS=${JSON.stringify(manifests)};\n`);
}
