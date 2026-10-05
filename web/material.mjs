import {questionKey,validateQuestions} from './core.mjs';

// Keep loading separate from persisted state; failed fetches never overwrite records.
export class MaterialLibrary {
  constructor(index,packs,request=(...args)=>fetch(...args)) {this.base=index.map(q=>({...q}));this.packs=packs;this.request=request;this.loaded=new Set();this.pending=new Map();}
  has(examId) {return this.packs.some(p=>p.examId===examId);}
  async load(examId) {
    if(this.loaded.has(examId)) return;
    if(this.pending.has(examId)) return this.pending.get(examId);
    const promise=(async()=>{
      const packs=this.packs.filter(p=>p.examId===examId), rows=[];
      for(const pack of packs) {
        const response=await this.request(pack.url,{credentials:'same-origin',redirect:'error',signal:AbortSignal.timeout(30000)});
        if(!response.ok) throw new Error('教材を取得できません。通信・ログインを確認して再試行してください。');
        const raw=await response.text();
        if(pack.sha256) {const hash=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(raw))),v=>v.toString(16).padStart(2,'0')).join('');if(hash!==pack.sha256) throw new Error('教材が更新されています。ページを再読み込みしてください。');}
        const checked=validateQuestions(JSON.parse(raw),rows,false,examId);
        if(checked.length!==pack.count) throw new Error('教材の件数が索引と一致しません。再読み込みしてください。');
        rows.push(...checked);
      }
      const expected=this.base.filter(q=>q.examId===examId), byId=new Map(rows.map(q=>[questionKey(q),q]));
      if(expected.length!==rows.length || expected.some(q=>{const r=byId.get(questionKey(q));return !r || r.type!==q.type || r.options.length!==q.options.length;})) throw new Error('教材と索引の対応が不正です。');
      for(let i=0;i<this.base.length;i++) if(this.base[i].examId===examId) this.base[i]=byId.get(questionKey(this.base[i]));
      this.loaded.add(examId);
    })();
    this.pending.set(examId,promise);
    try {await promise;} finally {this.pending.delete(examId);}
  }
}
