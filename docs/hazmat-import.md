# 危険物取扱者 乙種の問題登録

## 非公式の予想・練習問題も対象にした追加登録

2026-10-07。GitHubの5リポジトリから607問を取得し、乙2の完全一致重複1問を除く **606問** を本人用ローカル教材に追加しました。公式過去問という表示はせず、問題ごとに「非公式練習問題」、取得元、正答・解説の内容未検証を明示します。

| 試験 | 今回のGitHub追加 | 公式を含む合計 | 取得元 |
| --- | ---: | ---: | --- |
| 乙1 | 100 | 135 | [hutatumekozou/kikenbutu-otsu1syu](https://github.com/hutatumekozou/kikenbutu-otsu1syu/tree/ce5908b5c7a50a3d26f28325b5f7cd4dd810a5b2) |
| 乙2 | 149 | 184 | [akiina999/otsu2-training](https://github.com/akiina999/otsu2-training/tree/d8232fba101f81c2c6c59c1f4dcb35dcf79f6ea4) |
| 乙3 | 151 | 186 | [tetsu0950120/otsu3](https://github.com/tetsu0950120/otsu3/tree/15cfc691dd80552e361ba9e01c6561a6e24f1308) |
| 乙4 | 105 | 140 | [M-HMMY/kikenbutsu_otsu4_exam_app](https://github.com/M-HMMY/kikenbutsu_otsu4_exam_app/tree/ab91eba24067500362f36d524a76d73cd789e978) |
| 乙5 | 101 | 136 | [tetsu0950120/otsu5](https://github.com/tetsu0950120/otsu5/tree/b4cd732e0a20539817973c6db53c405e2e25fa1d) |
| 乙6 | 0 | 35 | 公式教材を保持。今回のGitHub検索では危険物乙6の追加データを確定できず |
| **合計** | **606** | **816** | |

乙1・乙2・乙4は提供元の解説付きで、乙2の図付き4問もPNGへ変換して保持します。乙3・乙5は掲載正答のみで、提供元の採点処理が配列の先頭を正答として扱うことを確認しました。アプリでの演習時には選択肢順を既存機能でシャッフルします。乙1は4択の練習問題です。

乙1リポジトリの `basic_questions_part*.json` はバス・タクシーに関する別試験の問題だったため、危険物用の `class1_*.json` だけを取り込みます。「otsu6」で見つかった消防設備士乙6の教材も、危険物乙6へは混入させません。

全606問の本文・選択肢・正答番号・解説の取得元との一致を検査し、SVGから変換した4図の表示も目視確認しました。これは提供元の正答・解説の専門的な正しさを保証する検証ではありません。明示的な再配布許諾は未確認のため、今回も本人用ローカル教材として管理し、公開版・クラウドには含めません。前回の「公式のみ・非公式候補は保留」という扱いは、今回の予想・練習問題も登録するというユーザー指定に合わせて変更しました。

取得元の固定コミット・元ファイル・SHA-256は `private-data/github-candidates/inventory.json` と `acquisition.json`、登録数と除外記録は同 `prepared/report.json` が正本です。既存の取得処理 `python scripts/import-github-candidates.py --download` でも再取得できます。

登録後のGitHub教材検査（全50取得元）、既存公式教材保持検査、JavaScriptデータ解析検査、調査台帳検査、`npm run check` は合格しました。追加前の全パックのSHA-256が保持されていることも確認しています。実ブラウザでの追加検査と全体再ビルドは未実施です。

```powershell
python scripts/prepare-github-candidates.py --repos akiina999/otsu2-training M-HMMY/kikenbutsu_otsu4_exam_app tetsu0950120/otsu3 tetsu0950120/otsu5 hutatumekozou/kikenbutu-otsu1syu
python checks/hazmat-candidates-check.py
node scripts/append-food-material.mjs github-hazmat
node checks/github-candidates-check.mjs
npm run inventory:exams
```

## 先行作業：公式問題の登録

2026-10-07（日本時間）。本人用ローカル教材へ乙1・2・3・5・6の公式公開問題を各35問、計175件追加。既存の乙4公式35問を保持し、全6類で計210件を登録します。クラウド配備は実施していません。

## 登録元と問題の数え方

[消防試験研究センターの公開案内](https://www.shoubo-shiken.or.jp/kikenbutsu/exercise.html)から、[乙1・2・3・5・6の公式PDF](https://www.shoubo-shiken.or.jp/content/kikenbutsu_otsu.pdf)を取得しました。2026年6月更新の掲載資料で、各問の実施年度は不明です。2026年度の本試験問題という意味ではありません。

共通の法令15問・物理化学10問と、各類の性質・消火10問から構成されます。共通25問を5類それぞれで演習できるように登録するため、追加登録175件に対して異なる原問は75問です。問題番号26〜35の正答表は類ごとに異なるため、類別に対応させています。

本文・図表・選択肢は原本画像で表示し、1〜5を選んで自動採点します。解答後は対応する公式正答表の画像も表示します。理由解説は未収録です。

公式サイトは教育目的（非営利）の例外を示しています。本件は本人の学習用として非公開・ローカル限定で保存し、公開Web版やGitHubへ問題本文・画像を追加していません。

## 先行調査時点の非公式・GitHub候補（上記の追加登録前）

| 取得元 | 確認内容 | 今回の扱い |
| --- | --- | --- |
| [akiina999/otsu2-training](https://github.com/akiina999/otsu2-training/tree/d8232fba101f81c2c6c59c1f4dcb35dcf79f6ea4) | 乙2用。READMEで個人学習用のオリジナル再構成問題と説明。問題JS15ファイルを確認 | 候補記録。明示的な利用許諾を確認できず本文の追加は保留。READMEの件数とファイル構成に差があるため現在数は未確定 |
| [M-HMMY/kikenbutsu_otsu4_exam_app](https://github.com/M-HMMY/kikenbutsu_otsu4_exam_app/tree/ab91eba24067500362f36d524a76d73cd789e978) | READMEが確認問題105問と説明。科目別問題ファイルを確認 | 候補記録。明示的な利用許諾と全問の正答は未確認 |
| [dokechin/otsu](https://github.com/dokechin/otsu/tree/f6f13e22e1add96c4ebbe5b54833a74f4a3b6dc6) | 学習記事HTMLの一覧を確認 | 問題・選択肢・正答を備えたデータセットとして未確定 |
| [危険物取扱者問題集](https://kikenbutsu.shiryu.work/questions/) | 全551問と表示される無料問題一覧。乙1〜6等の分類あり | 外部参照候補。551問全部が乙種用という意味ではない。転載許諾・全問正答は未確認 |
| [ケンテイラボ](https://kentei-lab.com/exams/kikenotsu12356/questions/1-%E5%85%B1%E9%80%9A%E6%80%A7%E8%B3%AA) | 乙1・2・3・5・6の共通性質41問の掲載を検索結果で確認 | 外部参照候補。本文ページの再取得・利用条件確認は未完了 |

今回の非公式・GitHub由来の問題本文追加は0件です。公開されていることと収録許諾、READMEの記載数と実データ数を区別しています。

## 再生成と検証

原本、原本SHA-256に結び付けた目視記録 `hazmat-review.json`、追加前の `hazmat-baseline.json` は `private-data/github-material/` に保存します。非公開ファイルを失った場合は、同じ原本の再取得とページ・正答表の目視照合が必要です。

```powershell
python scripts/prepare-hazmat-material.py
node scripts/append-food-material.mjs hazmat
node checks/hazmat-material-check.mjs
npm run inventory:exams
```

全体再生成 `npm run build:private` も専用の検証済みレポートを読み込みます。公開版には教材を含めません。

問題43ページの番号・類見出しと正答表3ページを目視照合し、生成画像46ページすべてを原本レンダリングと画素単位で比較します。登録検査は問題・科目・正答表の割当、正誤判定、既存パックのハッシュ保持を対象とします。全問の現行法令適合性・専門家による内容監修・実ブラウザでの動作確認は未実施です。

今回、画像一致検査・`checks/hazmat-material-check.mjs`・`npm run check`・GitHub調査台帳検査に合格しました。本人用ビルドへの追加と件数表の自動更新を完了しています。全体再ビルドは未実施で、既存の追記処理を使用しました。
