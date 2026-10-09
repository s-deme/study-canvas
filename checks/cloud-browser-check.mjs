// Requires an isolated headless Chrome on 9238; owns a fresh loopback preview on 8767.
import assert from 'node:assert/strict';
import {mkdirSync,writeFileSync} from 'node:fs';
import {questions as fixtures} from './fixtures.mjs';
import {servePreview} from './cloud-preview.mjs';
import {emptyState,newSession,submit} from '../web/core.mjs';

const browser=await (await fetch((process.env.STUDY_CANVAS_BROWSER_URL || 'http://127.0.0.1:9238')+'/json/version')).json();
const ws=new WebSocket(browser.webSocketDebuggerUrl);
await new Promise((resolve,reject)=>{ ws.addEventListener('open',resolve,{once:true}); ws.addEventListener('error',reject,{once:true}); });
let id=0; const waiting=new Map();
ws.addEventListener('message',event=>{
  const result=JSON.parse(event.data), pending=waiting.get(result.id);
  if (pending) { waiting.delete(result.id); result.error?pending.reject(new Error(result.error.message)):pending.resolve(result.result); }
});
function send(method,params={},sessionId) {
  const request={id:++id,method,params,...(sessionId?{sessionId}:{})};
  return new Promise((resolve,reject)=>{ waiting.set(request.id,{resolve,reject}); ws.send(JSON.stringify(request)); });
}
async function evaluate(sessionId,expression) {
  const result=await send('Runtime.evaluate',{expression,returnByValue:true,awaitPromise:true},sessionId);
  if (result.exceptionDetails) throw new Error(result.exceptionDetails.text+': '+JSON.stringify(result.exceptionDetails.exception));
  return result.result.value;
}
const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
async function until(sessionId,expression) {
  const deadline=Date.now()+20000;
  while (Date.now()<deadline) { if (await evaluate(sessionId,expression)) return; await pause(100); }
  throw new Error('Timed out: '+expression+'; UI: '+await evaluate(sessionId,'document.body.innerText'));
}
async function page(width,height) {
  const {browserContextId}=await send('Target.createBrowserContext');
  const {targetId}=await send('Target.createTarget',{url:'about:blank',browserContextId});
  const {sessionId}=await send('Target.attachToTarget',{targetId,flatten:true});
  await send('Page.enable',{},sessionId); await send('Network.enable',{},sessionId);
  await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<500},sessionId);
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-color-scheme',value:'light'}]},sessionId);
  await send('Page.navigate',{url:'http://127.0.0.1:8767/'},sessionId);
  await until(sessionId,"document.querySelector('#sync-panel')?.dataset.kind==='synced'");
  return sessionId;
}
mkdirSync(new URL('../dist/screenshots',import.meta.url),{recursive:true});
async function screenshot(sessionId,name) {
  await evaluate(sessionId,'new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))');
  const size=await evaluate(sessionId,'({width:innerWidth,height:Math.max(innerHeight,document.documentElement.scrollHeight)})');
  const {data}=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,...size,scale:1}},sessionId);
  writeFileSync(new URL('../dist/screenshots/'+name+'.png',import.meta.url),Buffer.from(data,'base64'));
}
const preview=await servePreview();
const contexts=[];
try {
  const phone=await page(390,844); contexts.push(phone);
  assert.equal(await evaluate(phone,"document.querySelector('#main').innerText.includes('にはまだ問題がありません')"),true);
  assert.equal(await evaluate(phone,"fetch('/questions.json').then(r=>r.status)"),404);
  assert.equal(await evaluate(phone,"fetch('/private-data/questions.json').then(r=>r.status)"),404);
  assert.equal(await evaluate(phone,'document.documentElement.scrollWidth<=innerWidth'),true);
  await screenshot(phone,'empty-phone');
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-color-scheme',value:'dark'}]},phone);
  await screenshot(phone,'empty-phone-dark');
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-color-scheme',value:'light'}]},phone);
  const file=JSON.stringify(JSON.stringify(fixtures.slice(0,20).map(q=>({...q,id:q.id.slice(7)}))));
  await evaluate(phone,`(()=>{const input=document.querySelector('#import-questions'),transfer=new DataTransfer();transfer.items.add(new File([${file}],'test-questions.json',{type:'application/json'}));input.files=transfer.files;input.dispatchEvent(new Event('change',{bubbles:true}));})()`);
  await until(phone,"!!document.querySelector('[data-action=commit-import]')");
  await evaluate(phone,"document.querySelector('[data-action=commit-import]').click()");
  await until(phone,"document.querySelector('#main').innerText.includes('20') && document.querySelector('#sync-panel').dataset.kind==='synced'");
  await evaluate(phone,"location.hash='#home'");
  await until(phone,"!!document.querySelector('[data-action=daily]')");
  await send('Page.reload',{},phone);
  await until(phone,"!!document.querySelector('[data-action=daily]') && document.querySelector('#sync-panel').dataset.kind==='synced'");
  await evaluate(phone,"document.querySelector('[data-action=daily]').click()");
  await until(phone,"!!document.querySelector('input[name=answer]')");
  await evaluate(phone,"document.querySelector('input[name=answer]').click();document.querySelector('[data-action=answer]').click()");
  await until(phone,"document.querySelector('#sync-panel').dataset.kind==='synced'");
  await evaluate(phone,"document.querySelector('[data-action=bookmark]').click()");
  await until(phone,"document.querySelector('#sync-panel').dataset.kind==='synced'");
  await screenshot(phone,'cloud-phone-synced');
  const expected=await evaluate(phone,"JSON.parse(localStorage.getItem('gstudy.web.v1'))");
  const pc=await page(1100,900); contexts.push(pc);
  const actual=await evaluate(pc,"JSON.parse(localStorage.getItem('gstudy.web.v1'))");
  assert.deepEqual(actual.session,expected.session); assert.deepEqual(actual.stats,expected.stats);
  await evaluate(pc,"document.querySelector('[data-action=resume]').click()");
  await until(pc,"!!document.querySelector('[data-action=next]')");
  await screenshot(pc,'cloud-pc-resumed');
  await send('Emulation.setEmulatedMedia',{features:[{name:'prefers-color-scheme',value:'dark'}]},phone);
  await screenshot(phone,'cloud-phone-dark');
  assert.equal(await evaluate(phone,'document.documentElement.scrollWidth<=innerWidth'),true);

  // Leave edits pending on the PC, then commit a different edit from the phone.
  await until(pc,"document.querySelector('#sync-panel').dataset.kind==='synced'");
  const baselineRevision=await evaluate(pc,"JSON.parse(localStorage.getItem('gstudy.web.v1')).cloud.revision");
  await evaluate(phone,"window.dispatchEvent(new Event('online'))");
  await until(phone,`document.querySelector('#sync-panel').dataset.kind==='synced' && JSON.parse(localStorage.getItem('gstudy.web.v1')).cloud.revision===${baselineRevision}`);
  await send('Network.emulateNetworkConditions',{offline:true,latency:0,downloadThroughput:-1,uploadThroughput:-1},pc);
  await evaluate(pc,"document.querySelector('[data-action=bookmark]').click()");
  await until(pc,"document.querySelector('#sync-panel').dataset.kind==='error'");
  assert.equal(await evaluate(pc,"document.querySelector('#sync-panel').hidden || document.querySelector('#sync-actions').hidden"),false);
  await screenshot(pc,'cloud-offline');
  await evaluate(phone,"document.querySelector('[data-action=next]').click()");
  await until(phone,"document.querySelector('#sync-panel').dataset.kind==='synced'");
  const cloudRevision=await evaluate(phone,"JSON.parse(localStorage.getItem('gstudy.web.v1')).cloud.revision");
  await send('Network.emulateNetworkConditions',{offline:false,latency:0,downloadThroughput:-1,uploadThroughput:-1},pc);
  await evaluate(pc,"window.dispatchEvent(new Event('online'))");
  await until(pc,"document.querySelector('#sync-panel').dataset.kind==='conflict'");
  assert.equal(await evaluate(pc,"document.querySelector('#sync-panel').hidden || document.querySelector('#sync-actions').hidden"),false);
  assert.equal(await evaluate(pc,"document.querySelector('#sync-remote').hidden"),false);
  assert.equal(await evaluate(pc,"JSON.parse(localStorage.getItem('gstudy.web.v1')).cloud.dirty"),true);
  const remote=await (await fetch('http://127.0.0.1:8767/api/state')).json();
  assert.equal(remote.revision,cloudRevision);
  assert.equal(remote.state.session.index,1);
  await screenshot(pc,'cloud-conflict');
  await send('Emulation.setDeviceMetricsOverride',{width:390,height:844,deviceScaleFactor:1,mobile:true},pc);
  assert.equal(await evaluate(pc,'document.documentElement.scrollWidth<=innerWidth'),true);
  await screenshot(pc,'cloud-conflict-phone');
  await evaluate(pc,"location.hash='#exams'");
  await until(pc,"!!document.querySelector('[data-action=export]')");
  assert.equal(await evaluate(pc,"document.querySelector('#main').innerText.includes('端末間の自動同期はありません')"),false);
  await send('Input.dispatchKeyEvent',{type:'keyDown',key:'Tab',code:'Tab',windowsVirtualKeyCode:9},pc);
  await send('Input.dispatchKeyEvent',{type:'keyUp',key:'Tab',code:'Tab',windowsVirtualKeyCode:9},pc);
  assert.equal(await evaluate(pc,"['BUTTON','A','INPUT','SELECT','SUMMARY'].includes(document.activeElement.tagName)"),true);

  // An old session without bundled text must survive startup and private reimport.
  const oldQuestion={...fixtures[0],id:'original:legacy-browser-check'};
  const old=emptyState(); old.session=newSession([oldQuestion],1,'旧演習');
  old.session.pending=0; submit(old,[oldQuestion]);
  const result=await fetch('http://127.0.0.1:8767/api/state',{method:'PUT',headers:{Origin:'http://127.0.0.1:8767','Content-Type':'application/json'},body:JSON.stringify({revision:remote.revision,mutationId:'legacy-browser-0000',state:old})});
  assert.equal(result.status,200);
  const legacy=await page(390,844);
  assert.equal(await evaluate(legacy,"document.querySelector('#main').innerText.includes('以前の演習は保持しています')"),true);
  await evaluate(legacy,"location.hash='#quiz'");
  await until(legacy,"document.querySelector('#main').innerText.includes('演習に使った教材を取り込んでください')");
  assert.equal(await evaluate(legacy,"!!document.querySelector('input[name=answer]')"),false);
  await screenshot(legacy,'legacy-waiting');
  const oldFile=JSON.stringify(JSON.stringify([oldQuestion]));
  await evaluate(legacy,`(()=>{const input=document.querySelector('#import-questions'),transfer=new DataTransfer();transfer.items.add(new File([${oldFile}],'legacy.json',{type:'application/json'}));input.files=transfer.files;input.dispatchEvent(new Event('change',{bubbles:true}));})()`);
  await until(legacy,"!!document.querySelector('[data-action=commit-import]')");
  await evaluate(legacy,"document.querySelector('[data-action=commit-import]').click()");
  await until(legacy,"location.hash==='#manage' && document.querySelector('#sync-panel').dataset.kind==='synced'");
  await evaluate(legacy,"location.hash='#quiz'");
  await until(legacy,"!!document.querySelector('[data-action=next]')");
  const resumed=await evaluate(legacy,"JSON.parse(localStorage.getItem('gstudy.web.v1'))");
  assert.deepEqual(resumed.session,old.session); assert.deepEqual(resumed.stats,old.stats);
  console.log('PASS: empty start, private file 404, import/reload, two-device resume, light/dark mobile layout, offline/conflict and old session preservation/reimport');
} finally {
  try { await send('Browser.close'); ws.close(); }
  finally { await new Promise(resolve=>preview.server.close(resolve)); preview.fixture.restore(); }
}
