# 消防設備士の取り込み

## 2026-10-08 追加拡充

公式・非公式・GitHubを再調査し、新しいGitHub取得元7件から1,271問を本人用ローカル教材へ追加。消防設備士の登録は614件から1,885件です。新規分は選択式1,161問・暗記カードの記述式110問で、数値置換による自動生成は行っていません。

| 取得元 | 追加数 | 登録先 |
| --- | ---: | --- |
| [shinki5301-art/-6](https://github.com/shinki5301-art/-6) | 2 | 乙6 |
| [mitsugeek/shoubo-shiken](https://github.com/mitsugeek/shoubo-shiken) | 87 | 乙6 |
| [hkosu813-ux/shobo-quiz](https://github.com/hkosu813-ux/shobo-quiz) | 184 | 甲4 |
| [terukatsu58-hash/Shobo-quiz](https://github.com/terukatsu58-hash/Shobo-quiz) | 14 | 甲1 |
| [jiagyebo19891011/shoubou-otsu6](https://github.com/jiagyebo19891011/shoubou-otsu6) | 748 | 乙6 |
| [yousukeee/otsu6-cards](https://github.com/yousukeee/otsu6-cards) | 110 | 乙6・自己採点 |
| [altxxxtla-lab/shoubou-setsubishi-drill](https://github.com/altxxxtla-lab/shoubou-setsubishi-drill) | 126 | 甲1：34、甲4：40、乙6：34、共通：18 |

追加後は甲1が69件、甲4が239件、乙6が1,236件、共通教材が74件。ほかの区分は変更ありません。共通18問は各類に複製せず共通教材へ登録しました。同一試験の本文・選択肢一致48件、必要図表が未対応の7件は除外。別HTMLの110カードは、104件が完全一致、6件が同じ学習内容の文言・解答補足の差分であることを確認し、追加登録していません。意味的に近い設問や同じ知識の反復は残ります。

取得は固定コミット・Git blob・SHA-256で照合し、配布コードを実行せずデータだけを解析します。提供元の正答を保持し、1始まりの番号・複数選択・正誤・カード解答を既存形式に変換。全件に非公式・正答と法改正対応は未検証の表示を付けています。専門家監修・法令の全件照合済み教材ではありません。新しい取得元は再配布許諾を確認していないため `localOnly` とし、クラウド配備や公開リポジトリへの問題同梱は行いません。

### 再調査した非収録候補

- [公式公開ページ](https://www.shoubo-shiken.or.jp/shoubou/exercise.html)：令和8年6月更新の甲種・乙種を確認。現在登録済みの公開問題と同じ対象で、追加対象を確認できませんでした。
- `m3tk0616-lab/shobo-tokurui-quiz`：15問。冒頭のルートBの説明・引用条文に疑義があるため、条文と正答の確認まで保留。提供元が引用する法17条の2の5と、[消防庁の設備体系資料](https://www.fdma.go.jp/laws/tutatsu/items/tuchi1605/pdf/040531_6b.pdf)・[法令本文](https://laws.e-gov.go.jp/law/323AC1000000186?occasion_date=20260609)の対応を確認しました。
- `tyaamarukusu-svg/study-os-shobo6`：購入者向けアクセス区画と市販参考書由来の表示があり非収録。アクセスゲートの解除はしていません。
- `taaaaho/shobo4`、`taaaaho/shobo6`：公開ファイル一覧は紹介・規約ページ等で、問題データを確認できませんでした。
- [消防設備士ラボ](https://shoubou-lab.com/)、[ぴよパス](https://piyopass.com/shoubosetsubishi-otsu6)、設備資格ドリル：公開教材を調査しましたが、利用条件ページの取得・取り込み条件の確認を完了できず追加していません。

### 今回の再生成・検査

`scripts/fetch-new-exam-candidates.py` に固定コミットを登録しています。取得・変換とも `--repos` の後へ上表の取得元を指定すると、ほかの教材を保持して再実行できます。

```powershell
npm run build:private
python checks/fire-expansion-check.py
node checks/github-candidates-check.mjs
node checks/private-material-check.mjs
python checks/github-literals-check.py
npm run check
npm run inventory:exams
```

追加前の基準は `private-data/github-candidates/fire-expansion-baseline.json`。検査は追加全問の原本との正答対応、既存全パックのメタデータ・SHA-256保持、ローカル限定、出典・図表参照、実際の採点処理を対象にします。実ブラウザでの新規全問の表示確認は未実施です。

実施結果：ビルド、消防追加1,271問の原本・正答対応、追加前の全パック保持、GitHub候補76取得元の採点・整合性・重複除外、本人用全106,922問の形式・画像・索引・同期検査、通常テスト、管理表更新に合格。全体件数には同時期に反映された別資格の追加も含むため、今回の増分は消防設備士だけを集計しています。カード別HTMLの6件の文言差を確認して検査を修正し、再検査済みです。

## 前回の公式問題追加

2026-10-07。本人用ローカル教材へ、公式の実技17題を追加しました。既存の公式筆記76問もPDFの類別表示に沿って13区分へ登録しています。既存の甲種・乙種まとめ教材と非公式共通教材56問は保持しました。

今回の追加登録は232件（筆記215件・実技17題）。筆記は既存76問の類別登録で、共通問題は複数の類に所属します。新しい問題本文は実技17題であり、232問の新作・新規過去問ではありません。実技は小問一式を1題として数えます。

| 区分 | 今回の登録数（実技を含む） |
| --- | ---: |
| 甲種特類 | 4 |
| 甲種第1類 | 21 |
| 甲種第2類 | 22 |
| 甲種第3類 | 20 |
| 甲種第4類 | 15 |
| 甲種第5類 | 14 |
| 乙種第1類 | 23 |
| 乙種第2類 | 23 |
| 乙種第3類 | 23 |
| 乙種第4類 | 19 |
| 乙種第5類 | 16 |
| 乙種第6類 | 15 |
| 乙種第7類 | 17 |

## 出典と形式

[消防試験研究センターの公開問題](https://www.shoubo-shiken.or.jp/shoubou/exercise.html)の甲種・乙種PDFを使用します。2026年6月更新の案内で、出題年度は特定されていません。既存の取得済み原本をSHA-256で照合し再利用しました。教育目的の本人学習用とし、全追加パックは `localOnly` です。

筆記は四択の自動採点で、公式正答表画像を解答後に表示します。甲種第1～5類には鑑別等・製図各1題、乙種第1～7類には鑑別等各1題を追加しました。実技の写真・配管図・回路図・製図条件は原本ページを保持し、公式解答画像で自己採点します。作図入力機能は追加せず、紙などに描いて比較する案内です。

## 非公式教材の確認

登録済みの [no2shi4ni0-dot/syoubou-quiz](https://github.com/no2shi4ni0-dot/syoubou-quiz) 56問は「消防設備士向け共通対策教材（GitHub）」として維持しました。類別の完全対応が未確認のため、各類へ推測で振り分けていません。

[設備資格ドリル乙6](https://setsubi.shikakumon.com/shoubou6/)、[消防設備士ラボ](https://shoubou-lab.com/)、[ぴよパス](https://piyopass.com/hub/shoubo-shibu-shi)にも非公式問題の公開を確認しました。今回は追加登録していません。設備資格ドリルの利用規約ページはWeb取得に失敗し、ローカルcurlも接続失敗しました。他の2サイトも取り込み条件・問題と正答の全件対応は未確認です。公開閲覧できることを転載許可の確認とは扱いません。

## 再生成・検証

```powershell
python scripts/prepare-fire-material.py
npm run build:private
node checks/fire-material-check.mjs
node checks/private-material-check.mjs
npm run check
npm run inventory:exams
```

類別見出し全76件と連番、既存正答と公式正答表、実技17題のページ・類別・解答例の対応を確認します。新規画像は原本レンダリングとの画素一致を検査します。既存パックのハッシュ保持、追加232件の出典・正答・画像・採点・ローカル限定属性を検査します。正答の独立再計算、現行法令への全問適合確認、理由解説の追加、実ブラウザでの全問表示確認は実施していません。

現在の総数は [試験管理表](exam-inventory.md) と [取り込み状況](import-status.md) を参照してください。公開版への問題同梱、クラウド配備、Git pushは行っていません。

2026-10-08完了：上記の全コマンドに合格。本人用ビルドは100,077件・2,114パックとなり、追加前99,845件の全既存パックのハッシュ保持を確認しました。件数表は初回の書き込み拒否後、権限付き実行で更新済みです。
