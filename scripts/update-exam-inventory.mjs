import assert from 'node:assert/strict';
import {existsSync,readFileSync,writeFileSync} from 'node:fs';
import {EXAM_CATALOG,groupExams,examSource} from '../web/exams.mjs';
import {DEFAULT_EXAMS} from '../web/core.mjs';
import {createHash} from 'node:crypto';

const root=new URL('../',import.meta.url),privateManifest=new URL('build/private/manifest.json',root);
const material=existsSync(privateManifest)?JSON.parse(readFileSync(privateManifest,'utf8')):null;
const exams=new Map([...DEFAULT_EXAMS,...EXAM_CATALOG].map(e=>[e.id,{...e,count:0}]));
const imported=new Map(),origins=new Map();
if(material) {
  const {MATERIAL_EXAMS,MATERIAL_INDEX,MATERIAL_PACKS}=await import('../build/private/web/catalog.mjs');
  for(const e of MATERIAL_EXAMS) exams.set(e.id,{...e,count:0});
  const keys=new Set();
  for(const pack of MATERIAL_PACKS) {
    const bytes=readFileSync(new URL('build/private/web/'+pack.url,root));
    assert.equal(createHash('sha256').update(bytes).digest('hex'),pack.sha256,'Changed pack '+pack.id);
    const rows=JSON.parse(bytes);assert.equal(rows.length,pack.count);
    const origin=pack.id.startsWith('school-extra-') && pack.origin!=='original'?'学校向け外部教材（正答未独立照合）':pack.repo?'GitHub候補教材':pack.id.startsWith('medical-jmed-')?'外部公開過去問（JMed48k・正答未独立照合）':pack.id.startsWith('archive-')?'公式原本追加教材':'既存・自作・復帰教材';
    origins.set(origin,(origins.get(origin)||0)+rows.length);
    if(pack.repo) imported.set(pack.repo.toLowerCase(),(imported.get(pack.repo.toLowerCase())||0)+rows.length);
    for(const q of rows) {
      const key=q.examId+'::'+q.id;assert.ok(!keys.has(key),'Duplicate '+key);keys.add(key);
      assert.ok(exams.has(q.examId),'Unknown exam '+q.examId);exams.get(q.examId).count++;
    }
  }
  assert.equal(keys.size,MATERIAL_INDEX.length);assert.equal(keys.size,material.questions);
  assert.equal(new Set(MATERIAL_INDEX.map(q=>q.examId+'::'+q.id)).size,keys.size,'Duplicate index entry');
  for(const q of MATERIAL_INDEX) assert.ok(keys.has(q.examId+'::'+q.id),'Index entry missing from packs');
  assert.deepEqual(MATERIAL_PACKS,material.packs,'Build catalog and manifest differ');
  for(const e of material.exams) assert.equal(exams.get(e.id).count,e.count);
}
const rows=[...exams.values()],grouped=groupExams(rows),total=rows.reduce((n,e)=>n+e.count,0);
const date=new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Tokyo'}).format(new Date());
const escape=value=>String(value).replaceAll('|','\\|');
const searchFile=new URL('docs/github-exam-search.json',root);
const search=existsSync(searchFile)?JSON.parse(readFileSync(searchFile,'utf8')):{version:1,exams:[]};
assert.equal(search.version,1);
const searchStates={'not-found':'検索済み・候補未発見',review:'検索済み・要精査',candidate:'候補あり・本文未確認',held:'既存候補保留',blocked:'検索未確認',confirmed:'問題本文確認済み'};
const searched=new Map();
for(const record of search.exams) {
  assert.ok(exams.has(record.examId),'Unknown search exam '+record.examId);
  assert.ok(!searched.has(record.examId),'Duplicate search exam '+record.examId);
  assert.ok(record.history.length,'Empty search history '+record.examId);
  for(const h of record.history) {
    assert.ok(searchStates[h.status],'Unknown search status '+h.status);
    assert.match(h.date,/^\d{4}-\d{2}-\d{2}$/);
    assert.ok(h.queries.length && h.queries.every(q=>typeof q==='string' && q.trim()),'Missing search query');
    for(const url of [...h.results,...(h.source?[h.source]:[])]) assert.match(url,/^https:\/\/(github\.com|gist\.github\.com)\//);
  }
  searched.set(record.examId,record.history.at(-1));
}
const pending=rows.filter(e=>!e.count && (!searched.has(e.id)||searched.get(e.id).status==='blocked'));
const searchLines=['# 問題未登録試験のGitHub調査台帳','',`集計日：${date}（日本時間）。現在の問題未登録は${rows.filter(e=>!e.count).length}試験。未調査・検索未確認は${pending.length}試験。`,'',
  '正本は [調査データ](github-exam-search.json)。試験IDごとに検索日・検索語・結果URL・判定を履歴として保存します。この文書は `npm run inventory:exams` で生成します。登録数は [試験管理表](exam-inventory.md) と同じビルドです。','',
  '## 再調査を避ける運用','',
  '1. 次回は下の「未調査・検索未確認」だけを検索します。「候補未発見」は通常の検索対象から外します。期限で自動的に未調査へ戻しません。',
  '2. 「要精査」「候補あり」は保存済みURLを確認します。試験・級の一致、設問本文、正答、利用条件の確認を進め、新規検索を繰り返しません。',
  '3. 新しい候補の情報、提供元の修正、明示的な再調査依頼があるときだけ再調査します。以前の履歴を消さず、理由をnoteへ記載してhistoryに追記します。',
  '4. 新しい試験は記録がなければ自動的に未調査になります。登録後もJSONの調査履歴は保持します。生成処理は検索や問題取得を実行しません。','',
  '## 判定の意味','',
  '「候補未発見」は記録したWeb検索の範囲で見つからなかった意味です。GitHubに存在しないという断定ではありません。検索結果は書誌・資格一覧・別試験などを含みます。「要精査」は結果URLがあるだけで、問題データ発見の判定ではありません。「候補あり」も本文・正答・収録許諾の確認完了ではありません。2026-10-07の調査は正式名称を中心に268試験を一次検索し、一部は級を外した名称でも検索しました。追加検索語と結果はJSONのfamilySearchesへ保存しています。全ファイルの検査や問題登録は行っていません。','',
  '既存候補の取得・変換・保留理由は [取り込み状況](import-status.md) と [候補調査記録](github-candidates.md) を参照します。級未確定の既存候補は各級の発見済み記録へ一律に転記しません。','',
  '## 調査状態の集計','', '| 状態 | 試験数 |', '| --- | ---: |',
  ...Object.entries(searchStates).map(([key,label])=>`| ${label} | ${rows.filter(e=>!e.count && searched.get(e.id)?.status===key).length} |`),
  `| 未調査 | ${rows.filter(e=>!e.count && !searched.has(e.id)).length} |`, '',
  '## 未調査・検索未確認','',...pending.map(e=>`- ${escape(e.name)}（${e.id}）`),...(pending.length?[]:['なし。']),
  '', '## 現在の問題未登録試験','', '| 試験 | ID | 調査状態 | 最終検索日 | 検索語 | 結果・次の作業 |', '| --- | --- | --- | --- | --- | --- |'];
for(const e of rows.filter(e=>!e.count)) {
  const h=searched.get(e.id);
  searchLines.push(`| ${escape(e.name)} | ${e.id} | ${h?searchStates[h.status]:'未調査'} | ${h?.date||'—'} | ${escape(h?.queries.join(' / ')||'—')} | ${h?`${h.source?`[確認先](${h.source}) / `:''}${escape(h.note)} / [結果URL・履歴](github-exam-search.json)`:'次回の検索対象'} |`);
}
const lines=['# 試験管理表','',`集計日：${date}（日本時間）。${EXAM_CATALOG.length}試験の登録先、既存の自作教材を含め${rows.length}試験・教材、${grouped.size}カテゴリ、登録問題合計${total.toLocaleString('ja-JP')}問。`,'',
  '級・種別は別の登録先として扱い、年度・科目は問題側で管理します。「問題未登録」は登録先だけ準備した状態です。収録内容と取得元は [GitHub経由の過去問収録](github-material.md) と [本人用教材の管理](private-material.md) を参照してください。全試験の出題範囲や本番形式への対応を意味しません。音声・面接・実技の本番再現や公式スコア換算は対象外です。','',
  material?'登録数はローカル本人用ビルドの各問題ファイルから再集計した値です。クラウド配備版やブラウザ内の個別持込問題は含みません。アプリの「試験管理表」はその環境の配布教材と持込問題を集計します。':'本人用ビルドがないため、公開版の問題未登録状態を集計しています。','',
  '行政書士・第二種衛生管理者・日本農業検定3級の既存自作対策教材は、従来のIDと教材名のまま別行で保持します。新しい試験の登録先へ自動移動・二重計上していません。','',
  '公式案内は試験情報の参照先です。過去問の有無や転載・収録許諾の確認状況を示すものではありません。問題登録時に年度・出題範囲・利用条件を確認してください。試験数の固定上限はありません。GitHubの検索済み・候補未発見・次の確認対象は [GitHub調査台帳](github-exam-search.md) で管理します。','',
  '自動生成文書です。直接編集せず `npm run inventory:exams` で更新します。同時に [取り込み状況](import-status.md) を生成します。登録先の定義は `web/exams.mjs`、登録数の正本は実際の問題ファイルです。文書の役割と更新手順は [docs案内](README.md) を参照してください。','',
  '## カテゴリ別集計','','| カテゴリ | 試験・教材数 | 登録あり | 問題未登録 | 登録問題数 |','| --- | ---: | ---: | ---: | ---: |'];
for(const [field,items] of grouped) lines.push(`| ${escape(field)} | ${items.length} | ${items.filter(e=>e.count).length} | ${items.filter(e=>!e.count).length} | ${items.reduce((n,e)=>n+e.count,0)} |`);
for(const [field,items] of grouped) {
  lines.push('',`## ${field}`,'','| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |','| --- | --- | ---: | --- | --- |');
  for(const e of items) lines.push(`| ${escape(e.name)} | ${e.id} | ${e.count} | ${e.count?'登録あり':'問題未登録'} | ${examSource(e)?`[公式案内](${examSource(e)})`:'—'} |`);
}
const status=['# 教材の取り込み状況','',`集計日：${date}（日本時間）。[試験管理表](exam-inventory.md) と同じローカル本人用ビルドから自動生成します。直接編集しません。`,'',
  '件数は重複除外後にビルドへ収録された問題数です。取得ファイル数・変換候補数とは区別します。クラウド配備・内容検証の合否を示す表ではありません。ビルド後に `npm run inventory:exams` で両文書を更新してください。','',
  '## 収録元別（重複なく合計）','','| 収録元 | 登録問題数 |','| --- | ---: | ---: |'];
for(const [origin,count] of origins) status.push(`| ${origin} | ${count} |`);
status.push(`| **合計** | **${total}** |`,'','公式原本追加教材にはJLPTを含みます。JLPTの件数をこの合計へ再加算しません。既存教材にはFP・IPA・自作教材などを含みます。年度違いの再出題や試験別の共通午前Ⅰは別の出題として数えます。意味が近い問題の全面的な除去は保証しません。');
if(!material) status.push('','本人用ビルドがないため、取り込み状況は未確認です。0問は取得元に問題がないことを意味しません。');
const reportFile=new URL('private-data/github-candidates/prepared/report.json',root);
if(material && existsSync(reportFile)) {
  const report=JSON.parse(readFileSync(reportFile,'utf8')),seen=new Set();
  status.push('','## GitHub候補ごとの収録状況','','変換時の非収録理由はローカルの `private-data/github-candidates/prepared/report.json` が正本です。下表の登録数はビルド結果です。変換記録は収録数の合計へ加算しません。全件の内容検証・利用条件確認の完了を意味しません。','','| 取得元 | ビルド登録数 | 状態 | 変換時の非収録理由 |','| --- | ---: | --- | --- |');
  for(const r of report.repositories) {
    const key=r.repo.toLowerCase();assert.ok(!seen.has(key),'Duplicate repository '+key);seen.add(key);
    const count=imported.get(key)||0;
    const reasons=Object.entries(r.excluded).map(([reason,n])=>`${reason}（${n}件）`).join(' / ')||'なし';
    status.push(`| [${escape(r.repo)}](https://github.com/${r.repo}/tree/${r.commit}) | ${count} | ${count?'収録あり':'未収録'} | ${escape(reasons)} |`);
  }
  for(const key of imported.keys()) assert.ok(seen.has(key),'Repository missing from conversion report '+key);
  const built=new Map(material.packs.map(p=>[p.id,p]));
  for(const p of report.packs) {
    const b=built.get(p.id);
    if(b) assert.ok(b.count<=p.count,'Build count exceeds converted candidate count');
  }
  status.push('','非収録理由は変換時点の記録です。公式原本から別経路で収録できた場合も、この取得元の未収録状態とは区別します（例：GitHubのJLPT OCR候補とJLPT公式教材）。');
}
status.push('','## 詳細・検証記録','','- [本人用教材の管理](private-material.md)：保存・再生成・互換性。','- [公式原本追加の記録](github-material.md)、[GitHub候補取り込みの記録](github-import-results.md)、[JLPTの利用・検査](jlpt-import.md)。','- [取得元の管理](github-sources.md)：ファイル再取得の防止。候補調査は [調査記録](github-candidates.md)。','- [docs案内](README.md)：管理元・重複の扱い・更新手順。');
writeFileSync(new URL('docs/exam-inventory.md',root),lines.join('\n')+'\n');
writeFileSync(new URL('docs/import-status.md',root),status.join('\n')+'\n');
writeFileSync(new URL('docs/github-exam-search.md',root),searchLines.join('\n')+'\n');
console.log(`Inventory: ${rows.length} exams/materials, ${grouped.size} categories, ${total} questions`);
