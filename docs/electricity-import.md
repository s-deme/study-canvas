# 電気・通信の過去問取り込み

2026年10月7日。公式公開PDFと外部アーカイブから問題・公表正答を取得し、原本画像付きでローカル教材に追加しました。空欄ごとに解答する問題は、空欄を1問として数えています。

追加は21資格、427パック、17,726問（選択式2,999問、番号・記号入力による自己採点14,727問）。原本画像4,263枚を共有します。公式取得7,492問、外部取得10,234問で、実施年は2002～2026年です。610候補のうち、170件は番号・正答の読み取り等を保留、9件は取得失敗、4件は同一原本として除外しました。第三級・第四級アマチュア無線技士は、今回対応を確定できる過去問を追加していません。公式CBT例題は過去問として扱っていません。

反映後のカテゴリ合計は **1,490問 → 19,216問**、登録済み資格は **3 → 24** です。全17,726問と全4,263画像の原本照合、登録IDの一意性、ビルド先画像のハッシュ、選択式採点・入力式自己評価、既存教材の保持を確認しました。`npm run check` と反映後の `checks/private-material-check.mjs` も通過し、[試験管理表](exam-inventory.md)を更新しました。

## 取得元

- [電気技術者試験センター：電験一種](https://www.shiken.or.jp/chief/first/qa/)、[電験二種](https://www.shiken.or.jp/chief/second/qa/)の一次試験。
- [日本データ通信協会：電気通信主任技術者](https://www.dekyo.or.jp/shiken/chief/exam)、[工事担任者](https://www.dekyo.or.jp/shiken/charge/exam)。
- [日本無線協会：試験問題と解答](https://www.nichimu.or.jp/kshiken/siken/index.html)。英語科目は転用不可のため対象外。
- [JJ1SXA：一アマ過去問](https://240sxa.net/1ama-qa.html)、[電気通信主任技術者 過去問解説.com](https://denkitsushin.com/blog-entry-25.html)。
- [DIGIRADIO：工事担任者総合](https://digiradio.simple-was-best.com/ins-tech-kakomon/)、[二陸特](https://digiradio.simple-was-best.com/2rikutoku-kakomon/)。外部取得の正答は掲載原本との照合であり、発行団体との独立照合は未実施。

GitHubも検索し、既存取得済みの [Consuke/denken-with-llm](https://github.com/Consuke/denken-with-llm)、[officeharukaze/denko2](https://github.com/officeharukaze/denko2)、[onokumao-png/gokaku-denki-quiz](https://github.com/onokumao-png/gokaku-denki-quiz) を確認しました。今回の追加は原本・正答を対応付けられるPDFを中心とし、重複登録を避けています。[PG-MANA/MN2](https://github.com/PG-MANA/MN2) は練習システムで、今回追加できる過去問データは確認できませんでした。

## 形式・検査

問題本文、数式、図表、選択肢は原本PDFのページ画像で保持しています。選択肢番号を確認できた問題は選択式、その他の空欄は番号・記号入力と公表正答による自己採点です。理由解説は未収録です。年度・科目・問題番号・出典URLを各問に付与しました。

正答表のセル位置、問題番号、試験記号・年月、ファイルハッシュを検査します。画像はPDF再描画との全画素一致を検査し、PDF間の描画キャッシュをクリアします。全問目視ではなく代表例の目視確認です。番号対応が不明、正答表を読めない、取得できない、原本が重複する場合は保留・除外し、レポートに理由を記録しています。

原本・取得記録は `private-data/github-material/`、準備済みデータは同ディレクトリの `prepared/electricity-report.json`、検証結果は `electricity-verification.json` に保存します。追加教材はローカル利用限定です。

再実行は `python scripts/prepare-electricity-material.py --fetch`、`python scripts/prepare-electricity-material.py`、`python checks/electricity-material-check.py` の順です。検証後、通常のプライベートビルド、または `node scripts/append-food-material.mjs electricity` で反映します。`node checks/electricity-build-check.mjs` で収録先と解答操作を検査します。
