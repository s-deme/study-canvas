import {CATEGORIES,KEY,indexQuestions,questionIndex,makeDeck,questionKey,questionCategory,isChoice,correctAnswer,allQuestions,validateQuestions,validateExam,previewImport,emptyState,dayKey,newSession,remaining,expired,sessionSummary,finish,submit,selfEvaluate,next,validateState,saveState} from './core.mjs';
import {MATERIAL_MANIFESTS} from './library-catalog.mjs';
import {MaterialLibrary} from './material.mjs';
import {esc,richText} from './render.mjs';
import {CloudSync,cloudRequest} from './sync.mjs';
import {groupExams,examSource} from './exams.mjs';
const $=selector=>document.querySelector(selector);
const button=(label,action,primary=false)=>`<button data-action="${esc(action)}" class="${primary?'primary':''}">${esc(label)}</button>`;
const link=(label,hash,primary=false)=>`<a class="button ${primary?'primary':''}" href="#${hash}">${esc(label)}</a>`;
const external=(label,url)=>`<a class="button" href="${esc(url)}" target="_blank" rel="noopener noreferrer">${esc(label)} ↗</a>`;
const card=html=>`<section class="card">${html}</section>`;
const heading=(title,subtitle)=>`<h1>${esc(title)}</h1><p class="subtitle">${esc(subtitle)}</p>`;
const questionCounts=()=>library.counts(state.custom);
const library=new MaterialLibrary([],[],undefined,MATERIAL_MANIFESTS);
const base=library.base;
let materialError='',loadingExam=null;
const filters={year:'',term:'',subject:''};
let filterExam=null;
let viewBase=null,viewCustom='',viewRows=[];
const visibleQuestions=()=>{const map=questionIndex(base),custom=JSON.stringify(state.custom);if(map!==viewBase || custom!==viewCustom) {viewRows=allQuestions(base,state);indexQuestions(viewRows);viewBase=map;viewCustom=custom;}return viewRows;};
async function loadMaterial(examId,body=false,keys=null) {
  const token=JSON.stringify([examId,body,filters,keys?[...keys]:null]);
  if(loadingExam===token) return;loadingExam=token;materialError='';
  try {
    if(body) await library.load(examId,keys?{}:{...filters},keys,({done,total})=>{if(state.selectedExam===examId && $('#material-progress')) $('#material-progress').textContent=`教材を読み込んでいます… ${done} / ${total}`;});
    else await library.loadIndex(examId);
    questions=visibleQuestions();
  }catch(error) {if(state.selectedExam===examId) materialError=error.message;}
  finally {if(loadingExam===token) loadingExam=null;render(false);}
}
function materialFilters() {
 const all=questions.filter(q=>q.examId===state.selectedExam),active=Object.values(filters).some(Boolean);
 return `<details class="filter-panel" ${active?'open':''}><summary>出題条件${active?' · '+esc(Object.values(filters).filter(Boolean).join(' / ')):''} <small>${pool().length}問</small></summary><div class="material-filters">`+[['year','年度'],['term','期'],['subject','科目']].map(([key,label])=>`<label>${label}<select data-material-filter="${key}"><option value="">すべて</option>${[...new Set(all.map(q=>q[key]).filter(Boolean))].sort().map(v=>`<option value="${esc(v)}" ${filters[key]===v?'selected':''}>${esc(v)}</option>`).join('')}</select></label>`).join('')+`<p>${pool().length}問 / 全${all.length}問</p>${active?button('年度・期・科目を解除','clear-material-filters'):''}</div></details>`;
}
let questions=[],state,serialized,searchPool,searchTitle='問題と解説',noticeTimer,sync=null,initializing=true;
let editingExam=null,editingQuestion=null,pendingImport=null,starting=false,importPage=0,imageOpener=null;
let practiceItems=null,practiceTitle='演習',practiceMode='all',managePage=0,manageNeedle='',searchNeedle='',searchPageNumber=0;
const practiceCandidates=()=>{const items=practiceItems?pool().filter(q=>practiceItems.has(questionKey(q))):pool();return items.filter(q=>practiceMode==='unseen'?stat(q).attempts===0:practiceMode==='weak'?weak(q):practiceMode==='marked'?stat(q).bookmark:true);};
function preparePractice(items,title,mode='all') {practiceItems=new Set(items.map(questionKey));practiceTitle=title;practiceMode=mode;go('practice');}
function practice() {return heading('出題条件を選ぶ',practiceTitle)+card(`<form id=practice-form><label>対象<select id=practice-mode>${[['all','すべて'],['unseen','未学習'],['weak','誤答・要復習'],['marked','ブックマーク']].map(([v,t])=>`<option value="${v}" ${practiceMode===v?'selected':''}>${t}</option>`).join('')}</select></label><label>問題数<select id=practice-count><option>10</option><option>20</option><option>50</option><option value=all>全問</option></select></label><p id=practice-count-help role=status></p><button class=primary type=submit>演習をはじめる</button></form>`);}
function practiceCount() {const n=practiceCandidates().length,count=$('#practice-count').value;$('#practice-count-help').textContent=`対象 ${n}問から ${count==='all'?n:Math.min(n,Number(count))}問を出題`;$('#practice-form button').disabled=!n;}
const exam=()=>state.exams.find(e=>e.id===state.selectedExam);
const pool=()=>questions.filter(q=>q.examId===state.selectedExam && Object.entries(filters).every(([k,v])=>!v || q[k]===v));
const stat=q=>state.stats[questionKey(q)] || {attempts:0,correct:0,bookmark:false};
const weak=q=>stat(q).attempts>0 && !stat(q).lastCorrect;
const rate=(correct,total)=>total?`${Math.round(correct*100/total)}％`:'—';
const categories=()=>[...new Set([...exam().categories,...pool().map(questionCategory)])];
const sessionDeck=()=>state.session.ids.map(id=>questionIndex(questions).get(id));
const sessionAvailable=()=>!state.session || state.session.ids.every(id=>{const q=questionIndex(questions).get(id);return q && !q.catalogOnly;});
function notice(message) {$('#notice').textContent=message;$('#notice').hidden=false;clearTimeout(noticeTimer);noticeTimer=setTimeout(()=>$('#notice').hidden=true,8000);}
function safe(action) {try {const result=action();if(result?.catch) result.catch(error=>notice(error.message));}catch(error) {notice(error.message);}}
function transact(action) {const updated=structuredClone(state);action(updated);const checked=validateState(updated,base);serialized=sync?sync.save(checked,serialized):saveState(localStorage,checked,serialized);state=checked;questions=visibleQuestions();}
function go(route) {if(location.hash==='#'+route) render();else location.hash=route;}
async function start(items,count,title) {
  if(starting) return;
  if(state.session && !state.session.ended && !confirm('途中の演習があります。新しく始めると置き換わります。学習記録は残ります。新しく始めますか？')) return;
  const examId=state.selectedExam,previous=JSON.stringify(state.session),route=location.hash,selected=makeDeck(items,count),keys=new Set(selected.map(questionKey));
  starting=true;notice('演習を準備しています…');
  try {
    await library.load(examId,{},keys,({done,total})=>notice(`演習を準備しています… ${done} / ${total}`));
    if(state.selectedExam!==examId || JSON.stringify(state.session)!==previous || location.hash!==route) throw new Error('学習対象が変更されました。もう一度開始してください');
    questions=visibleQuestions();const deck=selected.map(q=>questionIndex(questions).get(questionKey(q)));
    transact(s=>s.session=newSession(deck,deck.length,title));$('#notice').hidden=true;go('quiz');
  }catch(error) {notice(error.message);} finally {starting=false;}
}
function importPrompt(title='教材を用意してください') {
  return heading(title,`${exam().name}にはまだ問題がありません。`)+card('<p>教材／設定から問題の登録・JSON・CSVの取り込みができます。</p>'+link('教材／設定を開く','exams'))+(state.session&&!sessionAvailable()?card('<h2>以前の演習は保持しています</h2><p>同じIDの教材を取り込むと再開できます。模試の制限時間は引き継ぎます。</p>'):'');
}
function counts(items) {return items.reduce((out,q)=>{const s=stat(q);out.attempts+=s.attempts;out.graded+=s.gradedAttempts ?? s.attempts;out.correct+=s.correct;for(const k of ['done','partial','review']) out.self[k]+=s.self?.[k] || 0;return out;},{attempts:0,graded:0,correct:0,self:{done:0,partial:0,review:0}});}
const selfText=s=>`自己評価：できた ${s.done} · 一部できた ${s.partial} · 要復習 ${s.review}${s.pending?' · 未回答 '+s.pending:''}`;
function home() {
  const resume=state.session&&!state.session.ended,shortcuts='<div class="quick-links"><a href="#search">問題を検索</a><a href="#records">学習記録</a></div>';
  if(!pool().length) return (resume?card(button(`${state.exams.find(e=>e.id===state.session.examId).name}の演習を再開`,'resume',true)):'')+importPrompt()+shortcuts;
  const today=state.daily[(state.selectedExam==='gken'?'':state.selectedExam+'::')+dayKey()] || 0,wrong=pool().filter(weak).length;
  const primary=resume?button(`${state.exams.find(e=>e.id===state.session.examId).name}の演習を再開`,'resume',true):wrong?button('苦手を復習する','weak',true):button('今日の10問をはじめる','daily',true);
  return heading('今日の学習',exam().name)+card(`<div class="study-summary"><p><strong>${today}</strong> 問 <small>今日の回答</small></p><p><strong>${wrong}</strong> 問 <small>復習対象</small></p></div><div class="study-start">${primary}</div>${resume||wrong?'<div class="secondary-actions">'+button('今日の10問','daily')+'</div>':''}`)+shortcuts;
}
function subjects() {
  return heading('科目・分野から学ぶ',`${exam().name} · 上の条件で絞り込み、出題数を選んで開始できます。`)+button('この条件で演習を設定','subject',true)+`<div class="grid">`+categories().map((name,i)=>{const items=pool().filter(q=>questionCategory(q)===name),seen=items.filter(q=>stat(q).attempts>0).length;return items.length?card(`<h2>${esc(name)}</h2><p class="muted">${items.length}問 · 学習済み ${seen}問</p>${button('この分野を演習','category-'+i)}`):'';}).join('')+'</div>';
}
function review() {const wrong=pool().filter(weak),marked=pool().filter(q=>stat(q).bookmark);return heading('復習','正解または「できた」で復習対象から外れます。')+'<div class="grid">'+card(`<h2>復習対象 ${wrong.length}問</h2><p>選択式の誤答、記述・論述の「一部できた」「要復習」。</p>${wrong.length?button('まとめて復習','weak',true)+button('解説を見る','browse-weak'):'<p class="empty">復習対象はまだありません。</p>'}`)+card(`<h2>ブックマーク ${marked.length}問</h2>${marked.length?button('保存した問題を演習','marked')+button('解説を見る','browse-marked'):'<p class="empty">保存した問題はまだありません。</p>'}`)+'</div>';}
function material(q) {
  const images=q.images.map(image=>`<a href="${esc(image.src)}" target="_blank" rel="noopener noreferrer" aria-label="${esc(image.alt)}を拡大"><img class="question-image" src="${esc(image.src)}" alt="${esc(image.alt)}" loading="lazy"></a>`).join('');
  const audio=(q.audio || []).map(item=>`<p>${esc(item.label)}</p><audio controls preload="none" aria-label="${esc(item.label)}" src="${esc(item.src)}"><a href="${esc(item.src)}">音声を開く</a></audio>`).join('');
  const verified=q.textReview?.passage==='source-verified';
  const cropped=q.images.some(image=>image.src.startsWith('assets/transcription/'));
  const passage=q.passage?`<section class="passage" aria-label="共通本文">${verified?'<p class="muted">原本照合済みの文字。'+(q.images.length?'図形・数式の組版は原本画像も参照してください。':'')+'</p>':''}${richText(q.passage)}</section>`:'';
  if(cropped) return richText(q.prompt)+audio+(verified?'':'<p class="muted">文字は原本未照合です。誤読や欠落を含む場合があります。</p>')+passage+'<p class="muted">図・文字化できない部分は、画像をタップして拡大できます。</p>'+images;
  return richText(q.prompt)+audio+(q.images.length?'<p class="muted">問題の画像をタップすると、この画面で拡大して読めます。</p>'+images+(verified?passage:q.passage?`<details><summary>補助テキストを表示（原本未照合・OCRの誤読を含む場合があります。原本画像を参照）</summary>${richText(q.passage)}</details>`:''):passage);
}
function solution(q) {return `<h3>${isChoice(q)?'正解':q.evaluationGuide&&!q.modelAnswer?'出題趣旨・自己評価資料（模範解答ではありません）':q.answerKind==='answer-example'?'公式解答例・解答の要点':'模範解答'}</h3>${richText(isChoice(q)?(q.type==='multiple'?q.answer:[q.answer]).map(i=>q.options[i]).join(' ／ '):q.modelAnswer || q.evaluationGuide)}${q.modelAnswer && q.evaluationGuide?'<h3>出題趣旨・自己評価資料（解答例とは別の資料）</h3>'+richText(q.evaluationGuide):''}${(q.solutionImages || []).map(image=>`<a href="${esc(image.src)}" target="_blank" rel="noopener noreferrer"><img class="question-image" loading="lazy" src="${esc(image.src)}" alt="${esc(image.alt)}"></a>`).join('')}<p class="eyebrow">${esc(q.explanationSource)}</p>${q.explanationKind==='grading-commentary'?'<h3>採点講評</h3>':q.explanationKind==='official-explanation'?'<h3>原本の解説</h3>':''}${richText(q.explanation || (q.explanationKind==='absent-in-source'?'確認した原本には解説がありません。':'解説は登録されていません。'))}`;}
function quiz() {
  const s=state.session;if(s&&!sessionAvailable()) return importPrompt('演習に使った教材を取り込んでください。');if(!s) return heading('演習はまだありません','ホームから学習を始めましょう。')+link('ホームへ','home');if(s.ended) return results();
  const q=sessionDeck()[s.index],answer=s.answers[s.index],answered=answer!==-1,selected=answered?answer:s.pending,unrated=typeof answer==='object' && !Array.isArray(answer) && answer?.review===null;
  let controls;
  if(isChoice(q)) controls=`<fieldset aria-labelledby="question-prompt"><legend>${q.type==='multiple'?'正しい選択肢をすべて選んでください':'選択肢を一つ選んでください'}</legend>${s.orders[s.index].map(v=>`<label class="option"><input type="${q.type==='multiple'?'checkbox':'radio'}" name="answer" value="${v}" ${(Array.isArray(selected)?selected.includes(v):selected===v)?'checked':''} ${answered?'disabled':''}><span>${esc(q.options[v])}</span></label>`).join('')}</fieldset>`;
  else controls=`<label for="written-answer">あなたの回答</label><textarea id="written-answer" name="written-answer" rows="${q.type==='essay'?10:5}" maxlength="50000" ${answered?'readonly':''}>${esc(answered?(answer.text || ''):(typeof selected==='string'?selected:''))}</textarea>`;
  const feedback=answered&&!s.mock?`<div class="feedback">${isChoice(q)?`<h3 class="${correctAnswer(q,answer)?'correct':'incorrect'}">${correctAnswer(q,answer)?'正解！':'解説を確認して復習しよう'}</h3>`:''}${solution(q)}${unrated?'<h3>'+ (q.evaluationGuide&&!q.modelAnswer?'評価資料を参考に自己評価':'模範解答と比べて自己評価')+'</h3><div class="actions">'+button('できた','self-done',true)+button('一部できた','self-partial')+button('要復習','self-review')+'</div>':!isChoice(q)?`<p>自己評価：${{done:'できた',partial:'一部できた',review:'要復習'}[answer.review] || '未回答・要復習'}</p>`:''}</div>`:'';
  return `<div class="question"><div class="quiz-head"><div>${heading(s.title,`${s.index+1} / ${s.ids.length}問 · ${questionCategory(q)} ${q.subject}`)}</div>${s.mock?'<p id="timer" class="timer" role="timer"></p>':''}</div><progress max="${s.ids.length}" value="${s.index+1}" aria-label="演習の進み具合"></progress>`+card(`<details class="question-source" ${q.source.includes('未検証')?'open':''}><summary>出典${q.source.includes('未検証')?'（未検証）':''}</summary><p>${esc(q.source)}</p>${q.sourceUrl?external('出典資料',q.sourceUrl):''}</details><h2 id="question-prompt">${esc(q.topic || '問題')}</h2>${material(q)}${controls}${feedback}`)+`<div class="actions">${answered&&!s.mock?(unrated?'<p class="muted">自己評価を選ぶと次へ進めます。</p>':button(s.index+1===s.ids.length?'結果を見る':'次の問題','next',true)):button(s.mock?'回答して次へ':'回答する','answer',true)+button('この問題をスキップ','skip')}</div><div class="secondary-actions">${button(stat(q).bookmark?'保存済み · ブックマークを外す':'この問題を保存','bookmark')}${button('中断 / 終了','pause-dialog')}</div></div>`;
}
function results() {
  const s=state.session;if(s&&!sessionAvailable()) return importPrompt('結果を確認するために、教材を取り込んでください。');if(!s?.ended) return heading('終了した演習はまだありません','演習の結果はここに表示します。')+link('ホームへ','home');
  const summary=sessionSummary(s,questions),wrong=sessionDeck().filter((q,i)=>!correctAnswer(q,s.answers[i])).length;
  return heading('演習の結果',s.title)+card(`<div class="big-number">${rate(summary.correct,summary.gradedTotal)}</div><p>選択式：${summary.correct} / ${summary.gradedTotal}問正解</p><p>${selfText(summary.self)}</p><p class="muted">練習用の結果です。自己評価は正答率に含めません。</p>`)+`<div class="actions">${button('今回の問題と解説を見る','browse-result',true)}${wrong?button(`${wrong}問を復習する`,'retry'):''}${link('ホームへ','home')}</div>`;
}
function searchPage() {return heading(searchTitle,`${exam().name}の問題文・選択肢・共通本文・解答・出題趣旨・解説から検索。`)+`<label for="search-input">検索する言葉</label><input id="search-input" type="search" placeholder="調べたい用語" value="${esc(searchNeedle)}"><p id="search-count" class="muted" role="status"></p><div id="search-results"></div>`;}
function updateSearch() {
  const needle=$('#search-input').value.trim().toLocaleLowerCase('ja'),matches=(searchPool?searchPool.map(q=>questionIndex(questions).get(questionKey(q))).filter(Boolean):pool()).filter(q=>`${q.topic} ${q.prompt} ${q.passage} ${q.options.join(' ')} ${q.modelAnswer} ${q.evaluationGuide} ${q.explanation}`.toLocaleLowerCase('ja').includes(needle));
  searchPageNumber=Math.min(searchPageNumber,Math.max(0,Math.ceil(matches.length/50)-1));
  $('#search-count').textContent=`${matches.length}問が見つかりました`;
  $('#search-results').innerHTML=matches.slice(searchPageNumber*50,(searchPageNumber+1)*50).map(q=>card(`<p class="eyebrow">${esc(questionCategory(q))} · ${esc(q.subject)}</p><h2>${esc(q.topic || q.prompt.slice(0,100))}</h2><details><summary>問題・正解・解説を見る</summary>${material(q)}${solution(q)}<p>${esc(q.source)}</p></details><div class="actions"><button data-question="${esc(questionKey(q))}">この1問を解く</button></div>`)).join('')+(matches.length?`<div class=actions>${searchPageNumber?button('前の50問','search-prev'):''}<span>${searchPageNumber+1} / ${Math.ceil(matches.length/50)}ページ</span>${matches.length>(searchPageNumber+1)*50?button('次の50問','more'):''}</div>`:'') || '<p class="empty">該当する問題はありません。検索語や年度・期・科目の条件を変更してください。</p>'+(needle?button('検索語をクリア','clear-search'):'');
}
function records() {
  const items=pool(),c=counts(items),history=state.history.filter(h=>h.examId===state.selectedExam);
  return heading('学習記録',`${exam().name} · ${sync?'自分専用のクラウドに同期':'このブラウザに保存'}`)+card(`<div class="stats"><div class="stat">${c.attempts}<small>累計回答数</small></div><div class="stat">${rate(c.correct,c.graded)}<small>選択式の正答率</small></div><div class="stat">${items.length}<small>問題数</small></div></div><p>${selfText(c.self)}</p>`)+card('<h2>分野別の記録</h2>'+categories().map(name=>{const n=counts(items.filter(q=>questionCategory(q)===name));return `<div class="record-row"><strong>${esc(name)}</strong><span>${n.attempts}回答 · 選択式 ${rate(n.correct,n.graded)}<small>${selfText(n.self)}</small></span></div>`;}).join(''))+card('<h2>最近の演習（この試験の30回まで）</h2>'+(history.length?[...history].reverse().map(h=>`<div class="record-row"><span>${esc(h.title)}<small> · ${new Date(h.at).toLocaleString('ja-JP')}</small></span><span>選択式 ${h.correct} / ${h.gradedTotal ?? h.total}<small>${h.self?selfText(h.self):''}</small></span></div>`).join(''):'<p class="empty">演習を終えると結果が並びます。</p>'));
}
function official() {
  const refs={gken:[['JDLA · 試験概要','https://www.jdla.org/certificate/general/'],['JDLA · 例題・過去問','https://www.jdla.org/certificate/general/issues/']],sg:[['IPA · SG試験概要','https://www.ipa.go.jp/shiken/kubun/sg.html'],['IPA · 公開問題','https://www.ipa.go.jp/shiken/mondai-kaiotu/sg_fe/koukai/index.html']],fe:[['IPA · FE試験概要','https://www.ipa.go.jp/shiken/kubun/fe.html'],['IPA · 公開問題','https://www.ipa.go.jp/shiken/mondai-kaiotu/sg_fe/koukai/index.html']],boki3:[['日商簿記 · 試験概要','https://www.kentei.ne.jp/bookkeeping'],['日商簿記 · 公式サンプル','https://www.kentei.ne.jp/44844']]};
  return heading('教材と出典',exam().name)+library.packs.filter(p=>p.examId===state.selectedExam).map(p=>card(`<h2>${esc([p.year,p.term,p.subject].filter(Boolean).join(' ') || '復帰教材')}</h2><p>${p.count}問 · ${esc(p.verification || 'ID・件数・画像参照を検査済み')}</p><details><summary>出典・ハッシュ</summary><p style="overflow-wrap:anywhere">教材 SHA-256: ${esc(p.sha256)}</p>${(p.sources || []).map(s=>`<p style="overflow-wrap:anywhere">${external(s.file,s.url)}<br>原本 SHA-256: ${esc(s.sha256)}</p>`).join('')}</details>`)).join('')+card('<h2>自分の問題で学ぶ</h2><p>本アプリは、利用者が試験と問題を登録して学習するための仕組みです。公開版には形式確認用サンプルを用意し、本人用版には個人用教材を読み込みます。問題ごとの出典と年度を確認してください。</p><p>手持ちの教材を画面で登録するか、JSON・CSVを取り込んでください。教材の利用条件は提供元で確認できます。</p><div class="actions">'+(refs[exam().id] || []).map(([label,url])=>external(label,url)).join('')+'</div>')+link('問題を追加する','manage');
}
const inputField=(label,name,value='',required=false)=>`<label>${esc(label)}<input name="${name}" value="${esc(value)}" ${required?'required':''} maxlength="200"></label>`;
const area=(label,name,value='',required=false)=>`<label>${esc(label)}<textarea name="${name}" rows="4" ${required?'required':''} maxlength="50000">${esc(value)}</textarea></label>`;
function manage() {
  const items=pool();let preview='';
  if(pendingImport) preview=card(`<h2>取り込み前の確認</h2><p>取り込み先：${esc(state.exams.find(e=>e.id===pendingImport.examId).name)}</p>${pendingImport.error?`<p role="alert" class="incorrect">${esc(pendingImport.error)}</p><p>保存していません。ファイルを修正して再度取り込んでください。</p>`:`<p>${pendingImport.rows.length}問 · エラーなし · ${importPage+1} / ${Math.ceil(pendingImport.rows.length/50)}ページ</p>${pendingImport.rows.slice(importPage*50,(importPage+1)*50).map(q=>`<details><summary>${esc(q.id)} · ${esc(q.topic || q.prompt.slice(0,60))} · ${esc(q.type)}</summary>${material(q)}${solution(q)}</details>`).join('')}<div class=actions>${importPage?button('前の50問','import-prev'):''}${(importPage+1)*50<pendingImport.rows.length?button('次の50問','import-next'):''}</div>${button('この内容で登録する','commit-import',true)}`}<div class="actions">${button('確認を閉じる','cancel-import')}</div>`);
  return heading('試験・問題を管理',`${exam().name} · ${items.length}問`)+link('全試験の管理表','exams')+preview+card(`<h2>試験の設定</h2><p>分野：${esc(exam().field || '未設定')} · 科目：${esc(exam().subjects.join('、') || '未設定')}</p><div class="actions">${button('新しい試験を追加','new-exam',true)}${button('この試験を編集','edit-exam')}</div>`)+card('<h2>問題を追加</h2><p>JSON・CSVは2MB、持込問題は全試験合計2000問まで。追加前に内容を確認できます。</p><div class="actions">'+button('画面で問題を登録','new-question',true)+button('JSON・CSVを取り込む','import-questions')+'</div><div class="actions"><a class="button" href="sample-questions-v2.json" download>JSONの見本</a><a class="button" href="sample-questions.csv" download>CSVの見本</a></div>')+card('<h2>登録済みの問題</h2><label>問題名・ID・本文で検索<input id=manage-search type=search value="'+esc(manageNeedle)+'"></label><div id=manage-results></div>');
}
function updateManage() {
  const needle=manageNeedle.toLocaleLowerCase('ja'),items=pool().filter(q=>`${q.id} ${q.topic} ${q.prompt}`.toLocaleLowerCase('ja').includes(needle));
  managePage=Math.min(managePage,Math.max(0,Math.ceil(items.length/50)-1));
  $('#manage-results').innerHTML=`<p role=status>${items.length}問 · ${items.length?managePage+1:0} / ${Math.ceil(items.length/50)}ページ</p>`+items.slice(managePage*50,(managePage+1)*50).map(q=>`<div class="record-row"><span>${esc(q.topic || q.prompt.slice(0,80))}<small>${esc(q.id)} · ${esc(q.type)}</small></span><button data-edit-question="${esc(questionKey(q))}">編集</button></div>`).join('')+`<div class=actions>${managePage?button('前の50問','manage-prev'):''}${(managePage+1)*50<items.length?button('次の50問','manage-next'):''}</div>`+(items.length?'':'<p class=empty>一致する問題はありません。</p>');
}

function examList() {
  const n=questionCounts(),registered=state.exams.filter(e=>n[e.id]).length;
  const settings=card('<h2>教材の管理</h2><div class="actions">'+link('試験・問題を管理','manage')+button('試験を追加','new-exam')+link('教材・参考資料','official')+'</div>')+card('<h2>保存とバックアップ</h2><p id="settings-storage" role="status">'+esc(sync?$('#sync-status').textContent:'記録はこのブラウザに保存されています')+'</p><p>バックアップには試験設定・持込問題・学習記録を含みます。配布教材の本文と画像は含まず、同じ教材がある環境で記録を復元できます。</p><div class="actions">'+button('バックアップを書き出す','export')+button('バックアップを読み込む','import-backup')+'</div>');
  return heading('教材／設定',`${state.exams.length}試験・教材 · 問題登録あり ${registered} · 未登録 ${state.exams.length-registered}`)+`<details class="settings-panel"><summary>教材の管理・保存設定</summary>${settings}</details><p>試験名を選ぶと学習ホームへ進みます。登録数は配布教材と持込問題の合計です。同じIDの編集は重複計上しません。</p><div class="material-filters"><label for="exam-field-filter">カテゴリ<select id="exam-field-filter"><option value="">すべて</option>${[...groupExams(state.exams).keys()].map(field=>`<option>${esc(field)}</option>`).join('')}</select></label><label for="exam-name-filter">試験名・IDで検索<input id="exam-name-filter" type="search" placeholder="例：簿記、英検"></label></div><label>表示<select id=exam-status-filter><option value=all>すべて</option><option value=available>問題あり</option><option value=recent>最近学習した試験</option></select></label><p id="exam-list-count" role="status"></p><div id="exam-inventory"></div>`;
}
function updateExamList() {
  const field=$('#exam-field-filter').value,needle=$('#exam-name-filter').value.trim().toLocaleLowerCase('ja'),n=questionCounts();let shown=0;
  $('#exam-inventory').innerHTML=[...groupExams(state.exams)].filter(([category])=>!field || category===field).map(([category,exams])=>{
    const status=$('#exam-status-filter').value,recent=new Set([state.session?.examId,...state.history.map(h=>h.examId)]);const matches=exams.filter(e=>`${e.name} ${e.id}`.toLocaleLowerCase('ja').includes(needle) && (status==='available'?n[e.id]>0:status==='recent'?recent.has(e.id):true));shown+=matches.length;if(!matches.length) return '';
    return card(`<h2>${esc(category)} <small>${matches.length}試験・教材</small></h2><div class="table-scroll" tabindex="0" role="region" aria-label="${esc(category)}の管理表"><table><caption>${esc(category)}の登録状況</caption><thead><tr><th scope="col">試験・教材</th><th scope="col">登録数</th><th scope="col">状態</th><th scope="col">案内</th></tr></thead><tbody>${matches.map(e=>`<tr><th scope="row"><button data-select-exam="${esc(e.id)}">${esc(e.name)}</button><small class="exam-id">${esc(e.id)}</small></th><td>${n[e.id] || 0}問</td><td>${n[e.id]?'登録あり':'問題未登録'}</td><td>${examSource(e)?external('公式案内',examSource(e)):'—'}</td></tr>`).join('')}</tbody></table></div>`);
  }).join('') || '<p class="empty">該当する試験はありません。カテゴリや検索語を変更してください。</p>';
  $('#exam-list-count').textContent=`${shown} / ${state.exams.length}試験・教材を表示${shown?' · 表は横にスクロールできます':''}`;
}
function examEditor() {
  const e=editingExam || {id:'exam-'+crypto.randomUUID(),name:'',field:'',subjects:[],categories:[]};
  return heading(editingExam?'試験を編集':'試験を追加','試験名だけでも登録できます。科目と学習分野は1行に1件。')+card(`<form id="exam-form"><input name="id" type="hidden" value="${esc(e.id)}">${inputField('試験名','name',e.name,true)}${inputField('分野（例：会計、語学、法律）','field',e.field)}${area('科目（任意）','subjects',e.subjects.join('\n'))}${area('学習分野（任意）','categories',e.categories.join('\n'))}<p id="form-error" role="alert" class="incorrect"></p><div class="actions"><button type="submit" class="primary">保存する</button>${link('キャンセル','manage')}</div></form>`);
}
function questionEditor() {
  const q=editingQuestion || {id:'custom:'+crypto.randomUUID(),type:'single',category:'',subject:'',topic:'',prompt:'',passage:'',options:['選択肢1','選択肢2'],answer:0,modelAnswer:'',explanation:'',source:'持込問題',year:'',images:[]};
  return heading(editingQuestion?'問題を編集':'問題を登録',`${exam().name} · 本文は表（Markdown）・コードブロックに対応。`)+card(`<form id="question-form"><label>問題ID<input name="id" value="${esc(q.id)}" maxlength="120" required ${editingQuestion?'readonly':''}></label><label>解答形式<select name="type">${[['single','単一選択'],['multiple','複数選択'],['written','記述'],['essay','論述']].map(([v,label])=>`<option value="${v}" ${q.type===v?'selected':''}>${label}</option>`).join('')}</select></label>${inputField('科目（任意）','subject',q.subject)}${inputField('学習分野（任意）','category',typeof q.category==='number'?CATEGORIES[q.category]:q.category)}${inputField('タイトル・テーマ（任意）','topic',q.topic)}${area('問題文','prompt',q.prompt,true)}${area('共通本文（任意）','passage',q.passage)}<div id="choice-fields"><div id="editor-options">${(q.options.length?q.options:['','']).map((value,i)=>area('選択肢'+(i+1),'option',value)).join('')}</div><div class="actions"><button type="button" data-action="add-option">選択肢を追加</button><button type="button" data-action="remove-option">最後の選択肢を削除</button></div>${inputField('正解の選択肢番号（1から。複数選択は例：1,3）','correct-answer',q.answer===null?'1':(Array.isArray(q.answer)?q.answer:[q.answer]).map(i=>i+1).join(','))}</div><div id="written-fields">${area('模範解答','modelAnswer',q.modelAnswer)}${area('論述の評価資料（模範解答がない場合）','evaluationGuide',q.evaluationGuide || '')}</div>${area('解説（任意）','explanation',q.explanation)}${inputField('出典','source',q.source,true)}${inputField('年度（任意）','year',q.year)}${inputField('期（任意）','term',q.term || '')}${area('図（任意。JSON配列、例：[{"src":"https://…/図.png","alt":"図の説明"}]）','images',JSON.stringify(q.images,null,2))}<p id="form-error" role="alert" class="incorrect"></p><div class="actions"><button type="submit" class="primary">保存する</button>${link('キャンセル','manage')}</div></form>`);
}
function editorFields() {const type=$('#question-form select[name=type]')?.value;if(!type) return;const choice=['single','multiple'].includes(type);$('#choice-fields').hidden=!choice;$('#written-fields').hidden=choice;}
function render(focus=true) {
  if(!state || initializing) return;
  if(filterExam!==state.selectedExam) {Object.keys(filters).forEach(k=>filters[k]='');filterExam=state.selectedExam;materialError='';practiceItems=null;manageNeedle='';managePage=0;searchNeedle='';searchPageNumber=0;}
  if(sessionAvailable() && expired(state.session)) transact(s=>finish(s,questions));
  const route=location.hash.slice(1) || 'home';if(route==='mock') {location.replace('#home');return;}document.body.dataset.route=route;
  const studying=route==='quiz' && state.session && !state.session.ended;document.body.classList.toggle('studying',!!studying);
  $('nav').hidden=!!studying;$('.exam-bar').hidden=!!studying || route==='exams';$('footer').hidden=!!studying;
  if (['quiz','results'].includes(route) && state.session && state.selectedExam!==state.session.examId) transact(s=>s.selectedExam=s.session.examId);
  const pages={home,subjects,review,practice,quiz,results,search:searchPage,records,official,sources:official,manage,exams:examList,'exam-editor':examEditor,'question-editor':questionEditor};
  const n=questionCounts();
  $('#exam-select').innerHTML=[...groupExams(state.exams)].map(([field,exams])=>`<optgroup label="${esc(field)}">${exams.map(e=>`<option value="${esc(e.id)}" ${e.id===state.selectedExam?'selected':''}>${esc(e.name)}（${n[e.id] || 0}問）</option>`).join('')}</optgroup>`).join('');
  const keys=['quiz','results'].includes(route) && state.session?new Set(state.session.ids):route==='search' && searchPool?new Set(searchPool.map(questionKey)):null,body=['search','manage','quiz','results'].includes(route);
  if(route!=='exams' && library.has(state.selectedExam) && (!library.indexed.has(state.selectedExam) || body && !library.available(state.selectedExam,keys?{}:filters,keys))) {
    $('#main').innerHTML=heading(exam().name,materialError?'教材を読み込めませんでした':'教材を読み込んでいます…')+card(materialError?`<p role="alert">${esc(materialError)}</p>${button('再試行','retry-material',true)}`:'<p id=material-progress role=status>保存済みの学習記録は保持しています。</p>'+link('別の教材を選ぶ','exams'));
    if(!materialError) void loadMaterial(state.selectedExam,body,keys);return;
  }
  $('#main').innerHTML=!pool().length && ['subjects','review','search'].includes(route)?importPrompt():(pages[route] || home)();
  if(['home','subjects','review','search','manage','practice'].includes(route) && questions.some(q=>q.examId===state.selectedExam)) {$('#main').insertAdjacentHTML('afterbegin',materialFilters());if(!pool().length && route!=='manage') $('#main').innerHTML=materialFilters()+heading('条件に一致する問題がありません','年度・期・科目の条件を変更してください。')+(route==='home' && state.session && !state.session.ended?card(button(`${state.exams.find(e=>e.id===state.session.examId).name}の演習を再開`,'resume',true)):'')+(route==='home'?'<div class="quick-links"><a href="#search">問題を検索</a><a href="#records">学習記録</a></div>':'');}
  document.querySelectorAll('nav a').forEach(a=>{if(a.hash==='#'+(route==='practice'?'subjects':['manage','official','sources','exam-editor','question-editor'].includes(route)?'exams':route)) a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
  if(route==='search' && pool().length) {updateSearch();$('#search-input').addEventListener('input',event=>{searchNeedle=event.target.value;searchPageNumber=0;updateSearch();});}
  if(route==='exams') {updateExamList();$('#exam-field-filter').addEventListener('change',updateExamList);$('#exam-name-filter').addEventListener('input',updateExamList);$('#exam-status-filter').addEventListener('change',updateExamList);}
  if(route==='manage' && $('#manage-search')) {updateManage();$('#manage-search').addEventListener('input',event=>{manageNeedle=event.target.value;managePage=0;updateManage();});}
  if(route==='practice' && $('#practice-form')) practiceCount();
  editorFields();tick();if(focus) {$('#main').focus({preventScroll:true});window.scrollTo(0,0);}
}
function tick() {if(!state || initializing) return;
  if(filterExam!==state.selectedExam) {Object.keys(filters).forEach(k=>filters[k]='');filterExam=state.selectedExam;materialError='';practiceItems=null;manageNeedle='';managePage=0;searchNeedle='';searchPageNumber=0;}
  if(sessionAvailable() && expired(state.session)) {transact(s=>finish(s,questions));go('results');return;}if($('#timer') && state.session) {const seconds=remaining(state.session.deadline);$('#timer').textContent=`残り ${String(Math.floor(seconds/60)).padStart(2,'0')}:${String(seconds%60).padStart(2,'0')}`;}}
function browse(items,title) {searchPool=items;searchTitle=title;searchNeedle='';searchPageNumber=0;go('search');}
function download(content,name) {const url=URL.createObjectURL(new Blob([content],{type:'application/json;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
const actions={
  'clear-search':()=>{searchNeedle='';searchPageNumber=0;$('#search-input').value='';updateSearch();$('#search-input').focus();},
  'clear-material-filters':()=>{Object.keys(filters).forEach(k=>filters[k]='');searchPool=null;materialError='';managePage=0;searchPageNumber=0;render();},
  'retry-material':()=>{materialError='';render(false);},
  daily:()=>start(pool(),10,'今日の10問'),weak:()=>preparePractice(pool(),'苦手復習','weak'),marked:()=>preparePractice(pool(),'ブックマーク','marked'),
  answer:()=>{transact(s=>submit(s,questions));go(state.session.ended?'results':'quiz');},skip:()=>{transact(s=>submit(s,questions,true));go(state.session.ended?'results':'quiz');},next:()=>{transact(s=>next(s,questions));go(state.session.ended?'results':'quiz');},
  resume:()=>{transact(s=>s.selectedExam=s.session.examId);searchPool=null;go('quiz');},
  bookmark:()=>{const q=sessionDeck()[state.session.index];transact(s=>{const old=s.stats[questionKey(q)] || {attempts:0,correct:0,bookmark:false};s.stats[questionKey(q)]={...old,bookmark:!old.bookmark};});render(false);},
  'pause-dialog':()=>{const answer=state.session.answers[state.session.index],unrated=answer && typeof answer==='object' && !Array.isArray(answer) && answer.review===null;$('#finish').disabled=unrated;$('#pause-help').textContent=unrated?'この回答は自己評価が必要です。「続ける」で模範解答を確認してください。保存して中断することもできます。':'回答と選択中の内容は保存しています。'+(state.session.mock?'模試は中断中も時間が進みます。':'');$('#pause-dialog').showModal();},'browse-weak':()=>browse(pool().filter(weak),'復習対象の問題と解説'),'browse-marked':()=>browse(pool().filter(q=>stat(q).bookmark),'保存した問題と解説'),'browse-result':()=>browse(sessionDeck(),'今回の問題と解説'),
  retry:()=>{const s=state.session;preparePractice(sessionDeck().filter((q,i)=>!correctAnswer(q,s.answers[i])),'今回の復習');},more:()=>{searchPageNumber++;updateSearch();},'search-prev':()=>{searchPageNumber=Math.max(0,searchPageNumber-1);updateSearch();},'manage-next':()=>{managePage++;updateManage();},'manage-prev':()=>{managePage--;updateManage();},
  'import-questions':()=>$('#import-questions').click(),'import-backup':()=>$('#import-backup').click(),export:()=>download(JSON.stringify(state,null,2),`study-canvas-backup-${dayKey()}.json`),
  'new-exam':()=>{editingExam=null;go('exam-editor');},'edit-exam':()=>{editingExam=structuredClone(exam());go('exam-editor');},'new-question':()=>{editingQuestion=null;go('question-editor');},
  'commit-import':()=>{if(!pendingImport || pendingImport.error) throw new Error('取り込み内容を確認してください');const checked=validateQuestions(pendingImport.rows,questions);if(state.custom.length+checked.length>2000) throw new Error('持込問題は合計2000問までです');transact(s=>{s.custom.push(...checked);s.selectedExam=pendingImport.examId;});pendingImport=null;searchPool=null;go('manage');notice(`${checked.length}問を登録しました`);},
  'import-prev':()=>{importPage--;render(false);},'import-next':()=>{importPage++;render(false);},
  'cancel-import':()=>{pendingImport=null;render();},
  'add-option':()=>{const n=$('#editor-options').children.length;if(n>=26) throw new Error('選択肢は26個までです');$('#editor-options').insertAdjacentHTML('beforeend',area('選択肢'+(n+1),'option',''));},
  'remove-option':()=>{const options=$('#editor-options');if(options.children.length<=2) throw new Error('選択肢は2個以上必要です');options.lastElementChild.remove();},
  subject:()=>preparePractice(pool(),filters.subject || '科目別演習')
};
$('#main').addEventListener('click',event=>{
  const image=event.target.closest('a')?.querySelector('.question-image');if(image) {event.preventDefault();imageOpener=event.target.closest('a');imageOpener.focus({preventScroll:true});$('#image-view').src=image.src;$('#image-view').alt=image.alt;$('#image-dialog').showModal();return;}
  const target=event.target.closest('button');if(!target || !state) return;
  safe(()=>{
    if(target.dataset.selectExam) {transact(s=>s.selectedExam=target.dataset.selectExam);searchPool=null;go('home');}
    else if(target.dataset.question) {const q=questions.find(q=>questionKey(q)===target.dataset.question);start([q],1,'1問演習');}
    else if(target.dataset.editQuestion) {editingQuestion=structuredClone(questions.find(q=>questionKey(q)===target.dataset.editQuestion));if(state.session && !state.session.ended && state.session.ids.includes(questionKey(editingQuestion))) throw new Error('この問題を使う演習を終了してから編集してください');go('question-editor');}
    else if(target.dataset.action?.startsWith('category-')) {const name=categories()[Number(target.dataset.action.slice(9))];preparePractice(pool().filter(q=>questionCategory(q)===name),name);}
    else if(target.dataset.action?.startsWith('self-')) {transact(s=>selfEvaluate(s,questions,target.dataset.action.slice(5)));render(false);}
    else actions[target.dataset.action]?.();
  });
});
$('#main').addEventListener('change',event=>{
  if(event.target.dataset.materialFilter) {filters[event.target.dataset.materialFilter]=event.target.value;searchPool=null;materialError='';managePage=0;searchPageNumber=0;render(false);return;}
  if(event.target.id==='practice-mode') {practiceMode=event.target.value;practiceCount();return;}
  if(event.target.id==='practice-count') {practiceCount();return;}
  if(event.target.name==='type') {editorFields();return;}
  if(event.target.name!=='answer') return;
  safe(()=>{if(expired(state.session)) {transact(s=>finish(s,questions));go('results');return;}const q=sessionDeck()[state.session.index];transact(s=>s.session.pending=q.type==='multiple'?[...document.querySelectorAll('input[name=answer]:checked')].map(i=>Number(i.value)):Number(event.target.value));});
});
$('#main').addEventListener('input',event=>{if(event.target.name==='written-answer') safe(()=>transact(s=>s.session.pending=event.target.value));});
$('#main').addEventListener('submit',event=>{
  event.preventDefault();try {
    const f=new FormData(event.target);
    if(event.target.id==='practice-form') {const n=$('#practice-count').value;void start(practiceCandidates(),n==='all'?practiceCandidates().length:Number(n),practiceTitle);return;}
    if(event.target.matches('#exam-form')) {
      const lines=name=>f.get(name).split(/\r?\n/).map(v=>v.trim()).filter(Boolean),e=validateExam({id:f.get('id'),name:f.get('name'),field:f.get('field'),subjects:lines('subjects'),categories:lines('categories')});
      transact(s=>{const index=s.exams.findIndex(x=>x.id===e.id);if(index<0) s.exams.push(e);else s.exams[index]=e;s.selectedExam=e.id;});editingExam=null;
    }else if(event.target.matches('#question-form')) {
      const row=Object.fromEntries(f),choice=isChoice(row);row.examId=state.selectedExam;row.options=choice?f.getAll('option'):[];const numbers=row['correct-answer'].split(',').map(v=>Number(v.trim())-1);row.answer=choice?(row.type==='multiple'?numbers:numbers.length===1?numbers[0]:null):null;row.images=JSON.parse(row.images || '[]');delete row.option;delete row['correct-answer'];
      if(editingQuestion) {row.audio=editingQuestion.audio;row.solutionImages=editingQuestion.solutionImages;row.sourceUrl=editingQuestion.sourceUrl;row.explanationSource=editingQuestion.explanation===row.explanation?editingQuestion.explanationSource:'登録者による編集解説';const sameQuestion=['type','prompt','passage','options'].every(field=>JSON.stringify(row[field])===JSON.stringify(editingQuestion[field]));row.textReview=Object.fromEntries(Object.entries(editingQuestion.textReview || {}).filter(([field])=>JSON.stringify(row[field])===JSON.stringify(editingQuestion[field]) && (!['answer','modelAnswer','evaluationGuide','explanation'].includes(field) || sameQuestion)));if(sameQuestion && row.modelAnswer===editingQuestion.modelAnswer && JSON.stringify(row.answer)===JSON.stringify(editingQuestion.answer)) row.answerKind=editingQuestion.answerKind;if(row.explanation===editingQuestion.explanation) row.explanationKind=editingQuestion.explanationKind;if(editingQuestion.sourceUrl.includes('ipa.go.jp') && !row.source.includes('編集あり')) row.source+='（利用者による編集あり）';}
      const oldKey=editingQuestion?questionKey(editingQuestion):null,q=validateQuestions([row],questions.filter(q=>questionKey(q)!==oldKey),false,state.selectedExam)[0];
      transact(s=>{if(s.session?.ids.includes(questionKey(q))) {if(!s.session.ended) throw new Error('演習を終了してから編集してください');s.session=null;}const index=s.custom.findIndex(x=>questionKey(x)===questionKey(q));if(index<0) {if(s.custom.length>=2000) throw new Error('持込問題は合計2000問までです');s.custom.push(q);}else s.custom[index]=q;});editingQuestion=null;
    }else return;
    searchPool=null;go('manage');notice('保存しました');
  }catch(error) {if($('#form-error')) {$('#form-error').textContent=error.message;$('#form-error').scrollIntoView({block:'center'});}else notice(error.message);}
});
$('#exam-select').onchange=event=>safe(()=>{transact(s=>s.selectedExam=event.target.value);Object.keys(filters).forEach(k=>filters[k]='');materialError='';searchPool=null;pendingImport=null;go('home');});
document.addEventListener('click',event=>{if(event.target.closest('a')?.hash==='#search') {if(searchPool) {searchNeedle='';searchPageNumber=0;}searchPool=null;searchTitle='問題と解説';if(location.hash==='#search') render();}});
$('#image-close').onclick=()=>$('#image-dialog').close();
$('#image-zoom').onchange=event=>$('#image-view').style.width=event.target.checked?'auto':'100%';
$('#image-dialog').addEventListener('close',()=>{$('#image-view').removeAttribute('src');$('#image-view').style.width='100%';$('#image-zoom').checked=false;const opener=imageOpener?.isConnected?imageOpener:[...document.querySelectorAll('#main a')].find(a=>a.href===imageOpener?.href);opener?.focus({preventScroll:true});imageOpener=null;});
$('#keep-studying').onclick=()=>$('#pause-dialog').close();$('#pause').onclick=()=>{$('#pause-dialog').close();go('home');};$('#finish').onclick=()=>safe(()=>{transact(s=>finish(s,questions));$('#pause-dialog').close();go('results');});
async function readFile(input,max,json=true) {const file=input.files[0];input.value='';if(!file) return undefined;if(file.size>max) throw new Error(`ファイルは${max/1024/1024}MB以内にしてください`);const content=await file.text();if(!json) return {content,name:file.name};try {return JSON.parse(content);}catch {throw new Error('JSONファイルを読み込めません。形式を確認してください');}}
$('#import-questions').onchange=async event=>{
  try {const file=await readFile(event.target,2*1024*1024,false);if(!file) return;importPage=0;pendingImport={examId:state.selectedExam,rows:[]};try {pendingImport.rows=previewImport(file.name.toLowerCase().endsWith('.csv')?file.content:JSON.parse(file.content),questions,state.selectedExam);if(state.custom.length+pendingImport.rows.length>2000) throw new Error('持込問題は合計2000問までです');}catch(error) {pendingImport.error=error.message;}go('manage');}catch(error) {notice(error.message);}
};
$('#import-backup').onchange=async event=>{
  try {const input=await readFile(event.target,10*1024*1024);if(input===undefined) return;await library.prepareState(input);const checked=validateState(input,base);if(!confirm('すべての試験・記録・持込問題・途中の演習をバックアップの内容に置き換えます。必要な記録は先に書き出してください。読み込みますか？')) return;serialized=sync?sync.save(checked,serialized):saveState(localStorage,checked,serialized);state=checked;questions=visibleQuestions();searchPool=null;pendingImport=null;go('records');notice('バックアップを読み込みました');}catch(error) {notice(error.message);}
};
window.addEventListener('hashchange',()=>safe(render));
window.addEventListener('storage',async event=>{if(event.key!==KEY && event.key!==null) return;try {await library.prepareState(JSON.parse(localStorage.getItem(KEY) || 'null'));}catch(error) {notice(error.message);return;}if(sync) {safe(()=>sync.reload());void sync.refresh();return;}safe(()=>{const raw=localStorage.getItem(KEY);state=raw?validateState(JSON.parse(raw),base):emptyState();serialized=raw;questions=visibleQuestions();searchPool=null;render();notice('別のタブで更新された記録を読み込みました');});});
document.addEventListener('visibilitychange',()=>{if(!document.hidden) {safe(tick);void sync?.refresh();}});window.addEventListener('online',()=>void sync?.refresh());window.addEventListener('beforeunload',event=>{if(sync?.meta.dirty) {event.preventDefault();event.returnValue='';}});
setInterval(()=>{if(!document.hidden) void sync?.refresh();},15000);setInterval(()=>safe(tick),1000);
function showSync({kind,message}) {
  const labels={syncing:'クラウドと同期しています…',synced:'同期済み · 別の端末でも続きから学習できます',pending:'未同期 · 記録は端末に保存されています',error:'未同期 · '+message,conflict:'記録の競合 · '+(message || '自動上書きを停止しました。端末の記録を書き出してからクラウドの記録を読み込んでください')};
  $('#sync-panel').hidden=!['pending','error','conflict'].includes(kind); $('#sync-panel').dataset.kind=kind;
  $('#sync-status').textContent=labels[kind];
  if($('#settings-storage')) $('#settings-storage').textContent=labels[kind];
  $('#sync-actions').hidden=!['error','conflict'].includes(kind);
  $('#sync-remote').hidden=kind!=='conflict';
  $('#sync-retry').hidden=kind==='conflict';
}
$('#sync-retry').onclick=()=>void sync?.refresh();
$('#sync-login').onclick=()=>location.reload();
$('#sync-backup').onclick=()=>actions.export();
$('#sync-remote').onclick=async () => {
  if (!confirm('端末の記録をバックアップとして書き出し、クラウドの記録に切り替えます。端末の未同期の変更はクラウドへ送信されません。続けますか？')) return;
  try { await sync.useRemote(local=>download(JSON.stringify(local,null,2),`study-canvas-conflict-${Date.now()}.json`)); render(false); }
  catch (error) { notice(error.message); }
};
try {
  serialized=localStorage.getItem(KEY);await library.prepareState(JSON.parse(serialized || 'null')); state=serialized?validateState(JSON.parse(serialized),base):emptyState(); questions=visibleQuestions();
  if (serialized && JSON.parse(serialized).version===1) {
    const previous=JSON.parse(serialized);
    if (!localStorage.getItem(KEY+'.migration-v1')) localStorage.setItem(KEY+'.migration-v1',serialized);
    serialized=saveState(localStorage,{...state,...(previous.cloud?{cloud:{...previous.cloud,dirty:true}}:{})},serialized);
  }
  const probe='study-canvas.storage-check'; localStorage.setItem(probe,'1'); localStorage.removeItem(probe);
  let config;
  try { config=await cloudRequest('/api/config'); }
  catch (error) {
    const localHost=/^(localhost|127\.0\.0\.1|\[::1\]|10\.\d+\.\d+\.\d+|192\.168\.\d+\.\d+|172\.(1[6-9]|2\d|3[01])\.\d+\.\d+)$/.test(location.hostname);
    if (error.status!==404 || !localHost) throw error;
    if (JSON.parse(serialized || '{}').cloud) throw new Error('この記録はクラウド同期用です。同期できる配信元で開いてください');
  }
  if (config) {
    if (config.enabled!==true || typeof config.owner!=='string') throw new Error('クラウドの設定を確認できません');
    sync=new CloudSync({storage:localStorage,base,owner:config.owner,onStatus:showSync,prepare:input=>library.prepareState(input),
      // Share the existing lock with older tabs to keep cloud writes serialized.
      lock:task=>navigator.locks ? navigator.locks.request('gstudy-cloud-sync',task) : task(),
      onState:(updated,raw)=>{
        const changed=JSON.stringify(state)!==JSON.stringify(updated);
        state=updated; serialized=raw; questions=visibleQuestions();
        if (changed) { searchPool=null; queueMicrotask(()=>safe(()=>render(false))); }
      }
    });
    serialized=sync.raw;
    await sync.refresh();
  }
  initializing=false; render(false);
} catch (error) {
  initializing=false;
  state=null;
  $('#main').innerHTML=heading('記録を読み込めませんでした','保存済みの記録は保持しています。')+card(`<p>${esc(error.message)}</p><p>ローカルで使う場合は「Webアプリを起動.cmd」から開いてください。ブラウザの保存設定と空き容量も確認してください。</p><div class="actions">${button('保存データを退避','raw-backup')}${button('バックアップを読み込む','recovery')}</div>`);
  $('#main').onclick=event => safe(() => {
    const action=event.target.closest('button')?.dataset.action;
    if (action==='raw-backup') download(localStorage.getItem(KEY) || '{}','study-canvas-recovery.json');
    if (action==='recovery') $('#import-backup').click();
  });
}
