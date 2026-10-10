// Real representative material, isolated Chrome context and loopback authentication fixture.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
import {join,resolve,sep} from 'node:path';
import {pathToFileURL} from 'node:url';
import {servePreview} from './cloud-preview.mjs';
import {bundledAsset} from '../scripts/cloud-runtime.mjs';
import {validateQuestions} from '../web/core.mjs';
const read=file=>JSON.parse(readFileSync(file));
const directory=process.env.STUDY_CANVAS_PRIVATE_ROOT || read('build/private-compact/current.json').directory,root=pathToFileURL(resolve(directory)+sep);
const manifest=read(join(directory,'manifest.json'));
const samples=[['native','fe::2023r05_fe_kamoku_a-q003'],['table','boki3::boki3-original-18'],
  ['table-image','fe::2023r05_fe_kamoku_a-q002'],['formula','ap::2023r05a_ap_am-q01'],
  ['diagram','fe::2023r05_fe_kamoku_a-q013'],['scan','nw::2009h21a_nw_am2-q001'],
  ['code','fe::2023r05_fe_kamoku_b-q001'],['multipage','st::2023r05h_st_pm1-q01-s1']];
const evidence=Object.values(read(join(read('build/private-compact/current.json').directory,'text-evidence.json')));
const answerPatch=evidence.find(p=>p.solution?.removed.length && p.original.type==='written');
if(answerPatch) samples.push(['answer-text',answerPatch.original.examId+'::'+answerPatch.original.id]);
const explanationPatch=evidence.find(p=>p.solution?.field==='explanation' && p.solution.kind!=='official-answer-mark') || evidence.find(p=>p.solution?.field==='explanation');
if(explanationPatch) samples.push(['explanation-text',explanationPatch.original.examId+'::'+explanationPatch.original.id]);
const partialPatch=evidence.find(p=>p.question?.retained.length);
if(partialPatch) samples.push(['partial-text',partialPatch.original.examId+'::'+partialPatch.original.id]);
for(const kind of ['fp','food','electricity']) {
  const patch=evidence.find(p=>p.mode==='passage' && ['single','multiple'].includes(p.original.type) && (kind==='fp'?p.original.examId.startsWith('fp'):p.sourceFile.startsWith(kind+'-')));
  assert.ok(patch,'Missing native representative: '+kind);samples.push(['native-'+kind,patch.original.examId+'::'+patch.original.id]);
}
const selected=new Map();
for(const p of manifest.packs) for(const q of validateQuestions(read(join(directory,'web',p.url)))) {
  const key=q.examId+'::'+q.id;if(samples.some(s=>s[1]===key)) selected.set(key,q);
}
const {onRequestGet,onRequestPut}=await import(new URL('functions/api/state.js',root));
const preview=await servePreview(8771,{webRoot:new URL('web/',root),getState:onRequestGet,putState:onRequestPut,assetHandler:process.env.STUDY_CANVAS_PRIVATE_ROOT?bundledAsset:null});
const browser=await(await fetch('http://127.0.0.1:9238/json/version')).json();
const ws=new WebSocket(browser.webSocketDebuggerUrl);await new Promise((ok,fail)=>{ws.onopen=ok;ws.onerror=fail;});
let id=0,context;const pending=new Map(),errors=[];
ws.onmessage=e=>{const r=JSON.parse(e.data),p=pending.get(r.id);if(p){pending.delete(r.id);r.error?p.reject(new Error(r.error.message)):p.resolve(r.result);}if(r.method==='Runtime.exceptionThrown') errors.push(r.params.exceptionDetails);};
const send=(method,params={},sessionId)=>new Promise((resolve,reject)=>{const key=++id;pending.set(key,{resolve,reject});ws.send(JSON.stringify({id:key,method,params,...(sessionId?{sessionId}:{})}));});
async function evaluate(s,expression) {const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
async function until(s,expression) {const end=Date.now()+60000;while(Date.now()<end){if(await evaluate(s,expression)) return;await new Promise(ok=>setTimeout(ok,100));}throw new Error('Timed out: '+expression);}
const click=(s,selector)=>evaluate(s,`document.querySelector(${JSON.stringify(selector)}).click()`);
const field=(s,selector,value,event='change')=>evaluate(s,`(()=>{const el=document.querySelector(${JSON.stringify(selector)});el.value=${JSON.stringify(value)};el.dispatchEvent(new Event(${JSON.stringify(event)},{bubbles:true}));})()`);
mkdirSync('tmp/compact-screenshots',{recursive:true});
try {
  context=(await send('Target.createBrowserContext')).browserContextId;
  const t=await send('Target.createTarget',{url:'about:blank',browserContextId:context});
  const {sessionId:s}=await send('Target.attachToTarget',{targetId:t.targetId,flatten:true});
  await send('Page.enable',{},s);await send('Runtime.enable',{},s);
  await send('Emulation.setDeviceMetricsOverride',{width:1100,height:1000,deviceScaleFactor:1,mobile:false},s);
  await send('Page.navigate',{url:'http://127.0.0.1:8771/#home'},s);
  await until(s,"!!document.querySelector('#exam-select') && document.querySelector('#sync-panel')?.dataset.kind==='synced'");
  await evaluate(s,'window.confirm=()=>true');
  if(manifest.assetAliases) {
    const alias=Object.keys(manifest.assetAliases).find(p=>p.includes('2023r05_fe_kamoku_a-q013-'));
    for(const old of [alias]) {
      const result=await evaluate(s,`fetch(${JSON.stringify(old)}).then(async r=>{const image=await createImageBitmap(await r.blob());return {status:r.status,type:r.headers.get('Content-Type'),width:image.width,height:image.height};})`);
      assert.equal(result.status,200);assert.ok(result.width>0 && result.height>0);assert.equal(result.type,manifest.assetAliases[old]?'image/webp':'image/png');
    }
    console.log('PASS: retained image legacy PNG URLs decode after WebP conversion');
    const retired=evidence.flatMap(p=>p.textSha256?p.original.images:[]).find(i=>!manifest.assetAliases[i.src] && !manifest.assetHashes[i.src]);
    assert.ok(retired,'Missing retired image sample');
    assert.equal(await evaluate(s,`fetch(${JSON.stringify(retired.src)}).then(r=>r.status)`),404);
  }
  for(const [name,key] of samples) {
    const q=selected.get(key);assert.ok(q,key);
    await field(s,'#exam-select',q.examId);
    await until(s,`location.hash==='#home' && JSON.parse(localStorage.getItem('gstudy.web.v1')).selectedExam===${JSON.stringify(q.examId)}`);
    await evaluate(s,"location.hash='#search'");await until(s,"!!document.querySelector('#search-input')");
    await field(s,'#search-input',q.topic,'input');
    const selector=`[data-question="${key}"]`;await until(s,`!!document.querySelector(${JSON.stringify(selector)})`);
    await click(s,selector);await until(s,"location.hash==='#quiz' && !!document.querySelector('[data-action=answer]')");
    await evaluate(s,"document.querySelectorAll('.question-image').forEach(i=>i.loading='eager')");
    await until(s,"[...document.querySelectorAll('.question-image')].every(i=>i.complete&&i.naturalWidth>0)");
    if(name.startsWith('native')) {
      assert.equal(await evaluate(s,"document.querySelectorAll('.question-image').length"),0);
      if(name==='native') assert.ok(await evaluate(s,"document.querySelector('main').textContent.includes('メモリインタリーブ')"));
      else {
        const line=q.passage.split('\n').find(line=>line.trim().length>10 && !line.startsWith('|'));assert.ok(line,name);
        assert.ok(await evaluate(s,`document.querySelector('.passage')?.textContent.includes(${JSON.stringify(line)})`));
        assert.ok(await evaluate(s,`document.querySelector('main').textContent.includes(${JSON.stringify(q.prompt)})`));
      }
      assert.deepEqual(await evaluate(s,"[...document.querySelectorAll('.option span')].map(s=>s.textContent).sort()"),q.options.slice().sort());
    } else if(name==='table') assert.ok(await evaluate(s,"!!document.querySelector('table th[scope=col]')"));
    else assert.equal(await evaluate(s,"document.querySelectorAll('.question-image').length"),q.images.length);
    if(name==='partial-text') assert.ok(await evaluate(s,"document.querySelector('main').textContent.includes('原本資料（文字化済み領域）')"));
    if(name==='code') assert.ok(await evaluate(s,"!!document.querySelector('.passage pre code')"));
    if(name==='multipage') assert.ok(await evaluate(s,"document.querySelector('.passage').textContent.includes('ウォレット機能')"));
    const size=await send('Page.getLayoutMetrics',{},s);
    const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width:1100,height:Math.min(3000,size.cssContentSize.height),scale:1}},s);
    writeFileSync(`tmp/compact-screenshots/${name}.png`,Buffer.from(shot.data,'base64'));
    for(const width of [320,390,1100]) {
      await send('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:width<500},s);
      assert.equal(await evaluate(s,'document.documentElement.scrollWidth<=innerWidth'),true,name+' '+width);
    }
    if(name==='native') {
      await click(s,`input[name=answer][value="${q.answer}"]`);await click(s,'[data-action=answer]');
      await until(s,"!!document.querySelector('[data-action=next]')");
      await until(s,"document.querySelector('#sync-panel')?.dataset.kind==='synced'");
      const raw=await evaluate(s,"JSON.parse(localStorage.getItem('gstudy.web.v1'))");
      assert.ok(raw.stats[key].correct>0);
      await evaluate(s,'window.compactBeforeReload=true');
      await send('Page.reload',{},s);await until(s,"!window.compactBeforeReload && !!document.querySelector('[data-action=next]') && document.querySelector('#sync-panel')?.dataset.kind==='synced'");
      assert.deepEqual((await evaluate(s,"JSON.parse(localStorage.getItem('gstudy.web.v1'))")).session,raw.session);
    }
    if(name==='answer-text' || name==='explanation-text') {
      if(q.type==='written') await field(s,'#written-answer','検査用の回答','input');
      else await click(s,`input[name=answer][value="${q.answer}"]`);
      await click(s,'[data-action=answer]');await until(s,"!!document.querySelector('.feedback')");
      const solution=evidence.find(p=>p.original.examId+'::'+p.original.id===key).solution;
      const snippet=solution.kind==='official-answer-mark'?q.explanation:solution.text.split('\n').find(line=>line.trim().length>5 && !line.startsWith('|'));
      assert.ok(snippet && await evaluate(s,`document.querySelector('.feedback').textContent.includes(${JSON.stringify(snippet)})`));
      assert.equal(await evaluate(s,"document.querySelectorAll('.feedback .question-image').length"),q.solutionImages.length);
      for(const width of [320,390,1100]) {
        await send('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:width<500},s);
        assert.equal(await evaluate(s,'document.documentElement.scrollWidth<=innerWidth'),true,name+' '+width);
      }
      await evaluate(s,"document.querySelector('.feedback').scrollIntoView()");
      const shot=await send('Page.captureScreenshot',{format:'png'},s);writeFileSync(`tmp/compact-screenshots/${name}-feedback.png`,Buffer.from(shot.data,'base64'));
      if(q.type==='written') await click(s,'[data-action=self-done]');
    }
    await click(s,'[data-action=pause-dialog]');await click(s,'#finish');await until(s,"location.hash==='#results'");
    console.log('PASS: representative '+name+' '+key);
  }
  assert.deepEqual(errors,[]);
  writeFileSync(join(directory,'browser-verification.json'),JSON.stringify({passed:true,samples:samples.map(s=>s[0]),screenshots:resolve('tmp/compact-screenshots'),widths:[320,390,1100],at:new Date().toISOString()},null,2));
} finally {
  if(context) await send('Target.disposeBrowserContext',{browserContextId:context});ws.close();
  await new Promise(ok=>preview.server.close(ok));preview.fixture.restore();
}
