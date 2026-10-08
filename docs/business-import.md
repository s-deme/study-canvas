# 経営・事務・販売の過去問取り込み

2026-10-07実施。公式・GitHub・外部サイトを調査し、公式原本から3,431問を追加。現在のカテゴリ別・試験別件数は [試験管理表](exam-inventory.md) を参照します。本人用ローカル教材への追加です。

| 追加教材 | 追加数 | 収録方式 |
| --- | ---: | --- |
| 中小企業診断士 第1次試験 | 3,141 | 2012～2026年度・7科目。近年は枝問別の選択式、旧PDFと2023年運営管理は大問別の画像・自己採点 |
| 中小企業診断士 第2次試験 | 232 | 2010年度事例Ⅰ、2012～2025年度の全事例。57冊。大問別に事例全文・公式出題趣旨を収録 |
| 秘書検定 | 20 | 1級・準1級・2級・3級の公式問題例 |
| ビジネス文書検定 | 5 | 1級・2級・3級の公式問題例 |
| ビジネス実務マナー検定 | 12 | 1級・2級・3級の公式問題例 |
| サービス接遇検定 | 13 | 1級・2級・3級の公式問題例 |
| ビジネスマネジャー検定 | 2 | 公式試験問題例・選択式 |
| 販売士検定 | 6 | 1級・2級・3級各2問。2026年リーフレットの公式問題例・自己採点 |
| **合計** | **3,431** | **179パック・18試験、選択式1,979問・自己採点1,452問** |

第2次試験の出題趣旨は模範解答ではありません。公式模範解答・詳細採点基準は収録せず、解答後に出題趣旨を確認する形式です。旧PDFの自己採点問題は枝問をまとめた大問1件として数え、枝問数を重複加算していません。公式問題例は実施年度のある過去問と区別しています。販売士の2026年はリーフレットの公開年です。

## 取得元と調査範囲

- [日本中小企業診断士協会連合会・過去問](https://www.jf-cmca.jp/contents/010_c_/shikenmondai.html)、[第2次試験出題趣旨](https://www.jf-cmca.jp/contents/010_c_/001_shiken_kakokekka_syusi.html)。年度別公式正解・配点ページから訂正版を優先して取得。
- [秘書](https://jitsumu-ginou-kentei.jp/HS/example)、[ビジネス文書](https://jitsumu-ginou-kentei.jp/BB/example)、[ビジネス実務マナー](https://jitsumu-ginou-kentei.jp/BZ/example)、[サービス接遇](https://jitsumu-ginou-kentei.jp/SV/example)の公式問題・解答・解説。
- [東京商工会議所・ビジネスマネジャー問題例](https://kentei.tokyo-cci.or.jp/bijimane/support/challenge/example.html)。試験管理表の公式案内URLも訂正。
- [日本商工会議所・販売士サンプル](https://www.kentei.ne.jp/retailsales/sample)、[2026年公式リーフレット](https://www.kentei.ne.jp/wp/wp-content/uploads/2026/02/2026RML.pdf)、[リーフレット問題の公式解答](https://www.kentei.ne.jp/retailsales/answers)。解答付きリーフレット6問を収録。
- 外部サイトの[診断士過去問リンク一覧](https://shigyo-get.com/shindanshi-kakomon-muryou-download/)で公式年度別資料を探索。外部サイトの解説本文は複製していません。
- GitHubの[toru830/shindanshi](https://github.com/toru830/shindanshi)は既存候補教材10問が登録済み。今回の追加数へ重複加算していません。既存GitHub教材の正答を公式正解として保証するものではありません。名称・過去問・questions等で追加候補を検索しましたが、今回新しく取り込める問題データは確定しませんでした。

## 保留と利用条件

205パック候補のうち26パックを保留。第1次試験2011年度7科目と、第2次試験2007～2009年度・2010年度事例Ⅱ～Ⅳ・2011年度は、文字情報と問題番号の対応検証が成立していません。第1次試験2007～2010年度は公式正解資料の対応が未確定、2023年度再試験は別の正解資料の対応が未確認で、登録数へ含めていません。

近年の選択式では、単一の公式正解が取れない問題や枝問・選択肢記号の検証が成立しない問題を除外。2023年度運営管理の訂正版画像は目視確認し、全員正解の第14問・第31問を除外。実務技能検定の図表画像を伴う一部問題は保留。サービス接遇準1級は面接試験のため今回の筆記問題登録はありません。販売士の別公開サンプル冊子は参考ハンドブックのページのみで公式正答が含まれず、推測採点をせず保留にしています。

全パックに`localOnly: true`を付け、クラウド用ビルドで停止します。[診断士の利用規約](https://www.jf-cmca.jp/contents/016_riyoukiyaku.html)、各提供元の著作権・転載条件に従う本人用の学習資料です。原本・問題本文・画像・取得キャッシュは`private-data/`と`build/private/`に保存し、Gitや公開配信へ含めません。

## 再生成と検証

```powershell
python scripts/prepare-business-material.py --fetch --fetch-cases
python checks/business-material-check.py
node checks/business-material-check.mjs
node scripts/append-food-material.mjs business
node checks/private-material-check.mjs
npm run inventory:exams
```

取得済み原本を再利用する変換は`python scripts/prepare-business-material.py`。既存のPDF画像・取得・汎用追加ビルド処理を再利用します。通常の`build:private`にも読み込みを追加しました。既存教材を保持した追加更新は汎用追加スクリプトの`business`指定を使います。

検証対象は、原本・問題パック・画像のSHA-256、公式解答表の列位置による独立対応、問題番号の連続性・旧PDFの一貫した文字対応、第2次試験の出題趣旨にある問題番号、全原本画像の画素一致、18試験の選択式・自己採点操作、既存パックの保持です。代表的な原本・訂正表を目視確認しましたが、全設問の目視校正・理由解説の作成・法制度の現行化はしていません。

ローカルの`private-data/github-material/prepared/business-report.json`が候補・保留・除外理由と出典ハッシュの正本、`business-verification.json`が検証記録です。
