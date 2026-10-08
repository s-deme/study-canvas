# 数学・統計の追加教材

2026-10-07：本人用ローカル版へ **480問・16試験ID・32教材パック**を追加。公式公開過去問470問、公式サンプル10問。自作教材とは分けて登録した。

| 教材 | 登録数 |
| --- | ---: |
| 数学検定1級 / 準1級 | 各28 |
| 数学検定2級 / 準2級 | 44 / 50 |
| 数学検定3級 / 4級 / 5級 | 各50 |
| 算数検定6級 / 7級 / 8級 | 各30 |
| 算数検定9級 / 10級 / 11級 | 各20 |
| 統計検定1級 | 20 |
| 統計検定DS発展 / DSエキスパート（サンプル） | 8 / 2 |

問題の数え方：準2級以下は通し番号の小問単位。上位級・統計検定1級・DSエキスパートは大問単位で枝問をまとめている。上位級の選択問題も学習用にすべて収録する。数学検定には日本語版375問と、内容が異なる上位級の英語版75問を含む。統計応用の4分野で共通の問1・問5、および人文問4と理工問3は一度だけ登録した。

## 出典と調査結果

- [日本数学検定協会・日本語公開過去問](https://www.su-gaku.net/suken/support/past_questions/)：1〜11級・準級の20冊を取得。
- [日本数学検定協会・英語公開問題](https://www.su-gaku.net/suken/support/past_questions_en/)：1級・準1級・2級・準2級の8冊を取得。日本語版と同じ数式の3級以下を重複追加していない。フォルダ名の2023等を実施年度と推定せず「実施年度不明」とした。
- [統計検定・過去問題](https://www.toukei-kentei.jp/preparation/kakomon/)：2025年11月の統計数理・統計応用と公式略解。問題冊子の日本語文字コードが崩れるため、原本画像を使う。統計数値表5ページも保持。
- [DS発展](https://www.toukei-kentei.jp/grade/ds_advanced/)・[DSエキスパート](https://www.toukei-kentei.jp/grade/ds_expert/)：公式問題と解説を取得。本試験過去問と区別した。
- [DS基礎](https://www.toukei-kentei.jp/grade/ds_basic_analytics/)：資料は取得したが、数値の完全な公式解答がなくExcelの外部データ操作が必要なため保留。
- 外部サイト：[あつまれ統計の森・2019年6月2級](https://www.hello-statisticians.com/toukei-kentei-2-kakomon-cat/201906-1)、[TECH PLAY・2021年6月2級への参照](https://techplay.jp/event/935355)、[過去問一覧](https://starpentagon.net/analytics/stat_certificate_2nd_past_problems/)も調査。参照された2019年公式PDFは404、2021年の旧staticホストは名前解決失敗。問題全文と公式解答の組を取得できず追加しなかった。
- GitHub：[統計検定受験記](https://github.com/zaemon1251-hesty/zenn-content/blob/main/articles/20221227_statistics.md)、[準1級補助資料集](https://github.com/ryosuzaki/zenn-content/blob/main/articles/718fd8051b40a6.md)、[学習データパイプライン](https://github.com/kou-sato-ds/stat-learning-data-pipeline)などを確認。受験記・解説リンク・学習管理コードは過去問題集として取り込んでいない。公式解答と対応する追加問題データは今回の検索範囲では確認できなかった。

## 表示・検証

全問を原本画像＋公式解答画像の自己採点形式とした。数式・図表・証明・作図をOCRで推測していない。全画像で元PDFとの画素一致、取得資料と出力のSHA-256、問題番号と解答資料、既存教材の保持を検査。全問の目視確認、個別解説の追記、自動採点は未実施。

共有ビルド待ちの間に[建築・土木の取り込み](construction-import.md)が一級建築士のGitHub重複教材777問を公式原本へ置き換えた。開始時点との差分3パックは、取得時点を固定したGitHub原本と現行の重複除去処理から再計算して検証した。それ以外の開始時点の教材はハッシュ一致を確認した。

原本・生成教材・出典ハッシュはgit管理外の `private-data/github-material/`。すべて `localOnly: true`、公開版への収録やクラウド配備は行わない。

```powershell
python scripts/prepare-math-material.py --fetch
python scripts/prepare-math-material.py
npm run build:private
node checks/math-material-check.mjs
```

別カテゴリの未完成資料で全体ビルドが通らない場合、既存の成功ビルドを検証して保持する追記経路：`node scripts/append-food-material.mjs math`。
