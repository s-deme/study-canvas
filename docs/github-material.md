# GitHub経由の過去問収録

この文書の件数・保留状況は以下の実施時点の記録です。現在の登録数は [試験管理表](exam-inventory.md)、現在の収録状況は [取り込み状況](import-status.md) を参照してください。後続の候補取り込みによる登録は、この文書の保留記録とは別に管理します。

2026-10-06。GitHub上の公開問題データ・リンク集から公式原本をたどり、本人用教材に累計17,698問を追加しました。今回の追加は、問題未登録だった看護師・保健師・助産師・臨床検査技師の4試験5,952問です。追加前16,032問と合わせて21,984問です。問題・原本・画像・検査記録はGit対象外の `private-data/github-material/` に保存します。

## 収録結果

| 試験 | 追加 | 登録合計 |
| --- | ---: | ---: |
| ITパスポート | 1,900 | 1,900 |
| 情報セキュリティマネジメント | 445 | 460 |
| 基本情報技術者 | 1,598 | 1,624 |
| 応用情報技術者 | 1,739 | 2,469 |
| ITストラテジスト | 325 | 532 |
| システムアーキテクト | 300 | 507 |
| プロジェクトマネージャ | 300 | 498 |
| ネットワークスペシャリスト | 325 | 546 |
| データベーススペシャリスト | 325 | 533 |
| エンベデッドシステムスペシャリスト | 325 | 517 |
| ITサービスマネージャ | 325 | 526 |
| システム監査技術者 | 300 | 516 |
| 情報処理安全確保支援士 | 650 | 1,074 |
| 測量士（午前） | 140 | 140 |
| 測量士補 | 140 | 140 |
| 第一種電気工事士 | 300 | 300 |
| 第二種電気工事士 | 550 | 550 |
| 第三種電気主任技術者（電験三種） | 640 | 640 |
| 医師国家試験 | 397 | 397 |
| 歯科医師国家試験 | 383 | 383 |
| 薬剤師国家試験 | 339 | 339 |
| 看護師国家試験 | 2,441 | 2,441 |
| 保健師国家試験 | 1,165 | 1,165 |
| 助産師国家試験 | 1,111 | 1,111 |
| 臨床検査技師国家試験 | 1,235 | 1,235 |
| **計** | **17,698** | **既存の他教材を含め21,984** |

今回の4試験は2014〜2025年の公式原本から86冊5,952問を収録しました。看護師・保健師・助産師はGitHubの看護問題CSV、臨床検査技師はKensagishiQAを発見元とし、GitHub側の解説は転載せず、厚生労働省の公式冊子・正答表から登録しています。取得台帳にはコミット固定URLとSHA-256を保存しました。公式サイトの移動で切れた旧年度リンクは、確認した公式移動先から取得しました。

取得した127冊のうち41冊は、画像PDF・文字マップ・番号の全並び・正答表を確定できず保留です。収録した冊子内でも、削除問題・別の正答が認められる問題・数字記入式・選択肢番号を確定できない問題・別冊図版が必要なページは除外しました。原本ページを共有し、近接する共通症例のページも表示します。全問の目視確認は未実施です。詳細は `prepared/expansion-report.json` に記録します。

柔道整復師・保育士・宅建・管理栄養士・社会福祉士・臨床工学技士などのGitHub候補も探索しました。柔道整復師・保育士の候補ファイルは取得台帳に記録しましたが、公式原本との照合と再利用条件の確認が済んでいないため登録していません。候補取得を問題登録数には含めません。

IPAは2009〜2026年の公開資料から選択式の問題・公式解答261組を取得。204冊8,857問を追加し、39冊と部分登録を含む既存1,292問を除外しました。18冊は問題区切り・解答表を確定できず登録保留です。国土地理院は2022〜2026年の10冊280問を追加し、共通の関数表も表示します。科目Bの多肢選択にも対応しています。

非ITは公式問題冊子192冊を取得し、93冊2,609問を追加しました。残る99冊は番号の並び・正答表を確定できず保留です。第一種電気工事士は2018・2023〜2026年度、第二種は2022〜2026年度、電験三種は2022〜2026年度（理論・電力・機械・法規、枝問は別問として登録）です。画像型の問題は原本ページを共有するため、隣の設問も表示されます。解く問題番号を問題文に明記します。

医師は第112〜116回（2018〜2022年）、歯科医師は第116〜117回（2023〜2024年）。GitHubの本文・全選択肢を公式PDFと照合し、選択肢が原本で同じ順序にあることも検査します。図版依存、削除・複数の正答組合せ、文字化け等で照合できない問題は除外しました。共通症例を確認できる原本ページも表示します。薬剤師は第111回（2026年）を原本画像から339問追加。問92・316の削除、問199・220・221の訂正、問287の特殊な正答条件を除外し、6択5問にも対応しています。画像中の選択肢数23問は原本を目視して確認し、原本SHA-256と結び付けました。

宅建、危険物乙4、解剖学、中小企業診断士、FPなどのGitHub候補も調査しました。自作・再構成問題、実体のないデータ、商用書籍由来、利用条件・公式正答を確定できない候補は追加しませんでした。FP2・FP3の既存教材と簿記3級の既存自作教材は維持しています。

同じ公式PDFの同じ問題番号は二重登録しません。年度違いの再出題や高度試験の共通午前Ⅰは、年度・試験ごとの出題として数えます。意味が同じ設問をすべて除いた件数ではありません。

日商簿記3級は、利用条件・公式正答を確認できるGitHubの過去問データを今回は確保できず、既存の自作20問のままです。未収録試験に問題を生成して埋めてはいません。

## 発見元と公式資料

取得済みの12リポジトリと1件のGistは [取得元の管理台帳](github-sources.md) に登録しています。共通の取得処理で取得済みファイルを再利用し、同じリポジトリの未取得年度・ファイルは引き続き追加できます。

- [amapyonのIPA過去問リンク集](https://gist.github.com/amapyon/477930159cb5b0c47f401b0d4a09b1aa)
- [inamuu/ITPassportExams](https://github.com/inamuu/ITPassportExams)
- [kosukekkk-ops/fe-master-app](https://github.com/kosukekkk-ops/fe-master-app)
- [onochin/assistant-surveyor-pwa](https://github.com/onochin/assistant-surveyor-pwa)
- [GitHubの看護問題CSV](https://github.com/seika759931-cloud/quiz-app_web)、[KensagishiQA](https://github.com/bioinfo-tsukuba/KensagishiQA)
- [IPA公式過去問題](https://www.ipa.go.jp/shiken/mondai-kaiotu/index.html)、[SG・FE公開問題](https://www.ipa.go.jp/shiken/mondai-kaiotu/sg_fe/koukai/index.html)、[ITパスポート公開問題](https://www3.jitec.ipa.go.jp/JitesCbt/html/openinfo/questions.html)
- [国土地理院公式過去問](https://www.gsi.go.jp/LAW/SHIKEN/past.html)
- [officeharukaze/denko2](https://github.com/officeharukaze/denko2)、[onokumao-png/gokaku-denki-quiz](https://github.com/onokumao-png/gokaku-denki-quiz)、[Consuke/denken-with-llm](https://github.com/Consuke/denken-with-llm)
- [aistairc/medLLM_QA_benchmark](https://github.com/aistairc/medLLM_QA_benchmark)（IgakuQA・DenQA）、[inumanma/Pharmacist-bench](https://github.com/inumanma/Pharmacist-bench)
- [電気工事士第一種](https://www.shiken.or.jp/construction/first/qa/)、[第二種](https://www.shiken.or.jp/construction/second/qa/)、[電験三種](https://www.shiken.or.jp/chief/third/qa/)の公式問題・解答
- [厚生労働省の国家試験問題](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/topics_150873_139_140.html)、[第111回薬剤師問題・正答・訂正](https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/0000198929.html)

GitHubのデータは取得先の発見と医療問題の文字起こしの照合に使用し、問題画像・正答は公式PDFから作成しています。第三者の解説やAI生成問題・推測した正答は取り込んでいません。

[IPAのFAQ](https://www.ipa.go.jp/shiken/faq.html) にある教育目的の過去問利用条件、[国土地理院コンテンツ利用規約](https://www.gsi.go.jp/kikakuchousei/kikakuchousei40182.html) を確認し、各問に出典・年度・科目・問題番号・原本URLを表示します。GSI画像は設問単位に加工したことを明記します。原本の図表を保持し、第三者の権利は本プロジェクトのMITライセンスへ変更しません。

[電気技術者試験センターのFAQ](https://www.shiken.or.jp/shiken/faq/faq08/000082.html) は教育目的の公表過去問利用について許諾・使用料不要とし、出典表示と利用状況のメール連絡を求めています。出典・著作権・加工内容を各問に表示済みです。利用連絡は未送信で、ローカルに `ecee-usage-notification.txt` の下書きを用意しました。[厚生労働省の利用規約](https://www.mhlw.go.jp/chosakuken/index.html) に基づき、出典、PDL1.0、加工内容、省が作成したアプリではないことを表示します。

## 利用と再検査

この作業環境では `Webアプリを起動.cmd` から本人用ローカル版を起動してください。「試験管理表」で登録数を確認し、試験・年度・科目を選んで検索・演習できます。公開版 `web/` に問題は含まれません。今回の追加分はクラウド未配備です。全教材はPagesの20,000ファイル上限を超えるため、本人用ローカル版で利用します。クラウド用ビルドは `--cloud` で上限を検査し、超過時に停止します。

```powershell
python scripts/fetch-github-material.py
python scripts/prepare-github-material.py
python scripts/prepare-gsi-material.py
python scripts/fetch-nonit-material.py
python scripts/prepare-nonit-material.py
python scripts/expand-github-material.py fetch
python scripts/expand-github-material.py prepare
python checks/github-expansion-check.py
python scripts/verify-github-material.py
python checks/nonit-material-check.py
npm run build:private
node checks/github-material-check.mjs
node checks/private-material-check.mjs
npm run inventory:exams
```

抽出には既存の `build/python-deps` のPyMuPDF・Pillow、`build/tessdata` の日本語・英語OCR辞書を使用します。新規取得した資料のOCRキャッシュはローカルに保存します。GSIの関数表は文字認識で見出しを取り逃したため、原本を目視し、ページ位置を原本SHA-256と結び付けた `gsi-function-tables-verified.json` を使用します。原本が変われば再確認が必要です。

`prepared/report.json` は収録・既存除外・保留の一覧、`prepared/nonit-report.json` は非ITの内訳、`prepared/verification.json` は検査結果です。全問の公式正答、原本・問題・画像のSHA-256、原本から再描画した画素の一致を検査します。IPAの公式キーは抽出時の行配置とは別に単語配置から再照合します。電験の(b)は直前の(a)との行配置で照合し、不可視の番号に誤りがあるPDFにも対応します。検査用に2024年度の4科目の公式解答列を原本画像から転記して照合します。OCRの問題番号だけを正答の根拠にしません。ビルド時にも証跡とハッシュを再検査します。非IT追加前の既存387パックの内容とIDは維持します。

画像の目視確認は代表例と共通関数表です。全問の目視確認や独立した人によるレビューは未実施で、公式資料にない理由解説は付けていません。採点後に「理由解説は未収録」と表示し、実施当時の制度・規格を前提とします。

今回の検査は累計17,698問の原本画像・公式正答照合、全21,984問の教材・索引整合性、追加前480パックの内容維持、改変・重複の拒否を通過しました。ビルドは566パック・22,444ファイルです。公式正答表の複数選択と別解列の区別、数字記入式の除外、中央・右揃え・分割文字の問題番号抽出も検査しました。GitHubの公開問題データ357問の正答は公式PDFと一致しました（別のサンプル問題55件は対象外）。

隔離Chromeで新しい4試験と既存のFE・SG・IP・測量士・測量士補・電気工事士2種・電験三種・医師・歯科医師・薬剤師の画像表示・年度検索・採点・記録を確認しました。歯科の複数選択、薬剤師の6択、2コンテキスト間の記録同期・復元、320px幅の検査も通過しました。新しい4試験の代表画面を目視確認しました。全問の目視確認ではありません。

本人ログイン後の本番クラウド操作は未確認です。全件版はローカルに登録し、クラウドには配備していません。
