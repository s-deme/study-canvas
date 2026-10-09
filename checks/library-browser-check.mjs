// Real private material stays in the local build; only timings and assertions are reported.
import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync,statSync} from 'node:fs';
import {servePreview} from './cloud-preview.mjs';
import {pathToFileURL} from 'node:url';
import {resolve,sep} from 'node:path';
import {bundledAsset} from '../scripts/cloud-runtime.mjs';
const privateRoot=process.env.STUDY_CANVAS_PRIVATE_ROOT?pathToFileURL(resolve(process.env.STUDY_CANVAS_PRIVATE_ROOT)+sep):new URL('../build/private/',import.meta.url);
const {onRequestGet,onRequestPut}=await import(new URL('functions/api/state.js',privateRoot));
const {MATERIAL_MANIFESTS}=await import(new URL('web/library-catalog.mjs',privateRoot));
const browser=await(await fetch((process.env.STUDY_CANVAS_BROWSER_URL || 'http://127.0.0.1:9238')+'/json/version')).json();
const ws=new WebSocket(browser.webSocketDebuggerUrl);await new Promise((ok,fail)=>{ws.onopen=ok;ws.onerror=fail;});
let id=0;const pending=new Map(),contexts=[],errors=[],requests=[],metrics={};
ws.onmessage=e=>{const r=JSON.parse(e.data),p=pending.get(r.id);if(p){pending.delete(r.id);r.error?p.reject(new Error(r.error.message)):p.resolve(r.result);}if(r.method==='Runtime.exceptionThrown') errors.push(r.params.exceptionDetails);if(r.method==='Network.requestWillBeSent') requests.push(r.params.request.url);};
const send=(method,params={},sessionId)=>new Promise((resolve,reject)=>{const key=++id;pending.set(key,{resolve,reject});ws.send(JSON.stringify({id:key,method,params,...(sessionId?{sessionId}:{})}));});
async function evaluate(s,expression) {const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
const pause=ms=>new Promise(ok=>setTimeout(ok,ms));
async function until(s,expression) {const end=Date.now()+60000;while(Date.now()<end) {if(await evaluate(s,expression)) return;await pause(100);}throw new Error('Timed out: '+expression+'; heading: '+await evaluate(s,"document.querySelector('h1')?.textContent"));}
const click=(s,selector)=>evaluate(s,`document.querySelector(${JSON.stringify(selector)}).click()`);
const raw=s=>evaluate(s,"JSON.parse(localStorage.getItem('gstudy.web.v1'))");
async function route(s,hash,selector) {await evaluate(s,`location.hash=${JSON.stringify('#'+hash)}`);await until(s,`!!document.querySelector(${JSON.stringify(selector)})`);}
async function select(s,examId) {await evaluate(s,`(()=>{const el=document.querySelector('#exam-select');el.value=${JSON.stringify(examId)};el.dispatchEvent(new Event('change'));})()`);await until(s,`location.hash==='#home' && document.querySelector('[data-action=daily]') && JSON.parse(localStorage.getItem('gstudy.web.v1')).selectedExam===${JSON.stringify(examId)}`);}
async function field(s,selector,value,event='change') {await evaluate(s,`(()=>{const el=document.querySelector(${JSON.stringify(selector)});el.value=${JSON.stringify(value)};el.dispatchEvent(new Event(${JSON.stringify(event)},{bubbles:true}));})()`);}
async function page() {const c=await send('Target.createBrowserContext');contexts.push(c.browserContextId);const t=await send('Target.createTarget',{url:'about:blank',browserContextId:c.browserContextId}),{sessionId:s}=await send('Target.attachToTarget',{targetId:t.targetId,flatten:true});await send('Page.enable',{},s);await send('Runtime.enable',{},s);await send('Network.enable',{},s);await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},s);await send('Page.navigate',{url:'http://127.0.0.1:8770/#exams'},s);await until(s,"document.querySelector('#exam-inventory') && document.querySelector('#sync-panel')?.dataset.kind==='synced'");await evaluate(s,'window.confirm=()=>true');return s;}
mkdirSync(new URL('../dist/screenshots/',import.meta.url),{recursive:true});
async function screenshot(s,name) {const r=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false},s);writeFileSync(new URL('../dist/screenshots/'+name+'.png',import.meta.url),Buffer.from(r.data,'base64'));}
const preview=await servePreview(8770,{webRoot:new URL('web/',privateRoot),getState:onRequestGet,putState:onRequestPut,assetHandler:process.env.STUDY_CANVAS_PRIVATE_ROOT?bundledAsset:null});
try {
  const begin=performance.now(),s=await page();metrics.overviewMs=Math.round(performance.now()-begin);
  metrics.questions=MATERIAL_MANIFESTS.reduce((n,p)=>n+p.count,0);metrics.overviewBytes=statSync(new URL('../build/private/web/library-catalog.mjs',import.meta.url)).size;
  assert.ok(metrics.questions>=198268);assert.ok(metrics.overviewBytes<300000);
  assert.ok(!requests.some(url=>url.endsWith('/catalog.mjs') || /\/material\//.test(url)),'Overview must not fetch question indexes or bodies');
  await field(s,'#exam-status-filter','available');assert.equal(await evaluate(s,"[...document.querySelectorAll('#exam-inventory tbody tr')].every(r=>!r.innerText.includes('問題未登録'))"),true);
  await field(s,'#exam-name-filter','school-high-2','input');await click(s,'[data-select-exam="school-high-2"]');await until(s,"location.hash==='#home' && !!document.querySelector('[data-action=daily]')");
  assert.equal(requests.filter(url=>/\/material\//.test(url)).length,1,'Home loads only the selected exam index');
  await route(s,'subjects','[data-action=subject]');assert.equal(await evaluate(s,"document.querySelectorAll('#subject-filter').length"),0);
  await click(s,'[data-action=subject]');await until(s,"!!document.querySelector('#practice-form')");await field(s,'#practice-mode','unseen');await field(s,'#practice-count','20');
  assert.ok(await evaluate(s,"document.querySelector('#practice-count-help').textContent.includes('20問を出題')"));
  const start=performance.now();await evaluate(s,"document.querySelector('#practice-form').requestSubmit()");await until(s,"location.hash==='#quiz' && !!document.querySelector('input[name=answer],#written-answer')");metrics.start20Ms=Math.round(performance.now()-start);
  assert.equal((await raw(s)).session.ids.length,20);
  const allPacks=await evaluate(s,"fetch('material/index-school-high-2.json').then(r=>r.json()).then(x=>x.packs.length)");
  assert.ok(new Set(requests.filter(url=>/\/material\/(?!index-)/.test(url))).size<allPacks,'20 questions should not fetch the entire exam');
  await click(s,'[data-action=bookmark]');
  if(await evaluate(s,"!!document.querySelector('#written-answer')")) await field(s,'#written-answer','途中の回答','input');
  else await click(s,'input[name=answer]');
  await until(s,"document.querySelector('#sync-panel').dataset.kind==='synced'");const saved=(await raw(s)).session;
  await send('Page.reload',{},s);await until(s,"!!document.querySelector('[data-action=answer]') && document.querySelector('#sync-panel').dataset.kind==='synced'");assert.deepEqual((await raw(s)).session,saved);
  const tick=performance.now();await click(s,'[data-action=answer]');await until(s,"!!document.querySelector('[data-action=next],[data-action=self-done]')");metrics.answerMs=Math.round(performance.now()-tick);
  if(await evaluate(s,"!!document.querySelector('[data-action=self-done]')")) await click(s,'[data-action=self-done]');
  await click(s,'[data-action=pause-dialog]');await click(s,'#finish');await until(s,"location.hash==='#results'");
  await route(s,'review','[data-action=marked]');await click(s,'[data-action=marked]');await until(s,"!!document.querySelector('#practice-form')");assert.ok(await evaluate(s,"document.querySelector('#practice-count-help').textContent.includes('対象 1問')"));
  await route(s,'manage','#manage-results');assert.equal(await evaluate(s,"document.querySelectorAll('#manage-results [data-edit-question]').length"),50);
  await click(s,'[data-action=manage-next]');assert.equal(await evaluate(s,"document.querySelectorAll('#manage-results [data-edit-question]').length"),50);
  const searchId=await evaluate(s,"document.querySelector('#manage-results [data-edit-question]').dataset.editQuestion.split('::')[1]");await field(s,'#manage-search',searchId,'input');assert.ok(await evaluate(s,"document.querySelectorAll('#manage-results [data-edit-question]').length<=50"));
  await route(s,'search','#search-input');assert.equal(await evaluate(s,"document.querySelectorAll('#search-results [data-question]').length"),50);await click(s,'[data-action=more]');assert.equal(await evaluate(s,"document.querySelectorAll('#search-results [data-question]').length"),50);
  const searchStart=performance.now();await field(s,'#search-input','unlikely-no-match-xyz','input');metrics.searchMs=Math.round(performance.now()-searchStart);assert.equal(await evaluate(s,"document.querySelectorAll('#search-results [data-question]').length"),0);
  await evaluate(s,"location.hash='#mock'");await until(s,"location.hash==='#home' && !!document.querySelector('[data-action=daily]')");assert.equal(await evaluate(s,"!!document.querySelector('#mock-form')"),false);
  await select(s,'sg');await route(s,'search','#search-input');
  const imageQuestion=await evaluate(s,"[...document.querySelectorAll('#search-results .card')].find(el=>el.querySelector('.question-image'))?.querySelector('[data-question]')?.dataset.question");assert.ok(imageQuestion,'SG fixtures include images');
  await click(s,`[data-question="${imageQuestion}"]`);await until(s,"location.hash==='#quiz' && !!document.querySelector('.question-image')");
  const imageSession=(await raw(s)).session;await click(s,'.question-image');assert.equal(await evaluate(s,"document.querySelector('#image-dialog').open"),true);await screenshot(s,'library-image-phone');await click(s,'#image-zoom');assert.equal(await evaluate(s,"document.querySelector('#image-view').style.width"),'auto');await click(s,'#image-close');assert.deepEqual((await raw(s)).session,imageSession);
  assert.equal(await evaluate(s,"document.activeElement.tagName"),'A');
  for(const width of [320,1100]) {await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<500},s);assert.equal(await evaluate(s,'document.documentElement.scrollWidth<=innerWidth'),true);await screenshot(s,'library-question-'+width);}
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-color-scheme',value:'dark'}]},s);await evaluate(s,"document.documentElement.style.fontSize='24px'");assert.equal(await evaluate(s,'document.documentElement.scrollWidth<=innerWidth'),true);await screenshot(s,'library-question-dark-large');
  await until(s,"document.querySelector('#sync-panel').dataset.kind==='synced'");const expected=await raw(s),other=await page();assert.deepEqual((await raw(other)).stats,expected.stats);assert.deepEqual((await raw(other)).session,expected.session);
  assert.deepEqual(errors,[]);console.log('PASS: real private library overview, lazy indexes/bodies, practice settings, resume, search/manage pagination, removed mock setup, modal images, responsive layouts and two-device sync');console.log(JSON.stringify(metrics));
} finally {for(const context of contexts) await send('Target.disposeBrowserContext',{browserContextId:context});await new Promise(ok=>preview.server.close(ok));preview.fixture.restore();ws.close();}
