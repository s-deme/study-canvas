// Reuse the existing loopback/auth fixture and isolated Chrome approach with corrected real material.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {join,resolve,sep} from 'node:path';
import {pathToFileURL} from 'node:url';
import {servePreview} from './cloud-preview.mjs';
import {validateQuestions} from '../web/core.mjs';
const read=file=>JSON.parse(readFileSync(file));
const directory=process.argv[2] || read('build/material-transcription/current.json').directory,root=pathToFileURL(resolve(directory)+sep);
const manifest=read(join(directory,'manifest.json'));
const samples=[['prose','fe::2023r05_fe_kamoku_a-q003','独立して動作'],['table','fe::2023r05_fe_kamoku_a-q002','新たな社員G'],
  ['formula','ap::2023r05a_ap_am-q01','x₁x₂'],['code','fe::2023r05_fe_kamoku_b-q001','findPrimeNumbers'],
  ['scan','nw::2009h21a_nw_am2-q001','0.02'],['multi-page','st::2023r05h_st_pm1-q01-s4','ウォレット機能'],
  ['unreviewed','fe::2023r05_fe_kamoku_a-q013','2023年度 公開問題 基本情報技術者 科目A 問13']];
const selected=new Map();
for(const pack of manifest.packs.filter(p=>['fe','ap','nw','st'].includes(p.examId))) for(const q of validateQuestions(read(join(directory,'web',pack.url)))) {
  const key=q.examId+'::'+q.id;if(samples.some(s=>s[1]===key)) selected.set(key,q);
}
const {onRequestGet,onRequestPut}=await import(new URL('functions/api/state.js',root));
const preview=await servePreview(8771,{webRoot:new URL('web/',root),getState:onRequestGet,putState:onRequestPut});
const browser=await(await fetch('http://127.0.0.1:9238/json/version')).json();
const ws=new WebSocket(browser.webSocketDebuggerUrl);await new Promise((ok,fail)=>{ws.onopen=ok;ws.onerror=fail;});
let id=0,context;const pending=new Map(),errors=[];
ws.onmessage=e=>{const r=JSON.parse(e.data),p=pending.get(r.id);if(p){pending.delete(r.id);r.error?p.reject(new Error(r.error.message)):p.resolve(r.result);}if(r.method==='Runtime.exceptionThrown') errors.push(r.params.exceptionDetails);};
const send=(method,params={},sessionId)=>new Promise((resolve,reject)=>{const key=++id;pending.set(key,{resolve,reject});ws.send(JSON.stringify({id:key,method,params,...(sessionId?{sessionId}:{})}));});
async function evaluate(s,expression) {const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
async function until(s,expression) {const end=Date.now()+60000;while(Date.now()<end){if(await evaluate(s,expression)) return;await new Promise(ok=>setTimeout(ok,100));}throw new Error('Timed out: '+expression);}
const click=(s,selector)=>evaluate(s,`document.querySelector(${JSON.stringify(selector)}).click()`);
const field=(s,selector,value,event='change')=>evaluate(s,`(()=>{const el=document.querySelector(${JSON.stringify(selector)});el.value=${JSON.stringify(value)};el.dispatchEvent(new Event(${JSON.stringify(event)},{bubbles:true}));})()`);
mkdirSync('tmp/transcription/screenshots',{recursive:true});
try {
  context=(await send('Target.createBrowserContext')).browserContextId;
  const t=await send('Target.createTarget',{url:'about:blank',browserContextId:context});
  const {sessionId:s}=await send('Target.attachToTarget',{targetId:t.targetId,flatten:true});
  await send('Page.enable',{},s);await send('Runtime.enable',{},s);
  await send('Emulation.setDeviceMetricsOverride',{width:1100,height:1000,deviceScaleFactor:1,mobile:false},s);
  await send('Page.navigate',{url:'http://127.0.0.1:8771/#home'},s);
  await until(s,"!!document.querySelector('#exam-select') && document.querySelector('#sync-panel')?.dataset.kind==='synced'");
  await evaluate(s,'window.confirm=()=>true');
  for(const [name,key,query] of samples) {
    const q=selected.get(key);assert.ok(q,key);
    await field(s,'#exam-select',q.examId);
    await until(s,`JSON.parse(localStorage.getItem('gstudy.web.v1')).selectedExam===${JSON.stringify(q.examId)}`);
    await evaluate(s,"location.hash='#search'");await until(s,"!!document.querySelector('#search-input')");
    await field(s,'#search-input',q.topic,'input');
    const selector=`[data-question="${key}"]`;await until(s,`!!document.querySelector(${JSON.stringify(selector)})`);
    await field(s,'#search-input',query,'input');await until(s,`!!document.querySelector(${JSON.stringify(selector)})`);
    if(name==='multi-page') {
      // These phrases occur in official answer/purpose, not in the question or commentary.
      for(const query of ['NFTの二次流通においてもその収益の一部を著作者に還元させる','構想・計画の実行と評価・改善']) {
        await field(s,'#search-input',query,'input');await until(s,`!!document.querySelector(${JSON.stringify(selector)})`);
      }
    }
    await click(s,selector);await until(s,"location.hash==='#quiz' && !!document.querySelector('[data-action=answer]')");
    await evaluate(s,"document.querySelectorAll('.question-image').forEach(i=>i.loading='eager')");
    await until(s,"[...document.querySelectorAll('.question-image')].every(i=>i.complete&&i.naturalWidth>0)");
    assert.equal(await evaluate(s,"document.querySelectorAll('.question-image').length"),q.images.length);
    assert.ok(await evaluate(s,`document.querySelector('main').textContent.includes(${JSON.stringify(q.prompt)})`));
    if(q.textReview?.passage==='source-verified' && q.passage) assert.ok(await evaluate(s,"!!document.querySelector('section.passage') && !document.querySelector('section.passage').closest('details')"));
    if(name==='table') assert.equal(await evaluate(s,"document.querySelectorAll('.passage table').length"),2);
    if(name==='code') assert.ok(await evaluate(s,"document.querySelector('.passage pre code').textContent.includes('      if (［b］)\\n          divideFlag ← false')"));
    if(name==='unreviewed') {
      if(q.images.some(i=>i.src.startsWith('assets/transcription/'))) {
        assert.ok(await evaluate(s,"!!document.querySelector('.passage') && !document.querySelector('.passage').closest('details')"));
        assert.ok(await evaluate(s,"document.querySelector('main').textContent.includes('原本未照合')"));
        assert.ok(await evaluate(s,"!!(document.querySelector('.passage').compareDocumentPosition(document.querySelector('.question-image')) & Node.DOCUMENT_POSITION_FOLLOWING)"));
      }else assert.ok(await evaluate(s,"[...document.querySelectorAll('details summary')].some(e=>e.textContent.includes('原本未照合'))"));
    }
    if(q.type==='single') {assert.deepEqual(await evaluate(s,"[...document.querySelectorAll('.option span')].map(e=>e.textContent).sort()"),q.options.slice().sort());await click(s,`input[name=answer][value="${q.answer}"]`);}
    else await field(s,'#written-answer','原本との比較のためのテスト回答','input');
    await click(s,'[data-action=answer]');await until(s,"!!document.querySelector('.feedback')");
    if(q.type==='single') assert.ok(await evaluate(s,`document.querySelector('.feedback').textContent.includes(${JSON.stringify(q.options[q.answer])})`));
    if(name==='multi-page') for(const expected of ['公式解答例・解答の要点','出題趣旨・自己評価資料','採点講評',q.modelAnswer.split('\n')[1]]) assert.ok(await evaluate(s,`document.querySelector('.feedback').textContent.includes(${JSON.stringify(expected)})`));
    if(q.type!=='single') await click(s,'[data-action=self-done]');
    await until(s,"!!document.querySelector('[data-action=next]') && document.querySelector('#sync-panel')?.dataset.kind==='synced'");
    const state=await evaluate(s,"JSON.parse(localStorage.getItem('gstudy.web.v1'))");
    await evaluate(s,'window.transcriptionBeforeReload=true');
    await send('Page.reload',{},s);await until(s,"!window.transcriptionBeforeReload && !!document.querySelector('.feedback') && !!document.querySelector('[data-action=next]') && document.querySelector('#sync-panel')?.dataset.kind==='synced'");
    await evaluate(s,"document.querySelectorAll('.question-image').forEach(i=>i.loading='eager')");
    await until(s,"[...document.querySelectorAll('.question-image')].every(i=>i.complete&&i.naturalWidth>0)");
    assert.deepEqual((await evaluate(s,"JSON.parse(localStorage.getItem('gstudy.web.v1'))")).session,state.session);
    for(const width of [320,390,1100]) {
      await send('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:width<500},s);
      assert.equal(await evaluate(s,'document.documentElement.scrollWidth<=innerWidth'),true,name+' '+width);
      if(name==='table' && width===320) assert.ok(await evaluate(s,"[...document.querySelectorAll('.passage .table-scroll')].every(e=>e.scrollWidth>e.clientWidth && e.tabIndex===0)"));
      if(name==='code') assert.equal(await evaluate(s,"document.querySelector('.passage pre').tabIndex"),0);
      if(width===320 && ['table','code'].includes(name)) {
        const selector=name==='table'?'.passage .table-scroll':'.passage pre';
        await evaluate(s,`document.querySelector(${JSON.stringify(selector)}).focus()`);
        await send('Input.dispatchKeyEvent',{type:'keyDown',key:'ArrowRight',code:'ArrowRight',windowsVirtualKeyCode:39},s);
        await send('Input.dispatchKeyEvent',{type:'keyUp',key:'ArrowRight',code:'ArrowRight',windowsVirtualKeyCode:39},s);
        await until(s,`document.querySelector(${JSON.stringify(selector)}).scrollLeft>0`);
        await evaluate(s,`document.querySelector(${JSON.stringify(selector)}).scrollLeft=0`);
      }
      const size=await send('Page.getLayoutMetrics',{},s);
      const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width,height:Math.min(15000,size.cssContentSize.height),scale:1}},s);
      writeFileSync(`tmp/transcription/screenshots/${name}-${width}.png`,Buffer.from(shot.data,'base64'));
      if(width===320) for(const selector of ['.passage','.feedback']) {
        const rect=await evaluate(s,`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e) return null;const r=e.getBoundingClientRect();return {x:0,y:r.top+scrollY,width:innerWidth,height:Math.min(1300,r.height),scale:1};})()`);
        if(rect) {const part=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:rect},s);writeFileSync(`tmp/transcription/screenshots/${name}-${selector.slice(1)}.png`,Buffer.from(part.data,'base64'));}
      }
    }
    await click(s,'[data-action=pause-dialog]');await click(s,'#finish');await until(s,"location.hash==='#results'");
    console.log('PASS: search/question/graded solution/resume/narrow widths '+name+' '+key);
  }
  const edited=selected.get('nw::2009h21a_nw_am2-q001');
  await field(s,'#exam-select','nw');await evaluate(s,"location.hash='#manage'");await until(s,"!!document.querySelector('#manage-search')");
  await field(s,'#manage-search',edited.id,'input');await until(s,"!!document.querySelector('[data-edit-question]')");await click(s,'[data-edit-question]');await until(s,"!!document.querySelector('#question-form')");
  await field(s,'textarea[name=prompt]',edited.prompt+'（編集テスト）','input');
  await evaluate(s,"document.querySelector('#question-form').requestSubmit()");await until(s,"location.hash==='#manage'");
  const custom=await evaluate(s,`JSON.parse(localStorage.getItem('gstudy.web.v1')).custom.find(q=>q.id===${JSON.stringify(edited.id)} && q.examId==='nw')`);
  assert.ok(custom);assert.equal(custom.textReview?.prompt,undefined);assert.equal(custom.textReview?.options,'source-verified');assert.equal(custom.textReview?.answer,undefined);assert.equal(custom.answerKind,undefined);
  console.log('PASS: editing only the prompt clears dependent official answer review; unchanged option text remains source-verified');
  assert.deepEqual(errors,[]);
  writeFileSync(join(directory,'browser-verification.json'),JSON.stringify({passed:true,samples:samples.map(s=>s[0]),widths:[320,390,1100],screenshots:resolve('tmp/transcription/screenshots'),at:new Date().toISOString()},null,2));
  const reportFile=join(directory,'transcription-report.json');
  if(existsSync(reportFile)) {const report=read(reportFile);report.checks.browser='pass';writeFileSync(reportFile,JSON.stringify(report,null,2));}
} finally {
  if(context) await send('Target.disposeBrowserContext',{browserContextId:context});ws.close();
  await new Promise(ok=>preview.server.close(ok));preview.fixture.restore();
}
