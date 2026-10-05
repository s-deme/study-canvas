// Isolated headless Chrome (9238), loopback authenticated preview (8769).
import assert from 'node:assert/strict';
import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {onRequestGet,onRequestPut} from '../build/private/functions/api/state.js';
import {servePreview} from './cloud-preview.mjs';
import {MATERIAL_EXAMS,MATERIAL_PACKS} from '../build/private/web/catalog.mjs';
import {AVAILABLE_EXAMS} from '../build/private/web/core.mjs';
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

try {
 const phone=await page(390);await until(phone,"!!document.querySelector('[data-action=daily]')");
 assert.equal(await evaluate(phone,"document.querySelector('#exam-select').options.length"),AVAILABLE_EXAMS.length);
 await route(phone,'exams');assert.equal(await evaluate(phone,"document.querySelectorAll('#exam-inventory tbody tr').length"),AVAILABLE_EXAMS.length);
 for(const [examId,count] of [['ap',730],['sg',15],['fe',26],['boki3',20],['eiken3',0]]) assert.equal(await evaluate(phone,`document.querySelector('[data-select-exam="${examId}"]').closest('tr').children[1].textContent`),count+'問');
 assert.equal(await evaluate(phone,'document.documentElement.scrollWidth<=innerWidth'),true);await screenshot(phone,'exam-inventory-private-phone');
 await select(phone,'gken');await route(phone,'home');
 const loaded=await evaluate(phone,"performance.getEntriesByType('resource').filter(r=>r.name.includes('/material/')&&r.name.endsWith('.json')).map(r=>r.name)");assert.equal(loaded.length,1);assert.ok(loaded[0].includes('gken-restored'));
 for(const examId of ['fp2','fp3'].filter(id=>MATERIAL_EXAMS.some(e=>e.id===id))) {
  await select(phone,examId);await until(phone,"!!document.querySelector('[data-material-filter=year]')");await route(phone,'search');
  await click(phone,'[data-question]');await until(phone,"!!document.querySelector('input[name=answer]')");
  await until(phone,"[...document.querySelectorAll('#main img')].every(i=>i.complete && i.naturalWidth>0)");
  assert.equal(await evaluate(phone,"document.querySelector('#main').innerText.includes('施行の法令')"),true);
  assert.equal(await evaluate(phone,"document.querySelector('#main').innerText.includes('公式解答：')"),false);
  await until(phone,"document.querySelector('#sync-panel').dataset.kind==='synced'");
  await screenshot(phone,'private-'+examId+'-phone');await click(phone,'input[name=answer]');await click(phone,'[data-action=answer]');
  assert.equal(await evaluate(phone,"document.querySelector('#main').innerText.includes('公式解答：')"),true);
  await click(phone,'[data-action=next]');
 }
 for(const pack of MATERIAL_PACKS.filter(p=>p.kind==='official' && p.examId==='ap')) {
  const rows=JSON.parse(readFileSync(new URL('../build/private/web/'+pack.url,import.meta.url),'utf8'));
  await select(phone,'ap');await until(phone,"!!document.querySelector('[data-material-filter=year]')");
  await evaluate(phone,`(()=>{const s=document.querySelector('[data-material-filter=year]');s.value=${JSON.stringify(pack.year)};s.dispatchEvent(new Event('change',{bubbles:true}));})()`);await route(phone,'search');
  for(const q of rows.filter((q,i)=>i===0 || /-q(06|23|28|29)$/.test(q.id))) {
  await route(phone,'search');
  await evaluate(phone,`(()=>{const s=document.querySelector('#search-input');s.value=${JSON.stringify(q.topic || q.prompt.split(/\r?\n/)[0])};s.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  const selector=`[data-question="ap::${q.id}"]`;
  await until(phone,`!!document.querySelector(${JSON.stringify(selector)})`);
  await click(phone,selector);await until(phone,"!!document.querySelector('input[name=answer]')");
  assert.equal((await raw(phone)).session.ids[0],'ap::'+q.id);
  await until(phone,"[...document.querySelectorAll('#main img')].every(i=>i.complete && i.naturalWidth>0)");
  assert.equal(await evaluate(phone,"document.querySelector('#main').innerText.includes('公式解答：')"),false);
  const name=pack.id.endsWith('-001') ? (q===rows[0]?'private-ap-2022-001-phone':'private-ap-2022-q06-phone') : 'private-'+pack.id+(q===rows[0]?'':'-'+q.id.split('-').at(-1))+'-phone';
  await screenshot(phone,name);await click(phone,'input[name=answer]');await click(phone,'[data-action=answer]');
  assert.ok(await evaluate(phone,"document.querySelector('#main').innerText.includes('公式解答：') && document.querySelector('#main').innerText.includes('独自作成の解説：')"));
  await click(phone,'[data-action=next]');await until(phone,"document.querySelector('#sync-panel').dataset.kind==='synced'");
  }
 }
 for(const pack of MATERIAL_PACKS.filter(p=>p.kind==='original')) {
  const examId=pack.examId;
  const first=JSON.parse(readFileSync(new URL('../build/private/web/'+pack.url,import.meta.url),'utf8'))[0];
  await select(phone,examId);await until(phone,"!!document.querySelector('[data-material-filter=subject]')");
  await evaluate(phone,`(()=>{const s=document.querySelector('[data-material-filter=subject]');s.value=${JSON.stringify(pack.subject)};s.dispatchEvent(new Event('change',{bubbles:true}));})()`);await route(phone,'search');
  await evaluate(phone,`(()=>{const s=document.querySelector('#search-input');s.value=${JSON.stringify(first.topic || first.prompt.split(/\r?\n/)[0])};s.dispatchEvent(new Event('input',{bubbles:true}));})()`);
  const firstSelector=`[data-question="${examId}::${first.id}"]`;
  await until(phone,`!!document.querySelector(${JSON.stringify(firstSelector)})`);
  await click(phone,firstSelector);await until(phone,"!!document.querySelector('input[name=answer]')");
  assert.equal((await raw(phone)).session.ids[0],examId+'::'+first.id);
  const renderedPrompt=first.prompt.replace(/^```[^\n]*$/gm,'').replace(/\s+/g,' ').trim();
  assert.ok(await evaluate(phone,`document.querySelector('#main').innerText.replace(/\\s+/g,' ').includes(${JSON.stringify(renderedPrompt)})`),pack.id+' prompt differs');
  assert.ok(await evaluate(phone,"document.querySelector('#main').innerText.includes('自作問題')"));
  assert.equal(await evaluate(phone,"document.querySelector('#main').innerText.includes('公式解答')"),false);
  await until(phone,"document.querySelector('#sync-panel').dataset.kind==='synced'");
  await screenshot(phone,'private-'+examId+(pack.id.endsWith('-001')?'':'-'+pack.id.split('-').at(-1))+'-phone');await click(phone,'input[name=answer]');await click(phone,'[data-action=answer]');
  assert.ok(await evaluate(phone,"document.querySelector('#main').innerText.includes('独自作成の解説')"));
  assert.equal(await evaluate(phone,"document.querySelector('#main').innerText.includes('公式解答')"),false);
  await click(phone,'[data-action=next]');
  await until(phone,"document.querySelector('#sync-panel').dataset.kind==='synced'");
 }
 await select(phone,'ap');await until(phone,"!!document.querySelector('[data-material-filter=year]')");
 await evaluate(phone,"(()=>{const s=document.querySelector('[data-material-filter=year]');s.value='2024';s.dispatchEvent(new Event('change',{bubbles:true}));})()");await route(phone,'search');assert.equal(await evaluate(phone,"[...document.querySelectorAll('[data-question]')].every(b=>b.dataset.question.includes('2024r06'))"),true);
 await click(phone,'[data-question]');await until(phone,"!!document.querySelector('input[name=answer]')");await until(phone,"[...document.querySelectorAll('#main img')].every(i=>i.complete && i.naturalWidth>0)");await screenshot(phone,'private-choice-phone');await click(phone,'input[name=answer]');await click(phone,'[data-action=answer]');await click(phone,'[data-action=next]');
 await select(phone,'es');await until(phone,"!!document.querySelector('[data-material-filter=year]')");await evaluate(phone,"(()=>{const s=document.querySelector('[data-material-filter=subject]');s.value='午後Ⅱ';s.dispatchEvent(new Event('change',{bubbles:true}));})()");await route(phone,'search');await click(phone,'[data-question]');await until(phone,"!!document.querySelector('#written-answer')");
 await evaluate(phone,"(()=>{const a=document.querySelector('#written-answer');a.value='途中の論述';a.dispatchEvent(new Event('input',{bubbles:true}));})()");await until(phone,"document.querySelector('#sync-panel').dataset.kind==='synced'");await send('Page.reload',{},phone);await until(phone,"document.querySelector('#written-answer')?.value==='途中の論述'");await click(phone,'[data-action=answer]');await until(phone,"!!document.querySelector('[data-action=self-partial]')");assert.equal(await evaluate(phone,"document.querySelector('#main').innerText.includes('評価資料')"),true);await screenshot(phone,'private-essay-phone');await click(phone,'[data-action=self-partial]');await click(phone,'[data-action=next]');await until(phone,"document.querySelector('#sync-panel').dataset.kind==='synced'");
 const expected=await raw(phone),pc=await page(1100);assert.deepEqual((await raw(pc)).stats,expected.stats);assert.equal(expected.custom.length,0);assert.ok(Object.keys(expected.stats).some(k=>k.startsWith('ap::')));assert.ok(Object.keys(expected.stats).some(k=>k.startsWith('es::')));
 for(const [id,n] of [['sg',15],['fe',26],['boki3',20],['gken',240]]) {await select(pc,id);await until(pc,"!!document.querySelector('[data-material-filter=year]')");assert.ok(await evaluate(pc,`document.querySelector('.material-filters').innerText.includes('全${n}問')`));}

 const before=await raw(pc);await send('Network.enable',{},pc);await send('Network.setBlockedURLs',{urls:['*gken-restored.json']},pc);await send('Page.reload',{},pc);await until(pc,"!!document.querySelector('[data-action=retry-material]')");assert.equal(await evaluate(pc,"document.querySelector('#main').innerText.includes('まだ問題がありません')"),false);assert.deepEqual((await raw(pc)).stats,before.stats);await send('Network.setBlockedURLs',{urls:[]},pc);await click(pc,'[data-action=retry-material]');await until(pc,"!!document.querySelector('[data-action=daily]')");
 await evaluate(pc,'window.confirm=()=>true');const backup=JSON.stringify(await raw(pc));await evaluate(pc,`(()=>{const input=document.querySelector('#import-backup'),d=new DataTransfer();d.items.add(new File([${JSON.stringify(backup)}],'backup.json'));input.files=d.files;input.dispatchEvent(new Event('change'));})()`);await until(pc,"location.hash==='#records' && document.querySelector('#sync-panel').dataset.kind==='synced'");assert.deepEqual((await raw(pc)).stats,before.stats);await route(pc,'home');
 await screenshot(pc,'private-restored-desktop');await send('Emulation.setDeviceMetricsOverride',{width:320,height:844,deviceScaleFactor:1,mobile:true},phone);await route(phone,'home');assert.equal(await evaluate(phone,'document.documentElement.scrollWidth<=innerWidth'),true);assert.equal(errors.length,0,JSON.stringify(errors));console.log('PASS private browser: lazy packs, filters, images, essay guidance, draft reload, two-device record isolation, restored counts, 320px');
} finally {for(const context of contexts) await send('Target.disposeBrowserContext',{browserContextId:context});await new Promise(ok=>preview.server.close(ok));preview.fixture.restore();ws.close();}
