import {KEY,validateState,saveState} from './core.mjs';

export async function cloudRequest(path,options={}) {
  let response;
  try {
    response=await fetch(path,{cache:'no-store',credentials:'same-origin',redirect:'error',signal:AbortSignal.timeout(15000),...options});
  } catch { throw new Error('クラウドに接続できません。通信・ログインを確認して再試行してください'); }
  if (!response.headers.get('Content-Type')?.includes('application/json')) {
    const error=new Error(response.status===404?'同期機能が設定されていません':'ログインし直してから同期してください'); error.status=response.status; throw error;
  }
  const value=await response.json();
  if (!response.ok) {
    const error=new Error(value.error || 'ログインし直してから同期してください'); error.status=response.status; throw error;
  }
  return value;
}

export class CloudSync {
  constructor({storage,base,owner,request=cloudRequest,onState=()=>{},onStatus=()=>{},lock=task=>task(),prepare=async()=>{}}) {
    Object.assign(this,{storage,base,owner,request,onState,onStatus,lock,prepare});
    this.busy=false; this.conflict=false; this.timer=null;
    this.reload();
    if (!this.meta) this.write(this.state,{owner,revision:0,dirty:this.raw!==null,flightId:null});
  }
  reload() {
    const raw=this.storage.getItem(KEY);if(this.raw!==undefined && this.raw===raw) return;
    const input=raw ? JSON.parse(raw) : null;
    const state=validateState(input || {version:1,custom:[],stats:{},daily:{},history:[],session:null},this.base);
    const meta=input?.cloud || null;
    if (meta && (meta.owner!==this.owner || !Number.isSafeInteger(meta.revision) || meta.revision<0 || typeof meta.dirty!=='boolean' || !(meta.flightId===null || typeof meta.flightId==='string'))) {
      throw new Error('同期情報が不正か、別のアカウントの記録です。先にバックアップしてください');
    }
    if (this.raw!==undefined && this.meta && !meta) throw new Error('ブラウザの同期情報が変更されました。ページを再読み込みしてください');
    const changed=this.raw!==undefined && this.raw!==raw;
    this.raw=raw; this.state=state; this.meta=meta;
    if (changed) this.onState(state,raw);
  }
  write(state,meta,notify=true) {
    const raw=saveState(this.storage,{...state,cloud:meta},this.raw);
    this.raw=raw; this.state=state; this.meta=meta;
    if (notify) this.onState(state,raw);
    return raw;
  }
  save(state,expected) {
    if (this.storage.getItem(KEY)!==expected) throw new Error('別のタブで記録が更新されました。ページを再読み込みしてください');
    this.reload();
    const canonical=validateState(state,this.base);
    if (new TextEncoder().encode(JSON.stringify(canonical)).length>10*1024*1024) throw new Error('同期できる記録は10MBまでです。変更は確定していません');
    const raw=this.write(canonical,{...this.meta,dirty:true},false);
    this.status(this.conflict?'conflict':'pending');
    this.schedule();
    return raw;
  }
  status(kind,message='') {
    this.kind=kind;
    this.onStatus({kind,message,dirty:this.meta?.dirty || false});
  }
  schedule() {
    clearTimeout(this.timer);
    this.timer=setTimeout(()=>void this.refresh(),500);
  }
  remote(value) {
    if (!Number.isSafeInteger(value.revision) || value.revision<0 || (value.revision===0)!==(value.state===null) || !(value.mutationId===null || typeof value.mutationId==='string')) throw new Error('クラウドの同期情報が不正です');
    return {...value,state:value.state===null ? null : validateState(value.state,this.base)};
  }
  async refresh() {
    if (this.busy || this.conflict) return;
    this.busy=true; clearTimeout(this.timer); this.status('syncing');
    try {
      await this.lock(async () => {
        await this.prepare(JSON.parse(this.storage.getItem(KEY) || 'null'));
        this.reload();
        const value=await this.request('/api/state');await this.prepare(value.state);
        const remote=this.remote(value);
        await this.prepare(JSON.parse(this.storage.getItem(KEY) || 'null'));
        this.reload();
        // Recover a successful upload whose response was lost, including after reload.
        if (this.meta.flightId && remote.mutationId===this.meta.flightId) {
          this.write(this.state,{...this.meta,revision:remote.revision,flightId:null});
        }
        if (remote.revision!==this.meta.revision) {
          if (this.meta.dirty) {
            this.conflict=true; this.status('conflict','別の端末でも記録が更新されています。端末の記録を書き出してから、クラウドの記録を読み込んでください'); return;
          }
          if (remote.state===null) throw new Error('クラウドの記録が初期化されています。端末の記録をバックアップしてください');
          this.write(remote.state,{owner:this.owner,revision:remote.revision,dirty:false,flightId:null});
        }
        if (!this.meta.dirty) { this.status('synced'); return; }
        const sent=JSON.stringify(this.state), revision=this.meta.revision, mutationId=crypto.randomUUID();
        this.write(this.state,{...this.meta,flightId:mutationId});
        const result=await this.request('/api/state',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision,mutationId,state:this.state})});
        if (result.revision!==revision+1 || result.mutationId!==mutationId) throw new Error('クラウドの保存結果を確認できません。端末の記録は保持しています');
        await this.prepare(JSON.parse(this.storage.getItem(KEY) || 'null'));
        this.reload();
        if (this.meta.revision!==revision || this.meta.flightId!==mutationId) throw new Error('別のタブの同期が進行しています。再試行してください');
        const dirty=JSON.stringify(this.state)!==sent;
        this.write(this.state,{...this.meta,revision:result.revision,flightId:null,dirty});
        this.status(dirty?'pending':'synced');
        if (dirty) this.schedule();
      });
    } catch (error) {
      if (error.status===409) { this.conflict=true; this.status('conflict','別の端末で記録が更新されています。自動上書きを停止しました'); }
      else this.status('error',error.message);
    } finally { this.busy=false; }
  }
  async useRemote(backup) {
    if (this.busy) throw new Error('同期処理が終わってから、もう一度操作してください');
    this.busy=true;
    try {
      await this.lock(async () => {
        const value=await this.request('/api/state');await this.prepare(value.state);
        const remote=this.remote(value);
        if (remote.state===null) throw new Error('クラウドにはまだ記録がありません');
        await this.prepare(JSON.parse(this.storage.getItem(KEY) || 'null'));
        this.reload();
        // Preserve a recoverable copy before explicit conflict resolution.
        await backup(this.state);
        this.write(remote.state,{owner:this.owner,revision:remote.revision,dirty:false,flightId:null});
        this.conflict=false; this.status('synced');
      });
    } finally { this.busy=false; }
  }
}
