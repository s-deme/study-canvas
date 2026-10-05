import assert from 'node:assert/strict';
import {existsSync,readFileSync,writeFileSync} from 'node:fs';
import {EXAM_CATALOG,groupExams,examSource} from '../web/exams.mjs';
import {DEFAULT_EXAMS} from '../web/core.mjs';

const root=new URL('../',import.meta.url),privateManifest=new URL('build/private/manifest.json',root);
const material=existsSync(privateManifest)?JSON.parse(readFileSync(privateManifest,'utf8')):null;
const exams=new Map([...DEFAULT_EXAMS,...EXAM_CATALOG].map(e=>[e.id,{...e,count:0}]));
if(material) {
  const {MATERIAL_EXAMS,MATERIAL_INDEX,MATERIAL_PACKS}=await import('../build/private/web/catalog.mjs');
  for(const e of MATERIAL_EXAMS) exams.set(e.id,{...e,count:0});
  const keys=new Set();
  for(const pack of MATERIAL_PACKS) {
    const rows=JSON.parse(readFileSync(new URL('build/private/web/'+pack.url,root),'utf8'));assert.equal(rows.length,pack.count);
    for(const q of rows) {
      const key=q.examId+'::'+q.id;assert.ok(!keys.has(key),'Duplicate '+key);keys.add(key);
      assert.ok(exams.has(q.examId),'Unknown exam '+q.examId);exams.get(q.examId).count++;
    }
  }
  assert.equal(keys.size,MATERIAL_INDEX.length);assert.equal(keys.size,material.questions);
  for(const e of material.exams) assert.equal(exams.get(e.id).count,e.count);
}
const rows=[...exams.values()],grouped=groupExams(rows),total=rows.reduce((n,e)=>n+e.count,0);
const date=new Intl.DateTimeFormat('sv-SE',{timeZone:'Asia/Tokyo'}).format(new Date());
const escape=value=>String(value).replaceAll('|','\\|');
const lines=['# 試験管理表','',`集計日：${date}（日本時間）。${EXAM_CATALOG.length}試験の登録先、既存の自作教材を含め${rows.length}試験・教材、${grouped.size}カテゴリ、登録問題合計${total.toLocaleString('ja-JP')}問。`,'',
  '級・種別は別の登録先として扱い、年度・科目は問題側で管理します。「問題未登録」は登録先だけ準備した状態です。今回の試験追加では問題を作成・収録していません。全試験の出題範囲や本番形式への対応を意味しません。音声・面接・実技の本番再現や公式スコア換算は対象外です。','',
  material?'登録数はローカル本人用ビルドの各問題ファイルから再集計した値です。クラウド配備版やブラウザ内の個別持込問題は含みません。アプリの「試験管理表」はその環境の配布教材と持込問題を集計します。':'本人用ビルドがないため、公開版の問題未登録状態を集計しています。','',
  '行政書士・第二種衛生管理者・日本農業検定3級の既存自作対策教材は、従来のIDと教材名のまま別行で保持します。新しい試験の登録先へ自動移動・二重計上していません。','',
  '公式案内は試験情報の参照先です。過去問の有無や転載・収録許諾の確認状況を示すものではありません。問題登録時に年度・出題範囲・利用条件を確認してください。試験数の固定上限はありません。','',
  '更新：`node scripts/update-exam-inventory.mjs`。登録先の定義は `web/exams.mjs`、登録数の正本は実際の問題ファイルです。','',
  '## カテゴリ別集計','','| カテゴリ | 試験・教材数 | 登録あり | 問題未登録 | 登録問題数 |','| --- | ---: | ---: | ---: | ---: |'];
for(const [field,items] of grouped) lines.push(`| ${escape(field)} | ${items.length} | ${items.filter(e=>e.count).length} | ${items.filter(e=>!e.count).length} | ${items.reduce((n,e)=>n+e.count,0)} |`);
for(const [field,items] of grouped) {
  lines.push('',`## ${field}`,'','| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |','| --- | --- | ---: | --- | --- |');
  for(const e of items) lines.push(`| ${escape(e.name)} | ${e.id} | ${e.count} | ${e.count?'登録あり':'問題未登録'} | ${examSource(e)?`[公式案内](${examSource(e)})`:'—'} |`);
}
writeFileSync(new URL('docs/exam-inventory.md',root),lines.join('\n')+'\n');
console.log(`Inventory: ${rows.length} exams/materials, ${grouped.size} categories, ${total} questions`);
