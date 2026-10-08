# GitHub候補リポジトリからの問題取り込み結果

2026-10-07の未収録予想・練習問題の追加は [取り込み記録](practice-import.md) を参照してください。

この文書は実施時点の取り込み・検証履歴です。現在の登録数は [試験管理表](exam-inventory.md)、取得元別の収録状況は [取り込み状況](import-status.md) を参照してください。後続のJLPT公式教材の追加は [JLPTの取り込み内容と検査](jlpt-import.md) に記録しています。

## 未登録試験の追加取り込み（2026-10-06）

追加候補5リポジトリを全件取得し、4件から2,450問を本人用ローカル版へ追加しました。登録問題合計は33,485問です。既存候補と合わせて42リポジトリ、29件から11,501問を収録しています。取得台帳は3,013ファイル（既存を含む）、失敗0件です。

| 試験 | 取得元 | 新規登録 | 非収録・形式 |
| --- | --- | ---: | --- |
| 司法試験 | keisks/j_bar_exam | 538 | 同文21件を重複除外。憲法・民法・刑法、2019〜2023年。元の記述・番号付き選択肢と正答番号を保持し、自己採点で演習 |
| LPIC-1（102-500） | stueja/lpic-1-102-500-anki-flashcards | 639 | 640ノート中、同文1件を除外。英語の一問一答・自己採点。解答画像2件を保持。READMEの641カードという記載と実データのノート数は異なる |
| Linux Essentials | MCCMDave/linux-essentials-quiz | 276 | ドイツ語の選択式。提供元の「公式問題」という表記は未検証 |
| AWS SAA-C03 | CarbonRaven/AWS-Quiz-SAA-C03 | 997 | 1,018件中、選択肢不備19件・重複選択肢2件を除外。英語の単一・複数選択を保持 |
| JLPT N1〜N5 | eulerex/jlpt-test | 0 | 158回分のJSONとOCR原本を全件保存。冊子単位の文章で、複数年度の混入・OCR誤り・正答との対応不明があるため問題登録を保留 |

問題・正答・解説の内容は未検証です。固定コミット・Git blob・SHA-256、問題形式、AWSの正答文字から番号への変換、採点、LPICの解答画像、重複除外、公開版への混入防止を検査済みです。ライセンス等の取得ファイルも本人用領域に保持します。翻訳・公式試験の得点換算は行っていません。クラウド配備は実施していません。

既存保留候補も再確認しました。気象予報士は教材利用条件が別で引き続き保留、英検は本文と設問の不整合、統計検定・漢検は問題実体なし、色彩検定は仮問題のみで、追加登録していません。

以下は最初の37件を取り込んだ時点の記録です。

対象タスク：`01a10ecb-5aa8-75e0-9d25-bb361c7c9bed`。実施日：2026-10-06。

全37リポジトリを確認し、25リポジトリから9,051問を本人用ローカル版へ追加しました。総数は31,035問です。全37件から選定した1,351ファイルを保存し、固定コミットのGit blob SHA-1と取得後のSHA-256を検査しました。

教材全文と図版はGit対象外です。今回の追加分は公式原本との一致・正答・解説を独立検証していません。問題画面と教材の出典画面に未検証であることを表示し、既存の公式原本照合済み教材は従来の検査を維持します。

全件の機械用結果と非収録理由は `private-data/github-candidates/prepared/report.json` に保存しています。

## 全37リポジトリの結果

| リポジトリ | 新規登録数 | 非収録・留意点 |
| --- | ---: | --- |
| [tossh23/architect-study-app](https://github.com/tossh23/architect-study-app/tree/4551d7777646edaf527266ba30128812ab09cb8c) | 1,108 | 必要図版がリポジトリにない（140件） / 選択肢不備（1件） / 削除・複数許容または正答不明（1件） |
| [pousan/mansion-exam-prediction](https://github.com/pousan/mansion-exam-prediction/tree/3fe69828392e3eb51d109d44bb78ec988e09d750) | 347 | 削除・複数許容または正答不明（3件） |
| [medicalillustotter/PTOT-kokushi-study](https://github.com/medicalillustotter/PTOT-kokushi-study/tree/66e9405e3c33c3f81a7358aa19e1ccaaaea7e34d) | 172 | 必要図版なし・削除または別正答あり（28件） |
| [yma3mama-tech/hoikushi-shiken-app](https://github.com/yma3mama-tech/hoikushi-shiken-app/tree/4d6f268c787529f63d318fc7dad00f78b545ac3c) | 310 | 形式検査済み。正答・解説の内容は未検証。 |
| [kikkawamotoharu/sharoushi-app](https://github.com/kikkawamotoharu/sharoushi-app/tree/dbb451c9f8051631950929a6b56c08e79cbfd793) | 9 | 第三者の市販模試由来で出典・利用条件未確定（1件） |
| [masatopapa/unkan-quiz](https://github.com/masatopapa/unkan-quiz/tree/c46bee3448733cf30484d43a255d3f8a450c1cbc) | 216 | 形式検査済み。正答・解説の内容は未検証。 |
| [mjrt0817/gyoseishoshi](https://github.com/mjrt0817/gyoseishoshi/tree/2a2660c8b81f4bb6613cd38b16c4cd1419154600) | 406 | 形式検査済み。正答・解説の内容は未検証。 |
| [masaosan425-alt/takken-app](https://github.com/masaosan425-alt/takken-app/tree/72127a69ea7c2b1afbe7396040220def8cc6ee13) | 100 | 形式検査済み。正答・解説の内容は未検証。 |
| [nappe0209/hoikushi-quiz](https://github.com/nappe0209/hoikushi-quiz/tree/9b312c6fa255e432a124728fe6ae6327e5df7e74) | 442 | 同一試験の本文・共通本文・選択肢が既存問題と一致（8件） |
| [inamuu/KikenbutsuExams](https://github.com/inamuu/KikenbutsuExams/tree/c20c30d75ce7a3907fe5940019e4fee20496a38f) | 25 | 形式検査済み。正答・解説の内容は未検証。 |
| [shajime0909-bit/eisei2](https://github.com/shajime0909-bit/eisei2/tree/6dc451738952a710c0217b6652d3c938c844bb6c) | 300 | 形式検査済み。正答・解説の内容は未検証。 |
| [no2shi4ni0-dot/syoubou-quiz](https://github.com/no2shi4ni0-dot/syoubou-quiz/tree/8e48acf9a985997502f3c7549d39692dfbd5085d) | 56 | 形式検査済み。正答・解説の内容は未検証。 |
| [5150kouhei-rgb/fp2-drill](https://github.com/5150kouhei-rgb/fp2-drill/tree/3b9fd56fdcf27f43dcfebf8c8c72866f9f82ddb8) | 500 | 形式検査済み。正答・解説の内容は未検証。 |
| [fp-hitorigoto/fp3-quiz](https://github.com/fp-hitorigoto/fp3-quiz/tree/6c0a955097345ede7b9d86821da24933155849dc) | 120 | 形式検査済み。正答・解説の内容は未検証。 |
| [edwin6780-tech/Boki-3](https://github.com/edwin6780-tech/Boki-3/tree/d649171eb1843beed4eb912510ca804b6889c53e) | 79 | 形式検査済み。正答・解説の内容は未検証。 |
| [yuaoki08/kokunai-travel-exam](https://github.com/yuaoki08/kokunai-travel-exam/tree/2d8694765c578d638ad78294bb121a2037e2120f) | 205 | 形式検査済み。正答・解説の内容は未検証。 |
| [pose-shell/weather-quiz-app](https://github.com/pose-shell/weather-quiz-app/tree/11c3232201d140c41baab33f8eee6f8549867d8b) | 0 | 教材はコードのMIT対象外。複製条件を確定するまで原本保存のみ |
| [nomu770501-Git/chouri-quiz](https://github.com/nomu770501-Git/chouri-quiz/tree/369c7582ad43208b1790d65f9c3f047bbf5963aa) | 558 | 同一試験の本文・共通本文・選択肢が既存問題と一致（42件） |
| [bang-prog/nutritionist](https://github.com/bang-prog/nutritionist/tree/4af250831e8f434b4b858ec8ccc17b9530db5306) | 45 | 形式検査済み。正答・解説の内容は未検証。 |
| [toru830/shindanshi](https://github.com/toru830/shindanshi/tree/78285be816164fe84ee62d369d9e8459a68c0228) | 10 | 形式検査済み。正答・解説の内容は未検証。 |
| [wangchang2049/eikenQuest](https://github.com/wangchang2049/eikenQuest/tree/d487b2b279c4e13de99889b4ab1068b7a9e0a048) | 0 | 生成データの設問と本文・選択肢の対応が不整合。提供元修正待ち |
| [Ditectrev/Amazon-Web-Services-AWS-Certified-Cloud-Practitioner-CLF-C02-Practice-Tests-Exams-Questions-Answers](https://github.com/Ditectrev/Amazon-Web-Services-AWS-Certified-Cloud-Practitioner-CLF-C02-Practice-Tests-Exams-Questions-Answers/tree/765cfeae325f646db029f70a7212848a8affec3f) | 597 | 形式検査済み。正答・解説の内容は未検証。 |
| [hangonkou-ux/takken-app](https://github.com/hangonkou-ux/takken-app/tree/5759b6e42303aed78359967ad4e7a8a5fd254088) | 1,070 | 選択肢不備（4件） / 正答不明または複数許容（26件） |
| [makio1988/takkenkakomon](https://github.com/makio1988/takkenkakomon/tree/dd616962423cd5637c2d608e493616bcaecb156f) | 162 | 同一試験の本文・共通本文・選択肢が既存問題と一致（177件） / 選択肢不備（11件） |
| [Fkzyk/takken-dojo](https://github.com/Fkzyk/takken-dojo/tree/f3e20d55d5ddba57c60d9aae76483799f8ca2211) | 450 | 形式検査済み。正答・解説の内容は未検証。 |
| [kita0709/pt-exam-study-app](https://github.com/kita0709/pt-exam-study-app/tree/fea0d90122c7b240e5ddf1382a7a221c0da5c4d9) | 4 | 同一試験の本文・共通本文・選択肢が既存問題と一致（1件） |
| [nekomarugt/j-kokushi-portal](https://github.com/nekomarugt/j-kokushi-portal/tree/7a5076bd2a8b57f2eaea4ded4aaa68307c39096e) | 1,760 | 必要図版がリポジトリにない（3件） / 同一試験の本文・共通本文・選択肢が既存問題と一致（2件） |
| [oga3999/kokushi](https://github.com/oga3999/kokushi/tree/210cc6a2c0feb5cfe20d1675f42f57889649bdcc) | 0 | 配布された学習問題・正答の実体なし |
| [honnili/ClinicalEngineer](https://github.com/honnili/ClinicalEngineer/tree/d2612788e35da32172cac509825af27f9f21a240) | 0 | 配布された学習問題・正答の実体なし |
| [kyuuki/kanken-rails](https://github.com/kyuuki/kanken-rails/tree/c249e0696aae3d603e9cfa48554501190a517a90) | 0 | 配布された学習問題・正答の実体なし |
| [Valsuh45/LPIC-Past-Questions](https://github.com/Valsuh45/LPIC-Past-Questions/tree/7f647bf7b8552ff61ea36be43ec74e8243fc3f98) | 0 | 市販dumps由来・正答範囲外やカード状態を正答にした設問あり。教材化を保留 |
| [epaulcnjp-design/takken-quiz](https://github.com/epaulcnjp-design/takken-quiz/tree/872cc63e5bea420939be91f2737369612c332af5) | 0 | 配布された学習問題・正答の実体なし |
| [sshNH/statistics-kentei-v2](https://github.com/sshNH/statistics-kentei-v2/tree/635b860eeccd9462e8065bac01e6587d15d805da) | 0 | 配布された学習問題・正答の実体なし |
| [sparkrones/met_exam](https://github.com/sparkrones/met_exam/tree/a4af9f0723cdd6269ea04c650e1512c955378d97) | 0 | 配布された学習問題・正答の実体なし |
| [probono-a/shakaifukushi-quiz](https://github.com/probono-a/shakaifukushi-quiz/tree/a4b6a6791e1a6e085ae5529905d75804442edc39) | 0 | 配布された学習問題・正答の実体なし |
| [zakiyama777/domestic-travel-manager-coach](https://github.com/zakiyama777/domestic-travel-manager-coach/tree/a6c6c72e45be70b15cd7b8352c99e906d3ad006c) | 0 | 配布された学習問題・正答の実体なし |
| [Sunmax0731/color-certification-exam-trainer](https://github.com/Sunmax0731/color-certification-exam-trainer/tree/3f3e1231315df7f3f3da2756fb15331771e0b1c1) | 0 | 検証用の仮問題のみ。学習問題なし |

## 形式・重複・非収録の扱い

選択式は提供元の正答番号を0始まりへ変換し、複数選択、正誤、共通本文、組み合わせ表、図版を保持しました。FP実技の穴埋め・計算・組別正誤、行政書士の複合選択、簿記の仕訳は模範解答による自己評価です。削除・複数許容正答と通常の複数選択は区別しています。

同じ試験の問題文・共通本文・選択肢について、Unicode NFKCと空白除去後の完全一致で重複を除外しています。数値と選択肢の順序は維持し、意味が近いだけの問題は除外しません。重複による非収録は230問です。

英検候補は4,400件の生成データで本文と設問・選択肢の対応に不整合があり、原本保存にとどめました。気象予報士候補は教材がコードのMITとは別の権利条件なので保留です。LPIC候補は市販dumps由来で、正答が選択肢の範囲外、カードの状態表示を正答としている例があるため、PDF原本と抽出本文を品質確認用に保存しました。社労士の第三者模試由来の事例も保留しました。残る問題データのないリポジトリと色彩検定の仮問題は登録していません。

## 保存先と再実行

原本・取得記録：`private-data/github-candidates/`。変換済み教材・非収録理由：`private-data/github-candidates/prepared/`。アプリ：`build/private/web/`。クラウド配備は実施していません。

`INDEX.html` と `index.html` のようなWindowsで衝突する原本名は、Git blobごとのディレクトリで分けて保存しています。提供元のスクリプトは実行せず、JSON・CSV・SQLite・ExcelおよびデータだけのJS/Pythonリテラルを読み取りました。

変換処理は `openpyxl` と `pypdf` を使用します。今回はCodex同梱のPythonで実行しました。以下の `python` は両ライブラリを利用できるPythonに読み替えてください。

```powershell
python scripts/import-github-candidates.py --download
python scripts/prepare-github-candidates.py
npm run build:private
python checks/github-literals-check.py
node checks/github-candidates-check.mjs
node checks/private-material-check.mjs
node scripts/update-exam-inventory.mjs
```

本人用の起動：

```powershell
python -m http.server 8771 --bind 127.0.0.1 --directory build/private/web
```

ブラウザで `http://127.0.0.1:8771/` を開きます。公開版の `web/` は問題未登録のままです。

## 検証

既存の `npm run check`、安全なリテラル解析、取り込み元・教材のハッシュ、形式・採点・重複除外、全教材インデックス、公開版への混入防止を検査しました。ブラウザでは複数選択、記述式の自己評価、図版付き問題、共通対策教材、保存・再読込・端末別記録・320px幅の表示を確認しました。問題の正答や解説の事実確認はこの検証に含みません。
