import {questionKey,validateQuestions,indexQuestions,questionIndex} from './core.mjs';

export class MaterialLibrary {
  constructor(index,packs,request=(...args)=>fetch(...args),manifests=[]) {
    this.base=index.map(q=>({...q}));this.packs=[...packs];this.request=request;this.manifests=manifests;
    this.loaded=new Set();this.pending=new Map();this.indexed=new Set();this.ready=new Set();this.progress=new Map();
    indexQuestions(this.base);
  }
  has(examId) {return this.manifests.some(p=>p.examId===examId) || this.packs.some(p=>p.examId===examId);}
  async json(file) {
    const response=await this.request(file.url,{credentials:'same-origin',redirect:'error',signal:AbortSignal.timeout(30000)});
    if(!response.ok) throw new Error('教材を取得できません。通信・ログインを確認して再試行してください。');
    const raw=await response.text();
    if(file.sha256) {
      const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw))),v=>v.toString(16).padStart(2,'0')).join('');
      if(hash!==file.sha256) throw new Error('教材が更新されています。ページを再読み込みしてください。');
    }
    return JSON.parse(raw);
  }
  async once(key,task) {
    if(this.pending.has(key)) return this.pending.get(key);
    const promise=task();this.pending.set(key,promise);
    try {return await promise;} finally {this.pending.delete(key);}
  }
  async loadIndex(examId) {
    if(this.indexed.has(examId)) return;
    const manifest=this.manifests.find(p=>p.examId===examId);
    if(!manifest) {this.indexed.add(examId);return;}
    await this.once('index:'+examId,async()=>{
      const data=await this.json(manifest),keys=new Set();
      if(!Array.isArray(data.index) || data.index.length!==manifest.count || !Array.isArray(data.packs)) throw new Error('教材索引の件数が不正です');
      if(data.defaults!==undefined && (!data.defaults || typeof data.defaults!=='object' || Array.isArray(data.defaults))) throw new Error('教材索引の共通項目が不正です');
      data.index=data.index.map(q=>({...data.defaults,...q}));
      for(const p of data.packs) if(p.examId!==examId || !/^material\/[a-zA-Z0-9_.-]+\.json$/.test(p.url) || !Number.isSafeInteger(p.count) || p.count<1 || p.count>2000) throw new Error('教材索引の参照が不正です');
      const urls=new Set(data.packs.map(p=>p.url));
      for(const q of data.index) {
        if(q.examId!==examId || typeof q.id!=='string' || !q.id || q.id.length>120 || q.id.includes('::') || !['single','multiple','written','essay'].includes(q.type) || !Array.isArray(q.options) || q.options.length>26 || !q.catalogOnly || !urls.has(q.packUrl) || keys.has(questionKey(q))) throw new Error('教材索引の問題が不正です');
        keys.add(questionKey(q));
      }
      for(const p of data.packs) if(data.index.filter(q=>q.packUrl===p.url).length!==p.count) throw new Error('教材索引の対応が不正です');
      this.base.push(...data.index);this.packs.push(...data.packs);indexQuestions(this.base);this.indexed.add(examId);
    });
  }
  async prepareState(state) {
    if(!state || typeof state!=='object') return;
    const exams=new Set();
    for(const key of Object.keys(state.stats || {})) exams.add(key.includes('::')?key.split('::')[0]:'gken');
    for(const q of Array.isArray(state.custom)?state.custom:[]) exams.add(q.examId || 'gken');
    for(const h of Array.isArray(state.history)?state.history:[]) exams.add(h.examId || 'gken');
    if(state.session) exams.add(state.session.examId || 'gken');
    for(const examId of exams) await this.loadIndex(examId);
  }
  needed(examId,filters={},keys=null) {
    const selected=this.base.filter(q=>q.examId===examId && (!keys || keys.has(questionKey(q))) && Object.entries(filters).every(([k,v])=>!v || q[k]===v));
    const urls=new Set(selected.map(q=>q.packUrl));
    return this.packs.filter(p=>p.examId===examId && (!selected.every(q=>q.packUrl) || urls.has(p.url)));
  }
  available(examId,filters={},keys=null) {return this.indexed.has(examId) && this.needed(examId,filters,keys).every(p=>this.ready.has(p.url));}
  async load(examId,filters={},keys=null,onProgress=()=>{}) {
    await this.loadIndex(examId);
    const packs=this.needed(examId,filters,keys),total=packs.length;let done=0;
    const report=()=>{this.progress.set(examId,{done,total});onProgress({done,total});};report();
    // Four requests at a time; reuse completed packs after a failed request.
    let cursor=0;
    const worker=async()=>{while(cursor<packs.length) {
      const pack=packs[cursor++];
      if(!this.ready.has(pack.url)) await this.once('pack:'+pack.url,async()=>{
        const rows=validateQuestions(await this.json(pack),[],false,examId);
        const byId=new Map(rows.map(q=>[questionKey(q),q]));
        const expected=this.base.filter(q=>q.examId===examId && (q.packUrl?q.packUrl===pack.url:byId.has(questionKey(q))));
        if(rows.length!==pack.count || expected.length!==rows.length || expected.some(q=>{const r=byId.get(questionKey(q));return !r || r.type!==q.type || r.options.length!==q.options.length;})) throw new Error('教材と索引の対応が不正です。');
        for(let i=0;i<this.base.length;i++) {const row=byId.get(questionKey(this.base[i]));if(row) this.base[i]={...row,packUrl:pack.url};}
        indexQuestions(this.base);this.ready.add(pack.url);
      });
      done++;report();
    }};
    const results=await Promise.allSettled(Array.from({length:Math.min(4,total)},worker));
    const failure=results.find(r=>r.status==='rejected');if(failure) throw failure.reason;
    if(this.packs.filter(p=>p.examId===examId).every(p=>this.ready.has(p.url))) this.loaded.add(examId);
  }
  counts(custom=[]) {
    const out=Object.create(null),map=questionIndex(this.base);
    for(const p of this.manifests.length?this.manifests:this.packs) out[p.examId]=(out[p.examId] || 0)+p.count;
    for(const q of custom) if(!map.has(questionKey(q))) out[q.examId]=(out[q.examId] || 0)+1;
    return out;
  }
}
