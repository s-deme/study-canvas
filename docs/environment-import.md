# 環境・自然科学の過去問取り込み

2026-10-07の調査・取り込み記録です。現在の登録件数は [試験管理表](exam-inventory.md) を参照してください。

## 気象予報士試験

[気象業務支援センターの公式公開原本](https://www.jmbsc.or.jp/jp/examination/examination-7.html) の第57〜66回を対象に、学科の一般知識・専門知識を取り込みました。第60回一般知識の問3・問8は公式訂正で全ての解答を正解とするため、通常の単一正答演習から除外します。最新の訂正版ZIPを優先します。

第59回専門知識の問8も、公式訂正で④または⑤を正解とするため除外します。
第57回一般知識の問3も、公式訂正で受験者全員を正解とするため除外します。合計300問中4問を除外し、296問を収録します。

問題は原本ページ画像で表示し、指定した問題番号に解答します。同じページの別問題も写ります。文字化けした本文を教材文へ変換しません。五択の正答は公式表の行・科目列と読み取り順の二通りで照合します。理由解説は未収録です。

実技・解答用紙・模範解答は原本に保存しています。実技の小問と解答の対応は未検証のため、演習件数に含めません。全問題の目視確認は未実施です。

[TeamSABOTENの公式原本配布ページ](https://www.team-saboten.com/school/kakomon-kaisetsu) から、第44・45・46・49・50・51・53・54・55回の学科問題と公式解答も270問追加しました。今回の収録は合計19回分・566問です。配布ページは気象業務支援センターへの掲載連絡を明記しています。独自解説は収録しません。第42・43・47・48・52・56回は訂正資料の確認が必要なため保留です。外部配布原本の実技は収録対象外です。

[提供元の利用条件](https://www.jmbsc.or.jp/jp/comment/jmbsc-hp-comment.html) に合わせ、本人用ローカル教材へ収録します。公開版へ同梱せず、`localOnly`を付けた教材を含むクラウドビルドは停止します。

再生成・検証：

```powershell
python scripts/prepare-weather-material.py --mirrors
python checks/weather-material-check.py
python scripts/verify-github-material.py
npm run build:private
npm run inventory:exams
```

取得済み原本は既存の取得処理で再利用します。ZIPと抽出PDFの対応・SHA-256は `private-data/github-material/prepared/weather-report.json` に保存します。

## eco検定とGitHub・外部サイト

- [公式お試し受験](https://kentei.tokyo-cci.or.jp/lp/eco/)：過去出題問題の抜粋。入力を伴う受験サービスで、問題データの再利用許諾は未確認。
- [過去問倶楽部](https://r-o-y.info/test/eco/index.html)：問題ページを確認。転載許諾と公式正答との一致は未確認のため収録保留。
- [ケンテイラボ](https://kentei-lab.com/exams/eco/questions)：311問と案内。過去問由来・転載許諾を確認できず収録保留。
- [シカクモン](https://shikakumon.com/eco/)：練習問題・対策教材。公式過去問として扱わず、転載許諾未確認のため収録保留。
- [pose-shell/weather-quiz-app](https://github.com/pose-shell/weather-quiz-app)：取得済みの `LICENSE-CONTENT.md` は教材をMIT対象外・著者権利留保と明記。模擬問題を公式過去問として扱わず、収録保留を維持。

GitHubは両試験名・「過去問」「問題」で再検索しました。利用可能な新規過去問候補は見つからず、書誌データ・学習記録アプリのプライバシーポリシーを問題データとして取り込みません。今回の再検索結果はこの文書に記録します。
