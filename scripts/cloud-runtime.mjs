export class CompactQuestionIndex extends Map {
  get(key) {
    const code=super.get(key);
    if(code===undefined) return undefined;
    const split=key.indexOf('::');
    return {id:split<0?key:key.slice(split+2),examId:split<0?'gken':key.slice(0,split),type:['single','multiple','written','essay'][code>>5],options:Array(code&31),catalogOnly:true};
  }
}

export function assetShard(path) {
  let hash=0;
  for(let i=0;i<path.length;i++) hash=(Math.imul(hash,31)+path.charCodeAt(i))|0;
  return (hash>>>0)%64;
}

export async function bundledAsset({request,env}) {
  if(!['GET','HEAD'].includes(request.method)) return new Response('Method not allowed',{status:405});
  const path=new URL(request.url).pathname.slice(1);
  if(!/^assets\/[a-zA-Z0-9_./-]+\.(png|webp|jpg|mp3)$/.test(path) || path.includes('..')) return new Response('Not found',{status:404});
  try {
    const index=await env.ASSETS.fetch(new URL(`/bundles/index-${assetShard(path)}.json`,request.url));
    if(!index.ok) throw new Error('Missing asset index');
    const entry=(await index.json())[path];
    if(!entry) return env.ASSETS.fetch(request);
    const [file,offset,length,type]=entry;
    let start=0,end=length-1,status=200;
    const range=request.headers.get('Range');
    if(range) {
      const match=/^bytes=(\d*)-(\d*)$/.exec(range);
      if(!match || (!match[1]&&!match[2])) return new Response(null,{status:416,headers:{'Content-Range':`bytes */${length}`}});
      start=match[1]?Number(match[1]):Math.max(0,length-Number(match[2]));
      end=match[1]&&match[2]?Math.min(Number(match[2]),end):end;
      if(!Number.isSafeInteger(start)||!Number.isSafeInteger(end)||start>end||start>=length) return new Response(null,{status:416,headers:{'Content-Range':`bytes */${length}`}});
      status=206;
    }
    const headers={'Content-Type':type,'Content-Length':String(end-start+1),'Accept-Ranges':'bytes'};
    if(status===206) headers['Content-Range']=`bytes ${start}-${end}/${length}`;
    if(request.method==='HEAD') return new Response(null,{status,headers});
    const response=await env.ASSETS.fetch(new Request(new URL('/'+file,request.url),{headers:{Range:`bytes=${offset+start}-${offset+end}`}}));
    if(response.status!==200 && response.status!==206) throw new Error('Missing asset bundle');
    const bytes=await response.arrayBuffer();
    const body=response.status===206?bytes:bytes.slice(offset+start,offset+end+1);
    if(body.byteLength!==end-start+1) throw new Error('Incomplete asset bundle');
    return new Response(body,{status,headers});
  } catch {return new Response('教材の画像を取得できません。再試行してください。',{status:503});}
}
