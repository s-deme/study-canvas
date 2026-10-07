# GitHubにある試験問題の候補一覧

試験ごとの検索済み・候補未発見・要精査の管理は [GitHub調査台帳](github-exam-search.md) を参照します。次回の検索は台帳の未調査だけを対象にし、候補未発見を再検索しません。

このページは調査時点の記録です。現在の取得元別の収録状況は [取り込み状況](import-status.md)、実施時点の非収録理由・検証範囲は [取り込み記録](github-import-results.md) を参照してください。

調査日：2026-10-06。study-canvasの試験一覧を起点に、日本の資格・国家試験を中心として、GitHubの試験名・ローマ字名・過去問・問題などを検索しました。AWS・LPICは英語名でも検索しています。

今回ファイル一覧を調べた37リポジトリのうち、問題本文を確認できたものは22件、ファイルの存在などまで確認したものは9件、学習用の設問本文を確認できなかったものは6件です。22件には既存台帳の保育士候補1件を含み、新しく本文を確認した候補は21件です。GitHub全体・全321試験の網羅一覧ではありません。

次の原本照合の候補は、一級建築士、マンション管理士、理学療法士、保育士です。年度・問番号・正答や原本をたどれる構成が確認できました。これは収録可能と判定した意味ではありません。今回の作業は候補調査で、アプリへの追加、原本照合、正答検証は実施していません。

## 問題本文を確認した候補

「過去問表記」は提供元が過去問として掲載している意味です。公式原本との一致は別途確認します。件数はJSONの配列等を数えたものとREADME記載を区別し、年度違い・肢単位・模擬問題を合算した総問題数は出していません。リンクは確認時のコミットに固定しています。

| 試験 | リポジトリと確認ファイル | 形式 | 内容と範囲 | 種別 |
| --- | --- | --- | --- | --- |
| 一級建築士 | [tossh23/architect-study-app](https://github.com/tossh23/architect-study-app/blob/4551d7777646edaf527266ba30128812ab09cb8c/csv/utf8_2025-kakomon.csv) — `csv/utf8_2025-kakomon.csv` | 年度別CSV | 2016〜2025年のファイルあり。2025年分の本文・4選択肢・正答を確認。 | 過去問表記 |
| マンション管理士 | [pousan/mansion-exam-prediction](https://github.com/pousan/mansion-exam-prediction/blob/3fe69828392e3eb51d109d44bb78ec988e09d750/02_%E3%83%9E%E3%82%B9%E3%82%BF%E3%83%BC%E3%83%87%E3%83%BC%E3%82%BF/%E5%95%8F%E9%A1%8C%E3%83%86%E3%82%AD%E3%82%B9%E3%83%88.jsonl) — `02_マスターデータ/問題テキスト.jsonl` | JSONL＋正解CSV＋PDF | 2019〜2025年。本文350件、正解表・問題PDF・解答PDFあり。 | 過去問表記 |
| 理学療法士 | [medicalillustotter/PTOT-kokushi-study](https://github.com/medicalillustotter/PTOT-kokushi-study/blob/66e9405e3c33c3f81a7358aa19e1ccaaaea7e34d/data/questions.json) — `data/questions.json` | JSON | 第61回200問。画像必要20問、解説は全200問空欄。作業療法士の収録は確認できない。 | 過去問表記 |
| 保育士 | [yma3mama-tech/hoikushi-shiken-app](https://github.com/yma3mama-tech/hoikushi-shiken-app/blob/4d6f268c787529f63d318fc7dad00f78b545ac3c/index.html) — `index.html` | HTML内JSON | R7後期・R8前期、9科目310問。既存の取得台帳にある候補。 | 過去問表記 |
| 社労士 | [kikkawamotoharu/sharoushi-app](https://github.com/kikkawamotoharu/sharoushi-app/blob/dbb451c9f8051631950929a6b56c08e79cbfd793/INDEX.html) — `INDEX.html` | HTML内配列 | 年度・問番号付きの正誤問題。法改正に合わせて本文を書き換えた例あり。小文字index.htmlは大容量で取得不可、別のINDEX.htmlを確認。 | 再構成を含む |
| 運行管理者 貨物 | [masatopapa/unkan-quiz](https://github.com/masatopapa/unkan-quiz/blob/c46bee3448733cf30484d43a255d3f8a450c1cbc/index.html) — `index.html` | HTML内JSON | READMEはR2〜R6の216問と記載。複数選択を4択に再構成、解説はAI作成と明記。 | 再構成 |
| 行政書士 | [mjrt0817/gyoseishoshi](https://github.com/mjrt0817/gyoseishoshi/blob/2a2660c8b81f4bb6613cd38b16c4cd1419154600/questions.csv) — `questions.csv` | CSV | 本文・選択肢・正答あり。別途terms.csv、written_prompts.csv。app_data_summary.jsonの記載は382問・記述24題。 | 対策問題 |
| 宅建 | [masaosan425-alt/takken-app](https://github.com/masaosan425-alt/takken-app/blob/72127a69ea7c2b1afbe7396040220def8cc6ee13/src/data/questions.ts) — `src/data/questions.ts` | TypeScript配列 | 正誤・選択式の本文・選択肢・正答・解説あり。年度別公式過去問としての一致は未確認。 | 対策問題 |
| 保育士 | [nappe0209/hoikushi-quiz](https://github.com/nappe0209/hoikushi-quiz/blob/9b312c6fa255e432a124728fe6ae6327e5df7e74/src/App.js) — `src/App.js` | JavaScript配列 | 9科目の問題・選択肢・正答・解説を内蔵。 | 対策問題 |
| 危険物 丙種 | [inamuu/KikenbutsuExams](https://github.com/inamuu/KikenbutsuExams/blob/c20c30d75ce7a3907fe5940019e4fee20496a38f/data/practiceExams.mjs) — `data/practiceExams.mjs` | MJS | 25問の本文・選択肢・正答あり。READMEが公開PDFの論点を再構成したオリジナル問題と明記。 | オリジナルと明記 |
| 第二種衛生管理者 | [shajime0909-bit/eisei2](https://github.com/shajime0909-bit/eisei2/blob/6dc451738952a710c0217b6652d3c938c844bb6c/index.html) — `index.html` | HTML | 本文・5選択肢・正答・解説を内蔵。READMEはClaudeアーティファクト由来と説明。 | 対策問題 |
| 消防設備士 | [no2shi4ni0-dot/syoubou-quiz](https://github.com/no2shi4ni0-dot/syoubou-quiz/blob/8e48acf9a985997502f3c7549d39692dfbd5085d/quiz_data.py) — `quiz_data.py` | Pythonのデータ定義 | 自動火災報知設備・消防法令などの問題・選択肢・正答あり。級・類の完全対応は未確認。 | 対策問題 |
| FP2級 | [5150kouhei-rgb/fp2-drill](https://github.com/5150kouhei-rgb/fp2-drill/blob/3b9fd56fdcf27f43dcfebf8c8c72866f9f82ddb8/index.html) — `index.html` | HTML内データ | 問題文・選択肢・解説あり。公式問題との一致・出典の確定は別途必要。 | 出典未確定 |
| FP3級 | [fp-hitorigoto/fp3-quiz](https://github.com/fp-hitorigoto/fp3-quiz/blob/6c0a955097345ede7b9d86821da24933155849dc/index.html) — `index.html` | HTML内配列 | 問題・4選択肢・正答・解説あり。「過去問」の名称だけでは公式過去問と確定できない。 | 出典未確定 |
| 簿記3級 | [edwin6780-tech/Boki-3](https://github.com/edwin6780-tech/Boki-3/blob/d649171eb1843beed4eb912510ca804b6889c53e/CBT.txt) — `CBT.txt` | TXT内HTML | 仕訳問題と借方・貸方の模範解答を内蔵。過去問としての出典は未確認。 | 対策問題 |
| 国内旅行業務取扱管理者 | [yuaoki08/kokunai-travel-exam](https://github.com/yuaoki08/kokunai-travel-exam/blob/2d8694765c578d638ad78294bb121a2037e2120f/questions.js) — `questions.js` | JavaScript＋bank/*.js | READMEは205問と記載。主要・頻出論点から作成した非公式教材。MIT表記あり。 | 対策問題 |
| 気象予報士 | [pose-shell/weather-quiz-app](https://github.com/pose-shell/weather-quiz-app/blob/11c3232201d140c41baab33f8eee6f8549867d8b/assets/data/questions/observation.json) — `assets/data/questions/observation.json` | JSON | 観測分野5問の本文を確認。数値予報にも別JSONあり。LICENSE-CONTENT.mdに教材の利用制限があり、コードのMITとは別。 | 対策問題 利用条件別 |
| 調理師 | [nomu770501-Git/chouri-quiz](https://github.com/nomu770501-Git/chouri-quiz/blob/369c7582ad43208b1790d65f9c3f047bbf5963aa/index.html) — `index.html` | HTML内JSON | 練習問題600問の本文・選択肢・正答・解説あり。 | 練習問題 |
| 管理栄養士 | [bang-prog/nutritionist](https://github.com/bang-prog/nutritionist/blob/4af250831e8f434b4b858ec8ccc17b9530db5306/data/questions.json) — `data/questions.json` | JSON＋PDF | JSONに45問。年度・isAIGeneratedの値はあるが、公式過去問との一致は未確認。 | 出典未確定 |
| 中小企業診断士 | [toru830/shindanshi](https://github.com/toru830/shindanshi/blob/78285be816164fe84ee62d369d9e8459a68c0228/questions.json) — `questions.json` | JSON＋PDF | 2025年経済学の本文・選択肢・正答あり。過去問原本との一致は未確認。 | 出典未確定 |
| 英検 | [wangchang2049/eikenQuest](https://github.com/wangchang2049/eikenQuest/blob/d487b2b279c4e13de99889b4ab1068b7a9e0a048/data/grade2/test_1.json) — `data/grade2/test_1.json` | JSON | 2級模擬テスト1は63件。READMEが選択肢の生成・言い換えを記載。意味が近い選択肢を含む例があり、品質確認が必要。 | 生成を含む模擬問題 |
| AWS Cloud Practitioner | [Ditectrev/Amazon-Web-Services-AWS-Certified-Cloud-Practitioner-CLF-C02-Practice-Tests-Exams-Questions-Answers](https://github.com/Ditectrev/Amazon-Web-Services-AWS-Certified-Cloud-Practitioner-CLF-C02-Practice-Tests-Exams-Questions-Answers/blob/765cfeae325f646db029f70a7212848a8affec3f/README.md) — `README.md` | Markdown | 英語の問題・選択肢・正答をREADMEに掲載。CLF-C02の対策教材。公式サンプル・公開過去問とは未確定。 | 対策問題 |

気象予報士候補の教材条件は [LICENSE-CONTENT.md](https://github.com/pose-shell/weather-quiz-app/blob/11c3232201d140c41baab33f8eee6f8549867d8b/LICENSE-CONTENT.md)、運行管理者の再構成・AI解説の説明は [README](https://github.com/masatopapa/unkan-quiz/blob/c46bee3448733cf30484d43a255d3f8a450c1cbc/README.md)、英検の生成・言い換えの説明は [ReadMe](https://github.com/wangchang2049/eikenQuest/blob/d487b2b279c4e13de99889b4ab1068b7a9e0a048/ReadMe.md) にあります。その他の候補も、問題本文・解説・画像それぞれの出典と利用条件を収録前に確定します。

## ファイルの存在などまで確認した候補

問題データがあると推測できるものも含みますが、本文確認済みの22件には数えません。

| 試験 | リポジトリ | 確認した対象 | 状態 |
| --- | --- | --- | --- |
| 宅建 | [hangonkou-ux/takken-app](https://github.com/hangonkou-ux/takken-app/tree/5759b6e42303aed78359967ad4e7a8a5fd254088) | 宅建過去問.csv | 約1.35MBのCSV。ファイル一覧まで。本文・件数・公式一致は未確認。 |
| 宅建 | [makio1988/takkenkakomon](https://github.com/makio1988/takkenkakomon/tree/dd616962423cd5637c2d608e493616bcaecb156f) | takken-exam-system/takken_exam.db | SQLite DBとuploads内PDFあり。DB・PDF本文は未読。 |
| 宅建 | [Fkzyk/takken-dojo](https://github.com/Fkzyk/takken-dojo/tree/f3e20d55d5ddba57c60d9aae76483799f8ca2211) | index.html | 約983KBのHTML。本文未確認。 |
| 理学療法士 | [kita0709/pt-exam-study-app](https://github.com/kita0709/pt-exam-study-app/tree/fea0d90122c7b240e5ddf1382a7a221c0da5c4d9) | questions.xlsx | 問題用Excelの存在を確認。中身は未読。 |
| 柔道整復師 | [nekomarugt/j-kokushi-portal](https://github.com/nekomarugt/j-kokushi-portal/tree/7a5076bd2a8b57f2eaea4ded4aaa68307c39096e) | anatomy/questions.json | 既存の取得台帳で保留。問題ファイル多数あり。今回の本文・件数・全体の利用条件は未確認。 |
| 国家試験関連 | [oga3999/kokushi](https://github.com/oga3999/kokushi/tree/210cc6a2c0feb5cfe20d1675f42f57889649bdcc) | index.html | 大きなPHPサイト。対象試験・配布問題データを今回確定できず。 |
| 臨床工学技士 | [honnili/ClinicalEngineer](https://github.com/honnili/ClinicalEngineer/tree/d2612788e35da32172cac509825af27f9f21a240) | services/db_utils.py | DB連携や学習機能のコードあり。配布問題の実体は今回確定できず。 |
| 漢検 | [kyuuki/kanken-rails](https://github.com/kyuuki/kanken-rails/tree/c249e0696aae3d603e9cfa48554501190a517a90) | db | 学習アプリのコードあり。公開問題データの実体は今回確定できず。 |
| LPIC | [Valsuh45/LPIC-Past-Questions](https://github.com/Valsuh45/LPIC-Past-Questions/tree/7f647bf7b8552ff61ea36be43ec74e8243fc3f98) | README.md | PDFの存在のみ確認。第三者教材名・dumps名を含む。PDF本文・出典・利用条件は未確認。 |

## 今回の問題データ候補から外したもの

| 試験 | リポジトリと確認ファイル | 理由 |
| --- | --- | --- |
| 宅建 | [epaulcnjp-design/takken-quiz](https://github.com/epaulcnjp-design/takken-quiz/blob/872cc63e5bea420939be91f2737369612c332af5/index.html) | 利用者のWord問題集を取り込むコード。配布問題本文は確認できない。 |
| 統計検定 | [sshNH/statistics-kentei-v2](https://github.com/sshNH/statistics-kentei-v2/blob/635b860eeccd9462e8065bac01e6587d15d805da/index.html) | Q1〜Q5等の記録枠を扱う学習管理。設問本文は確認できない。 |
| 気象予報士 | [sparkrones/met_exam](https://github.com/sparkrones/met_exam/blob/a4af9f0723cdd6269ea04c650e1512c955378d97/index.html) | 学習計画と使用教材の管理。設問本文は確認できない。 |
| 社会福祉士 | [probono-a/shakaifukushi-quiz](https://github.com/probono-a/shakaifukushi-quiz/blob/a4b6a6791e1a6e085ae5529905d75804442edc39/README.md) | READMEが問題データ非同梱と明記。 |
| 国内旅行業務取扱管理者 | [zakiyama777/domestic-travel-manager-coach](https://github.com/zakiyama777/domestic-travel-manager-coach/blob/a6c6c72e45be70b15cd7b8352c99e906d3ad006c/README.md) | 確認したツリーはREADMEと.gitignoreのみ。 |
| 色彩検定 | [Sunmax0731/color-certification-exam-trainer](https://github.com/Sunmax0731/color-certification-exam-trainer/blob/3f3e1231315df7f3f3da2756fb15331771e0b1c1/data/questions.json) | 検証用の仮問題2件。具体的な学習問題を収録した候補には含めない。 |

## 未登録試験の追加候補（2026-10-06）

- [eulerex/jlpt-test](https://github.com/eulerex/jlpt-test/tree/215b7ffd509824388541ab826b82053c7b185cd3)：JLPT N1〜N5、normalized/。
- [keisks/j_bar_exam](https://github.com/keisks/j_bar_exam/tree/7442d495c2060077689583184adfeb205cdb5ba5)：司法試験短答式、questions/。
- [stueja/lpic-1-102-500-anki-flashcards](https://github.com/stueja/lpic-1-102-500-anki-flashcards/tree/7555455260bea19447b485e235db5eddcfd9febb)：LPIC-1試験102、deck.json。
- [MCCMDave/linux-essentials-quiz](https://github.com/MCCMDave/linux-essentials-quiz/tree/0bb38557635cb1443037cac8e9a202b98f5d6116)：Linux Essentials、fragen.json。
- [CarbonRaven/AWS-Quiz-SAA-C03](https://github.com/CarbonRaven/AWS-Quiz-SAA-C03/tree/cb847d5ab9733fa6663385a9a1adbcda98e6f590)：AWS SAA-C03、questions/。

## 既存の取得元

既存の [取得元台帳](github-sources.md) は12リポジトリと1件のGistです。今回の検索結果を「取得済み教材」としてそこへ追加してはいません。今回も確認した保育士・柔道整復師候補は上表に含みます。既存のほかの取得元は次のとおりです。これらの収録状況は [過去問の収録結果](github-material.md) を参照してください。

| 試験 | 既存の取得元 | 台帳上の用途 |
| --- | --- | --- |
| ITパスポート | [inamuu/ITPassportExams](https://github.com/inamuu/ITPassportExams) | 問題データと公式問題の照合 |
| 基本情報 | [kosukekkk-ops/fe-master-app](https://github.com/kosukekkk-ops/fe-master-app) | 公式問題の発見・照合 |
| 測量士補 | [onochin/assistant-surveyor-pwa](https://github.com/onochin/assistant-surveyor-pwa) | 公式原本の発見 |
| 第二種電気工事士 | [officeharukaze/denko2](https://github.com/officeharukaze/denko2) | 公式原本の発見 |
| 電気工事士 | [onokumao-png/gokaku-denki-quiz](https://github.com/onokumao-png/gokaku-denki-quiz) | 公式原本の発見 |
| 電験三種 | [Consuke/denken-with-llm](https://github.com/Consuke/denken-with-llm) | 公式原本の発見 |
| 医師・歯科医師 | [aistairc/medLLM_QA_benchmark](https://github.com/aistairc/medLLM_QA_benchmark) | 本文の公式原本照合 |
| 薬剤師 | [inumanma/Pharmacist-bench](https://github.com/inumanma/Pharmacist-bench) | 公式原本の発見 |
| 看護師・保健師・助産師 | [seika759931-cloud/quiz-app_web](https://github.com/seika759931-cloud/quiz-app_web) | CSVを発見元として使用 |
| 臨床検査技師 | [bioinfo-tsukuba/KensagishiQA](https://github.com/bioinfo-tsukuba/KensagishiQA) | 公式原本の発見 |

IPA各試験には [amapyonの過去問リンク集](https://gist.github.com/amapyon/477930159cb5b0c47f401b0d4a09b1aa) もあります。リンク集と設問本文を収録したデータは区別します。

## 検索だけでは本文を確定できなかった分野

今回の検索では、中国語検定、日本語能力試験の過去問、数学検定、歴史検定、公務員、登録販売者、Pythonエンジニア認定の模擬問題で本文確認済みの候補を得られませんでした。介護福祉士では問題名のリポジトリが見つかりましたが、検索結果のサイズが0で追加確認していません。試験名・読み方・英語名・リポジトリ説明によって検索結果が変わるため、「GitHubにない」という判定ではありません。

## 次に確認すること

2026-10-07追加確認：未登録試験の本文未確認3候補を固定コミットで取得しました。

- [AWS AI Practitioner](https://github.com/iamirtasam/AWS-AI-Practitioner-Exam-Mock/tree/ac64b85382987814f4d86c811af10b4c1e94047a)：教材を含むMIT。選択式504問を本人用教材へ変換し、並べ替え24問は未対応として除外。公式試験問題ではないオリジナル英語教材。正答・解説の内容は未検証。
- [Python基礎](https://github.com/ikuma-hiroyuki/python_engineer_basic_demo/tree/1dc6079993288065435dbcd714b2f96996836087)：生成模擬問題のJSONを取得。教材の収録許諾を確認できず保留。
- [土地家屋調査士](https://github.com/ThREE100/chosashi-app/tree/22fbc96e5cb9886082ffc46e281dfa11c65ca413)：択一JSONを取得（meta.countは413）。教材の収録許諾を確認できず保留。

既存候補を再変換せず追加候補だけを変換する場合は、`python scripts/prepare-github-candidates.py --repos owner/repository`。他の取得元の変換記録を保持します。

1. 一級建築士・マンション管理士・理学療法士・保育士から、公式原本URLと正答表を確定する。
2. 問題番号・選択肢・図版・削除問題・複数正答を原本と照合する。対策問題や再構成問題は公式過去問と別に扱う。
3. 出典・利用条件を確定したデータだけを既存の取得処理で保存し、取得台帳に登録する。
