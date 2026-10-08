# 建築・土木の過去問取り込み

取得日：2026-10-07（日本時間）。本人用ローカル教材へ収録します。現在の件数は[試験管理表](exam-inventory.md)、全教材は[取り込み状況](import-status.md)を参照してください。

今回の追加原本は13試験区分・89パック・7,179問です。取得候補120パックのうち、29パックは保留、2パック・106問は取得経路違いの同一PDFとして除外しました。既存GitHub教材と公式原本の重複はビルド時にも除くため、7,179問を以前の総数へそのまま加算しません。測量士・測量士補の既存教材も保持します。

同日の反映結果はカテゴリ1,388問→7,790問（純増6,402問）、15試験すべて登録ありです。GitHubの一級建築士777問を公式原本へ置き換え、GitHub教材331問と測量教材280問を保持しました。年度の `H28`・`令和3年` などの表記差も重複比較時に西暦へ統一しています。これは作業時点の記録で、現在の件数は上記管理表を参照します。

## 取得元

- [建築技術教育普及センター](https://www.jaeic.or.jp/shiken/1k/1k-mondai.html)：一級・二級・木造建築士、建築設備士、インテリアプランナーの公開学科問題と正答表。
- [全国建設研修センター](https://www.jctc.jp/mondai/)：1級・2級の土木、管工事、造園、電気通信工事の公開問題と正答表。土木2級の土木・鋼構造物塗装・薬液注入も含みます。
- [土木のトリセツ](https://doboku-torisetsu.com/pastproblems)：公式一覧に残っていない年度の土木・造園の問題PDFと掲載正答表。年度別ページまで探索しています。外部取得分の正答は掲載表との一致を検査し、試験機関との独立照合済みとは扱いません。
- GitHub：既存の[tossh23/architect-study-app](https://github.com/tossh23/architect-study-app)と[onochin/assistant-surveyor-pwa](https://github.com/onochin/assistant-surveyor-pwa)の収録を確認しました。一級建築士は年度・科目・問題番号が一致する候補を公式原本へ置き換えます。今回のWeb検索では、新たに収録できるGitHub教材は発見できませんでした。

GitHub追加検索は `site:github.com "二級建築士"`、`site:github.com "施工管理" "問題"`、`site:github.com "architect-study-app"`、`site:github.com "測量士補" "問題"`、`site:github.com "管工事" "過去問"`、`site:github.com "造園" "過去問"` です。検索エンジンの結果に限る調査で、全リポジトリの網羅確認ではありません。

公式一覧の個人利用条件を保存し、全追加パックに `localOnly` を付けています。公開版・クラウドへは配備していません。原本・取得URL・SHA-256・変換候補は `private-data/github-material/construction-discovery.json`、問題ごとの原本ページ対応・非収録理由は `prepared/construction-report.json` が正本です。

## 検査と制限

本文、図表、数式は原PDFのページ画像を使用します。次ページに続く設問も含め、正答表は問題画像へ含めません。本文の文字起こしや理由解説は追加していません。試験実施当時の法令・規格を前提とした問題です。

正答はネイティブPDFの数字とセル座標から抽出します。四択・五択を冊子の注意書きで区別し、単一選択と複数選択に対応します。二級建築士の代表正答列と造園2級の複数選択正答は原本画像と照合し、回帰検査へ固定しました。全パックの正答・問題番号・ページ対応・ハッシュと、保存画像の全画素を原PDFの再描画と照合します。全設問の本文・選択肢を逐一目視した独立レビューではありません。

画像のみの正答表、問題見出しの対応が未確定の冊子は原本保存のみとします。本文省略・別正答許容・見出し欠落の問題、正答表にあるが問題冊子を取得できていない種別も除外します。29保留パックと各除外理由は上記ローカル報告に残し、件数へ含めません。設計製図・実技・第二次検定の記述答案の自動採点は追加していません。

## 再生成

```powershell
python scripts/prepare-construction-material.py --fetch
python scripts/prepare-construction-material.py
python checks/construction-material-check.py
npm run check
node checks/github-material-check.mjs --fixture-only
npm run build:private
node checks/construction-build-check.mjs
node checks/github-candidates-check.mjs
node checks/private-material-check.mjs
npm run inventory:exams
```

取得済みファイルは再利用します。壊れた途中生成PNGは読み込み時に検出して原本から再生成します。ビルドは既存の排他ロックを使用します。`construction-verification.json` と報告・原本・画像のハッシュが一致しない教材はビルドが拒否します。

ほかのカテゴリが検証途中で全体ビルドが停止する場合は、既存の追加処理 `node scripts/append-food-material.mjs construction` で最後に成功したローカル版へ検証済み教材だけを反映できます。元のパックのハッシュを確認し、同じ排他ロックを使います。一級建築士の候補パックは公式原本との年度・科目・問題番号の重複を除いた内容へ更新します。元データ・原本は削除しません。

実施時の検査は合格しました。7,179問・3,186ページ画像の原本照合、全件の本人用ローカル収録、単一・複数選択の採点、既存の保存・同期・旧試験一覧との互換性、候補教材の重複除外を確認しています。共通読み込み処理は完全一致する既存問題だけを再利用し、内容の異なる重複・改変画像・出典ファイルを拒否する回帰検査も通過しました。管理表は成功したローカル版から再生成しました。
