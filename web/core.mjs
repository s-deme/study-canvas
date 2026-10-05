import {MATERIAL_EXAMS} from './catalog.mjs';
export const CATEGORIES=['人工知能とは','人工知能をめぐる動向','機械学習の概要','ディープラーニングの概要','ディープラーニングの要素技術','ディープラーニングの応用例','AIの社会実装に向けて','数理・統計','法律と契約','倫理・AIガバナンス'];
// study-canvas keeps the old storage key and G検 IDs to preserve existing records.
export const KEY='gstudy.web.v1';
export const DEFAULT_EXAMS=[
  {id:'gken',name:'G検定',field:'IT・AI',subjects:[],categories:CATEGORIES},
  {id:'sg',name:'情報セキュリティマネジメント',field:'IT',subjects:['科目A','科目B'],categories:[]},
  {id:'fe',name:'基本情報技術者',field:'IT',subjects:['科目A','科目B'],categories:[]},
  {id:'boki3',name:'日商簿記3級',field:'会計',subjects:[],categories:['仕訳','計算','決算']}
];
const valid=(ok,message)=>{if(!ok) throw new Error(message);};
const object=v=>v!==null && typeof v==='object' && !Array.isArray(v);
const integer=(v,min,max)=>Number.isSafeInteger(v) && v>=min && v<=max;
const dangerous=v=>Object.hasOwn(Object.prototype,v) || v==='prototype';
// Retired built-in IDs preserve records without bundling their question text.
const retiredExamId=id=>typeof id==='string'?(id.match(/^(sg)::2026r08_sg-q\d{2}$|^(fe)::2026r08_fe_kamoku_[ab]-q\d{2}$|^(boki3)::boki3-original-\d{2}$/)?.slice(1).find(Boolean) || null):null;
function text(v,label,max,optional=false) {valid(typeof v==='string' && (optional || v.trim().length>0) && v.length<=max,`${label}の文章が不正です`);return v.trim();}
export const questionKey=q=>!q.examId || q.examId==='gken'?q.id:`${q.examId}::${q.id}`;
export const isChoice=q=>!q.type || ['single','multiple'].includes(q.type);
export const questionCategory=q=>typeof q.category==='number'?CATEGORIES[q.category]:q.category || '未分類';
export function validateExam(row) {
  valid(object(row) && typeof row.id==='string' && /^[a-zA-Z0-9_-]{1,80}$/.test(row.id) && !dangerous(row.id),'試験IDが不正です');
  const list=(values,label)=>{valid(Array.isArray(values) && values.length<=100,`${label}は100件以内で指定してください`);const out=values.map(v=>text(v,label,200));valid(new Set(out).size===out.length,`${label}が重複しています`);return out;};
  return {id:row.id,name:text(row.name,'試験名',200),field:text(row.field ?? '','分野',200,true),subjects:list(row.subjects ?? [],'科目'),categories:list(row.categories ?? [],'学習分野')};
}
function safeUrl(url) {valid(typeof url==='string' && /^https:\/\/[^\s<>"']+$/.test(url),'出典URLが不正です');return url;}
export function validateQuestions(input,existing=[],custom=false,examId) {
  if(object(input)) {
    valid(Array.isArray(input.questions),'questions配列が必要です');const passages=input.passages ?? [];
    valid(Array.isArray(passages) && passages.length<=2000,'共通本文の形式が不正です');const byId=new Map();
    for(const p of passages) {valid(object(p),'共通本文の形式が不正です');const id=text(p.id,'共通本文ID',120);valid(!byId.has(id),'共通本文IDが重複しています');byId.set(id,text(p.text,'共通本文',50000));}
    input=input.questions.map(q=>{valid(object(q),'問題の形式が不正です');if(!q.passageId) return q;valid(byId.has(q.passageId),`共通本文がありません：${q.passageId}`);return {...q,passage:byId.get(q.passageId)};});
  }
  valid(Array.isArray(input) && input.length>0 && input.length<=2000,'問題は1〜2000問で指定してください');const ids=new Set(existing.map(questionKey));
  return input.map((row,index)=>{
    try {
      valid(object(row),'問題の形式が不正です');const legacy=!row.type && !row.examId && (!examId || examId==='gken'),target=examId ?? row.examId ?? 'gken';
      valid(typeof target==='string' && /^[a-zA-Z0-9_-]{1,80}$/.test(target) && !dangerous(target),'試験IDが不正です');valid(!examId || !row.examId || row.examId===examId,'選択した試験と問題の試験IDが異なります');
      let id=text(row.id,'id',120);if(custom && legacy && !id.startsWith('original:') && !id.startsWith('custom:')) id='custom:'+id;
      valid(!dangerous(id) && !id.includes('::') && id.length<=120,'問題IDが不正です');const key=questionKey({id,examId:target});valid(!ids.has(key),`問題IDが重複しています：${id}`);ids.add(key);
      const type=row.type ?? 'single';valid(['single','multiple','written','essay'].includes(type),'解答形式が不正です');const category=row.category ?? '';
      valid(legacy?integer(category,0,9):typeof category==='string' && category.length<=200 || integer(category,0,9),'分野が不正です');
      let options=[],answer=null,modelAnswer='';
      if(isChoice({type})) {
        valid(Array.isArray(row.options) && row.options.length>=2 && row.options.length<=26 && (!legacy || row.options.length===4),'選択肢は2〜26個（旧形式は4個）必要です');options=row.options.map(v=>text(v,'選択肢',10000));valid(new Set(options).size===options.length,'選択肢は異なる文章にしてください');
        if(type==='single') {valid(integer(row.answer,0,options.length-1),'正解の番号が不正です');answer=row.answer;}
        else {valid(Array.isArray(row.answer) && row.answer.length>0 && row.answer.every(a=>integer(a,0,options.length-1)) && new Set(row.answer).size===row.answer.length,'正解の番号が不正です');answer=[...row.answer].sort((a,b)=>a-b);}
      }else modelAnswer=text(row.modelAnswer ?? '', '模範解答',50000,type==='essay' && !!row.evaluationGuide);
      const images=row.images ?? [];valid(Array.isArray(images) && images.length<=30,'図は30枚以内にしてください');
      const checkedImages=images.map(image=>{valid(object(image) && typeof image.src==='string' && (/^https:\/\/[^\s<>"']+$/.test(image.src) || /^assets\/[a-zA-Z0-9_./-]+\.(png|webp|jpg)$/.test(image.src) && !image.src.includes('..')),'図のURLが不正です');return {src:image.src,alt:text(image.alt,'図の説明',5000)};});
      const solutionImages=(row.solutionImages ?? []).map(image=>{valid(object(image) && typeof image.src==='string' && /^assets\/[a-zA-Z0-9_./-]+\.(png|webp|jpg)$/.test(image.src) && !image.src.includes('..'),'解答画像が不正です');return {src:image.src,alt:text(image.alt,'図の説明',1000)};});valid(solutionImages.length<=30,'解答画像が多すぎます');
      return {id,examId:target,type,term:text(row.term ?? '','期',40,true),evaluationGuide:text(row.evaluationGuide ?? '','評価資料',50000,true),solutionImages,category,subject:text(row.subject ?? '','科目',200,true),topic:text(row.topic ?? '','topic',200,true),prompt:text(row.prompt,'問題文',50000),options,answer,modelAnswer,explanation:text(row.explanation ?? '','解説',50000,true),source:text(row.source ?? '持込問題','出典',1000),year:text(String(row.year ?? ''),'年度',40,true),passage:text(row.passage ?? '','共通本文',50000,true),images:checkedImages,sourceUrl:row.sourceUrl?safeUrl(row.sourceUrl):'',explanationSource:text(row.explanationSource ?? '登録者による解説','解説の出典',200)};
    }catch(error) {throw new Error(`${index+1}問目：${error.message}`);}
  });
}
export function emptyState() {return {version:2,exams:structuredClone([...DEFAULT_EXAMS,...MATERIAL_EXAMS.filter(e=>!DEFAULT_EXAMS.some(d=>d.id===e.id))]),selectedExam:'gken',custom:[],stats:{},daily:{},history:[],session:null};}
export function allQuestions(base,state) {return [...new Map([...base,...state.custom].map(q=>[questionKey(q),q])).values()];}
export function dayKey(now=new Date()) {return `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`;}
export function shuffle(items,random=Math.random) {const out=[...items];for(let i=out.length-1;i>0;i--) {const j=Math.floor(random()*(i+1));[out[i],out[j]]=[out[j],out[i]];}return out;}
export function makeDeck(pool,count,mock=false,random=Math.random) {
  const shuffled=shuffle(pool,random),limit=Math.min(Math.max(count,0),pool.length);if(!mock) return shuffled.slice(0,limit);
  const categories=[...new Set(pool.map(questionCategory))],groups=categories.map(c=>shuffled.filter(q=>questionCategory(q)===c)),out=[];
  for(let round=0;out.length<limit;round++) for(const group of groups) if(round<group.length && out.length<limit) out.push(group[round]);return shuffle(out,random);
}
export function newSession(pool,count,title,mock=false,minutes=0,now=Date.now()) {
  const deck=makeDeck(pool,count,mock);valid(deck.length>0,'対象の問題がありません');const examId=deck[0].examId ?? 'gken';valid(deck.every(q=>(q.examId ?? 'gken')===examId),'異なる試験の問題を混ぜることはできません');valid(!mock || deck.every(isChoice),'記述・論述は通常の演習で自己評価してください');
  return {examId,ids:deck.map(questionKey),answers:deck.map(()=>-1),orders:deck.map(q=>shuffle(q.options.map((_,i)=>i))),index:0,pending:-1,title,mock,deadline:minutes?now+minutes*60000:0,ended:false};
}
export function remaining(deadline,now=Date.now()) {return Math.max(0,Math.ceil((deadline-now)/1000));}
export function expired(session,now=Date.now()) {return !!session && !session.ended && session.deadline>0 && remaining(session.deadline,now)===0;}
export function correctAnswer(q,answer) {if(!isChoice(q)) return object(answer) && answer.review==='done';if(q.type==='multiple') return Array.isArray(answer) && answer.length===q.answer.length && [...answer].sort((a,b)=>a-b).every((a,i)=>a===q.answer[i]);return answer===q.answer;}
export function record(state,q,answer,now) {
  const key=questionKey(q),old=state.stats[key] || {attempts:0,correct:0,bookmark:false},correct=correctAnswer(q,answer),choice=isChoice(q),self={done:0,partial:0,review:0,...old.self};if(!choice) self[object(answer) && answer.review || 'review']++;
  state.stats[key]={...old,attempts:old.attempts+1,correct:old.correct+(choice && correct?1:0),gradedAttempts:(old.gradedAttempts ?? old.attempts)+(choice?1:0),self,lastCorrect:correct,lastAt:now};
  const day=dayKey(new Date(now)),dailyKey=q.examId && q.examId!=='gken'?`${q.examId}::${day}`:day;state.daily[dailyKey]=(state.daily[dailyKey] || 0)+1;
}
export function score(session,questions) {const map=new Map(questions.map(q=>[questionKey(q),q]));return session.ids.reduce((n,id,i)=>n+(map.has(id) && isChoice(map.get(id)) && correctAnswer(map.get(id),session.answers[i])?1:0),0);}
export function sessionSummary(session,questions) {
  const map=new Map(questions.map(q=>[questionKey(q),q])),self={done:0,partial:0,review:0,pending:0};let gradedTotal=0;
  session.ids.forEach((id,i)=>{if(isChoice(map.get(id))) gradedTotal++;else {const a=session.answers[i];self[object(a)?a.review || 'pending':a===-1?'pending':'review']++;}});return {correct:score(session,questions),gradedTotal,self};
}
export function finish(state,questions,now=Date.now()) {
  const s=state.session;if(!s || s.ended) return;const map=new Map(questions.map(q=>[questionKey(q),q]));
  valid(s.answers.every(a=>!object(a) || a.review!==null),'記述・論述の自己評価を選んでから終了してください');
  if(s.mock) s.ids.forEach((id,i)=>record(state,map.get(id),s.answers[i],now));
  s.ended=true;s.pending=-1;state.history.push({examId:s.examId ?? 'gken',title:s.title,...sessionSummary(s,questions),total:s.ids.length,at:now});const counts={};state.history=state.history.slice().reverse().filter(h=>{const id=h.examId ?? 'gken';counts[id]=(counts[id] || 0)+1;return counts[id]<=30;}).reverse();
}
export function submit(state,questions,skip=false,now=Date.now()) {
  const s=state.session;valid(s && !s.ended,'進行中の演習がありません');if(expired(s,now)) {finish(state,questions,now);return;}if(s.answers[s.index]!==-1) return;
  const q=questions.find(q=>questionKey(q)===s.ids[s.index]);valid(q,'問題が見つかりません');let answer=skip?-2:s.pending;
  if(!skip) {if(isChoice(q)) valid(q.type==='multiple'?Array.isArray(answer) && answer.length>0 && answer.every(a=>integer(a,0,q.options.length-1)) && new Set(answer).size===answer.length:integer(answer,0,q.options.length-1),'選択肢を選んでください');else answer={text:text(answer,'回答',50000),review:null};}
  s.answers[s.index]=answer;s.pending=-1;if(!s.mock && (isChoice(q) || skip)) record(state,q,answer,now);else if(s.mock) next(state,questions,now);
}
export function selfEvaluate(state,questions,review,now=Date.now()) {
  const s=state.session;valid(s && !s.ended && ['done','partial','review'].includes(review),'自己評価が不正です');const q=questions.find(q=>questionKey(q)===s.ids[s.index]),answer=s.answers[s.index];valid(q && !isChoice(q) && object(answer) && answer.review===null,'自己評価できる回答がありません');answer.review=review;record(state,q,answer,now);
}
export function next(state,questions,now=Date.now()) {
  const s=state.session;valid(s && !s.ended && s.answers[s.index]!==-1,'先に回答してください');valid(!object(s.answers[s.index]) || s.answers[s.index].review!==null,'模範解答を確認して自己評価してください');if(expired(s,now) || s.index+1===s.ids.length) finish(state,questions,now);else {s.index++;s.pending=-1;}
}
export function validateState(input,base=[]) {
  valid(object(input) && [1,2].includes(input.version) && Array.isArray(input.custom) && input.custom.length<=2000,'Web版バックアップの形式が不正です');const legacy=input.version===1;
  const exams=legacy?structuredClone(DEFAULT_EXAMS):(valid(Array.isArray(input.exams) && input.exams.length>0 && input.exams.length<=100,'試験一覧が不正です'),input.exams.map(validateExam));const examIds=new Set(exams.map(e=>e.id));valid(examIds.size===exams.length && DEFAULT_EXAMS.every(e=>examIds.has(e.id)),'試験IDが重複または初期試験が不足しています');
  for(const e of MATERIAL_EXAMS) if(!examIds.has(e.id)) {exams.push(validateExam(e));examIds.add(e.id);}
  const selectedExam=legacy?'gken':input.selectedExam;valid(examIds.has(selectedExam),'選択した試験がありません');const custom=input.custom.length?validateQuestions(input.custom):[];valid(custom.every(q=>examIds.has(q.examId)),'問題の試験がありません');
  const questions=allQuestions(base,{custom}),map=new Map(questions.map(q=>[questionKey(q),q]));const knownId=id=>typeof id==='string' && !dangerous(id) && (map.has(id) || examIds.has(retiredExamId(id)) || id.startsWith('original:') && id.length>9 && id.length<=120);
  valid(object(input.stats) && object(input.daily) && Array.isArray(input.history) && input.history.length<=3000,'学習記録の形式が不正です');
  for(const [id,s] of Object.entries(input.stats)) {
    valid(knownId(id) && object(s) && integer(s.attempts,0,1e9) && integer(s.correct,0,s.attempts) && typeof s.bookmark==='boolean','回答記録が不正です');valid(s.attempts===0 || typeof s.lastCorrect==='boolean' && integer(s.lastAt,0,Number.MAX_SAFE_INTEGER),'回答日時が不正です');valid(s.gradedAttempts===undefined || integer(s.gradedAttempts,s.correct,s.attempts),'自動採点の記録が不正です');
    if(s.self!==undefined) valid(object(s.self) && ['done','partial','review'].every(k=>integer(s.self[k],0,s.attempts)) && Object.values(s.self).reduce((a,b)=>a+b,0)===s.attempts-(s.gradedAttempts ?? s.attempts),'自己評価の記録が不正です');
  }
  for(const [key,n] of Object.entries(input.daily)) {const parts=key.split('::');valid(parts.length<=2 && (parts.length===1 || examIds.has(parts[0])) && /^\d{4}-\d{2}-\d{2}$/.test(parts.at(-1)) && integer(n,0,1e9),'日別記録が不正です');}
  const history=input.history.map(h=>{
    valid(object(h),'履歴が不正です');text(h.title,'演習名',200);valid(integer(h.total,1,Math.max(2240,questions.length)) && integer(h.correct,0,h.total) && integer(h.at,0,Number.MAX_SAFE_INTEGER) && examIds.has(h.examId ?? 'gken'),'履歴が不正です');
    if(h.gradedTotal!==undefined) valid(integer(h.gradedTotal,h.correct,h.total) && object(h.self) && ['done','partial','review','pending'].every(k=>integer(h.self[k],0,h.total)) && Object.values(h.self).reduce((a,b)=>a+b,0)===h.total-h.gradedTotal,'履歴の自己評価が不正です');return {...h,examId:h.examId ?? 'gken'};
  });
  let s=input.session;
  if(s!==null) {
    valid(object(s) && Array.isArray(s.ids) && s.ids.length>0 && s.ids.length<=Math.max(2240,questions.length) && s.ids.every(knownId) && new Set(s.ids).size===s.ids.length,'演習の問題が不正です');s={...s,examId:s.examId ?? 'gken'};valid(examIds.has(s.examId) && s.ids.every(id=>map.has(id)?(map.get(id).examId ?? 'gken')===s.examId:s.examId===(retiredExamId(id) || 'gken')),'演習の試験が不正です');
    const answerValid=(a,q,pending=false,retired=false)=>{
      if(a===-1 || a===-2 && !pending) return true;if(!q && !retired) return integer(a,0,3);if(!q) {
        if(integer(a,0,25)) return true;
        if(Array.isArray(a)) return a.length<=26 && a.every(v=>integer(v,0,25)) && new Set(a).size===a.length;
        return pending?typeof a==='string' && a.length<=50000:object(a) && typeof a.text==='string' && a.text.trim().length>0 && a.text.length<=50000 && [null,'done','partial','review'].includes(a.review);
      }if(isChoice(q)) return q.type==='multiple'?Array.isArray(a) && a.every(v=>integer(v,0,q.options.length-1)) && new Set(a).size===a.length:integer(a,0,q.options.length-1);
      return pending?typeof a==='string' && a.length<=50000:object(a) && typeof a.text==='string' && a.text.trim().length>0 && a.text.length<=50000 && [null,'done','partial','review'].includes(a.review);
    };
    valid(Array.isArray(s.answers) && s.answers.length===s.ids.length && s.answers.every((a,i)=>answerValid(a,map.get(s.ids[i]),false,!!retiredExamId(s.ids[i]))),'演習の回答が不正です');valid(Array.isArray(s.orders) && s.orders.length===s.ids.length && s.orders.every((order,i)=>{const n=map.get(s.ids[i])?.options.length ?? (retiredExamId(s.ids[i])?order?.length:4);return Array.isArray(order) && integer(n,0,26) && order.length===n && order.every(v=>integer(v,0,n-1)) && new Set(order).size===n;}),'選択肢の順序が不正です');
    valid(integer(s.index,0,s.ids.length-1) && answerValid(s.pending,map.get(s.ids[s.index]),true,!!retiredExamId(s.ids[s.index])) && typeof s.mock==='boolean' && typeof s.ended==='boolean' && integer(s.deadline,0,Number.MAX_SAFE_INTEGER) && (s.mock?s.deadline>0:s.deadline===0),'演習の位置・制限時間が不正です');text(s.title,'演習名',200);
    valid(s.answers.slice(0,s.index).every(a=>a!==-1 && (!object(a) || a.review!==null)) && s.answers.slice(s.index+1).every(a=>a===-1),'演習の回答順序が不正です');valid(!s.mock || s.ended || s.answers[s.index]===-1,'模試の位置が不正です');valid(!s.mock || s.ids.every(id=>!map.has(id) || isChoice(map.get(id))),'模試の解答形式が不正です');valid(!s.ended || s.pending===-1,'終了した演習の選択が不正です');
  }
  return {version:2,exams,selectedExam,custom,stats:input.stats,daily:input.daily,history,session:s};
}
export function saveState(storage,nextState,expected) {valid(storage.getItem(KEY)===expected,'別のタブで記録が更新されました。ページを再読み込みしてください');const serialized=JSON.stringify(nextState);try {storage.setItem(KEY,serialized);}catch {throw new Error('記録を保存できません。ブラウザの保存設定や空き容量を確認してください。変更は確定していません');}return serialized;}
export function parseCSV(source) {
  valid(typeof source==='string','CSVの形式が不正です');const rows=[];let row=[],cell='',quoted=false,closed=false;source=source.replace(/^\uFEFF/,'');
  for(let i=0;i<source.length;i++) {const c=source[i];if(quoted) {if(c==='"') {if(source[i+1]==='"') {cell+='"';i++;}else {quoted=false;closed=true;}}else cell+=c;}
    else if(c===',' || c==='\n' || c==='\r') {row.push(cell);cell='';closed=false;if(c!==',') {if(c==='\r' && source[i+1]==='\n') i++;if(row.some(v=>v!=='')) rows.push(row);row=[];}}
    else if(c==='"' && cell==='' && !closed) quoted=true;else {valid(!closed && c!=='"','CSVの引用符が不正です');cell+=c;}}
  valid(!quoted,'CSVの引用符が閉じられていません');row.push(cell);if(row.some(v=>v!=='')) rows.push(row);valid(rows.length>1,'CSVには見出しと問題が必要です');const headers=rows.shift();valid(new Set(headers).size===headers.length && headers.includes('id') && headers.includes('prompt'),'CSVの見出しが不正です');
  return rows.map((values,i)=>{valid(values.length===headers.length,`CSV ${i+2}行目の列数が異なります`);const q=Object.fromEntries(headers.map((h,j)=>[h,values[j]]));for(const name of ['options','answer','images','solutionImages']) if(q[name]) {try {q[name]=JSON.parse(q[name]);}catch {throw new Error(`CSV ${i+2}行目の${name}はJSON形式で指定してください`);}}if(q.answer==='') delete q.answer;if(q.images==='') delete q.images;if(q.solutionImages==='') delete q.solutionImages;return q;});
}
export function previewImport(input,existing,examId) {return validateQuestions(typeof input==='string'?parseCSV(input):input,existing,true,examId);}
