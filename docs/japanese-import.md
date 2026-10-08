# 日本語・国語の過去問追加（2026-10-07）

漢検1〜10級・準1級・準2級の公式公開過去問を、2026年度第1回と2022年度第3回の24冊分、2,772小問追加しました。既存JLPT公式教材1,185問との合計は3,957問です。現在の登録数は [試験管理表](exam-inventory.md) が管理元です。自作国語教材はこの過去問合計に含めません。

| 級 | 今回追加（2回分） |
| --- | ---: |
| 1級 | 260 |
| 準1級 | 260 |
| 2級 | 240 |
| 準2級 | 240 |
| 3級 | 240 |
| 4級 | 240 |
| 5級 | 240 |
| 6級 | 240 |
| 7級 | 240 |
| 8級 | 200 |
| 9級 | 210 |
| 10級 | 162 |

## 出題・採点

問題冊子の原本画像を拡大し、指定された大問・小問番号を解く方式です。記号を答える設問も記述形式で登録し、解答後に公式標準解答画像で自己採点します。正答文字列の転記、自動採点、独自理由解説は追加していません。四字熟語の意味・読みなどは枝問を区別し、文章中の複数の空欄は公式の小問番号に従って数えています。例題は収録数に含めません。

問題・標準解答PDFの級と年度、標準解答の番号範囲を画像で確認しました。全24冊の原本ハッシュ、2,772件の番号対応、問題・解答画像の全画素を検査します。全問の正答を別の辞書等で検証したものではありません。

## 調査元と採否

- [漢検公式問題例](https://www.kanken.or.jp/kanken/grades/sample/)：2026年度第1回の12級分の問題と標準解答24PDFを採用。
- [外部の漢検過去問リンク集](https://kanken.crayonsite.com/)：旧公式 `kanken/outline/data/` のPDFを発見。2022年度第3回の12級分24PDFを公式ドメインから取得。リンク集で不足していた準2級標準解答と3級問題・解答は同じ公式ディレクトリで確認。外部Google Driveのコピーは使用しません。
- [kei-kmj/kanken_practice_note](https://github.com/kei-kmj/kanken_practice_note/tree/4cc182d20286823eeebd114f1f4ffb18c9701efc)：MITライセンスのアプリですが、`db/seeds.rb` は雛形だけで問題データなし。登録なし。
- [kyuuki/kanken-rails](https://github.com/kyuuki/kanken-rails/tree/c249e0696aae3d603e9cfa48554501190a517a90)：取得済みツリー・READMEを再確認。配布問題実体なし。登録なし。
- [JLPTのGitHub候補](https://github.com/eulerex/jlpt-test)：158回分の抽出データは取得済み。原本PDFが配布されておらず、既存のOCR崩れ・正答対応の保留理由は解消していないため追加登録なし。
- [OpenJLPT](https://github.com/evanclan/OpenJLPT) と [mimneko/kanji-data](https://github.com/mimneko/kanji-data)：語彙・漢字データで、実施済み過去問としては採用しません。

公式ページの利用注意事項は著作権法の範囲内の使用を求めています。本人用ローカル教材として保存し、`localOnly` を付けます。公開版への同梱・クラウド配備は行いません。

## 再生成・検査

原本と調査記録は `private-data/github-material/`、生成物は同ディレクトリの `prepared/`、番号確認と原本ハッシュは `kanken-reviewed-numbering.json` に保存します。GitHub候補のツリーと固定コミットのREADME・seed・ライセンスも原本ディレクトリに保存しています。

```powershell
python scripts/prepare-kanken-material.py
node checks/kanken-material-check.mjs
python checks/kanken-material-check.py
npm run build:private
npm run inventory:exams
```

漢検は独立の `kanken-report.json` / `kanken-verification.json` を既存の原本教材ローダーで読み込みます。未検査・原本変更・画像変更はローダーで拒否します。既存教材の集約レポートには漢検を再加算しません。

今回のローカル反映では、既存43859問のビルド検査を通した後、`tmp/append-kanken.mjs` で検証済み漢検パックだけを追記しました。既存パックのメタデータと本文ハッシュの不変、追加2772問、日本語・国語17試験3957問を検査し、試験管理表を更新しています。追記前マニフェストは `private-data/github-material/kanken-build-baseline.json` に保存しています。

`npm run check`、漢検の形式検査、漢検84ページ全画像の原本画素照合、JLPT既存15冊の検査は合格しました。通常の全体再生成は、別カテゴリの `safety-CS20241901.json` の画像検査に失敗して集約検証が更新できず保留です。この別教材を検査から除外したり、検証ハッシュを書き換えたりしていません。漢検の通常ビルド経路への追加は実装済みですが、全体再生成の合格を意味しません。クラウド配備は未実施です。
