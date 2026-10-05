// Isolated headless Chrome (9238), loopback authenticated preview (8769).
import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {onRequestGet,onRequestPut} from '../build/private/functions/api/state.js';
import {servePreview} from './cloud-preview.mjs';
import {MATERIAL_EXAMS,MATERIAL_PACKS} from '../build/private/web/catalog.mjs';
const browser=await(await fetch((process.env.STUDY_CANVAS_BROWSER_URL || 'http://127.0.0.1:9238')+'/json/version')).json(),ws=new WebSocket(browser.webSocketDebuggerUrl);
await new Promise((ok,fail)=>{ws.addEventListener('open',ok,{once:true});ws.addEventListener('error',fail,{once:true});});
let id=0;const waiting=new Map();ws.addEventListener('message',e=>{const r=JSON.parse(e.data),p=waiting.get(r.id);if(p) {waiting.delete(r.id);r.error?p.reject(new Error(r.error.message)):p.resolve(r.result);}});
const send=(method,params={},sessionId)=>new Promise((resolve,reject)=>{const key=++id;waiting.set(key,{resolve,reject});ws.send(JSON.stringify({id:key,method,params,...(sessionId?{sessionId}:{})}));});
async function evaluate(s,expression) {const r=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true},s);if(r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
const pause=ms=>new Promise(ok=>setTimeout(ok,ms));
async function until(s,expression) {const deadline=Date.now()+20000;while(Date.now()<deadline) {if(await evaluate(s,expression)) return;await pause(100);}throw new Error('Timed out: '+expression+'\n'+await evaluate(s,'document.body.innerText'));}
const preview=await servePreview(8770,{webRoot:new URL('../build/private/web/',import.meta.url),getState:onRequestGet,putState:onRequestPut}),contexts=[],errors=[];
ws.addEventListener('message',e=>{const r=JSON.parse(e.data);if(r.method==='Runtime.exceptionThrown') errors.push(r.params.exceptionDetails);});
async function page(width=390,seed=null) {const context=await send('Target.createBrowserContext');contexts.push(context.browserContextId);const t=await send('Target.createTarget',{url:'about:blank',browserContextId:context.browserContextId}),{sessionId:s}=await send('Target.attachToTarget',{targetId:t.targetId,flatten:true});await send('Page.enable',{},s);await send('Runtime.enable',{},s);if(seed) await send('Page.addScriptToEvaluateOnNewDocument',{source:`if(!localStorage.getItem('gstudy.web.v1')) localStorage.setItem('gstudy.web.v1',${JSON.stringify(JSON.stringify(seed))});`},s);await send('Emulation.setDeviceMetricsOverride',{width,height:844,deviceScaleFactor:1,mobile:width<500},s);await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-color-scheme',value:'light'}]},s);await send('Page.navigate',{url:'http://127.0.0.1:8770/'},s);await until(s,"document.querySelector('#sync-panel')?.dataset.kind==='synced'");await evaluate(s,'window.confirm=()=>true');return s;}
const click=(s,selector)=>evaluate(s,`document.querySelector(${JSON.stringify(selector)}).click()`);
async function route(s,hash) {await evaluate(s,`location.hash=${JSON.stringify('#'+hash)}`);await until(s,`location.hash===${JSON.stringify('#'+hash)} && !!document.querySelector('#main h1')`);await pause(150);}
async function select(s,value) {await evaluate(s,`(()=>{const i=document.querySelector('#exam-select');i.value=${JSON.stringify(value)};i.dispatchEvent(new Event('change'));})()`);await until(s,`JSON.parse(localStorage.getItem('gstudy.web.v1')).selectedExam===${JSON.stringify(value)}`);await pause(150);}
async function setForm(s,selector,values) {await evaluate(s,`(()=>{const f=document.querySelector(${JSON.stringify(selector)});for(const [k,v] of Object.entries(${JSON.stringify(values)})) {f.elements.namedItem(k).value=v;f.elements.namedItem(k).dispatchEvent(new Event('change',{bubbles:true}));}f.requestSubmit();})()`);}
async function importFile(s,name,content) {await evaluate(s,`(()=>{const input=document.querySelector('#import-questions'),d=new DataTransfer();d.items.add(new File([${JSON.stringify(content)}],${JSON.stringify(name)}));input.files=d.files;input.dispatchEvent(new Event('change'));})()`);await until(s,"location.hash==='#manage' && document.querySelector('#main').innerText.includes('取り込み前の確認')");}
mkdirSync(new URL('../private-data/additions/screenshots',import.meta.url),{recursive:true});
async function screenshot(s,name) {await evaluate(s,"document.querySelector('#notice').hidden=true");await evaluate(s,'new Promise(ok=>requestAnimationFrame(()=>requestAnimationFrame(ok)))');const size=await evaluate(s,'({width:innerWidth,height:Math.max(innerHeight,document.documentElement.scrollHeight)})');const r=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,...size,scale:1}},s);writeFileSync(new URL('../private-data/additions/screenshots/'+name+'.png',import.meta.url),Buffer.from(r.data,'base64'));}
const raw=s=>evaluate(s,"JSON.parse(localStorage.getItem('gstudy.web.v1'))");

const result=[];
try {
 const s=await page(390);
 await send('Page.addScriptToEvaluateOnNewDocument',{source:'window.confirm=()=>true;'},s);
 for(const examId of ['gyosei-original','health2-original','agri3-original']) {
  const packs=MATERIAL_PACKS.filter(p=>p.examId===examId),rows=packs.flatMap(p=>JSON.parse(readFileSync(new URL('../build/private/web/'+p.url,import.meta.url),'utf8')));
  await select(s,examId);await until(s,"!!document.querySelector('[data-material-filter=subject]')");
  const checked=[];
  for(const subject of [...new Set(rows.map(q=>q.subject))]) {
   await route(s,'subjects');
   await evaluate(s, '(()=>{const x=document.querySelector("[data-material-filter=subject]");x.value='+JSON.stringify(subject)+';x.dispatchEvent(new Event("change",{bubbles:true}));})()');
   await until(s,"!!document.querySelector('#subject-filter')");
   const expected=rows.filter(q=>q.subject===subject);
   assert.ok(await evaluate(s,'document.querySelector(".material-filters").innerText.includes('+JSON.stringify(expected.length+'問 / 全50問')+')'));
   for(const category of [...new Set(expected.map(q=>q.category))]) {
    await route(s,'subjects');
    await evaluate(s,'document.querySelector("#subject-filter").value='+JSON.stringify(subject));
    const action=await evaluate(s,'[...document.querySelectorAll("[data-action^=category-]")].find(b=>b.closest(".card").querySelector("h2").innerText==='+JSON.stringify(category)+')?.dataset.action');
    assert.ok(action,category);await click(s,'[data-action="'+action+'"]');
    await until(s,"!!document.querySelector('input[name=answer]')");
    const before=await raw(s),keys=expected.filter(q=>q.category===category).map(q=>examId+'::'+q.id);
    assert.deepEqual([...before.session.ids].sort(),[...keys].sort(),subject+'/'+category);
    const q=rows.find(q=>examId+'::'+q.id===before.session.ids[0]);
    const prompt=q.prompt.replace(/\s+/g,' ').trim();
    assert.ok(await evaluate(s,'document.querySelector("#main").innerText.replace(/\\s+/g," ").includes('+JSON.stringify(prompt)+')'));
    assert.ok(await evaluate(s,'document.querySelector("#main").innerText.includes("自作問題")'));
    assert.equal(await evaluate(s,'document.querySelector("#main").innerText.includes("公式解答")'),false);
    await click(s,'input[name=answer][value="'+q.answer+'"]');await click(s,'[data-action=answer]');
    assert.ok(await evaluate(s,'!!document.querySelector(".feedback .correct")'));
    const explanation=q.explanation.replace(/\s+/g,' ').trim();
    assert.ok(await evaluate(s,'document.querySelector(".feedback").innerText.replace(/\\s+/g," ").includes('+JSON.stringify(explanation)+')'));
    if(checked.length===0) {await until(s,"document.querySelector('#sync-panel').dataset.kind==='synced'");await screenshot(s,'new-genres-'+examId+'-answered');}
    checked.push({subject,category,questions:keys.length,example:q.id});
   }
  }
  // Wrong-answer feedback and record persistence for each new genre.
  await route(s,'search');await evaluate(s,'document.querySelector("[data-material-filter=subject]").value="";document.querySelector("[data-material-filter=subject]").dispatchEvent(new Event("change",{bubbles:true}))');
  const q=rows.at(-1);await evaluate(s,'document.querySelector("#search-input").value='+JSON.stringify(q.topic)+';document.querySelector("#search-input").dispatchEvent(new Event("input",{bubbles:true}))');
  const selector='[data-question="'+examId+'::'+q.id+'"]';await until(s,'!!document.querySelector('+JSON.stringify(selector)+')');await click(s,selector);await until(s,"!!document.querySelector('input[name=answer]')");
  await click(s,'input[name=answer][value="'+((q.answer+1)%3)+'"]');await click(s,'[data-action=answer]');assert.ok(await evaluate(s,'!!document.querySelector(".feedback .incorrect")'));
  await until(s,"document.querySelector('#sync-panel').dataset.kind==='synced'");const saved=await raw(s);
  await evaluate(s,'window.__beforeGenreReload=true');await send('Page.reload',{},s);
  await until(s,"!window.__beforeGenreReload && document.readyState==='complete' && !!document.querySelector('.feedback .incorrect') && document.querySelector('#sync-panel')?.dataset.kind==='synced'");
  assert.deepEqual((await raw(s)).stats,saved.stats);
  assert.equal(await evaluate(s,'document.documentElement.scrollWidth<=innerWidth'),true);
  result.push({examId,checked,correctAndIncorrect:'pass',explanation:'exact rendered text pass',reloadRecords:'pass',mobileOverflow:'pass'});
 }
 assert.equal(errors.length,0,JSON.stringify(errors));
 writeFileSync(new URL('../private-data/additions/new-genres-browser-verification.json',import.meta.url),JSON.stringify({browser:'actual headless Chrome, isolated profile, authenticated loopback fixture only',checkedOn:'2026-10-05',result,runtimeErrors:errors.length},null,2));
 console.log('PASS new genres browser: all subject/category combinations, correct/wrong grading, complete explanations, reload records and 390px');
} finally {for(const context of contexts) await send('Target.disposeBrowserContext',{browserContextId:context});await new Promise(ok=>preview.server.close(ok));preview.fixture.restore();ws.close();}
