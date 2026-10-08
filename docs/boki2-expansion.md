# 日商簿記2級の問題追加

2026年10月8日。対象は `boki2`。既存94問を保持し、自作221問を追加、計315問になった。追加教材はローカル本人用ビルドに登録済み。クラウド配備は行っていない。

| 区分 | 追加数 |
| --- | ---: |
| 商業簿記 | 122 |
| 工業簿記 | 99 |
| 合計 | 221 |

形式は計算160問、仕訳61問。模範解答と解説による自己採点を使用する。すべて自作・AI生成と表示し、公式過去問として扱わない。数値だけの変更による水増しは行わず、既存の数値を正規化する重複検査を通す。

商品売買、収益認識、銀行勘定調整、債権、有価証券、固定資産、外貨、引当金、税効果、純資産、本支店、連結と、材料・労務・経費、個別・部門別・総合・標準・直接原価計算、CVPを含む。単元の完全網羅や本試験形式の再現を保証しない。リース等の時点依存項目は2026年度向けと明示した。[2026年度に適用される公式出題区分表の案内](https://www.kentei.ne.jp/bookkeeping/exam-list)を参照し、2027年度の改定とは区別する。

## 外部教材の調査

| 対象 | 今回の扱い |
| --- | --- |
| [日本商工会議所の2級サンプル](https://www.kentei.ne.jp/bookkeeping/sample/sample-two) | 無断転載禁止の記載を確認。本文の新規収録はしない |
| [Pass Harbor](https://www.pass-harbor.com/jp/ja/nissho-boki-2-practice-test)、[資格道場](https://shikaku-dojo.lb-product.com/boki2/kougyou-hatten)、[ケンテイラボ](https://kentei-lab.com/exams/boki2kyu/questions) | 検索で公開問題候補を発見。再利用許諾を確認できておらず、全文収録はしない |
| [xxarupakaxx/boki-studio](https://github.com/xxarupakaxx/boki-studio/tree/fc985c9b95d0ae22e84bfe85cb43c472da218758) | MIT表記の候補。固定コミットにはLICENSEとREADMEのみで問題データなし |
| [kazenari99/boki](https://github.com/kazenari99/boki/tree/2cc2e695cb45697ae23352fedf9d05d46ab3cfaf) | MIT表記の候補。固定コミットにはLICENSEのみ |
| [Tpaefawzen/solve-boki](https://github.com/Tpaefawzen/solve-boki/tree/49972c18033f670c624ea4b020d34c0e683e0e33) | CC0表記の計算補助ツール。ファイル一覧とデータ形式説明から、2級の問題・模範解答集としての採用を見送る |
| [aztechaz357/project-gain](https://github.com/aztechaz357/project-gain/tree/ab70a2f5685e83ad3d81eb51f4a26573418e82d5) | MITライセンスと仕訳データを確認。簡易な会計導入教材であり、2級の追加問題には採用しない |

GitHub APIでは「簿記2級」「boki」「簿記」等を検索し、ライセンス付き候補を優先して固定コミットの一覧と本文を確認した。検索結果、候補一覧、取得本文は `private-data/boki2-expansion/` に保存した。全インターネットの網羅調査ではない。今回の新規追加はすべて独自作成で、外部教材の文章は使用していない。

## 再生成・検証

- 生成：`python private-data/local-practice/author.py`
- 再生成一致：`python private-data/local-practice/author.py --check`
- ビルド：`npm run build:private`
- 解答再実行：`python private-data/local-practice/check.py`
- 今回の221問・従来全問保持：`python private-data/boki2-expansion/check.py`
- 簿記2級の読み込み・自己採点・記録復元：`node private-data/boki2-expansion/check-runtime.mjs`
- 読み込み・改ざん検査：`node checks/local-practice-check.mjs`
- 全教材の形式・ハッシュ・同期：`node checks/private-material-check.mjs`
- 管理表更新：`npm run inventory:exams`

計算は式と別記した期待値を照合し、仕訳は貸借金額の一致を検査する。代表15件は生成コードと別の期待値でも確認する。これらは会計処理の専門家監修ではなく、全問の意味的正しさを保証するものではない。生成物・出題コード・解答検証資料は既存方針に合わせGit管理外の `private-data/` に置く。

[工業簿記の公式区分表](https://www.kentei.ne.jp/wp/wp-content/uploads/2021/12/2022_kogen.pdf)と[商業簿記の公式区分表](https://www.kentei.ne.jp/wp/wp-content/uploads/2024/12/shogyouboki_kubun.pdf)の級別欄を画像でも確認した。階梯式配賦、純粋相互配賦、多品種CVP、建物の連結未実現利益などの上位級論点は今回の追加教材に含めない。

完了検証：追加221問は重複除外なしで登録された。全自作教材1,059問の解答再実行、今回の代表15件、着手時の全104,335問の本文ハッシュ保持、全教材の形式・画像参照・同期検査、簿記2級315問の読み込みと自己採点記録の復元に合格。`npm run check` も合格し、集計スクリプトで管理表を更新した。実ブラウザでの全問目視は実施していない。

既存の自作教材保持テストは、追加教材で総件数が増えても失敗しないよう、保存済み問題IDの包含確認へ変更した。台帳がG検にも試験ID接頭辞を付ける形式に合わせて比較している。本文が変わっていないことは上記Python検査で別途確認する。
