# 取得済みGitHubリポジトリの管理

以下の表・保留表示は初回登録時点の記録です。取得ファイルの正本は [github-sources.json](github-sources.json)、現在の候補収録状況は [取り込み状況](import-status.md) を参照してください。両経路に同じ取得元があるため、リポジトリ数・ファイル数を単純加算しません。

この台帳は公式原本の発見・照合に使用した既存の12リポジトリとGistを管理します。後続の候補42リポジトリの取得記録は `private-data/github-candidates/acquisition.json`、収録・保留の結果は [候補の取り込み結果](github-import-results.md) に保存しています。候補の取得処理も固定コミットと保存済みファイルを検査し、再取得を避けます。

2026-10-06に、取得記録から12リポジトリ・1件のGist、計22ファイルを登録しました。機械用の台帳は [github-sources.json](github-sources.json) です。リポジトリURL、取得したファイルのURL、保存名、SHA-256、サイズを記録します。問題本文・原本はGit対象外の `private-data/github-material/` に保存します。

| 取得元 | 対象・用途 | 取得ファイル数 |
| --- | --- | ---: |
| [inamuu/ITPassportExams](https://github.com/inamuu/ITPassportExams) | ITパスポート、公式問題との照合 | 1 |
| [kosukekkk-ops/fe-master-app](https://github.com/kosukekkk-ops/fe-master-app) | 基本情報、公式問題の発見・照合 | 2 |
| [onochin/assistant-surveyor-pwa](https://github.com/onochin/assistant-surveyor-pwa) | 測量士補、公式原本の発見 | 1 |
| [officeharukaze/denko2](https://github.com/officeharukaze/denko2) | 第二種電気工事士、公式原本の発見 | 1 |
| [onokumao-png/gokaku-denki-quiz](https://github.com/onokumao-png/gokaku-denki-quiz) | 電気工事士、公式原本の発見 | 1 |
| [Consuke/denken-with-llm](https://github.com/Consuke/denken-with-llm) | 電験三種、公式原本の発見 | 1 |
| [aistairc/medLLM_QA_benchmark](https://github.com/aistairc/medLLM_QA_benchmark) | 医師・歯科医師、本文を公式原本と照合 | 2 |
| [inumanma/Pharmacist-bench](https://github.com/inumanma/Pharmacist-bench) | 薬剤師、公式原本の発見 | 1 |
| [amapyonのIPA過去問リンク集（Gist）](https://gist.github.com/amapyon/477930159cb5b0c47f401b0d4a09b1aa) | IPA各試験、公式原本の発見 | 1 |
| [seika759931-cloud/quiz-app_web](https://github.com/seika759931-cloud/quiz-app_web) | 看護系試験の発見（解説は未転載） | 1 |
| [bioinfo-tsukuba/KensagishiQA](https://github.com/bioinfo-tsukuba/KensagishiQA) | 臨床検査技師、公式原本の発見 | 8 |
| [nekomarugt/j-kokushi-portal](https://github.com/nekomarugt/j-kokushi-portal) | 柔道整復師候補、登録保留 | 1 |
| [yma3mama-tech/hoikushi-shiken-app](https://github.com/yma3mama-tech/hoikushi-shiken-app) | 保育士候補、登録保留 | 1 |

「取得済み」は上記ファイルを取得した意味です。リポジトリ全体の問題を収録し終えた意味ではありません。収録・保留の内訳は [過去問の収録結果](github-material.md) とローカルの `prepared/report.json`、`prepared/nonit-report.json` に記録しています。

## 次回の取得

1. GitHubで候補を見つけたら、この台帳で既存の取得元・ファイルを確認します。
2. GitHubのファイル取得は `scripts/fetch-github-material.py` の共通 `fetch(url, name)` を使います。非IT取得スクリプトも同じ処理を利用します。GitHub Raw・Gist Rawの取得に成功すると台帳へ自動登録します。
3. 同じURLのファイルはハッシュを確認してローカルから再利用します。保存名を変えても再ダウンロードしません。所有者・リポジトリ名の大文字小文字も統一します。
4. 同じリポジトリの未取得ファイルや新年度、別コミットのURLは追加できます。既存の保存名を別URLへ使い回す場合や、取得済みファイルが改変されている場合は停止します。

`main` などの同じURLは保存した時点の内容として扱います。更新版を取得する場合は新しいコミットを指定したRaw URLと別の保存名を使ってください。ローカル原本が欠けている場合は再取得できますが、記録したハッシュと一致する必要があります。台帳の更新を伴う取得コマンドは一度に1つ実行します。

既存の取得記録を台帳へ反映するコマンドと、ネット接続を使わない確認コマンドです。

```powershell
python scripts/fetch-github-material.py --register-existing
python checks/github-source-check.py
```

台帳へ登録するのは実際に取得した発見元・照合用ファイルです。調査しただけの候補は取得済み扱いにしません。公式PDFの同一問題番号が教材に重複登録されることは、既存の教材読み込み処理でも防いでいます。
