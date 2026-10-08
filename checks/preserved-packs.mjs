import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';

export function assertPreservedPacks(manifest,baseline) {
  const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
  let originalAif;
  for(const pack of baseline.packs) {
    const built=manifest.packs.find(p=>p.id===pack.id);assert.ok(built,'Missing pack: '+pack.id);
    const raw=readFileSync(new URL('../build/private/web/'+built.url,import.meta.url));
    assert.equal(hash(raw),built.sha256,'Built pack changed: '+pack.id);
    if(built.sha256!==pack.sha256 && pack.repo==='iamirtasam/AWS-AI-Practitioner-Exam-Mock') {
      // Ordering questions were inserted into the old 500-row chunks; compare all old rows unchanged.
      originalAif ??= manifest.packs.filter(p=>p.repo===pack.repo).flatMap(p=>JSON.parse(readFileSync(new URL('../build/private/web/'+p.url,import.meta.url)))).filter(q=>q.type!=='written');
      const start=(Number(pack.id.split('-').at(-1))-1)*500;
      assert.equal(hash(JSON.stringify(originalAif.slice(start,start+pack.count))),pack.sha256,'Previous AIF questions changed: '+pack.id);
    } else assert.equal(built.sha256,pack.sha256,'Existing pack changed: '+pack.id);
  }
}
