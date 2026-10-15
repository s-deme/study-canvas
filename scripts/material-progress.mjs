import {fieldStatus,sha} from './material-transcription.mjs';

export const imageKinds={original:'保持中の元画像',figureCandidate:'図の切り抜き候補（自動判定・未確認）',unreadableText:'未判読文字の切り抜き',unknownCrop:'用途未確定・混在の切り抜き'};
const usable=(q,f)=>['unreviewed-text','source-verified','not-applicable'].includes(fieldStatus(q,f));
export function questionProgress(q,excluded=false) {
  const textReady=usable(q,'prompt') && usable(q,'options') && !/判読保留|組版照合待ち/.test(q.prompt+q.options.join(''));
  return {excluded,images:q.images.map(i=>i.src),solutionImages:q.solutionImages.map(i=>i.src),textReady,
    textHash:sha(JSON.stringify([q.prompt,q.options,q.passage])),solutionHash:sha(JSON.stringify([q.modelAnswer,q.explanation,q.evaluationGuide])),
    solutionText:['modelAnswer','explanation','evaluationGuide'].some(f=>q[f] && usable(q,f)),
    sourceVerified:['prompt','options','passage'].every(f=>['source-verified','not-applicable'].includes(fieldStatus(q,f)))};
}

export function summarizeImages(rows,assets,cropSources) {
  const kinds=Object.fromEntries(Object.keys(imageKinds).map(k=>[k,{images:0,references:0,bytes:0}]));
  const unresolved={};
  for(const asset of assets.values()) {
    const uses=asset.references.map(i=>rows[i]),purposes=new Set(uses.map(r=>r.purpose));
    asset.kind=uses[0].origin==='original'?'original':purposes.size===1?uses[0].purpose:'unknownCrop';
    asset.parentImages=[...(cropSources.get(asset.src)?.parents || [])];
    asset.visualReview='not established by inventory';
    const count=kinds[asset.kind];count.images++;count.references+=uses.length;count.bytes+=asset.bytes;
  }
  for(const reason of ['文字コード・組版','OCR・原本照合待ち','問題範囲未確定','原本対応なし']) {
    const matching=rows.filter(r=>r.unresolved.includes(reason));
    unresolved[reason]={questions:new Set(matching.map(r=>r.key)).size,images:new Set(matching.map(r=>r.src)).size,references:matching.length};
  }
  const generated=[...cropSources.keys()],used=generated.filter(src=>assets.has(src));
  const coexistingParents=new Set(used.flatMap(src=>[...(cropSources.get(src).parents || [])]).filter(src=>assets.has(src)));
  return {kinds,unresolved,generatedCrops:generated.length,referencedGeneratedCrops:used.length,unusedGeneratedCrops:generated.length-used.length,coexistingParentImages:coexistingParents.size,
    storage:{scope:'原本保管領域全体・過去ビルドは未集計。以下は現在の問題が参照する画像と、このビルドの生成候補のみ。',archivePDFs:null,archiveImages:null}};
}

export function compareProgress(current,previous=null) {
  const changes={fullyText:[],partialText:[],restored:[],solutionUpdated:[],solutionImagesRemoved:[],solutionFullyText:[],addedQuestions:[],removedQuestions:[]};
  const quality={textReady:0,textOnly:0,sourceVerified:0,excludedOriginalQuestions:0,eligibleQuestions:0};
  for(const q of current.states.values()) {
    if(q.excluded) {quality.excludedOriginalQuestions++;continue;}
    quality.eligibleQuestions++;
    if(q.textReady) quality.textReady++;
    if(q.textReady && !q.images.length) quality.textOnly++;
    if(q.sourceVerified) quality.sourceVerified++;
  }
  if(!previous) return {baseline:null,comparable:false,changes:null,images:null,quality};
  for(const [key,q] of current.states) {
    const before=previous.states.get(key);
    if(!before) {changes.addedQuestions.push(key);continue;}
    if(q.excluded || before.excluded) continue;
    const fullyText=q.textReady && !q.images.length;
    if(fullyText && !(before.textReady && !before.images.length)) changes.fullyText.push(key);
    if(q.images.length && before.images.length && q.textHash!==before.textHash && usableState(q)) changes.partialText.push(key);
    if(!before.images.length && q.images.length) changes.restored.push(key);
    if(q.solutionHash!==before.solutionHash) changes.solutionUpdated.push(key);
    if(before.solutionImages.some(src=>!q.solutionImages.includes(src))) changes.solutionImagesRemoved.push(key);
    if(before.solutionImages.length && !q.solutionImages.length && q.solutionText) changes.solutionFullyText.push(key);
  }
  for(const key of previous.states.keys()) if(!current.states.has(key)) changes.removedQuestions.push(key);
  const added=[...current.assets.keys()].filter(src=>!previous.assets.has(src)),removed=[...previous.assets.keys()].filter(src=>!current.assets.has(src));
  return {baseline:previous.summary.source,comparable:true,changes,images:{added,removed,net:added.length-removed.length},quality};
}
// A changed text with retained images is an update, not proof of completed transcription.
const usableState=q=>q.textReady || q.images.some(src=>src.startsWith('assets/transcription/'));

export function progressMarkdown(report) {
  const {current,previous,comparison:c}=report,number=v=>v==null?'比較不可':v.toLocaleString('en-US');
  const lines=['# 文字化の進捗報告','',`対象ビルド: ${current.source}`,`比較元: ${c.baseline || 'なし（比較不可）'}`,'',
    '## 今回の変化（問題ID単位）','', '| 指標 | 今回 |','| --- | ---: |'];
  for(const [key,label] of Object.entries({fullyText:'新たに問題文・選択肢が文字になり問題画像がなくなった',partialText:'部分文字化・文字更新（問題画像あり）',restored:'問題画像を復元（前回は画像なし）',solutionUpdated:'回答・解説の文字更新',solutionImagesRemoved:'回答・解説画像の除去・置換',solutionFullyText:'回答・解説画像がなくなり文字を保持',addedQuestions:'対象問題の追加（成果に含めない）',removedQuestions:'対象問題の削除（成果に含めない）'})) lines.push(`| ${label} | ${number(c.changes?.[key].length)} 問 |`);
  lines.push('','各指標は重複するため合計しない。文字化・文字更新は原本照合完了を意味しない。','','## 現在参照する画像','', '| 種類 | 前回（画像） | 今回（画像） | 増減（画像） | 今回（参照） | 今回（bytes） |','| --- | ---: | ---: | ---: | ---: | ---: |');
  for(const [key,label] of Object.entries(imageKinds)) {
    const now=current.breakdown.kinds[key],before=previous?.breakdown.kinds[key];
    lines.push(`| ${label} | ${number(before?.images)} | ${number(now.images)} | ${number(before?now.images-before.images:null)} | ${number(now.references)} | ${number(now.bytes)} |`);
  }
  lines.push(`| 合計 | ${number(previous?.uniqueImages)} | ${number(current.uniqueImages)} | ${number(c.images?.net)} | ${number(current.imageReferences)} | ${number(Object.values(current.breakdown.kinds).reduce((n,k)=>n+k.bytes,0))} |`, '',
    `画像URLの追加 ${number(c.images?.added.length)} 画像／除去 ${number(c.images?.removed.length)} 画像。1枚から複数の切り抜きができるため、画像数の増加は進捗の後退を意味しない。`,
    `切り抜きと併存する親画像: ${number(current.breakdown.coexistingParentImages)} 画像（証跡で対応が分かる範囲。併存だけで不要とは判定しない）。`,
    '元画像は文字化処理前からあるページ・設問等の画像。画像数はURL単位、参照数は問題・欄ごとの利用回数。保管領域全体や配信パッケージ全体の容量ではない。','',
    '## 未解決の内容（重複あり・合計不可）','','| 理由 | 対象問題 | 画像 | 参照 |','| --- | ---: | ---: | ---: |');
  for(const [reason,n] of Object.entries(current.breakdown.unresolved)) lines.push(`| ${reason==='原本対応なし'?'原本対応なし（原本PDFへの対応情報なし）':reason} | ${number(n.questions)} 問 | ${number(n.images)} 画像 | ${number(n.references)} 参照 |`);
  lines.push('','## 保管・生成候補・確認品質','',
    `- 現在参照する画像に対応する原本PDF: ${number(current.uniquePDFs)} ファイル。原本保管総数ではない。`,
    '- 原本PDF・画像の保管総数、過去ビルドの容量: 未集計（削除・変更なし）。',
    `- このビルドの生成候補: ${number(current.breakdown.generatedCrops)} 画像。現在参照 ${number(current.breakdown.referencedGeneratedCrops)} 画像／未使用 ${number(current.breakdown.unusedGeneratedCrops)} 画像。未使用候補を残件数に加算しない。`,
    `- 自作問題を除く対象: ${number(c.quality.eligibleQuestions)} 問（除外 ${number(c.quality.excludedOriginalQuestions)} 問）。問題文・選択肢が文字の状態: ${number(c.quality.textReady)} 問、うち問題画像なし: ${number(c.quality.textOnly)} 問。`,
    `- 問題文・選択肢・共通本文の原本照合済み状態が登録されているもの: ${number(c.quality.sourceVerified)} 問。textReview の記録に限定し、別ファイルの目視記録は自動加算しない。自動抽出・OCR成功とは別の指標。`,
    '- 切り抜きの図判定は自動候補。必要性・完全性の目視確認を意味しない。文字状態の判定も既存のラベル・保留マーカーに基づき、全文の正しさを保証しない。',
    '- この台帳は生成済みデータを再集計する。全件目視や本番配備の完了を意味しない。','');
  return lines.join('\n');
}
