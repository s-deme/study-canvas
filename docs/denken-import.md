# 電気主任技術者の追加収録

2026年10月8日。電験一種・二種・三種のローカル本人用教材を拡充。公式公開原本202科目分から4,221問、GitHub公開教材から1,095問を追加しました。登録単位は従来同様、独立して回答する空欄・小問を含みます。一種2009年度一次と二次試験は大問単位です。

| 試験 | 追加前 | 公式追加 | GitHub追加 | 追加後 |
| --- | ---: | ---: | ---: | ---: |
| 第一種電気主任技術者 | 1,258 | 1,382 | 0 | 2,640 |
| 第二種電気主任技術者 | 1,150 | 1,720 | 1,082 | 3,952 |
| 第三種電気主任技術者 | 660 | 1,119 | 13 | 1,792 |
| 合計 | 3,068 | 4,221 | 1,095 | 8,384 |

## 取得元と範囲

- 電気技術者試験センターの[一種](https://www.shiken.or.jp/chief/first/qa/)、[二種](https://www.shiken.or.jp/chief/second/qa/)、[三種](https://www.shiken.or.jp/chief/third/qa/)。各一覧の2ページ目まで調査し、2009～2026年度の既存未収録分を追加。一種・二種の二次試験は2009～2025年度、各170問を標準解答画像とともに収録。
- [nemi2nd-dot/denken2-app](https://github.com/nemi2nd-dot/denken2-app/tree/319fb379e2c5ebed4d85347188d1d71972ce89bf)：二種向け公開練習962問。図・配置が不足する2件、構文不備6件、選択肢不備1件を除外。
- [5garashi/denken2](https://github.com/5garashi/denken2/tree/a980ad6bb134ce68bc674f59d3e27278e26a6c94)：四科目の頻出練習120問。本文・選択肢群・解答解説を保持した記述式自己採点。数式は提供元のLaTeX記法で保持。
- [nakasyo3519/denken3all](https://github.com/nakasyo3519/denken3all/tree/bdeb66077002b6635b4a9832c0a5a0ac60b45a06)：三種2008年度13問。2009年度以降302件は公式原本と重なるため除外。図版の照合が必要な2件は保留。
- [yamkenic/denken1-app](https://github.com/yamkenic/denken1-app/tree/ed75c7df87a015749e26ed1097027f7c469c199e)：取得・確認した問題データは公式過去問との重複や本文不足があり追加なし。[ayatonikuman/denken3](https://github.com/ayatonikuman/denken3/tree/5d8b310e5aca86b5b7fc1910fb68fc865b218696)は学習予定・外部リンクのみ。

GitHub公開リポジトリ検索、10件のファイル一覧調査、[電気の神髄の過去問一覧](https://denki-no-shinzui.com/denken-database/denken3/)、TAC等の公開案内も確認しました。市販書籍の取得・転載、認証や課金の回避は行っていません。Web全体の全問取得を保証するものではありません。

## 表示と検証範囲

公式教材は数式・回路図・訂正を原本ページ画像で保持。26科目分は問題番号の連続性を確認したページ範囲、176科目分は番号OCRが不確実なため冊子全体を表示します。後者は問題画面にその旨を表示し、指定された問番号・空欄を解きます。二次試験や文字だけで確定できない一次の正答は標準解答画像による自己採点です。三種2014年度機械の問8は公式の全員正解措置を確認し除外しました。

公式正答セルまたは標準解答画像、原本・問題データ・画像のSHA-256、全画像の原本再描画との画素一致を検査します。目視確認は代表例です。全問の内容レビュー・独立した解き直しは行っていません。GitHub教材は提供元の本文と解答の対応・構造を検査しますが、内容の正確さ、法改正への対応は未検証で、各問題にも表示します。

全追加分はローカル本人用教材です。クラウドへの配備は含みません。実際の登録数は[試験管理表](exam-inventory.md)を参照してください。

実行結果：公式4,221問・画像3,666枚の検査、追加5,316問のビルド検査、既存全パックのハッシュ保持、選択式採点・記述式自己評価を確認しました。`npm run check`、`checks/nonit-material-check.py`、`checks/github-literals-check.py`、`checks/github-candidates-check.mjs`、`checks/private-material-check.mjs`も通過。最終検査と管理表の生成は共有ビルドのロックを保持して実施しました。

## 再生成と確認

```powershell
python scripts/prepare-denken-material.py --fetch
python scripts/prepare-denken-material.py
python checks/denken-material-check.py
python scripts/fetch-denken-candidates.py
python scripts/prepare-github-candidates.py --repos nemi2nd-dot/denken2-app 5garashi/denken2 nakasyo3519/denken3all yamkenic/denken1-app ayatonikuman/denken3
node scripts/append-food-material.mjs denken,github-denken
node checks/denken-build-check.mjs
npm run inventory:exams
```

既に登録済みのGitHubパックを変更する場合は増分追記ではなく `npm run build:private` を使います。通常ビルドにも電験追加レポートを組み込み済みです。元データ・取得記録・追加前スナップショットは `private-data/github-material/denken-*`、公式準備結果・検証結果は同ディレクトリの `prepared/denken-*.json`、GitHub分は既存の `private-data/github-candidates/` に保存します。
