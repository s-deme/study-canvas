# 本人限定ログインと自動同期

Cloudflare PagesでWeb版を配信し、Accessで許可した本人のメールアドレスだけに利用を制限します。Pages Functionsが署名付きログイン情報を検証し、D1へ学習データを保存します。自宅PCの常時起動は不要です。クラウド版はオンライン利用を前提にしています。

本文のコマンドとファイルパスはプロジェクトルートを基準にしています。ローカル利用は [利用ガイド](usage.md)、公開対象と開発手順は [開発ガイド](development.md) を参照してください。

## 設定ファイルと検証範囲

収録済みの本人用教材をすべて使う更新は `npm run deploy:private` で行います。`deploy:cloud` は教材を同梱しない公開用アプリです。全教材の配信方式と検証手順は [本人用教材の管理](private-material.md#全教材の本人限定配備2026-10-09) を参照してください。

作業を再開するときは、まずGit管理外の `private-data/cloud-status.json`（最新配備・件数・確認結果）と `wrangler.local.jsonc`（既存環境）を確認します。以前の記録は `private-data/cloud-verification.json` と `private-data/expansion-cloud-verification.json` に残っています。現在の本番状態はWranglerの配備一覧と照合し、ローカルビルドの完了を配備済みと扱わないでください。

配備作業の途中経過は `private-data/cloud-update-progress.json`、小分け転送の確定済み単位は、同ファイルが示す配備候補内の `upload-progress.json` で確認します。

リポジトリの `wrangler.jsonc` は設定例で、DB IDはゼロの仮値です。自身のアカウント用の設定は `wrangler.local.jsonc` に保存します。このファイルと `.dev.vars` はGitの公開対象から除外します。設定例には実際のDB ID・メールアドレス・認証情報を記入しないでください。

ローカルの自動チェックとビルドは [Web版の検証結果](verification-web.md) を参照してください。本人の本番ログインと実端末間の同期は未検証です。配備後に下記の完了確認を行ってください。

Cloudflareの初回設定・料金条件は [公式の初回設定案内](https://developers.cloudflare.com/cloudflare-one/setup/) とアカウント画面で確認してください。

## 実装済みの動作

- 回答記録・日別記録・ブックマーク・直近30回の履歴・持込問題・選択中の回答を含む途中の演習を同期。
- 変更から約0.5秒後、表示中15秒ごと、画面復帰時、通信復帰時に同期。別端末で途中から再開できます。模試の締切は端末を切り替えても引き継ぎます。
- 通信やログインが切れても端末の記録を保持。「未同期」を表示し、再接続後に再試行。ページを閉じる時、未同期があればブラウザの確認を表示します。
- 更新番号を比較し、別端末の新しい記録を古い記録で上書きしない。競合時は自動同期を停止します。クラウド側を読み込む操作では、現在の端末の記録をJSONで書き出してから切り替えます。書き出したバックアップはダウンロード先に保存されていることを確認してください。
- 保存成功の応答が失われても、送信IDから保存済みと判定して回復。送信中に追加した回答も未同期として保持します。
- 元のJSONバックアップを取り込み可能。ローカル版から移行する場合、元のURLで書き出し、クラウド版の「記録」から読み込んでください。クラウド版での復元はクラウドにも同期します。
- 記録はUTF-8で10MBまで。D1の1行2MB制限に対応して分割し、更新番号と分割データは同じトランザクションで保存します。

クラウド側に記録があり、初回のブラウザにも既存の記録がある場合は競合として扱います。異なる端末で同時に演習を進めた記録の自動合算は行いません。片方をバックアップし、どちらを継続するか選びます。

## 必要なもの

- Cloudflareアカウント。
- ログインを許可するメールアドレス1件。メールのワンタイムコードを利用できます。
- Node.js 24以上（チェックには標準の `node:sqlite` を使用）。

独自ドメインは不要です。Pages・Access・Functions・D1の無料プランで開始できます。実際の利用量と無料プランの上限はアカウント画面で確認してください。

## 公開設定

次のコマンドは実際のアカウントとクラウドに変更を加えます。既存の環境を利用する場合、リソースを再作成せず、その設定をローカル設定ファイルに保存してください。

study-canvasへの名称変更では、既存のPagesプロジェクト名・D1の名前とID・Access設定を維持します。設定例と以下の名前は新規作成用です。既存環境では、D1コマンドのDB名を `wrangler.local.jsonc` の `database_name` に置き換えてください。URLを維持すると、同じ配信元の学習記録も引き続き利用できます。

1. 初回は設定例をコピーし、依存パッケージを取得してチェックします。既にローカル設定がある場合は上書きしません。

   ```powershell
   if (!(Test-Path -LiteralPath wrangler.local.jsonc)) {
     Copy-Item -LiteralPath wrangler.jsonc -Destination wrangler.local.jsonc
   }
   npm ci
   npm run check
   npm run build:cloud
   npx wrangler login
   ```

2. D1を作成します。

   ```powershell
   npx wrangler d1 create study-canvas-records
   ```

   出力された `database_id` を `wrangler.local.jsonc` のゼロのIDと置き換えます。DB名を変更した場合は `database_name` も合わせます。

   ```powershell
   npx wrangler d1 execute study-canvas-records --config wrangler.local.jsonc --remote --file schema.sql
   ```

3. Pagesプロジェクトを作成します。名前が既に使われている場合は別の名前を選び、`wrangler.local.jsonc` の `name` も合わせます。

   ```powershell
   npx wrangler pages project create study-canvas --production-branch main
   ```

4. Cloudflare Zero Trustでログイン方法を選択します。メールのワンタイムコードを使う場合は、その認証方法を追加して選択してください。Accessアプリケーションを作り、AllowのIncludeに **本人のメールアドレス1件**を指定します。`Everyone`・メールドメイン全体・Bypassは追加しません。

   本番の `<project>.pages.dev` とプレビューの `*.<project>.pages.dev` の両方を保護します。1つのAccessアプリケーションに両方のパブリックホスト名を追加し、同じ本人限定ポリシーを使用できます。Pagesの「Enable access policy」だけではプレビューのみが対象です。

5. 本番用AccessアプリケーションのAUDとZero TrustのチームURLを確認します。PagesプロジェクトのSettings → Variables and Secretsの **ProductionとPreviewの両方**に、次をSecret（Encryptを有効）として登録します。Secretは配置後も保持されます。Previewを本番と別AUDにする場合は、それぞれのAUDを設定します。

   | 名前 | 値 |
   | --- | --- |
   | `OWNER_EMAIL` | 許可する本人のメールアドレス |
   | `ACCESS_DOMAIN` | `https://<team>.cloudflareaccess.com` |
   | `ACCESS_AUD` | 対象のAccessアプリケーションのAUD |

   D1のbinding `DB` がProductionとPreviewで設定されていることも確認します。設定やDBが欠けている場合、アプリは **503でアクセスを拒否**します。未設定のまま配信しても教材や記録を公開しません。

6. Functionsを含めて配置します。

   ```powershell
   npm run deploy:cloud
   ```

   Dashboardへの `web/` フォルダのドラッグ＆ドロップは使用しません。Functionsを含むWranglerの配置を使用してください。`web/_routes.json` は全ルートを認証ミドルウェアへ通すため、削除しないでください。

## 本番での完了確認

未設定・未ログイン・許可外のメールアドレスで、以下が取得できないことを確認します。

- 本番ページとプレビューURL。
- `/app.mjs`、`/sample-questions.json` への未認証の直接アクセス。
- 本人認証後も `/questions.json` や `/private-data/questions.json` が教材を返さないこと（404または教材を含まない応答）。
- `/api/state` の読み取りと書き込み。

本人でログインし、スマホで回答・ブックマーク・問題取り込み・途中保存を行います。「同期済み」を確認してPCで読み込み、同じ記録・選択肢・途中位置になっていることを確認します。通信を切って回答し、未同期表示と再接続後の保存を確認します。両端末で更新して競合を発生させ、クラウドを上書きせず端末のバックアップを保持することを確認します。

## ローカル検証

```powershell
npm run check
npm run build:cloud
npm run check:runtime
node checks/cloud-preview.mjs
```

最後のコマンドは `http://127.0.0.1:8767` に検証用サーバーを起動します。使い捨てのSQLite DBと検証用署名付きログイン情報を使用し、本人認証を検証した上で画面を表示します。ブラウザでログインする操作は省略します。127.0.0.1だけで待ち受けます。終了するとDBは消えます。本番用サーバーとして使用しないでください。

通常のローカル版は従来どおり `Webアプリを起動.cmd` で使えます。クラウドで同期したブラウザ記録は、同期APIのない配信元では編集を停止します。

`npm run dev:cloud` は `wrangler.local.jsonc` と `.dev.vars` を使用します。上記の設定例をコピーしてDB IDを設定し、`.dev.vars.example` を `.dev.vars` にコピーして自身のAccess設定を指定してください。実際の署名付きログイン情報がない場合はアクセスを拒否します。ログイン操作なしでローカル検証する場合は `node checks/cloud-preview.mjs` を使用してください。

`npm run build:cloud` は公開用の設定例を使ってFunctionsをコンパイルします。開発・配置コマンドの前処理は、Wrangler標準の設定リダイレクト `.wrangler/deploy/config.json` を生成し、`wrangler.local.jsonc` を明示的に使用します。Pagesでは `--config` によるパス指定が非対応のため、この仕組みを使います。ローカル設定がない場合は前処理で停止します。`.wrangler/` もGit管理外です。

クラウドの開発・配置には `npm run dev:cloud`・`npm run deploy:cloud` を使用してください。手順にあるD1コマンドは `--config wrangler.local.jsonc` を使用できます。

## GitHubでのチェックと手動配備

GitHubはソース管理と自動チェックに使用します。`.github/workflows/ci.yml` は `main` へのpush・プルリクエストで、依存パッケージの取得、自動チェック、Workerのビルド、ローカルランタイム検証を実行します。Actions画面の「Run workflow」でもチェックできます。

このワークフローにはCloudflareへの配備処理はありません。GitHub ActionsへのCloudflare APIトークン・アカウントID・個人用設定の登録は不要です。`wrangler.local.jsonc` とWranglerのログイン情報は手元で管理します。公開用の `wrangler.jsonc` と使い捨ての検証用DBでチェックするため、CIから本番へ接続しません。

本番を更新するときは、Actionsの成功を確認し、同じ変更を手元でチェックして配備します。既存のPages・D1・AccessとURLをそのまま利用します。

```powershell
npm ci
npm run check
npm run build:cloud
npm run check:runtime
npm run deploy:cloud
```

配備には設定済みの `wrangler.local.jsonc` と手元のCloudflareログインが必要です。ログインが切れている場合は `npx wrangler login` を実行します。配備後はCloudflareの最新Production配備と、上記の「本番での完了確認」を確認してください。

`OWNER_EMAIL`・`ACCESS_DOMAIN`・`ACCESS_AUD` はCloudflare側のProductionとPreviewのSecretsとして保持します。D1の作成・初期化は初回設定時に行い、通常の更新では配備コマンドだけを使用します。

## 公式資料

- [AccessとPagesのJWT検証](https://developers.cloudflare.com/pages/functions/plugins/cloudflare-access/)
- [本番・プレビュー両方へのAccess設定](https://developers.cloudflare.com/pages/platform/known-issues/#enable-access-on-your-pagesdev-domain)
- [D1トランザクション](https://developers.cloudflare.com/d1/worker-api/d1-database/)
- [D1制限](https://developers.cloudflare.com/d1/platform/limits/)
- [Functions料金](https://developers.cloudflare.com/pages/functions/pricing/)
- [D1料金](https://developers.cloudflare.com/d1/platform/pricing/)

## 教材を配信しない構成

公開ソース・静的ファイルには形式確認用の自作サンプルだけを含め、Workerには問題集を組み込みません。すべての試験は問題未登録で始まり、JSON・CSVや画面入力で利用者が登録します。公式問題・図表・以前の独自問題集・旧G検教材は同梱しません。問題は本人専用のD1に学習記録と一緒に保存します。取り込んだ問題を一般公開するAPIはありません。`private-data/` はGit管理外で、配信対象の `web/` の外にあります。

今回のローカル変更だけでは、既に配備された古い教材やプレビューURLは更新されません。`npm run deploy:cloud` で教材を含まない構成を再配備し、必要に応じて旧配備・旧配布物も管理してください。本人限定のAccess設定は引き続き必要です。

新しい試験一覧・問題形式・自己評価はバージョン2の同期データで保存します。D1のスキーマは変更しません。WebとWorkerを一緒に更新し、既存のタブは再読み込みしてください。本番への配備は手元から `npm run deploy:cloud` を実行します。


本人用の教材復帰・年度別教材・公開版との分離については [本人用教材の管理](private-material.md) を参照してください。
