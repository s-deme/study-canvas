# JLPT公式教材の取り込み

以下は公式教材の取り込み時点の記録です。現在のレベル別登録数は [試験管理表](exam-inventory.md)、収録元別の件数は [取り込み状況](import-status.md) を参照してください。JLPTは公式原本追加教材に含まれ、合計へ再加算しません。

N1〜N5の2009年問題例集、2012・2018年公式問題集を全15冊分、1,185問追加。

| レベル | 登録数 |
|---|---:|
| N1 | 256 |
| N2 | 253 |
| N3 | 238 |
| N4 | 229 |
| N5 | 209 |

聴解は原本画像と公式音声で解答できます。原本冊子全体を画像表示し、指定された大問・解答番号を解く方式です。音声は大問全体（2009年はレベル全体）なので、該当問題まで再生してください。

公式PDF・音声145ファイルを `private-data/github-material/`、出題用JSON・画像・音声を同ディレクトリの `prepared/` に保存しています。聴解スクリプトと解答用紙も原本として保存しています。個人学習用のローカル版に取り込み、クラウドには配備していません。

教材は[公式問題集](https://www.jlpt.jp/samples/sampleindex.html)と[問題例集](https://www.jlpt.jp/samples/sample09.html)。個人学習での利用条件は[公式サイトの利用規約](https://www.jlpt.jp/policy.html)の1(1)を参照してください。

再生成は `scripts/prepare-jlpt-material.py`、原本・正答・画像・音声の一致検査は `scripts/verify-github-material.py`、全年度・全レベルの件数検査は `node checks/jlpt-material-check.mjs`。2009年の画像正答表は目視転記し、原本ハッシュ付きの `private-data/github-material/jlpt-2009-verified-answers.json` で固定しています。

GitHubの旧JLPT 158回分は抽出テキストとJSONを全て取得済みです。元PDFはリポジトリに含まれず、Releasesにも提供されていません。OCRの崩れと問題・正答の対応を元PDFで照合できないため、出題用には未登録です。公式15冊分とは別です。

検証済み：既存機能・公開教材混入防止、全原本・正答・画像画素・音声の一致、34,670問の索引と保存復元、N1〜N5のブラウザでの聴解音声読み込み・解答表示・320px幅。音声を人が全編聴いて確認した検査ではありません。
