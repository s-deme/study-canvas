# 会計・金融の過去問取り込み

調査日：2026-10-07（日本時間）。現在の登録数は [試験管理表](exam-inventory.md)、全体の取り込み状況は [教材の取り込み状況](import-status.md) を参照します。

## 今回の対象

公式・GitHub・外部サイトを調査し、公式原本と正答を対応付けられる過去問2,331問を本人用ローカル教材に追加しました。原本・画像・教材本文は `private-data/` と `build/private/` に保存し、公開版へ同梱しません。

| 教材 | 今回の登録数 | 出典・範囲 |
| --- | ---: | --- |
| 公認会計士短答式 | 2,271問 | 2013～2026年、27回・108科目。企業法・管理会計論・監査論・財務会計論 |
| FP3級実技 | 60問 | 日本FP協会、資産設計提案業務、2024・2025・2026年5月公表分、各20問 |
| 合計 | 2,331問 | 111パック。別年度の再出題は別出題として数える |

公認会計士の候補2,282問中、11問を公式の全員加点・複数許容または選択肢番号を確定できないため除外しました。設問単位の理由は `private-data/github-material/prepared/finance-report.json` に保存しています。FP実技は3回分の全60問です。登録した2,331問・原本ページ画像2,495枚は、公式正答と原本画素の検査に合格しました。

## 取得元と条件

- [公認会計士・監査審査会の過去試験](https://www.fsa.go.jp/cpaaob/kouninkaikeishi-shiken/kakoshiken.html) と [2026年試験](https://www.fsa.go.jp/cpaaob/kouninkaikeishi-shiken/2026shiken.html) の掲載リンクをたどり、公式問題・公式正答を取得。[利用ルール](https://www.fsa.go.jp/cpaaob/copyright.html) はPDL1.0を適用。出典・加工表示を各問に付記します。古い年度の一覧も確認しましたが、今回この取得経路で問題・正答を対応付けられた範囲は2013年以降です。
- [日本FP協会の問題・模範解答](https://www.jafp.or.jp/exam/mohan/) と [問題利用条件](https://www.jafp.or.jp/exam/mohan/files/exam_riyou.pdf) を確認。学科は既存収録分と一致するため、今回の追加は実技です。
- GitHub APIでFP・簿記・公認会計士・証券外務員の公開リポジトリを検索。[RenatusAuctor/cpa-tantou-kakomon-drill](https://github.com/RenatusAuctor/cpa-tantou-kakomon-drill)、[ronodera662/fp-study-app](https://github.com/ronodera662/fp-study-app)、[furumix2000/fp3-quiz-app](https://github.com/furumix2000/fp3-quiz-app)、[xinyue119-code/boki1-cards](https://github.com/xinyue119-code/boki1-cards)、[nktkt/bookkeeping-practice](https://github.com/nktkt/bookkeeping-practice)、[morikagesho/boki-quise](https://github.com/morikagesho/boki-quise) の固定コミットのツリーと本文またはREADMEを保存。独自編集・解説のライセンスを確認できず、新規GitHub本文の直接収録は保留。公認会計士候補が参照する公式原本を取得して収録します。検索履歴は [GitHub調査データ](github-exam-search.json)、取得本文は [取得元台帳](github-sources.json) に記録します。GitHub由来の5,452枚の編集カードを公式過去問5,452問として数えません。
- 外部の [FP試験ナビ2級](https://fp-navi.jp/fp2/mondai-2/)・[3級](https://fp-navi.jp/fp3/mondai-3/) を確認。公式PDFへの参照索引として使用し、独自解説を転載しません。おぼエルの索引は取得時403のため本文未取得です。
- [日商簿記2級](https://www.kentei.ne.jp/bookkeeping/class-s/sample/sample-two)・[3級](https://www.kentei.ne.jp/bookkeeping/sample/sample_3) の公式サンプル、[1級過去問](https://www.kentei.ne.jp/bookkeeping/class1/1qkako) は転載制限が明記されているため新規収録を保留。既存の簿記教材は保持します。
- [税理士試験](https://www.nta.go.jp/taxes/zeirishi/zeirishishiken/zeirishi.htm) の問題・答案用紙・出題ポイントは確認しましたが、答案用紙を模範解答と扱わず、今回の採点付き教材には未収録。[証券外務員](https://www.jsda.or.jp/gaimuin/)・[珠算](https://www.kentei.ne.jp/abacus) も今回確認した入口から問題・正答をそろえられず未収録です。過去問が存在しないという判定ではありません。

## 再生成と検証

```powershell
python scripts/prepare-finance-material.py --fetch
python scripts/prepare-finance-material.py
python checks/finance-material-check.py
npm run build:private
node checks/private-material-check.mjs
node checks/finance-import-check.mjs
npm run inventory:exams
```

既存のPDF取得・原本ページ画像・ビルドローダーを再利用します。URLは掲載リンクから取得し、未公開URLを推測しません。取得済み原本はキャッシュを再利用します。原本SHA-256、問題番号、正答、選択肢番号、画像参照を記録します。正答は位置による取得とは別に行グループ／PDF読順／HTML表セルで再読し、全登録画像を原本再描画と画素比較します。

他分野の教材で通常ビルドが停止する場合、最後に成功したビルドへ `node scripts/append-food-material.mjs finance` で検証済み会計・金融パックを追加できます。今回はこちらの既存追加処理で登録しました。ロックにより他のビルドと同時には書き込みません。合冊PDFの科目ごとに問題番号が再開するため、公認会計士の原本重複キーには科目も含めます。

図表・連問の共通資料を原本画像で保持します。同一ページの隣接問題も表示されます。正答に理由の解説はなく、出題当時の法令・会計基準を前提とします。公認会計士の2014年企業法、2025年財務会計論の連問資料、2026年FP実技の表を代表ページとして目視しました。全問の目視・専門家監修・実ブラウザの新規検査は未実施です。

新規分は本人用ローカルビルドに限定し、クラウド配備・pushはこの作業に含みません。

完了確認：公式正答・全画像の検査と、本人用全教材の形式・ハッシュ・同期検査が合格。追加2,331問の実登録、合冊科目の区別、再取り込みの重複除外、公認会計士・FP実技の正答判定と記録復元を検査しています。追加処理直後には追加前902パックの本文ハッシュが一致しました。その後の並行作業で建築士候補3パックの構成が変わったため、最終的な既存教材保持の検査は今回の対象である簿記3級・FP2級・FP3級の旧12パックに限定します。今回の処理は建築士の問題本文を編集していません。`npm run check` も合格し、公開版への教材混入はありません。管理表は成功した本人用ビルドから再生成しています。
