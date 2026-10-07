# 教材の取り込み状況

集計日：2026-10-07（日本時間）。[試験管理表](exam-inventory.md) と同じローカル本人用ビルドから自動生成します。直接編集しません。

件数は重複除外後にビルドへ収録された問題数です。取得ファイル数・変換候補数とは区別します。クラウド配備・内容検証の合否を示す表ではありません。ビルド後に `npm run inventory:exams` で両文書を更新してください。

## 収録元別（重複なく合計）

| 収録元 | 登録問題数 |
| --- | ---: | ---: |
| 既存・自作・復帰教材 | 4286 |
| 公式原本追加教材 | 73320 |
| 外部公開過去問（JMed48k・正答未独立照合） | 5941 |
| GitHub候補教材 | 11228 |
| **合計** | **94775** |

公式原本追加教材にはJLPTを含みます。JLPTの件数をこの合計へ再加算しません。既存教材にはFP・IPA・自作教材などを含みます。年度違いの再出題や試験別の共通午前Ⅰは別の出題として数えます。意味が近い問題の全面的な除去は保証しません。

## GitHub候補ごとの収録状況

変換時の非収録理由はローカルの `private-data/github-candidates/prepared/report.json` が正本です。下表の登録数はビルド結果です。変換記録は収録数の合計へ加算しません。全件の内容検証・利用条件確認の完了を意味しません。

| 取得元 | ビルド登録数 | 状態 | 変換時の非収録理由 |
| --- | ---: | --- | --- |
| [tossh23/architect-study-app](https://github.com/tossh23/architect-study-app/tree/4551d7777646edaf527266ba30128812ab09cb8c) | 331 | 収録あり | 必要図版がリポジトリにない（140件） / 選択肢不備（1件） / 削除・複数許容または正答不明（1件） |
| [pousan/mansion-exam-prediction](https://github.com/pousan/mansion-exam-prediction/tree/3fe69828392e3eb51d109d44bb78ec988e09d750) | 347 | 収録あり | 削除・複数許容または正答不明（3件） |
| [medicalillustotter/PTOT-kokushi-study](https://github.com/medicalillustotter/PTOT-kokushi-study/tree/66e9405e3c33c3f81a7358aa19e1ccaaaea7e34d) | 172 | 収録あり | 必要図版なし・削除または別正答あり（28件） |
| [yma3mama-tech/hoikushi-shiken-app](https://github.com/yma3mama-tech/hoikushi-shiken-app/tree/4d6f268c787529f63d318fc7dad00f78b545ac3c) | 310 | 収録あり | なし |
| [kikkawamotoharu/sharoushi-app](https://github.com/kikkawamotoharu/sharoushi-app/tree/dbb451c9f8051631950929a6b56c08e79cbfd793) | 9 | 収録あり | 第三者の市販模試由来で出典・利用条件未確定（1件） |
| [masatopapa/unkan-quiz](https://github.com/masatopapa/unkan-quiz/tree/c46bee3448733cf30484d43a255d3f8a450c1cbc) | 216 | 収録あり | なし |
| [mjrt0817/gyoseishoshi](https://github.com/mjrt0817/gyoseishoshi/tree/2a2660c8b81f4bb6613cd38b16c4cd1419154600) | 406 | 収録あり | なし |
| [masaosan425-alt/takken-app](https://github.com/masaosan425-alt/takken-app/tree/72127a69ea7c2b1afbe7396040220def8cc6ee13) | 100 | 収録あり | なし |
| [nappe0209/hoikushi-quiz](https://github.com/nappe0209/hoikushi-quiz/tree/9b312c6fa255e432a124728fe6ae6327e5df7e74) | 442 | 収録あり | 同一試験の本文・共通本文・選択肢が既存問題と一致（8件） |
| [inamuu/KikenbutsuExams](https://github.com/inamuu/KikenbutsuExams/tree/c20c30d75ce7a3907fe5940019e4fee20496a38f) | 25 | 収録あり | なし |
| [shajime0909-bit/eisei2](https://github.com/shajime0909-bit/eisei2/tree/6dc451738952a710c0217b6652d3c938c844bb6c) | 300 | 収録あり | なし |
| [no2shi4ni0-dot/syoubou-quiz](https://github.com/no2shi4ni0-dot/syoubou-quiz/tree/8e48acf9a985997502f3c7549d39692dfbd5085d) | 56 | 収録あり | なし |
| [5150kouhei-rgb/fp2-drill](https://github.com/5150kouhei-rgb/fp2-drill/tree/3b9fd56fdcf27f43dcfebf8c8c72866f9f82ddb8) | 500 | 収録あり | なし |
| [fp-hitorigoto/fp3-quiz](https://github.com/fp-hitorigoto/fp3-quiz/tree/6c0a955097345ede7b9d86821da24933155849dc) | 120 | 収録あり | なし |
| [edwin6780-tech/Boki-3](https://github.com/edwin6780-tech/Boki-3/tree/d649171eb1843beed4eb912510ca804b6889c53e) | 79 | 収録あり | なし |
| [yuaoki08/kokunai-travel-exam](https://github.com/yuaoki08/kokunai-travel-exam/tree/2d8694765c578d638ad78294bb121a2037e2120f) | 205 | 収録あり | なし |
| [pose-shell/weather-quiz-app](https://github.com/pose-shell/weather-quiz-app/tree/11c3232201d140c41baab33f8eee6f8549867d8b) | 0 | 未収録 | 教材はコードのMIT対象外。複製条件を確定するまで原本保存のみ（1件） |
| [nomu770501-Git/chouri-quiz](https://github.com/nomu770501-Git/chouri-quiz/tree/369c7582ad43208b1790d65f9c3f047bbf5963aa) | 558 | 収録あり | 同一試験の本文・共通本文・選択肢が既存問題と一致（42件） |
| [bang-prog/nutritionist](https://github.com/bang-prog/nutritionist/tree/4af250831e8f434b4b858ec8ccc17b9530db5306) | 45 | 収録あり | なし |
| [toru830/shindanshi](https://github.com/toru830/shindanshi/tree/78285be816164fe84ee62d369d9e8459a68c0228) | 10 | 収録あり | なし |
| [wangchang2049/eikenQuest](https://github.com/wangchang2049/eikenQuest/tree/d487b2b279c4e13de99889b4ab1068b7a9e0a048) | 0 | 未収録 | 生成データの設問と本文・選択肢の対応が不整合。提供元修正待ち（4400件） |
| [Ditectrev/Amazon-Web-Services-AWS-Certified-Cloud-Practitioner-CLF-C02-Practice-Tests-Exams-Questions-Answers](https://github.com/Ditectrev/Amazon-Web-Services-AWS-Certified-Cloud-Practitioner-CLF-C02-Practice-Tests-Exams-Questions-Answers/tree/765cfeae325f646db029f70a7212848a8affec3f) | 597 | 収録あり | なし |
| [hangonkou-ux/takken-app](https://github.com/hangonkou-ux/takken-app/tree/5759b6e42303aed78359967ad4e7a8a5fd254088) | 1070 | 収録あり | 選択肢不備（4件） / 正答不明または複数許容（26件） |
| [makio1988/takkenkakomon](https://github.com/makio1988/takkenkakomon/tree/dd616962423cd5637c2d608e493616bcaecb156f) | 162 | 収録あり | 同一試験の本文・共通本文・選択肢が既存問題と一致（177件） / 選択肢不備（11件） |
| [Fkzyk/takken-dojo](https://github.com/Fkzyk/takken-dojo/tree/f3e20d55d5ddba57c60d9aae76483799f8ca2211) | 450 | 収録あり | なし |
| [kita0709/pt-exam-study-app](https://github.com/kita0709/pt-exam-study-app/tree/fea0d90122c7b240e5ddf1382a7a221c0da5c4d9) | 4 | 収録あり | 同一試験の本文・共通本文・選択肢が既存問題と一致（1件） |
| [nekomarugt/j-kokushi-portal](https://github.com/nekomarugt/j-kokushi-portal/tree/7a5076bd2a8b57f2eaea4ded4aaa68307c39096e) | 1760 | 収録あり | 必要図版がリポジトリにない（3件） / 同一試験の本文・共通本文・選択肢が既存問題と一致（2件） |
| [oga3999/kokushi](https://github.com/oga3999/kokushi/tree/210cc6a2c0feb5cfe20d1675f42f57889649bdcc) | 0 | 未収録 | 配布された学習問題・正答の実体なし（1件） |
| [honnili/ClinicalEngineer](https://github.com/honnili/ClinicalEngineer/tree/d2612788e35da32172cac509825af27f9f21a240) | 0 | 未収録 | 配布された学習問題・正答の実体なし（1件） |
| [kyuuki/kanken-rails](https://github.com/kyuuki/kanken-rails/tree/c249e0696aae3d603e9cfa48554501190a517a90) | 0 | 未収録 | 配布された学習問題・正答の実体なし（1件） |
| [Valsuh45/LPIC-Past-Questions](https://github.com/Valsuh45/LPIC-Past-Questions/tree/7f647bf7b8552ff61ea36be43ec74e8243fc3f98) | 0 | 未収録 | 市販dumps由来・正答範囲外やカード状態を正答にした設問あり。教材化を保留（1件） |
| [epaulcnjp-design/takken-quiz](https://github.com/epaulcnjp-design/takken-quiz/tree/872cc63e5bea420939be91f2737369612c332af5) | 0 | 未収録 | 配布された学習問題・正答の実体なし（1件） |
| [sshNH/statistics-kentei-v2](https://github.com/sshNH/statistics-kentei-v2/tree/635b860eeccd9462e8065bac01e6587d15d805da) | 0 | 未収録 | 配布された学習問題・正答の実体なし（1件） |
| [sparkrones/met_exam](https://github.com/sparkrones/met_exam/tree/a4af9f0723cdd6269ea04c650e1512c955378d97) | 0 | 未収録 | 配布された学習問題・正答の実体なし（1件） |
| [probono-a/shakaifukushi-quiz](https://github.com/probono-a/shakaifukushi-quiz/tree/a4b6a6791e1a6e085ae5529905d75804442edc39) | 0 | 未収録 | 配布された学習問題・正答の実体なし（1件） |
| [zakiyama777/domestic-travel-manager-coach](https://github.com/zakiyama777/domestic-travel-manager-coach/tree/a6c6c72e45be70b15cd7b8352c99e906d3ad006c) | 0 | 未収録 | 配布された学習問題・正答の実体なし（1件） |
| [Sunmax0731/color-certification-exam-trainer](https://github.com/Sunmax0731/color-certification-exam-trainer/tree/3f3e1231315df7f3f3da2756fb15331771e0b1c1) | 0 | 未収録 | 検証用の仮問題のみ。学習問題なし（1件） |
| [eulerex/jlpt-test](https://github.com/eulerex/jlpt-test/tree/215b7ffd509824388541ab826b82053c7b185cd3) | 0 | 未収録 | 冊子単位OCRで問題・選択肢・正答の対応を確定できない。全原本を保存し登録保留（158件） |
| [keisks/j_bar_exam](https://github.com/keisks/j_bar_exam/tree/7442d495c2060077689583184adfeb205cdb5ba5) | 538 | 収録あり | 同一試験の本文・共通本文・選択肢が既存問題と一致（21件） |
| [stueja/lpic-1-102-500-anki-flashcards](https://github.com/stueja/lpic-1-102-500-anki-flashcards/tree/7555455260bea19447b485e235db5eddcfd9febb) | 639 | 収録あり | 同一試験の本文・共通本文・選択肢が既存問題と一致（1件） |
| [MCCMDave/linux-essentials-quiz](https://github.com/MCCMDave/linux-essentials-quiz/tree/0bb38557635cb1443037cac8e9a202b98f5d6116) | 276 | 収録あり | なし |
| [CarbonRaven/AWS-Quiz-SAA-C03](https://github.com/CarbonRaven/AWS-Quiz-SAA-C03/tree/cb847d5ab9733fa6663385a9a1adbcda98e6f590) | 997 | 収録あり | 選択肢不備（19件） / 重複選択肢（2件） |
| [iamirtasam/AWS-AI-Practitioner-Exam-Mock](https://github.com/iamirtasam/AWS-AI-Practitioner-Exam-Mock/tree/ac64b85382987814f4d86c811af10b4c1e94047a) | 504 | 収録あり | 並べ替え形式は未対応（24件） |
| [ikuma-hiroyuki/python_engineer_basic_demo](https://github.com/ikuma-hiroyuki/python_engineer_basic_demo/tree/1dc6079993288065435dbcd714b2f96996836087) | 0 | 未収録 | 本文データあり。教材の収録許諾を確認できず保留（1件） |
| [ThREE100/chosashi-app](https://github.com/ThREE100/chosashi-app/tree/22fbc96e5cb9886082ffc46e281dfa11c65ca413) | 0 | 未収録 | 本文データあり。教材の収録許諾を確認できず保留（1件） |

非収録理由は変換時点の記録です。公式原本から別経路で収録できた場合も、この取得元の未収録状態とは区別します（例：GitHubのJLPT OCR候補とJLPT公式教材）。

## 詳細・検証記録

- [本人用教材の管理](private-material.md)：保存・再生成・互換性。
- [公式原本追加の記録](github-material.md)、[GitHub候補取り込みの記録](github-import-results.md)、[JLPTの利用・検査](jlpt-import.md)。
- [取得元の管理](github-sources.md)：ファイル再取得の防止。候補調査は [調査記録](github-candidates.md)。
- [docs案内](README.md)：管理元・重複の扱い・更新手順。
