# 問題未登録試験のGitHub調査台帳

集計日：2026-10-08（日本時間）。現在の問題未登録は110試験。未調査・検索未確認は10試験。

正本は [調査データ](github-exam-search.json)。試験IDごとに検索日・検索語・結果URL・判定を履歴として保存します。この文書は `npm run inventory:exams` で生成します。登録数は [試験管理表](exam-inventory.md) と同じビルドです。

## 再調査を避ける運用

1. 次回は下の「未調査・検索未確認」だけを検索します。「候補未発見」は通常の検索対象から外します。期限で自動的に未調査へ戻しません。
2. 「要精査」「候補あり」は保存済みURLを確認します。試験・級の一致、設問本文、正答、利用条件の確認を進め、新規検索を繰り返しません。
3. 新しい候補の情報、提供元の修正、明示的な再調査依頼があるときだけ再調査します。以前の履歴を消さず、理由をnoteへ記載してhistoryに追記します。
4. 新しい試験は記録がなければ自動的に未調査になります。登録後もJSONの調査履歴は保持します。生成処理は検索や問題取得を実行しません。

## 判定の意味

「候補未発見」は記録したWeb検索の範囲で見つからなかった意味です。GitHubに存在しないという断定ではありません。検索結果は書誌・資格一覧・別試験などを含みます。「要精査」は結果URLがあるだけで、問題データ発見の判定ではありません。「候補あり」も本文・正答・収録許諾の確認完了ではありません。2026-10-07の調査は正式名称を中心に268試験を一次検索し、一部は級を外した名称でも検索しました。追加検索語と結果はJSONのfamilySearchesへ保存しています。全ファイルの検査や問題登録は行っていません。

既存候補の取得・変換・保留理由は [取り込み状況](import-status.md) と [候補調査記録](github-candidates.md) を参照します。級未確定の既存候補は各級の発見済み記録へ一律に転記しません。

## 調査状態の集計

| 状態 | 試験数 |
| --- | ---: |
| 検索済み・候補未発見 | 66 |
| 検索済み・要精査 | 33 |
| 候補あり・本文未確認 | 0 |
| 既存候補保留 | 1 |
| 検索未確認 | 0 |
| 問題本文確認済み | 0 |
| 未調査 | 10 |

## 未調査・検索未確認

- 皇宮護衛官採用試験（大卒程度試験）（imperial-guard-univ）
- 刑務官採用試験（大卒程度試験）（prison-officer-univ）
- 法務省専門職員（人間科学）採用試験（justice-human-science）
- 食品衛生監視員採用試験（food-sanitation-inspector）
- 海上保安官採用試験（coast-guard-officer）
- 国家公務員一般職（社会人試験）（civil-regular-career）
- 税務職員採用試験（tax-officer）
- 海上保安大学校学生採用試験（coast-guard-academy）
- 気象大学校学生採用試験（meteorological-college）
- 国家公務員経験者採用試験（civil-experienced）

## 現在の問題未登録試験

| 試験 | ID | 調査状態 | 最終検索日 | 検索語 | 結果・次の作業 |
| --- | --- | --- | --- | --- | --- |
| E資格 | eken | 検索済み・要精査 | 2026-10-07 | site:github.com E資格 practice questions | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| Generative AI Test | jdla-generative | 検索済み・要精査 | 2026-10-07 | site:github.com Generative AI Test practice questions | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| Python 3 エンジニア認定データ分析試験 | python-data | 検索済み・要精査 | 2026-10-07 | site:github.com Python 3 エンジニア認定データ分析試験 practice questions | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| Python 3 エンジニア認定データ分析実践試験 | python-data-practical | 検索済み・要精査 | 2026-10-07 | site:github.com Python 3 エンジニア認定データ分析実践試験 practice questions | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| LPIC-2 | lpic2 | 検索済み・要精査 | 2026-10-07 | site:github.com LPIC-2 practice questions | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| LPIC-3 Mixed Environments | lpic3-300 | 検索済み・要精査 | 2026-10-07 | site:github.com LPIC-3 Mixed Environments practice questions | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| LPIC-3 Security | lpic3-303 | 検索済み・要精査 | 2026-10-07 | site:github.com LPIC-3 Security practice questions | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| LPIC-3 Virtualization and Containerization | lpic3-305 | 検索済み・要精査 | 2026-10-07 | site:github.com LPIC-3 Virtualization and Containerization practice questions | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| LPIC-3 High Availability and Storage Clusters | lpic3-306 | 検索済み・要精査 | 2026-10-07 | site:github.com LPIC-3 High Availability and Storage Clusters practice questions | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| AWS Certified Developer - Associate | aws-dva | 検索済み・要精査 | 2026-10-07 | site:github.com AWS Certified Developer - Associate practice questions | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| AWS Certified Solutions Architect - Professional | aws-sap | 検索済み・要精査 | 2026-10-07 | site:github.com AWS Certified Solutions Architect - Professional practice questions | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| AWS Certified DevOps Engineer - Professional | aws-dop | 検索済み・要精査 | 2026-10-07 | site:github.com AWS Certified DevOps Engineer - Professional practice questions | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| MOS Word | mos-word | 検索済み・要精査 | 2026-10-07 | site:github.com MOS Word practice questions | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| MOS Word Expert | mos-word-expert | 検索済み・候補未発見 | 2026-10-07 | site:github.com "MOS Word Expert" practice questions | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| MOS Excel | mos-excel | 検索済み・要精査 | 2026-10-07 | site:github.com "MOS Excel" practice questions | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| MOS Excel Expert | mos-excel-expert | 検索済み・要精査 | 2026-10-07 | site:github.com "MOS Excel Expert" practice questions | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| MOS PowerPoint | mos-powerpoint | 検索済み・要精査 | 2026-10-07 | site:github.com "MOS PowerPoint" practice questions | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| MOS Access | mos-access | 検索済み・要精査 | 2026-10-07 | site:github.com "MOS Access" practice questions | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| MOS Outlook | mos-outlook | 検索済み・要精査 | 2026-10-07 | site:github.com "MOS Outlook" practice questions | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| 日商PC検定 文書作成1級 | nissho-pc-doc1 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "日商PC検定 文書作成1級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 日商PC検定 文書作成2級 | nissho-pc-doc2 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "日商PC検定 文書作成2級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 日商PC検定 文書作成3級 | nissho-pc-doc3 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "日商PC検定 文書作成3級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 日商PC検定 データ活用1級 | nissho-pc-data1 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "日商PC検定 データ活用1級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 日商PC検定 データ活用2級 | nissho-pc-data2 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "日商PC検定 データ活用2級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 日商PC検定 データ活用3級 | nissho-pc-data3 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "日商PC検定 データ活用3級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 日商PC検定 プレゼン資料作成1級 | nissho-pc-slide1 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "日商PC検定 プレゼン資料作成1級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 日商PC検定 プレゼン資料作成2級 | nissho-pc-slide2 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "日商PC検定 プレゼン資料作成2級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 日商PC検定 プレゼン資料作成3級 | nissho-pc-slide3 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "日商PC検定 プレゼン資料作成3級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 日商プログラミング検定 BASIC | nissho-program-basic | 検索済み・候補未発見 | 2026-10-07 | site:github.com "日商プログラミング検定 BASIC" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 日商プログラミング検定 STANDARD | nissho-program-standard | 検索済み・候補未発見 | 2026-10-07 | site:github.com "日商プログラミング検定 STANDARD" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 日商プログラミング検定 EXPERT | nissho-program-expert | 検索済み・候補未発見 | 2026-10-07 | site:github.com "日商プログラミング検定 EXPERT" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 司法試験予備試験 | shiho-yobi | 検索済み・要精査 | 2026-10-07 | site:github.com "司法試験予備試験" 過去問 問題 | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| 司法書士試験 | shihoshoshi | 検索済み・要精査 | 2026-10-07 | site:github.com "司法書士試験" 過去問 問題 | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| 日商簿記初級 | boki-basic | 検索済み・候補未発見 | 2026-10-07 | site:github.com "日商簿記初級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 日商原価計算初級 | cost-basic | 検索済み・要精査 | 2026-10-07 | site:github.com 原価計算 初級 問題 | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| FP技能検定1級 | fp1 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "FP技能検定1級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 税理士試験 | zeirishi | 検索済み・要精査 | 2026-10-07 | site:github.com "税理士試験" 過去問 問題 | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| 一種外務員資格試験 | securities1 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "一種外務員資格試験" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 二種外務員資格試験 | securities2 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "二種外務員資格試験" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 珠算能力検定1級 | abacus1 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "珠算能力検定1級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 珠算能力検定2級 | abacus2 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "珠算能力検定2級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 珠算能力検定3級 | abacus3 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "珠算能力検定3級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| サービス接遇検定準1級 | service-pre1 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "サービス接遇検定準1級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 英検1級 | eiken1 | 検索済み・要精査 | 2026-10-07 | site:github.com "英検1級" 過去問 問題 | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| 英検準1級 | eiken-pre1 | 検索済み・要精査 | 2026-10-07 | site:github.com "英検準1級" 過去問 問題 | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| 英検2級 | eiken2 | 既存候補保留 | 2026-10-07 | site:github.com "英検2級" 過去問 問題 | [確認先](https://github.com/wangchang2049/eikenQuest) / 既存候補wangchang2049/eikenQuestは設問・選択肢の不整合で保留済み。提供元修正待ち。 / [結果URL・履歴](github-exam-search.json) |
| 英検準2級プラス | eiken-pre2-plus | 検索済み・候補未発見 | 2026-10-07 | site:github.com "英検準2級プラス" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 英検準2級 | eiken-pre2 | 検索済み・要精査 | 2026-10-07 | site:github.com "英検準2級" 過去問 問題 | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| 英検3級 | eiken3 | 検索済み・要精査 | 2026-10-07 | site:github.com "英検3級" 過去問 問題 | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| 英検4級 | eiken4 | 検索済み・要精査 | 2026-10-07 | site:github.com "英検4級" 過去問 問題 | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| 英検5級 | eiken5 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "英検5級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| TOEIC Listening & Reading | toeic-lr | 検索済み・要精査 | 2026-10-07 | site:github.com "TOEIC Listening & Reading" 過去問 問題 | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| TOEIC Speaking & Writing | toeic-sw | 検索済み・要精査 | 2026-10-07 | site:github.com "TOEIC Speaking & Writing" 過去問 問題 | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| TOEIC Bridge Listening & Reading | toeic-bridge-lr | 検索済み・候補未発見 | 2026-10-07 | site:github.com "TOEIC Bridge Listening & Reading" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| TOEIC Bridge Speaking & Writing | toeic-bridge-sw | 検索済み・候補未発見 | 2026-10-07 | site:github.com "TOEIC Bridge Speaking & Writing" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 中国語検定1級 | chuken1 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "中国語検定1級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 中国語検定準1級 | chuken-pre1 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "中国語検定準1級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 中国語検定2級 | chuken2 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "中国語検定2級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 中国語検定3級 | chuken3 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "中国語検定3級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 中国語検定4級 | chuken4 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "中国語検定4級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 中国語検定準4級 | chuken-pre4 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "中国語検定準4級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| ハングル能力検定1級 | hangul1 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "ハングル能力検定1級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| ハングル能力検定2級 | hangul2 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "ハングル能力検定2級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| ハングル能力検定準2級 | hangul-pre2 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "ハングル能力検定準2級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| ハングル能力検定3級 | hangul3 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "ハングル能力検定3級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| ハングル能力検定4級 | hangul4 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "ハングル能力検定4級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| ハングル能力検定5級 | hangul5 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "ハングル能力検定5級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 実用フランス語技能検定1級 | french1 | 検索済み・要精査 | 2026-10-07 | site:github.com "実用フランス語技能検定1級" 過去問 問題 | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| 実用フランス語技能検定準1級 | french-pre1 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "実用フランス語技能検定準1級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 実用フランス語技能検定2級 | french2 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "実用フランス語技能検定2級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 実用フランス語技能検定準2級 | french-pre2 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "実用フランス語技能検定準2級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 実用フランス語技能検定3級 | french3 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "実用フランス語技能検定3級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 実用フランス語技能検定4級 | french4 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "実用フランス語技能検定4級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 実用フランス語技能検定5級 | french5 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "実用フランス語技能検定5級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| ドイツ語技能検定1級 | german1 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "ドイツ語技能検定1級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| ドイツ語技能検定準1級 | german-pre1 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "ドイツ語技能検定準1級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| ドイツ語技能検定2級 | german2 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "ドイツ語技能検定2級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| ドイツ語技能検定3級 | german3 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "ドイツ語技能検定3級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| ドイツ語技能検定4級 | german4 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "ドイツ語技能検定4級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| ドイツ語技能検定5級 | german5 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "ドイツ語技能検定5級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 統計検定準1級 | statistics-pre1 | 検索済み・候補未発見 | 2026-10-07 | site:github.com 統計検定 過去問 / site:github.com 統計検定 問題 pdf | 数学・統計の再検索。公式原本・解答で日本語数学375問、英語数学50問、統計1級20問、DS公式サンプル10問をローカル追加。GitHubの受験記・補助リンク・学習管理実装は過去問データとして採用しない。対象試験の問題全文と公式解答がそろう追加GitHub問題データは検索範囲で未確認。CBTの非公開問題は収録しない。 追記：準2級英語版の別問題25問も公式解答と照合し、合計480問（日本語数学375・英語数学75・統計1級20・DS公式サンプル10）とした。 / [結果URL・履歴](github-exam-search.json) |
| 統計検定4級 | statistics4 | 検索済み・候補未発見 | 2026-10-07 | site:github.com 統計検定 過去問 / site:github.com 統計検定 問題 pdf | 数学・統計の再検索。公式原本・解答で日本語数学375問、英語数学50問、統計1級20問、DS公式サンプル10問をローカル追加。GitHubの受験記・補助リンク・学習管理実装は過去問データとして採用しない。対象試験の問題全文と公式解答がそろう追加GitHub問題データは検索範囲で未確認。CBTの非公開問題は収録しない。 追記：準2級英語版の別問題25問も公式解答と照合し、合計480問（日本語数学375・英語数学75・統計1級20・DS公式サンプル10）とした。 / [結果URL・履歴](github-exam-search.json) |
| 統計検定 統計調査士 | statistics-survey | 検索済み・候補未発見 | 2026-10-07 | site:github.com 統計検定 過去問 / site:github.com 統計検定 問題 pdf | 数学・統計の再検索。公式原本・解答で日本語数学375問、英語数学50問、統計1級20問、DS公式サンプル10問をローカル追加。GitHubの受験記・補助リンク・学習管理実装は過去問データとして採用しない。対象試験の問題全文と公式解答がそろう追加GitHub問題データは検索範囲で未確認。CBTの非公開問題は収録しない。 追記：準2級英語版の別問題25問も公式解答と照合し、合計480問（日本語数学375・英語数学75・統計1級20・DS公式サンプル10）とした。 / [結果URL・履歴](github-exam-search.json) |
| 統計検定 専門統計調査士 | statistics-specialist | 検索済み・候補未発見 | 2026-10-07 | site:github.com 統計検定 過去問 / site:github.com 統計検定 問題 pdf | 数学・統計の再検索。公式原本・解答で日本語数学375問、英語数学50問、統計1級20問、DS公式サンプル10問をローカル追加。GitHubの受験記・補助リンク・学習管理実装は過去問データとして採用しない。対象試験の問題全文と公式解答がそろう追加GitHub問題データは検索範囲で未確認。CBTの非公開問題は収録しない。 追記：準2級英語版の別問題25問も公式解答と照合し、合計480問（日本語数学375・英語数学75・統計1級20・DS公式サンプル10）とした。 / [結果URL・履歴](github-exam-search.json) |
| 統計検定 データサイエンス基礎 | statistics-ds-basic | 検索済み・候補未発見 | 2026-10-07 | site:github.com 統計検定 過去問 / site:github.com 統計検定 問題 pdf | 数学・統計の再検索。公式原本・解答で日本語数学375問、英語数学50問、統計1級20問、DS公式サンプル10問をローカル追加。GitHubの受験記・補助リンク・学習管理実装は過去問データとして採用しない。対象試験の問題全文と公式解答がそろう追加GitHub問題データは検索範囲で未確認。CBTの非公開問題は収録しない。 追記：準2級英語版の別問題25問も公式解答と照合し、合計480問（日本語数学375・英語数学75・統計1級20・DS公式サンプル10）とした。 / [結果URL・履歴](github-exam-search.json) |
| 第三級アマチュア無線技士 | radio-amateur3 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "第三級アマチュア無線技士" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 第四級アマチュア無線技士 | radio-amateur4 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "第四級アマチュア無線技士" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 賃貸不動産経営管理士 | rental-manager | 検索済み・候補未発見 | 2026-10-07 | site:github.com "賃貸不動産経営管理士" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 言語聴覚士国家試験 | speech-therapist | 検索済み・候補未発見 | 2026-10-07 | site:github.com "言語聴覚士国家試験" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 歯科衛生士国家試験 | dental-hygienist | 検索済み・候補未発見 | 2026-10-07 | site:github.com "歯科衛生士国家試験" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 歯科技工士国家試験 | dental-technician | 検索済み・候補未発見 | 2026-10-07 | site:github.com "歯科技工士国家試験" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 救急救命士国家試験 | emergency-tech | 検索済み・候補未発見 | 2026-10-07 | site:github.com "救急救命士国家試験" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 公認心理師試験 | psychologist | 検索済み・候補未発見 | 2026-10-07 | site:github.com "公認心理師試験" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 食生活アドバイザー2級 | food-advisor2 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "食生活アドバイザー2級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 食生活アドバイザー3級 | food-advisor3 | 検索済み・候補未発見 | 2026-10-07 | site:github.com "食生活アドバイザー3級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 色彩検定1級 | color1 | 検索済み・要精査 | 2026-10-07 | site:github.com "色彩検定1級" 過去問 問題 | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| 色彩検定2級 | color2 | 検索済み・要精査 | 2026-10-07 | site:github.com "色彩検定2級" 過去問 問題 | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| 色彩検定3級 | color3 | 検索済み・要精査 | 2026-10-07 | site:github.com "色彩検定3級" 過去問 問題 | 検索結果あり。試験・級の一致、設問本文の有無は要精査。 / [結果URL・履歴](github-exam-search.json) |
| 色彩検定UC級 | color-uc | 検索済み・候補未発見 | 2026-10-07 | site:github.com "色彩検定UC級" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 国家公務員一般職（高卒者試験） | civil-regular-high | 検索済み・候補未発見 | 2026-10-07 | site:github.com "国家公務員一般職（高卒者試験）" 過去問 問題 | 一次検索範囲で問題候補未発見。検索結果なし、または書誌・資格一覧等のみ。 / [結果URL・履歴](github-exam-search.json) |
| 皇宮護衛官採用試験（大卒程度試験） | imperial-guard-univ | 未調査 | — | — | 次回の検索対象 |
| 刑務官採用試験（大卒程度試験） | prison-officer-univ | 未調査 | — | — | 次回の検索対象 |
| 法務省専門職員（人間科学）採用試験 | justice-human-science | 未調査 | — | — | 次回の検索対象 |
| 食品衛生監視員採用試験 | food-sanitation-inspector | 未調査 | — | — | 次回の検索対象 |
| 海上保安官採用試験 | coast-guard-officer | 未調査 | — | — | 次回の検索対象 |
| 国家公務員一般職（社会人試験） | civil-regular-career | 未調査 | — | — | 次回の検索対象 |
| 税務職員採用試験 | tax-officer | 未調査 | — | — | 次回の検索対象 |
| 海上保安大学校学生採用試験 | coast-guard-academy | 未調査 | — | — | 次回の検索対象 |
| 気象大学校学生採用試験 | meteorological-college | 未調査 | — | — | 次回の検索対象 |
| 国家公務員経験者採用試験 | civil-experienced | 未調査 | — | — | 次回の検索対象 |
