# 試験管理表

集計日：2026-10-07（日本時間）。339試験の登録先、既存の自作教材を含め355試験・教材、21カテゴリ、登録問題合計95,996問。

級・種別は別の登録先として扱い、年度・科目は問題側で管理します。「問題未登録」は登録先だけ準備した状態です。収録内容と取得元は [GitHub経由の過去問収録](github-material.md) と [本人用教材の管理](private-material.md) を参照してください。全試験の出題範囲や本番形式への対応を意味しません。音声・面接・実技の本番再現や公式スコア換算は対象外です。

登録数はローカル本人用ビルドの各問題ファイルから再集計した値です。クラウド配備版やブラウザ内の個別持込問題は含みません。アプリの「試験管理表」はその環境の配布教材と持込問題を集計します。

行政書士・第二種衛生管理者・日本農業検定3級の既存自作対策教材は、従来のIDと教材名のまま別行で保持します。新しい試験の登録先へ自動移動・二重計上していません。

公式案内は試験情報の参照先です。過去問の有無や転載・収録許諾の確認状況を示すものではありません。問題登録時に年度・出題範囲・利用条件を確認してください。試験数の固定上限はありません。GitHubの検索済み・候補未発見・次の確認対象は [GitHub調査台帳](github-exam-search.md) で管理します。

自動生成文書です。直接編集せず `npm run inventory:exams` で更新します。同時に [取り込み状況](import-status.md) を生成します。登録先の定義は `web/exams.mjs`、登録数の正本は実際の問題ファイルです。文書の役割と更新手順は [docs案内](README.md) を参照してください。

## カテゴリ別集計

| カテゴリ | 試験・教材数 | 登録あり | 問題未登録 | 登録問題数 |
| --- | ---: | ---: | ---: | ---: |
| IT・AI | 52 | 19 | 33 | 14955 |
| 会計・金融 | 15 | 4 | 11 | 3530 |
| 法律・行政 | 10 | 7 | 3 | 1006 |
| 経営・事務・販売 | 19 | 18 | 1 | 3441 |
| 英語 | 12 | 0 | 12 | 0 |
| 外国語 | 25 | 0 | 25 | 0 |
| 日本語・国語 | 17 | 17 | 0 | 3957 |
| 数学・統計 | 23 | 16 | 7 | 480 |
| 歴史・地理 | 11 | 11 | 0 | 198 |
| 電気・通信 | 26 | 24 | 2 | 19216 |
| 建築・土木 | 15 | 15 | 0 | 7790 |
| 不動産 | 4 | 3 | 1 | 3935 |
| 安全・消防・設備 | 38 | 15 | 23 | 1955 |
| 医療・健康 | 24 | 18 | 6 | 23298 |
| 福祉・介護・保育 | 7 | 7 | 0 | 1965 |
| 農業・食品 | 8 | 6 | 2 | 2396 |
| 観光・運輸 | 5 | 5 | 0 | 2730 |
| デザイン・生活 | 8 | 4 | 4 | 2045 |
| 環境・自然科学 | 2 | 2 | 0 | 569 |
| 公務員 | 23 | 12 | 11 | 1979 |
| 自作一般教材 | 11 | 11 | 0 | 551 |

## IT・AI

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| G検定 | gken | 240 | 登録あり | [公式案内](https://www.jdla.org/certificate/) |
| 情報セキュリティマネジメント | sg | 460 | 登録あり | [公式案内](https://www.ipa.go.jp/shiken/kubun/index.html) |
| 基本情報技術者 | fe | 1624 | 登録あり | [公式案内](https://www.ipa.go.jp/shiken/kubun/index.html) |
| ITパスポート | ip | 1900 | 登録あり | [公式案内](https://www.ipa.go.jp/shiken/kubun/index.html) |
| 応用情報技術者 | ap | 2469 | 登録あり | [公式案内](https://www.ipa.go.jp/shiken/kubun/index.html) |
| ITストラテジスト | st | 532 | 登録あり | [公式案内](https://www.ipa.go.jp/shiken/kubun/index.html) |
| システムアーキテクト | sa | 507 | 登録あり | [公式案内](https://www.ipa.go.jp/shiken/kubun/index.html) |
| プロジェクトマネージャ | pm | 498 | 登録あり | [公式案内](https://www.ipa.go.jp/shiken/kubun/index.html) |
| ネットワークスペシャリスト | nw | 546 | 登録あり | [公式案内](https://www.ipa.go.jp/shiken/kubun/index.html) |
| データベーススペシャリスト | db | 533 | 登録あり | [公式案内](https://www.ipa.go.jp/shiken/kubun/index.html) |
| エンベデッドシステムスペシャリスト | es | 517 | 登録あり | [公式案内](https://www.ipa.go.jp/shiken/kubun/index.html) |
| ITサービスマネージャ | sm | 526 | 登録あり | [公式案内](https://www.ipa.go.jp/shiken/kubun/index.html) |
| システム監査技術者 | au | 516 | 登録あり | [公式案内](https://www.ipa.go.jp/shiken/kubun/index.html) |
| 情報処理安全確保支援士 | sc | 1074 | 登録あり | [公式案内](https://www.ipa.go.jp/shiken/kubun/index.html) |
| E資格 | eken | 0 | 問題未登録 | [公式案内](https://www.jdla.org/certificate/) |
| Generative AI Test | jdla-generative | 0 | 問題未登録 | [公式案内](https://www.jdla.org/certificate/) |
| Python 3 エンジニア認定基礎試験 | python-basic | 0 | 問題未登録 | [公式案内](https://pythonic-exam.com/exam) |
| Python 3 エンジニア認定実践試験 | python-practical | 0 | 問題未登録 | [公式案内](https://pythonic-exam.com/exam) |
| Python 3 エンジニア認定データ分析試験 | python-data | 0 | 問題未登録 | [公式案内](https://pythonic-exam.com/exam) |
| Python 3 エンジニア認定データ分析実践試験 | python-data-practical | 0 | 問題未登録 | [公式案内](https://pythonic-exam.com/exam) |
| Linux Essentials | linux-essentials | 276 | 登録あり | [公式案内](https://www.lpi.org/our-certifications/summary-of-lpi-certifications/) |
| LPIC-1 | lpic1 | 639 | 登録あり | [公式案内](https://www.lpi.org/our-certifications/summary-of-lpi-certifications/) |
| LPIC-2 | lpic2 | 0 | 問題未登録 | [公式案内](https://www.lpi.org/our-certifications/summary-of-lpi-certifications/) |
| LPIC-3 Mixed Environments | lpic3-300 | 0 | 問題未登録 | [公式案内](https://www.lpi.org/our-certifications/summary-of-lpi-certifications/) |
| LPIC-3 Security | lpic3-303 | 0 | 問題未登録 | [公式案内](https://www.lpi.org/our-certifications/summary-of-lpi-certifications/) |
| LPIC-3 Virtualization and Containerization | lpic3-305 | 0 | 問題未登録 | [公式案内](https://www.lpi.org/our-certifications/summary-of-lpi-certifications/) |
| LPIC-3 High Availability and Storage Clusters | lpic3-306 | 0 | 問題未登録 | [公式案内](https://www.lpi.org/our-certifications/summary-of-lpi-certifications/) |
| AWS Certified Cloud Practitioner | aws-clf | 597 | 登録あり | [公式案内](https://aws.amazon.com/jp/certification/) |
| AWS Certified AI Practitioner | aws-aif | 504 | 登録あり | [公式案内](https://aws.amazon.com/jp/certification/) |
| AWS Certified Solutions Architect - Associate | aws-saa | 997 | 登録あり | [公式案内](https://aws.amazon.com/jp/certification/) |
| AWS Certified Developer - Associate | aws-dva | 0 | 問題未登録 | [公式案内](https://aws.amazon.com/jp/certification/) |
| AWS Certified Solutions Architect - Professional | aws-sap | 0 | 問題未登録 | [公式案内](https://aws.amazon.com/jp/certification/) |
| AWS Certified DevOps Engineer - Professional | aws-dop | 0 | 問題未登録 | [公式案内](https://aws.amazon.com/jp/certification/) |
| MOS Word | mos-word | 0 | 問題未登録 | [公式案内](https://mos.odyssey-com.co.jp/outline/) |
| MOS Word Expert | mos-word-expert | 0 | 問題未登録 | [公式案内](https://mos.odyssey-com.co.jp/outline/) |
| MOS Excel | mos-excel | 0 | 問題未登録 | [公式案内](https://mos.odyssey-com.co.jp/outline/) |
| MOS Excel Expert | mos-excel-expert | 0 | 問題未登録 | [公式案内](https://mos.odyssey-com.co.jp/outline/) |
| MOS PowerPoint | mos-powerpoint | 0 | 問題未登録 | [公式案内](https://mos.odyssey-com.co.jp/outline/) |
| MOS Access | mos-access | 0 | 問題未登録 | [公式案内](https://mos.odyssey-com.co.jp/outline/) |
| MOS Outlook | mos-outlook | 0 | 問題未登録 | [公式案内](https://mos.odyssey-com.co.jp/outline/) |
| 日商PC検定 文書作成1級 | nissho-pc-doc1 | 0 | 問題未登録 | [公式案内](https://www.kentei.ne.jp/) |
| 日商PC検定 文書作成2級 | nissho-pc-doc2 | 0 | 問題未登録 | [公式案内](https://www.kentei.ne.jp/) |
| 日商PC検定 文書作成3級 | nissho-pc-doc3 | 0 | 問題未登録 | [公式案内](https://www.kentei.ne.jp/) |
| 日商PC検定 データ活用1級 | nissho-pc-data1 | 0 | 問題未登録 | [公式案内](https://www.kentei.ne.jp/) |
| 日商PC検定 データ活用2級 | nissho-pc-data2 | 0 | 問題未登録 | [公式案内](https://www.kentei.ne.jp/) |
| 日商PC検定 データ活用3級 | nissho-pc-data3 | 0 | 問題未登録 | [公式案内](https://www.kentei.ne.jp/) |
| 日商PC検定 プレゼン資料作成1級 | nissho-pc-slide1 | 0 | 問題未登録 | [公式案内](https://www.kentei.ne.jp/) |
| 日商PC検定 プレゼン資料作成2級 | nissho-pc-slide2 | 0 | 問題未登録 | [公式案内](https://www.kentei.ne.jp/) |
| 日商PC検定 プレゼン資料作成3級 | nissho-pc-slide3 | 0 | 問題未登録 | [公式案内](https://www.kentei.ne.jp/) |
| 日商プログラミング検定 BASIC | nissho-program-basic | 0 | 問題未登録 | [公式案内](https://www.kentei.ne.jp/) |
| 日商プログラミング検定 STANDARD | nissho-program-standard | 0 | 問題未登録 | [公式案内](https://www.kentei.ne.jp/) |
| 日商プログラミング検定 EXPERT | nissho-program-expert | 0 | 問題未登録 | [公式案内](https://www.kentei.ne.jp/) |

## 会計・金融

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| 日商簿記3級 | boki3 | 99 | 登録あり | [公式案内](https://www.kentei.ne.jp/bookkeeping) |
| 日商簿記1級 | boki1 | 0 | 問題未登録 | [公式案内](https://www.kentei.ne.jp/bookkeeping) |
| 日商簿記2級 | boki2 | 0 | 問題未登録 | [公式案内](https://www.kentei.ne.jp/bookkeeping) |
| 日商簿記初級 | boki-basic | 0 | 問題未登録 | [公式案内](https://www.kentei.ne.jp/bookkeeping) |
| 日商原価計算初級 | cost-basic | 0 | 問題未登録 | [公式案内](https://www.kentei.ne.jp/bookkeeping) |
| FP技能検定1級 | fp1 | 0 | 問題未登録 | [公式案内](https://www.jafp.or.jp/exam/) |
| FP技能検定2級 | fp2 | 800 | 登録あり | [公式案内](https://www.jafp.or.jp/exam/) |
| FP技能検定3級 | fp3 | 360 | 登録あり | [公式案内](https://www.jafp.or.jp/exam/) |
| 税理士試験 | zeirishi | 0 | 問題未登録 | [公式案内](https://www.nta.go.jp/taxes/zeirishi/zeirishishiken/zeirishi.htm) |
| 公認会計士試験 | cpa | 2271 | 登録あり | [公式案内](https://www.fsa.go.jp/cpaaob/kouninkaikeishi-shiken/) |
| 一種外務員資格試験 | securities1 | 0 | 問題未登録 | [公式案内](https://www.jsda.or.jp/gaimuin/) |
| 二種外務員資格試験 | securities2 | 0 | 問題未登録 | [公式案内](https://www.jsda.or.jp/gaimuin/) |
| 珠算能力検定1級 | abacus1 | 0 | 問題未登録 | [公式案内](https://www.kentei.ne.jp/abacus) |
| 珠算能力検定2級 | abacus2 | 0 | 問題未登録 | [公式案内](https://www.kentei.ne.jp/abacus) |
| 珠算能力検定3級 | abacus3 | 0 | 問題未登録 | [公式案内](https://www.kentei.ne.jp/abacus) |

## 法律・行政

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| 行政書士試験 | gyosei | 406 | 登録あり | [公式案内](https://www.gyosei-shiken.or.jp/) |
| 社会保険労務士試験 | sharosi | 9 | 登録あり | [公式案内](https://www.sharosi-siken.or.jp/) |
| 司法試験 | shiho | 538 | 登録あり | [公式案内](https://www.moj.go.jp/qualification_test.html) |
| 司法試験予備試験 | shiho-yobi | 0 | 問題未登録 | [公式案内](https://www.moj.go.jp/qualification_test.html) |
| 司法書士試験 | shihoshoshi | 0 | 問題未登録 | [公式案内](https://www.moj.go.jp/qualification_test.html) |
| 土地家屋調査士試験 | land-surveyor | 0 | 問題未登録 | [公式案内](https://www.moj.go.jp/qualification_test.html) |
| ビジネス実務法務検定1級 | business-law1 | 1 | 登録あり | [公式案内](https://kentei.tokyo-cci.or.jp/houmu/) |
| ビジネス実務法務検定2級 | business-law2 | 1 | 登録あり | [公式案内](https://kentei.tokyo-cci.or.jp/houmu/) |
| ビジネス実務法務検定3級 | business-law3 | 1 | 登録あり | [公式案内](https://kentei.tokyo-cci.or.jp/houmu/) |
| 行政書士試験向け自作対策教材 | gyosei-original | 50 | 登録あり | — |

## 経営・事務・販売

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| リテールマーケティング（販売士）検定1級 | retail1 | 2 | 登録あり | [公式案内](https://www.kentei.ne.jp/retailsales) |
| リテールマーケティング（販売士）検定2級 | retail2 | 2 | 登録あり | [公式案内](https://www.kentei.ne.jp/retailsales) |
| リテールマーケティング（販売士）検定3級 | retail3 | 2 | 登録あり | [公式案内](https://www.kentei.ne.jp/retailsales) |
| ビジネスマネジャー検定 | business-manager | 2 | 登録あり | [公式案内](https://kentei.tokyo-cci.or.jp/bijimane/) |
| 秘書検定1級 | secretary1 | 5 | 登録あり | [公式案内](https://jitsumu-ginou-kentei.jp/) |
| 秘書検定準1級 | secretary-pre1 | 5 | 登録あり | [公式案内](https://jitsumu-ginou-kentei.jp/) |
| 秘書検定2級 | secretary2 | 5 | 登録あり | [公式案内](https://jitsumu-ginou-kentei.jp/) |
| 秘書検定3級 | secretary3 | 5 | 登録あり | [公式案内](https://jitsumu-ginou-kentei.jp/) |
| ビジネス文書検定1級 | business-doc1 | 1 | 登録あり | [公式案内](https://jitsumu-ginou-kentei.jp/) |
| ビジネス文書検定2級 | business-doc2 | 2 | 登録あり | [公式案内](https://jitsumu-ginou-kentei.jp/) |
| ビジネス文書検定3級 | business-doc3 | 2 | 登録あり | [公式案内](https://jitsumu-ginou-kentei.jp/) |
| ビジネス実務マナー検定1級 | business-manner1 | 4 | 登録あり | [公式案内](https://jitsumu-ginou-kentei.jp/) |
| ビジネス実務マナー検定2級 | business-manner2 | 3 | 登録あり | [公式案内](https://jitsumu-ginou-kentei.jp/) |
| ビジネス実務マナー検定3級 | business-manner3 | 5 | 登録あり | [公式案内](https://jitsumu-ginou-kentei.jp/) |
| サービス接遇検定1級 | service1 | 5 | 登録あり | [公式案内](https://jitsumu-ginou-kentei.jp/) |
| サービス接遇検定準1級 | service-pre1 | 0 | 問題未登録 | [公式案内](https://jitsumu-ginou-kentei.jp/) |
| サービス接遇検定2級 | service2 | 3 | 登録あり | [公式案内](https://jitsumu-ginou-kentei.jp/) |
| サービス接遇検定3級 | service3 | 5 | 登録あり | [公式案内](https://jitsumu-ginou-kentei.jp/) |
| 中小企業診断士試験 | sme-consultant | 3383 | 登録あり | — |

## 英語

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| 英検1級 | eiken1 | 0 | 問題未登録 | [公式案内](https://www.eiken.or.jp/eiken/exam/criteria/index.html) |
| 英検準1級 | eiken-pre1 | 0 | 問題未登録 | [公式案内](https://www.eiken.or.jp/eiken/exam/criteria/index.html) |
| 英検2級 | eiken2 | 0 | 問題未登録 | [公式案内](https://www.eiken.or.jp/eiken/exam/criteria/index.html) |
| 英検準2級プラス | eiken-pre2-plus | 0 | 問題未登録 | [公式案内](https://www.eiken.or.jp/eiken/exam/criteria/index.html) |
| 英検準2級 | eiken-pre2 | 0 | 問題未登録 | [公式案内](https://www.eiken.or.jp/eiken/exam/criteria/index.html) |
| 英検3級 | eiken3 | 0 | 問題未登録 | [公式案内](https://www.eiken.or.jp/eiken/exam/criteria/index.html) |
| 英検4級 | eiken4 | 0 | 問題未登録 | [公式案内](https://www.eiken.or.jp/eiken/exam/criteria/index.html) |
| 英検5級 | eiken5 | 0 | 問題未登録 | [公式案内](https://www.eiken.or.jp/eiken/exam/criteria/index.html) |
| TOEIC Listening & Reading | toeic-lr | 0 | 問題未登録 | [公式案内](https://www.iibc-global.org/toeic.html) |
| TOEIC Speaking & Writing | toeic-sw | 0 | 問題未登録 | [公式案内](https://www.iibc-global.org/toeic.html) |
| TOEIC Bridge Listening & Reading | toeic-bridge-lr | 0 | 問題未登録 | [公式案内](https://www.iibc-global.org/toeic.html) |
| TOEIC Bridge Speaking & Writing | toeic-bridge-sw | 0 | 問題未登録 | [公式案内](https://www.iibc-global.org/toeic.html) |

## 外国語

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| 中国語検定1級 | chuken1 | 0 | 問題未登録 | [公式案内](https://www.chuken.gr.jp/) |
| 中国語検定準1級 | chuken-pre1 | 0 | 問題未登録 | [公式案内](https://www.chuken.gr.jp/) |
| 中国語検定2級 | chuken2 | 0 | 問題未登録 | [公式案内](https://www.chuken.gr.jp/) |
| 中国語検定3級 | chuken3 | 0 | 問題未登録 | [公式案内](https://www.chuken.gr.jp/) |
| 中国語検定4級 | chuken4 | 0 | 問題未登録 | [公式案内](https://www.chuken.gr.jp/) |
| 中国語検定準4級 | chuken-pre4 | 0 | 問題未登録 | [公式案内](https://www.chuken.gr.jp/) |
| ハングル能力検定1級 | hangul1 | 0 | 問題未登録 | [公式案内](https://hangul.or.jp/) |
| ハングル能力検定2級 | hangul2 | 0 | 問題未登録 | [公式案内](https://hangul.or.jp/) |
| ハングル能力検定準2級 | hangul-pre2 | 0 | 問題未登録 | [公式案内](https://hangul.or.jp/) |
| ハングル能力検定3級 | hangul3 | 0 | 問題未登録 | [公式案内](https://hangul.or.jp/) |
| ハングル能力検定4級 | hangul4 | 0 | 問題未登録 | [公式案内](https://hangul.or.jp/) |
| ハングル能力検定5級 | hangul5 | 0 | 問題未登録 | [公式案内](https://hangul.or.jp/) |
| 実用フランス語技能検定1級 | french1 | 0 | 問題未登録 | [公式案内](https://apefdapf.org/) |
| 実用フランス語技能検定準1級 | french-pre1 | 0 | 問題未登録 | [公式案内](https://apefdapf.org/) |
| 実用フランス語技能検定2級 | french2 | 0 | 問題未登録 | [公式案内](https://apefdapf.org/) |
| 実用フランス語技能検定準2級 | french-pre2 | 0 | 問題未登録 | [公式案内](https://apefdapf.org/) |
| 実用フランス語技能検定3級 | french3 | 0 | 問題未登録 | [公式案内](https://apefdapf.org/) |
| 実用フランス語技能検定4級 | french4 | 0 | 問題未登録 | [公式案内](https://apefdapf.org/) |
| 実用フランス語技能検定5級 | french5 | 0 | 問題未登録 | [公式案内](https://apefdapf.org/) |
| ドイツ語技能検定1級 | german1 | 0 | 問題未登録 | [公式案内](https://www.dokken.or.jp/) |
| ドイツ語技能検定準1級 | german-pre1 | 0 | 問題未登録 | [公式案内](https://www.dokken.or.jp/) |
| ドイツ語技能検定2級 | german2 | 0 | 問題未登録 | [公式案内](https://www.dokken.or.jp/) |
| ドイツ語技能検定3級 | german3 | 0 | 問題未登録 | [公式案内](https://www.dokken.or.jp/) |
| ドイツ語技能検定4級 | german4 | 0 | 問題未登録 | [公式案内](https://www.dokken.or.jp/) |
| ドイツ語技能検定5級 | german5 | 0 | 問題未登録 | [公式案内](https://www.dokken.or.jp/) |

## 日本語・国語

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| 日本語能力試験N1 | jlpt-n1 | 256 | 登録あり | [公式案内](https://www.jlpt.jp/about/levelsummary.html) |
| 日本語能力試験N2 | jlpt-n2 | 253 | 登録あり | [公式案内](https://www.jlpt.jp/about/levelsummary.html) |
| 日本語能力試験N3 | jlpt-n3 | 238 | 登録あり | [公式案内](https://www.jlpt.jp/about/levelsummary.html) |
| 日本語能力試験N4 | jlpt-n4 | 229 | 登録あり | [公式案内](https://www.jlpt.jp/about/levelsummary.html) |
| 日本語能力試験N5 | jlpt-n5 | 209 | 登録あり | [公式案内](https://www.jlpt.jp/about/levelsummary.html) |
| 漢検1級 | kanken1 | 260 | 登録あり | [公式案内](https://www.kanken.or.jp/kanken/) |
| 漢検準1級 | kanken-pre1 | 260 | 登録あり | [公式案内](https://www.kanken.or.jp/kanken/) |
| 漢検2級 | kanken2 | 240 | 登録あり | [公式案内](https://www.kanken.or.jp/kanken/) |
| 漢検準2級 | kanken-pre2 | 240 | 登録あり | [公式案内](https://www.kanken.or.jp/kanken/) |
| 漢検3級 | kanken3 | 240 | 登録あり | [公式案内](https://www.kanken.or.jp/kanken/) |
| 漢検4級 | kanken4 | 240 | 登録あり | [公式案内](https://www.kanken.or.jp/kanken/) |
| 漢検5級 | kanken5 | 240 | 登録あり | [公式案内](https://www.kanken.or.jp/kanken/) |
| 漢検6級 | kanken6 | 240 | 登録あり | [公式案内](https://www.kanken.or.jp/kanken/) |
| 漢検7級 | kanken7 | 240 | 登録あり | [公式案内](https://www.kanken.or.jp/kanken/) |
| 漢検8級 | kanken8 | 200 | 登録あり | [公式案内](https://www.kanken.or.jp/kanken/) |
| 漢検9級 | kanken9 | 210 | 登録あり | [公式案内](https://www.kanken.or.jp/kanken/) |
| 漢検10級 | kanken10 | 162 | 登録あり | [公式案内](https://www.kanken.or.jp/kanken/) |

## 数学・統計

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| 数学検定1級 | suken1 | 28 | 登録あり | [公式案内](https://www.su-gaku.net/suken/) |
| 数学検定準1級 | suken-pre1 | 28 | 登録あり | [公式案内](https://www.su-gaku.net/suken/) |
| 数学検定2級 | suken2 | 44 | 登録あり | [公式案内](https://www.su-gaku.net/suken/) |
| 数学検定準2級 | suken-pre2 | 50 | 登録あり | [公式案内](https://www.su-gaku.net/suken/) |
| 数学検定3級 | suken3 | 50 | 登録あり | [公式案内](https://www.su-gaku.net/suken/) |
| 数学検定4級 | suken4 | 50 | 登録あり | [公式案内](https://www.su-gaku.net/suken/) |
| 数学検定5級 | suken5 | 50 | 登録あり | [公式案内](https://www.su-gaku.net/suken/) |
| 算数検定6級 | suken6 | 30 | 登録あり | [公式案内](https://www.su-gaku.net/suken/) |
| 算数検定7級 | suken7 | 30 | 登録あり | [公式案内](https://www.su-gaku.net/suken/) |
| 算数検定8級 | suken8 | 30 | 登録あり | [公式案内](https://www.su-gaku.net/suken/) |
| 算数検定9級 | suken9 | 20 | 登録あり | [公式案内](https://www.su-gaku.net/suken/) |
| 算数検定10級 | suken10 | 20 | 登録あり | [公式案内](https://www.su-gaku.net/suken/) |
| 算数検定11級 | suken11 | 20 | 登録あり | [公式案内](https://www.su-gaku.net/suken/) |
| 統計検定1級 | statistics1 | 20 | 登録あり | [公式案内](https://www.toukei-kentei.jp/) |
| 統計検定準1級 | statistics-pre1 | 0 | 問題未登録 | [公式案内](https://www.toukei-kentei.jp/) |
| 統計検定2級 | statistics2 | 0 | 問題未登録 | [公式案内](https://www.toukei-kentei.jp/) |
| 統計検定3級 | statistics3 | 0 | 問題未登録 | [公式案内](https://www.toukei-kentei.jp/) |
| 統計検定4級 | statistics4 | 0 | 問題未登録 | [公式案内](https://www.toukei-kentei.jp/) |
| 統計検定 統計調査士 | statistics-survey | 0 | 問題未登録 | [公式案内](https://www.toukei-kentei.jp/) |
| 統計検定 専門統計調査士 | statistics-specialist | 0 | 問題未登録 | [公式案内](https://www.toukei-kentei.jp/) |
| 統計検定 データサイエンス基礎 | statistics-ds-basic | 0 | 問題未登録 | [公式案内](https://www.toukei-kentei.jp/) |
| 統計検定 データサイエンス発展 | statistics-ds-advanced | 8 | 登録あり | [公式案内](https://www.toukei-kentei.jp/) |
| 統計検定 データサイエンスエキスパート | statistics-ds-expert | 2 | 登録あり | [公式案内](https://www.toukei-kentei.jp/) |

## 歴史・地理

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| 歴史能力検定 日本史1級 | rekiken-japan1 | 2 | 登録あり | [公式案内](https://www.rekiken.gr.jp/) |
| 歴史能力検定 日本史2級 | rekiken-japan2 | 9 | 登録あり | [公式案内](https://www.rekiken.gr.jp/) |
| 歴史能力検定 日本史3級 | rekiken-japan3 | 10 | 登録あり | [公式案内](https://www.rekiken.gr.jp/) |
| 歴史能力検定 世界史1級 | rekiken-world1 | 2 | 登録あり | [公式案内](https://www.rekiken.gr.jp/) |
| 歴史能力検定 世界史2級 | rekiken-world2 | 5 | 登録あり | [公式案内](https://www.rekiken.gr.jp/) |
| 歴史能力検定 世界史3級 | rekiken-world3 | 10 | 登録あり | [公式案内](https://www.rekiken.gr.jp/) |
| 歴史能力検定 準3級 | rekiken-pre3 | 10 | 登録あり | [公式案内](https://www.rekiken.gr.jp/) |
| 歴史能力検定4級 | rekiken4 | 10 | 登録あり | [公式案内](https://www.rekiken.gr.jp/) |
| 歴史能力検定5級 | rekiken5 | 8 | 登録あり | [公式案内](https://www.rekiken.gr.jp/) |
| 地図地理検定 基礎 | map-geography-basic | 60 | 登録あり | [公式案内](https://www.jmc.or.jp/keihatsu-kyouiku/chizuken/about-kentei/) |
| 地図地理検定 専門 | map-geography-specialist | 72 | 登録あり | [公式案内](https://www.jmc.or.jp/keihatsu-kyouiku/chizuken/about-kentei/) |

## 電気・通信

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| 第一種電気工事士 | electrician1 | 300 | 登録あり | [公式案内](https://www.shiken.or.jp/) |
| 第二種電気工事士 | electrician2 | 550 | 登録あり | [公式案内](https://www.shiken.or.jp/) |
| 第一種電気主任技術者 | denken1 | 1258 | 登録あり | [公式案内](https://www.shiken.or.jp/) |
| 第二種電気主任技術者 | denken2 | 1150 | 登録あり | [公式案内](https://www.shiken.or.jp/) |
| 第三種電気主任技術者 | denken3 | 640 | 登録あり | [公式案内](https://www.shiken.or.jp/) |
| 電気通信主任技術者 伝送交換主任技術者 | telecom-transmission | 1319 | 登録あり | [公式案内](https://www.dekyo.or.jp/shiken/) |
| 電気通信主任技術者 線路主任技術者 | telecom-line | 1319 | 登録あり | [公式案内](https://www.dekyo.or.jp/shiken/) |
| 工事担任者 総合通信 | telecom-installer-general | 3976 | 登録あり | [公式案内](https://www.dekyo.or.jp/shiken/) |
| 工事担任者 第一級アナログ通信 | telecom-installer-analog1 | 288 | 登録あり | [公式案内](https://www.dekyo.or.jp/shiken/) |
| 工事担任者 第二級アナログ通信 | telecom-installer-analog2 | 248 | 登録あり | [公式案内](https://www.dekyo.or.jp/shiken/) |
| 工事担任者 第一級デジタル通信 | telecom-installer-digital1 | 288 | 登録あり | [公式案内](https://www.dekyo.or.jp/shiken/) |
| 工事担任者 第二級デジタル通信 | telecom-installer-digital2 | 248 | 登録あり | [公式案内](https://www.dekyo.or.jp/shiken/) |
| 第一級陸上無線技術士 | radio-land1 | 350 | 登録あり | [公式案内](https://www.nichimu.or.jp/) |
| 第二級陸上無線技術士 | radio-land2 | 350 | 登録あり | [公式案内](https://www.nichimu.or.jp/) |
| 第一級陸上特殊無線技士 | radio-land-special1 | 144 | 登録あり | [公式案内](https://www.nichimu.or.jp/) |
| 第二級陸上特殊無線技士 | radio-land-special2 | 1032 | 登録あり | [公式案内](https://www.nichimu.or.jp/) |
| 第三級陸上特殊無線技士 | radio-land-special3 | 48 | 登録あり | [公式案内](https://www.nichimu.or.jp/) |
| 第一級アマチュア無線技士 | radio-amateur1 | 4170 | 登録あり | [公式案内](https://www.nichimu.or.jp/) |
| 第二級アマチュア無線技士 | radio-amateur2 | 297 | 登録あり | [公式案内](https://www.nichimu.or.jp/) |
| 第三級アマチュア無線技士 | radio-amateur3 | 0 | 問題未登録 | [公式案内](https://www.nichimu.or.jp/) |
| 第四級アマチュア無線技士 | radio-amateur4 | 0 | 問題未登録 | [公式案内](https://www.nichimu.or.jp/) |
| 第一級総合無線通信士 | radio-general1 | 315 | 登録あり | [公式案内](https://www.nichimu.or.jp/) |
| 第二級総合無線通信士 | radio-general2 | 360 | 登録あり | [公式案内](https://www.nichimu.or.jp/) |
| 第三級総合無線通信士 | radio-general3 | 292 | 登録あり | [公式案内](https://www.nichimu.or.jp/) |
| 航空無線通信士 | radio-aeronautical | 148 | 登録あり | [公式案内](https://www.nichimu.or.jp/) |
| 第四級海上無線通信士 | radio-maritime4 | 126 | 登録あり | [公式案内](https://www.nichimu.or.jp/) |

## 建築・土木

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| 一級建築士 | architect1 | 1329 | 登録あり | [公式案内](https://www.jaeic.or.jp/) |
| 二級建築士 | architect2 | 899 | 登録あり | [公式案内](https://www.jaeic.or.jp/) |
| 木造建築士 | architect-wood | 899 | 登録あり | [公式案内](https://www.jaeic.or.jp/) |
| 建築設備士 | building-equipment | 935 | 登録あり | [公式案内](https://www.jaeic.or.jp/) |
| インテリアプランナー | interior-planner | 439 | 登録あり | [公式案内](https://www.jaeic.or.jp/) |
| 1級土木施工管理技士 | civil-management1 | 879 | 登録あり | [公式案内](https://www.jctc.jp/) |
| 2級土木施工管理技士 | civil-management2 | 972 | 登録あり | [公式案内](https://www.jctc.jp/) |
| 1級管工事施工管理技士 | pipe-management1 | 70 | 登録あり | [公式案内](https://www.jctc.jp/) |
| 2級管工事施工管理技士 | pipe-management2 | 103 | 登録あり | [公式案内](https://www.jctc.jp/) |
| 1級造園施工管理技士 | landscape-management1 | 325 | 登録あり | [公式案内](https://www.jctc.jp/) |
| 2級造園施工管理技士 | landscape-management2 | 440 | 登録あり | [公式案内](https://www.jctc.jp/) |
| 1級電気通信工事施工管理技士 | telecom-management1 | 90 | 登録あり | [公式案内](https://www.jctc.jp/) |
| 2級電気通信工事施工管理技士 | telecom-management2 | 130 | 登録あり | [公式案内](https://www.jctc.jp/) |
| 測量士 | surveyor | 140 | 登録あり | [公式案内](https://www.gsi.go.jp/LAW/SHIKEN/past.html) |
| 測量士補 | surveyor-assistant | 140 | 登録あり | [公式案内](https://www.gsi.go.jp/LAW/SHIKEN/past.html) |

## 不動産

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| 宅地建物取引士 | takken | 2694 | 登録あり | [公式案内](https://www.retio.or.jp/exam/) |
| マンション管理士 | mankan | 347 | 登録あり | [公式案内](https://www.mankan.org/) |
| 管理業務主任者 | management-chief | 894 | 登録あり | [公式案内](https://www.kanrikyo.or.jp/) |
| 賃貸不動産経営管理士 | rental-manager | 0 | 問題未登録 | [公式案内](https://www.chintaikanrishi.jp/) |

## 安全・消防・設備

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| 危険物取扱者 甲種 | hazmat-a | 0 | 問題未登録 | [公式案内](https://www.shoubo-shiken.or.jp/kikenbutsu/) |
| 危険物取扱者 乙種第1類 | hazmat-b1 | 0 | 問題未登録 | [公式案内](https://www.shoubo-shiken.or.jp/kikenbutsu/) |
| 危険物取扱者 乙種第2類 | hazmat-b2 | 0 | 問題未登録 | [公式案内](https://www.shoubo-shiken.or.jp/kikenbutsu/) |
| 危険物取扱者 乙種第3類 | hazmat-b3 | 0 | 問題未登録 | [公式案内](https://www.shoubo-shiken.or.jp/kikenbutsu/) |
| 危険物取扱者 乙種第4類 | hazmat-b4 | 35 | 登録あり | [公式案内](https://www.shoubo-shiken.or.jp/kikenbutsu/) |
| 危険物取扱者 乙種第5類 | hazmat-b5 | 0 | 問題未登録 | [公式案内](https://www.shoubo-shiken.or.jp/kikenbutsu/) |
| 危険物取扱者 乙種第6類 | hazmat-b6 | 0 | 問題未登録 | [公式案内](https://www.shoubo-shiken.or.jp/kikenbutsu/) |
| 危険物取扱者 丙種 | hazmat-c | 50 | 登録あり | [公式案内](https://www.shoubo-shiken.or.jp/kikenbutsu/) |
| 消防設備士 甲種特類 | fire-a-special | 0 | 問題未登録 | [公式案内](https://www.shoubo-shiken.or.jp/shoubou/) |
| 消防設備士 甲種第1類 | fire-a1 | 0 | 問題未登録 | [公式案内](https://www.shoubo-shiken.or.jp/shoubou/) |
| 消防設備士 甲種第2類 | fire-a2 | 0 | 問題未登録 | [公式案内](https://www.shoubo-shiken.or.jp/shoubou/) |
| 消防設備士 甲種第3類 | fire-a3 | 0 | 問題未登録 | [公式案内](https://www.shoubo-shiken.or.jp/shoubou/) |
| 消防設備士 甲種第4類 | fire-a4 | 0 | 問題未登録 | [公式案内](https://www.shoubo-shiken.or.jp/shoubou/) |
| 消防設備士 甲種第5類 | fire-a5 | 0 | 問題未登録 | [公式案内](https://www.shoubo-shiken.or.jp/shoubou/) |
| 消防設備士 乙種第1類 | fire-b1 | 0 | 問題未登録 | [公式案内](https://www.shoubo-shiken.or.jp/shoubou/) |
| 消防設備士 乙種第2類 | fire-b2 | 0 | 問題未登録 | [公式案内](https://www.shoubo-shiken.or.jp/shoubou/) |
| 消防設備士 乙種第3類 | fire-b3 | 0 | 問題未登録 | [公式案内](https://www.shoubo-shiken.or.jp/shoubou/) |
| 消防設備士 乙種第4類 | fire-b4 | 0 | 問題未登録 | [公式案内](https://www.shoubo-shiken.or.jp/shoubou/) |
| 消防設備士 乙種第5類 | fire-b5 | 0 | 問題未登録 | [公式案内](https://www.shoubo-shiken.or.jp/shoubou/) |
| 消防設備士 乙種第6類 | fire-b6 | 0 | 問題未登録 | [公式案内](https://www.shoubo-shiken.or.jp/shoubou/) |
| 消防設備士 乙種第7類 | fire-b7 | 0 | 問題未登録 | [公式案内](https://www.shoubo-shiken.or.jp/shoubou/) |
| 消防設備士 甲種 筆記公開問題（各類の抜粋） | fire-a-public | 34 | 登録あり | [公式案内](https://www.shoubo-shiken.or.jp/shoubou/) |
| 消防設備士 乙種 筆記公開問題（各類の抜粋） | fire-b-public | 42 | 登録あり | [公式案内](https://www.shoubo-shiken.or.jp/shoubou/) |
| 第一種衛生管理者 | health1 | 88 | 登録あり | [公式案内](https://www.exam.or.jp/) |
| 第二種衛生管理者 | health2 | 330 | 登録あり | [公式案内](https://www.exam.or.jp/) |
| 特級ボイラー技士 | boiler-special | 0 | 問題未登録 | [公式案内](https://www.exam.or.jp/) |
| 一級ボイラー技士 | boiler1 | 80 | 登録あり | [公式案内](https://www.exam.or.jp/) |
| 二級ボイラー技士 | boiler2 | 760 | 登録あり | [公式案内](https://www.exam.or.jp/) |
| ボイラー整備士 | boiler-maintenance | 60 | 登録あり | [公式案内](https://www.exam.or.jp/) |
| クレーン・デリック運転士（限定なし） | crane-derrick | 0 | 問題未登録 | [公式案内](https://www.exam.or.jp/) |
| 移動式クレーン運転士 | mobile-crane | 80 | 登録あり | [公式案内](https://www.exam.or.jp/) |
| 揚貨装置運転士 | lifting-derrick | 80 | 登録あり | [公式案内](https://www.exam.or.jp/) |
| 潜水士 | diver | 80 | 登録あり | [公式案内](https://www.exam.or.jp/) |
| 第一種作業環境測定士 | work-environment1 | 0 | 問題未登録 | [公式案内](https://www.exam.or.jp/) |
| 第二種作業環境測定士 | work-environment2 | 0 | 問題未登録 | [公式案内](https://www.exam.or.jp/) |
| 労働衛生コンサルタント | health-consultant | 90 | 登録あり | [公式案内](https://www.exam.or.jp/) |
| 労働安全コンサルタント | safety-consultant | 90 | 登録あり | [公式案内](https://www.exam.or.jp/) |
| 消防設備士向け共通対策教材（GitHub） | github-fire-common | 56 | 登録あり | — |

## 医療・健康

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| 医師国家試験 | doctor | 2183 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 歯科医師国家試験 | dentist | 1695 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 薬剤師国家試験 | pharmacist | 1993 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 看護師国家試験 | nurse | 2609 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 保健師国家試験 | public-health-nurse | 1172 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 助産師国家試験 | midwife | 1137 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 臨床検査技師国家試験 | clinical-lab | 1608 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 診療放射線技師国家試験 | radiological-tech | 1626 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 理学療法士国家試験 | physical-therapist | 1648 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 作業療法士国家試験 | occupational-therapist | 1501 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 視能訓練士国家試験 | orthoptist | 1107 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 臨床工学技士国家試験 | clinical-engineer | 178 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 言語聴覚士国家試験 | speech-therapist | 0 | 問題未登録 | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 歯科衛生士国家試験 | dental-hygienist | 0 | 問題未登録 | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 歯科技工士国家試験 | dental-technician | 0 | 問題未登録 | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 救急救命士国家試験 | emergency-tech | 0 | 問題未登録 | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 管理栄養士国家試験 | nutritionist | 45 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| はり師国家試験 | acupuncturist | 1016 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| きゅう師国家試験 | moxibustion | 1016 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| あん摩マッサージ指圧師国家試験 | massage-therapist | 954 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 柔道整復師国家試験 | judo-therapist | 1760 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 公認心理師試験 | psychologist | 0 | 問題未登録 | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 登録販売者試験 | drug-seller | 0 | 問題未登録 | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 第二種衛生管理者向け自作対策教材 | health2-original | 50 | 登録あり | — |

## 福祉・介護・保育

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| 社会福祉士国家試験 | social-worker | 408 | 登録あり | [公式案内](https://www.sssc.or.jp/) |
| 介護福祉士国家試験 | care-worker | 374 | 登録あり | [公式案内](https://www.sssc.or.jp/) |
| 精神保健福祉士国家試験 | mental-social-worker | 427 | 登録あり | [公式案内](https://www.sssc.or.jp/) |
| 保育士試験 | childcare | 752 | 登録あり | [公式案内](https://www.hoyokyo.or.jp/exam/) |
| 福祉住環境コーディネーター検定1級 | welfare-housing1 | 1 | 登録あり | [公式案内](https://kentei.tokyo-cci.or.jp/fukushi/) |
| 福祉住環境コーディネーター検定2級 | welfare-housing2 | 1 | 登録あり | [公式案内](https://kentei.tokyo-cci.or.jp/fukushi/) |
| 福祉住環境コーディネーター検定3級 | welfare-housing3 | 2 | 登録あり | [公式案内](https://kentei.tokyo-cci.or.jp/fukushi/) |

## 農業・食品

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| 日本農業検定1級 | agri1 | 417 | 登録あり | [公式案内](https://nou-ken.jp/application/individual/) |
| 日本農業検定2級 | agri2 | 417 | 登録あり | [公式案内](https://nou-ken.jp/application/individual/) |
| 日本農業検定3級 | agri3 | 297 | 登録あり | [公式案内](https://nou-ken.jp/application/individual/) |
| 食生活アドバイザー2級 | food-advisor2 | 0 | 問題未登録 | [公式案内](https://flanet.jp/) |
| 食生活アドバイザー3級 | food-advisor3 | 0 | 問題未登録 | [公式案内](https://flanet.jp/) |
| 調理師試験 | cook | 857 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 製菓衛生師試験 | confectionery-hygiene | 358 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 日本農業検定3級向け自作対策教材 | agri3-original | 50 | 登録あり | — |

## 観光・運輸

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| 総合旅行業務取扱管理者 | travel-general | 695 | 登録あり | [公式案内](https://www.jata-net.or.jp/) |
| 国内旅行業務取扱管理者 | travel-domestic | 555 | 登録あり | [公式案内](https://www.anta.or.jp/) |
| 全国通訳案内士試験 | tour-guide | 291 | 登録あり | [公式案内](https://www.jnto.go.jp/projects/visitor-support/interpreter-guide-exams/) |
| 運行管理者（貨物） | transport-cargo | 733 | 登録あり | [公式案内](https://www.unkan.or.jp/) |
| 運行管理者（旅客） | transport-passenger | 456 | 登録あり | [公式案内](https://www.unkan.or.jp/) |

## デザイン・生活

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| 色彩検定1級 | color1 | 0 | 問題未登録 | [公式案内](https://www.aft.or.jp/exam-orders) |
| 色彩検定2級 | color2 | 0 | 問題未登録 | [公式案内](https://www.aft.or.jp/exam-orders) |
| 色彩検定3級 | color3 | 0 | 問題未登録 | [公式案内](https://www.aft.or.jp/exam-orders) |
| 色彩検定UC級 | color-uc | 0 | 問題未登録 | [公式案内](https://www.aft.or.jp/exam-orders) |
| カラーコーディネーター検定 スタンダードクラス | color-coordinator-standard | 1 | 登録あり | [公式案内](https://kentei.tokyo-cci.or.jp/color/) |
| カラーコーディネーター検定 アドバンスクラス | color-coordinator-advanced | 1 | 登録あり | [公式案内](https://kentei.tokyo-cci.or.jp/color/) |
| 理容師国家試験 | barber | 1013 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |
| 美容師国家試験 | beautician | 1030 | 登録あり | [公式案内](https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html) |

## 環境・自然科学

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| 環境社会検定（eco検定） | eco | 3 | 登録あり | [公式案内](https://kentei.tokyo-cci.or.jp/eco/) |
| 気象予報士試験 | weather | 566 | 登録あり | [公式案内](https://www.jmbsc.or.jp/jp/examination/examination-1.html) |

## 公務員

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| 国家公務員総合職（院卒者試験） | civil-general-grad | 716 | 登録あり | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 国家公務員総合職（大卒程度試験） | civil-general-univ | 95 | 登録あり | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 国家公務員一般職（大卒程度試験） | civil-regular-univ | 351 | 登録あり | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 国家公務員一般職（高卒者試験） | civil-regular-high | 0 | 問題未登録 | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 国税専門官採用試験 | tax-specialist | 250 | 登録あり | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 財務専門官採用試験 | finance-specialist | 213 | 登録あり | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 労働基準監督官採用試験 | labor-inspector | 94 | 登録あり | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 皇宮護衛官採用試験（大卒程度試験） | imperial-guard-univ | 0 | 問題未登録 | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 刑務官採用試験（大卒程度試験） | prison-officer-univ | 0 | 問題未登録 | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 法務省専門職員（人間科学）採用試験 | justice-human-science | 0 | 問題未登録 | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 食品衛生監視員採用試験 | food-sanitation-inspector | 0 | 問題未登録 | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 航空管制官採用試験 | air-traffic-controller | 60 | 登録あり | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 海上保安官採用試験 | coast-guard-officer | 0 | 問題未登録 | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 国家公務員一般職（社会人試験） | civil-regular-career | 0 | 問題未登録 | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 皇宮護衛官採用試験（高卒程度試験） | imperial-guard-high | 40 | 登録あり | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 刑務官採用試験（高卒程度試験） | prison-officer-high | 40 | 登録あり | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 入国警備官採用試験 | immigration-guard | 40 | 登録あり | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 税務職員採用試験 | tax-officer | 0 | 問題未登録 | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 航空保安大学校学生採用試験 | aviation-security-student | 40 | 登録あり | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 海上保安大学校学生採用試験 | coast-guard-academy | 0 | 問題未登録 | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 海上保安学校学生採用試験 | coast-guard-school | 40 | 登録あり | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 気象大学校学生採用試験 | meteorological-college | 0 | 問題未登録 | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |
| 国家公務員経験者採用試験 | civil-experienced | 0 | 問題未登録 | [公式案内](https://www.jinji.go.jp/saiyo/siken.html) |

## 自作一般教材

| 試験・教材 | ID | 登録数 | 状態 | 公式案内 |
| --- | --- | ---: | --- | --- |
| 自作会計・経営教材 | original-accounting | 48 | 登録あり | — |
| 自作電気・工学教材 | original-engineering | 48 | 登録あり | — |
| 自作英語教材 | original-english | 48 | 登録あり | — |
| 自作地理教材 | original-geography | 48 | 登録あり | — |
| 自作日本史教材 | original-japan-history | 48 | 登録あり | — |
| 自作国語教材 | original-japanese | 48 | 登録あり | — |
| 自作数学教材 | original-math | 71 | 登録あり | — |
| 自作IT・AI教材 | original-it | 48 | 登録あり | — |
| 自作自然科学教材 | original-science | 48 | 登録あり | — |
| 自作統計教材 | original-statistics | 48 | 登録あり | — |
| 自作世界史教材 | original-world-history | 48 | 登録あり | — |
