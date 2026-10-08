# 教材の取り込み状況

集計日：2026-10-08（日本時間）。[試験管理表](exam-inventory.md) と同じローカル本人用ビルドから自動生成します。直接編集しません。

件数は重複除外後にビルドへ収録された問題数です。取得ファイル数・変換候補数とは区別します。クラウド配備・内容検証の合否を示す表ではありません。ビルド後に `npm run inventory:exams` で両文書を更新してください。

## 収録元別（重複なく合計）

| 収録元 | 登録問題数 |
| --- | ---: | ---: |
| 既存・自作・復帰教材 | 39981 |
| 公式原本追加教材 | 79902 |
| 外部公開過去問（JMed48k・正答未独立照合） | 5941 |
| GitHub候補教材 | 19955 |
| 学校向け外部教材（正答未独立照合） | 52489 |
| **合計** | **198268** |

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
| [akiina999/otsu2-training](https://github.com/akiina999/otsu2-training/tree/d8232fba101f81c2c6c59c1f4dcb35dcf79f6ea4) | 149 | 収録あり | 同一試験の本文・共通本文・選択肢が既存問題と一致（1件） |
| [M-HMMY/kikenbutsu_otsu4_exam_app](https://github.com/M-HMMY/kikenbutsu_otsu4_exam_app/tree/ab91eba24067500362f36d524a76d73cd789e978) | 105 | 収録あり | なし |
| [tetsu0950120/otsu3](https://github.com/tetsu0950120/otsu3/tree/15cfc691dd80552e361ba9e01c6561a6e24f1308) | 151 | 収録あり | なし |
| [tetsu0950120/otsu5](https://github.com/tetsu0950120/otsu5/tree/b4cd732e0a20539817973c6db53c405e2e25fa1d) | 101 | 収録あり | なし |
| [hutatumekozou/kikenbutu-otsu1syu](https://github.com/hutatumekozou/kikenbutu-otsu1syu/tree/ce5908b5c7a50a3d26f28325b5f7cd4dd810a5b2) | 100 | 収録あり | なし |
| [iamirtasam/AWS-AI-Practitioner-Exam-Mock](https://github.com/iamirtasam/AWS-AI-Practitioner-Exam-Mock/tree/ac64b85382987814f4d86c811af10b4c1e94047a) | 528 | 収録あり | なし |
| [ikuma-hiroyuki/python_engineer_basic_demo](https://github.com/ikuma-hiroyuki/python_engineer_basic_demo/tree/1dc6079993288065435dbcd714b2f96996836087) | 82 | 収録あり | 同一試験の本文・共通本文・選択肢が既存問題と一致（3件） |
| [ThREE100/chosashi-app](https://github.com/ThREE100/chosashi-app/tree/22fbc96e5cb9886082ffc46e281dfa11c65ca413) | 553 | 収録あり | 提供元の取得失敗・削除問題または正答不明（6件） / 重複選択肢（1件） / 必要図版の対応未確定（2件） / 選択肢不備（4件） / 提供元の正答と解説内の説明が矛盾（2件） / 同一試験の本文・共通本文・選択肢が既存問題と一致（3件） / 記述問題の必要図版または模範解答なし（18件） |
| [morikagesho/boki-quise](https://github.com/morikagesho/boki-quise/tree/2b150e35d6ca06dc9d52ffcc453f93ce4160474e) | 0 | 未収録 | 配布された学習問題・正答の実体なし（1件） |
| [nktkt/bookkeeping-practice](https://github.com/nktkt/bookkeeping-practice/tree/bb3d86cd0ed719c3bb6983195c39a07624db57a1) | 269 | 収録あり | なし |
| [renatusauctor/cpa-tantou-kakomon-drill](https://github.com/renatusauctor/cpa-tantou-kakomon-drill/tree/874d1a2375858e1fe4751a797f48cd35e2e7f6bd) | 0 | 未収録 | 対応する公式原本は別経路で収録済み。第三者教材の抜粋カードは追加しない（1件） |
| [ronodera662/fp-study-app](https://github.com/ronodera662/fp-study-app/tree/286b44a07e8bb4fd157c6fd9014c017582a6e10f) | 740 | 収録あり | なし |
| [xinyue119-code/boki1-cards](https://github.com/xinyue119-code/boki1-cards/tree/baf15ba88a0526fd2f82c64e70b99a9898de81e7) | 313 | 収録あり | なし |
| [furumix2000/fp3-quiz-app](https://github.com/furumix2000/fp3-quiz-app/tree/4afe9ffd8c1679c44280df92f702dfdc5f3dee30) | 354 | 収録あり | 必要図版が仮URLまたは未取得（14件） / 同一試験の本文・共通本文・選択肢が既存問題と一致（2件） |
| [kosukekkk-ops/fe-master-app](https://github.com/kosukekkk-ops/fe-master-app/tree/11eb4fe420dd194bb9773450801f5bcd759ec55e) | 2632 | 収録あり | HTML図表の対応未確認（6件） |
| [AzFukami/Touhan-Quiz](https://github.com/AzFukami/Touhan-Quiz/tree/ca7ef538185cfeaad349a4fa7ac4979a0285cac2) | 119 | 収録あり | 栄養機能食品の届出に関する設問・正答・解説の矛盾（消費者庁FAQ照合）（1件） |
| [ot6-shibainu/ot6-shibainu-pwa](https://github.com/ot6-shibainu/ot6-shibainu-pwa/tree/350c85e96004e2e5f40d2dfe6a96897b0d44c90c) | 240 | 収録あり | 必要図版の対応未確認（10件） |
| [kids-jobai28/shoubou-quiz](https://github.com/kids-jobai28/shoubou-quiz/tree/f777e0032b7ea97ce3c5c738d528535cba4ddbbc) | 0 | 未収録 | 有料区画を含む。無料区画にも法令問題の条件不足があり今回は非収録（1件） |
| [kazuyan1004-a11y/fire-quiz-app](https://github.com/kazuyan1004-a11y/fire-quiz-app/tree/b00c100a7a0a4da304b8c563e2462c89f4fabdbf) | 10 | 収録あり | なし |
| [onokumao-png/gokaku-denki-quiz](https://github.com/onokumao-png/gokaku-denki-quiz/tree/8434af0dcba1b4a8f8aab13013dcc31ee20e671b) | 419 | 収録あり | 図表・写真を参照するが提供元データに図版なし（258件） / 重複選択肢（5件） / 同一試験の本文・共通本文・選択肢が既存問題と一致（9件） / 選択肢不備（1件） |
| [shinki5301-art/-6](https://github.com/shinki5301-art/-6/tree/81e9198cfe5c0d097cc6ee633976aa91e58313c7) | 2 | 収録あり | なし |
| [mitsugeek/shoubo-shiken](https://github.com/mitsugeek/shoubo-shiken/tree/642ecb82c3aec477962236b7859514c2b894be5c) | 87 | 収録あり | 同一試験の本文・共通本文・選択肢が既存問題と一致（6件） |
| [hkosu813-ux/shobo-quiz](https://github.com/hkosu813-ux/shobo-quiz/tree/2a9b0eb699a47990babbda38ef45d3f3ae3fe519) | 184 | 収録あり | 必要図表の対応未確認（7件） |
| [terukatsu58-hash/Shobo-quiz](https://github.com/terukatsu58-hash/Shobo-quiz/tree/09a53504eec4b8e379cb8eaa2a7393c94b4a007a) | 14 | 収録あり | なし |
| [m3tk0616-lab/shobo-tokurui-quiz](https://github.com/m3tk0616-lab/shobo-tokurui-quiz/tree/04163315e22d508fd35f8f83e05ba9c545baf250) | 0 | 未収録 | 冒頭のルートBの正答説明と引用条文に疑義。条文・全正答の確認まで保留（1件） |
| [jiagyebo19891011/shoubou-otsu6](https://github.com/jiagyebo19891011/shoubou-otsu6/tree/e20c04dd84cea99d386d2978bffa313190b7225c) | 748 | 収録あり | 同一試験の本文・共通本文・選択肢が既存問題と一致（42件） |
| [yousukeee/otsu6-cards](https://github.com/yousukeee/otsu6-cards/tree/9b4720e6ef3716aa956b48aa1e7d82cecb94207a) | 110 | 収録あり | なし |
| [tyaamarukusu-svg/study-os-shobo6](https://github.com/tyaamarukusu-svg/study-os-shobo6/tree/1679fb8d1e19b5783cf5080090d9402fd8e3c189) | 0 | 未収録 | 購入者向けアクセス区画・市販参考書由来の表示があるため非収録（1件） |
| [altxxxtla-lab/shoubou-setsubishi-drill](https://github.com/altxxxtla-lab/shoubou-setsubishi-drill/tree/f046c76a58551c0e4d87523883025bdb43de809c) | 126 | 収録あり | なし |
| [5garashi/denken2](https://github.com/5garashi/denken2/tree/a980ad6bb134ce68bc674f59d3e27278e26a6c94) | 120 | 収録あり | なし |
| [nakasyo3519/denken3all](https://github.com/nakasyo3519/denken3all/tree/bdeb66077002b6635b4a9832c0a5a0ac60b45a06) | 13 | 収録あり | 2009年度以降は公式原本の同一試験を収録（302件） / 図版照合が必要（2件） |
| [yamkenic/denken1-app](https://github.com/yamkenic/denken1-app/tree/ed75c7df87a015749e26ed1097027f7c469c199e) | 0 | 未収録 | 公式過去問と重複・一部は問題本文の代わりに概要や空欄指示のみ（1件） |
| [nemi2nd-dot/denken2-app](https://github.com/nemi2nd-dot/denken2-app/tree/319fb379e2c5ebed4d85347188d1d71972ce89bf) | 962 | 収録あり | 問題が参照する図版・配置の確認が必要（2件） / 提供元JavaScriptの構文不備（6件） / 選択肢不備（1件） |
| [ayatonikuman/denken3](https://github.com/ayatonikuman/denken3/tree/5d8b310e5aca86b5b7fc1910fb68fc865b218696) | 0 | 未収録 | 学習予定表・外部リンクのみで問題本文なし（1件） |

非収録理由は変換時点の記録です。公式原本から別経路で収録できた場合も、この取得元の未収録状態とは区別します（例：GitHubのJLPT OCR候補とJLPT公式教材）。

## 詳細・検証記録

- [本人用教材の管理](private-material.md)：保存・再生成・互換性。
- [公式原本追加の記録](github-material.md)、[GitHub候補取り込みの記録](github-import-results.md)、[JLPTの利用・検査](jlpt-import.md)。
- [取得元の管理](github-sources.md)：ファイル再取得の防止。候補調査は [調査記録](github-candidates.md)。
- [docs案内](README.md)：管理元・重複の扱い・更新手順。
