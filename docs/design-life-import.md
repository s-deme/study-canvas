# デザイン・生活の過去問取り込み

調査日：2026-10-07（日本時間）。対象は既存カテゴリの8試験。現在の登録数は [試験管理表](exam-inventory.md) を参照。

今回の変換結果：理容師1,013問、美容師1,030問、合計2,043問。60冊から収録し、正答印公開前の10冊は保留。収録冊子内にも番号・選択肢・正答印を確実に対応させられず保留した設問がある。色彩系6試験は今回の過去問追加なし。

## 収録元と扱い

| 対象 | 確認先 | 結果 |
| --- | --- | --- |
| 理容師・美容師 | [公式の過去の筆記試験問題](https://www.rbc.or.jp/exam/past_question/) | 第24〜54回、新旧試験・再試験を含む70冊を保存。第29回以降で問題番号、選択肢1〜4、正答印の対応を確認できた設問を収録 |
| 色彩検定1〜3級・UC級 | [公式教材・過去問題集](https://www.aft.or.jp/pages/official-product-orders/index.html)、[1級1次出題例](https://www.aft.or.jp/pages/feature/exam1-first)、[2級出題例](https://www.aft.or.jp/pages/feature/exam2)、[3級出題例](https://www.aft.or.jp/pages/feature/exam3)、[UC級出題例](https://www.aft.or.jp/images/examUc.pdf) | 公開出題例と販売教材の案内を確認。実施年度を特定できない出題例を過去問として計上していない。過去問題集の本文は未取得 |
| カラーコーディネーター スタンダード・アドバンス | [公式テキスト](https://kentei.tokyo-cci.or.jp/color/support/official-text.html)、[公式試験要項](https://kentei.tokyo-cci.or.jp/color/exam-info/) | 両クラスに対応する本文・正答付きの公開過去問データは今回の検索範囲で未確認。旧1〜3級を現行クラスへ流用していない |
| GitHub | [既存の資格一覧候補](https://gist.github.com/itsuki-hayashi/996fdfeec58bad7f0e71aed15ea16e09)、[書籍データ候補](https://gist.github.com/nihon-taro/b195c6a3b1a0f59c7a5f705232e5ab2f)、[辞書候補](https://gist.github.com/amane-katagiri/415ac496d7192eeb16bb64029c498b1b)、[書籍一覧候補](https://gist.github.com/aaaaninja/60911bc2ba15086a3c80d1f0f32c4269) | 保存済み候補を確認し、資格一覧・書籍・辞書であることを確認。追加Web検索でも取り込み可能な過去問集は未発見。GitHub全体の不存在を意味しない |
| 外部サイト | [JQOS理容師過去問](https://jqos.jp/kokka/riyoshi/kakomon)、[第53回美容師の共有教材](https://ankimaker.com/sl/workbooks/eee71690-fa5e-4225-b9be-e1b6e72740c4)、[色彩検定ONLINE](https://shikisaikentei-online.com/doukou_3kyu)、[資格もん](https://shikakudrill.com/shikisai-2kyu/questions/) | 理美容の転載教材は公式原本から取得。色彩系の分析記事・AI練習問題・予想問題を過去問として追加していない |

検索語は正式名称と `site:github.com`、`過去問`、`問題`、`questions`、`shikisai`、`biyoushi` 等を組み合わせた。旧調査履歴は [GitHub調査データ](github-exam-search.json) に保持。

## 保存と加工

原本・取得URL・SHA-256は `private-data/github-material/rbc-discovery.json`、変換結果と問題別の証跡は `private-data/github-material/prepared/design-report.json` に保存。問題本文と画像はGit管理対象外の本人用ローカル領域に置く。今回の作業でクラウド配備・公開・Git pushは行っていない。

`year` は実施した暦年で登録する（例：第29回は2014年、第41回は2020年、第54回は2026年）。春の試験は公式集計の会計年度では前年度に含まれるため、年度名と暦年を区別する。回数・新旧試験・再試験は `term` に保持。

公式PDFには正答の丸印が直接付いているため、問題画面用の画像では選択肢番号の余白にある赤い正答印を除く。薄いスキャンの丸印が残らないよう、同じ余白の明るい画素も白く補正する。本文・図表はこの余白の外側の原本画素を保持。解答画面には加工していない原本画像を表示する。隣の問題もページ画像に写るが、その正答印も問題画面では除去する。

番号の読み取りが曖昧、選択肢が連続する1〜4として確認できない、正答印が一意に対応しない問題は保留。欠けた番号を推測して補完しない。第24〜28回は公式ページが第29回から正答印を公表すると説明しているため保留。保留問題は登録件数に含めない。

## 再実行と検証

```powershell
python scripts/prepare-design-material.py --fetch
python scripts/verify-github-material.py
npm run build:private
node checks/design-material-check.mjs
npm run inventory:exams
```

取得済み原本とOCRは再利用する。通信なしで再変換する場合は `--fetch` を省略する。RBC教材は本人用ローカル限定として扱い、既存のクラウドビルドの制限を適用する。

公式正答印との対応、原本・データ・画像のハッシュ、加工後画像の再生成一致、問題IDの重複、採点と画像参照を自動検査する。第54回理容師・美容師の問1〜3は原本を目視し、両試験の正答3・4・3を照合。全問の目視確認、理由解説の追加、現在の法令への読み替えは未実施。
