# 未登録試験への公式問題追加

2026-10-07に、問題未登録だった12試験へ1,221問を本人用ローカル教材として追加。現在の件数は [試験管理表](exam-inventory.md) を参照。

| 試験 | 追加数 | 収録範囲・公式取得元 |
| --- | ---: | --- |
| 社会福祉士 | 408 | [第36〜38回](https://www.sssc.or.jp/shakai/past_exam/index.html)、2024〜2026年実施 |
| 介護福祉士 | 374 | [第36〜38回](https://www.sssc.or.jp/kaigo/past_exam/index.html)、2024〜2026年実施 |
| 精神保健福祉士 | 427 | [第26〜28回](https://www.sssc.or.jp/seishin/past_exam/index.html)、2024〜2026年実施 |
| ビジネス実務法務1・2・3級 | 各1 | [公式問題例](https://kentei.tokyo-cci.or.jp/houmu/support/challenge/example_03.html)の各級ページ |
| 福祉住環境コーディネーター1・2・3級 | 1・1・2 | [公式問題例](https://kentei.tokyo-cci.or.jp/fukushi/support/challenge/example_03.html)の各級ページ |
| カラーコーディネーター アドバンス・スタンダード | 各1 | [公式問題例](https://kentei.tokyo-cci.or.jp/color/support/challenge/example_01.html)の各クラスページ |
| eco検定 | 3 | [公式問題例](https://kentei.tokyo-cci.or.jp/eco/support/challenge/example.html) |

福祉国家試験は公式の音声読み上げ用HTMLを本文として保存し、公式PDFの正答と照合。図のある問題には公式の言語説明を使用し、図の再現や音声ファイルの収録はしていない。精神保健福祉士の共通科目と専門科目は問題番号が別々に1から始まるため、正答表の区分を分離した。両資格の共通科目はそれぞれの試験に属する出題として数える。

介護福祉士第36回・問46は単一選択で複数正答を許容する採点特例のため1問除外。選択数不一致を複数選択として誤登録していない。共通事例96問分、注記、全角の選択肢番号、公式HTMLの閉じタグ欠落・段落分割も検査する。

商工会議所の12問は公式の問題ブロック単位。穴埋めの複数空欄や正誤の複合設問を分割せず、公式解答との比較による自己採点形式とする。掲載年度不明のものを2026年度問題として扱わない。法令・統計は出題・掲載当時の前提であり、現行試験の全範囲対応や最新制度への改題は行わない。

原本HTML/PDF、URL、SHA-256、変換結果、除外理由、検証記録は `private-data/github-material/` に保存。公開コードや公開配信元 `web/` に問題本文を同梱しない。再配布許諾を確認していないため `localOnly` を付け、クラウド配備を拒否する。GitHub検索の過去履歴は、公式サイト経由の今回の収録とは別に保持する。

## 再取得・再生成・検査

```powershell
python scripts/prepare-welfare-material.py --fetch
python scripts/prepare-welfare-material.py
python scripts/prepare-welfare-material.py --verify
python scripts/prepare-public-examples.py --fetch
python scripts/prepare-public-examples.py --verify
node scripts/append-food-material.mjs welfare,public-examples
python checks/welfare-material-check.py
node checks/public-import-check.mjs
npm run inventory:exams
```

既存ビルドへの追加はステージング先で生成し、成功時のみ切り替える。検証済み教材の本文修正を反映するときに限り `--replace` を使用できる。問題ID・順序・索引項目・画像参照が変わる更新は拒否する。通常の `build:private` にも両取り込み元を追加済み。

自動検査は全1,221問の出典照合、選択式の正答採点、自己採点用回答の送信、追加前の全パック不変を対象とする。全問の人手による内容監修・理由解説の作成・実ブラウザ表示の全件確認は行っていない。公式PDFの番号区分と採点特例は代表ページを画像でも確認した。

上記の原本再照合・追加教材検査に加え、`npm run check`、`node checks/private-material-check.mjs`、`npm run inventory:exams` が合格。追加前94,775問の全パックが不変で、追加12試験・1,221問が出典データと一致することを確認した。

今回の追加後も未登録試験は残る。本記録は全未登録試験の調査・登録完了を意味しない。クラウド配備・Gitへのpushは実施していない。
