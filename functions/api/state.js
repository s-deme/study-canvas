import {validateState,indexQuestions} from '../../web/core.mjs';

import {BUILTIN_QUESTIONS,MATERIAL_INDEX} from '../../web/catalog.mjs';
const base = [...BUILTIN_QUESTIONS,...MATERIAL_INDEX];
indexQuestions(base);
const MAX_BYTES = 10 * 1024 * 1024;
const json = (value,status=200) => Response.json(value,{status});

export async function onRequestGet({env}) {
  try {
    // One transaction reads the revision and all chunks from the same snapshot.
    const [head, chunks] = await env.DB.batch([
      env.DB.prepare('SELECT revision, mutation_id, updated_at FROM sync_head WHERE id = 1'),
      env.DB.prepare('SELECT content FROM sync_chunks ORDER BY position')
    ]);
    const row = head.results[0];
    if (!row) throw new Error('schema');
    const state = row.revision ? validateState(JSON.parse(chunks.results.map(r => r.content).join('')),base) : null;
    return json({revision:row.revision, mutationId:row.mutation_id, updatedAt:row.updated_at, state});
  } catch {
    return json({error:'クラウドの記録を読み込めません。端末の記録は保持しています'},503);
  }
}

export async function onRequestPut({env,request}) {
  if (!request.headers.get('Content-Type')?.startsWith('application/json')) return json({error:'JSONで送信してください'},415);
  if (Number(request.headers.get('Content-Length')) > MAX_BYTES + 2048) return json({error:'記録は10MB以内にしてください'},413);
  let input;
  try {
    // Bound streamed requests too, even when Content-Length is absent.
    const reader = request.body?.getReader();
    if (!reader) throw new Error();
    const parts=[]; let size=0;
    while (true) {
      const {done,value}=await reader.read(); if (done) break;
      size += value.byteLength;
      if (size > MAX_BYTES + 2048) { await reader.cancel(); return json({error:'記録は10MB以内にしてください'},413); }
      parts.push(value);
    }
    const bytes=new Uint8Array(size); let offset=0;
    for (const part of parts) { bytes.set(part,offset); offset+=part.byteLength; }
    input=JSON.parse(new TextDecoder('utf-8',{fatal:true}).decode(bytes));
  } catch { return json({error:'送信データの形式が不正です'},400); }
  let serialized;
  try {
    if (!Number.isSafeInteger(input.revision) || input.revision < 0 || input.revision >= Number.MAX_SAFE_INTEGER || typeof input.mutationId!=='string' || !/^[a-z0-9-]{16,80}$/i.test(input.mutationId)) throw new Error();
    serialized=JSON.stringify(validateState(input.state,base));
    if (new TextEncoder().encode(serialized).length > MAX_BYTES) return json({error:'記録は10MB以内にしてください'},413);
  } catch { return json({error:'学習記録の形式が不正です'},400); }
  try {
    const expected=input.revision;
    const statements=[env.DB.prepare('DELETE FROM sync_chunks WHERE EXISTS (SELECT 1 FROM sync_head WHERE id = 1 AND revision = ?)').bind(expected)];
    // D1 rows have a 2 MB limit. 256K UTF-16 units keep each chunk below 1 MB.
    // At 10 MB, this transaction stays below the Free plan's 50-query limit.
    let position=0;
    for (let offset=0; offset<serialized.length;) {
      let end=Math.min(offset+256*1024,serialized.length);
      if (end<serialized.length && /[\uD800-\uDBFF]/.test(serialized[end-1])) end--;
      statements.push(env.DB.prepare('INSERT INTO sync_chunks (position, content) SELECT ?, ? WHERE EXISTS (SELECT 1 FROM sync_head WHERE id = 1 AND revision = ?)').bind(position++,serialized.slice(offset,end),expected));
      offset=end;
    }
    const updatedAt=Date.now();
    statements.push(env.DB.prepare('UPDATE sync_head SET revision = revision + 1, mutation_id = ?, updated_at = ? WHERE id = 1 AND revision = ?').bind(input.mutationId,updatedAt,expected));
    const result=await env.DB.batch(statements);
    if (result.at(-1).meta.changes !== 1) return json({error:'別の端末で記録が更新されています'},409);
    return json({revision:expected+1, mutationId:input.mutationId, updatedAt});
  } catch { return json({error:'クラウドに保存できません。端末の記録は保持しています'},503); }
}
