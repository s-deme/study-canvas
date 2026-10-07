# 農業・食品の過去問追加（2026-10-07）

本人用ローカル教材へ公式公開過去問28冊・1,788問を追加しました。現在の登録数は [試験管理表](exam-inventory.md) が正本です。公開版・Gitへの教材本文同梱やクラウド配備は行っていません。

| 試験 | 年度 | 今回の追加 |
| --- | --- | ---: |
| 日本農業検定1級 | 2020〜2025 | 417 |
| 日本農業検定2級 | 2020〜2025 | 417 |
| 日本農業検定3級 | 2020〜2025 | 297 |
| 調理師試験（栃木県） | 2022〜2026 | 299 |
| 製菓衛生師試験（栃木県） | 2022〜2026 | 358 |

取得元は [日本農業検定公式過去問](https://nou-ken.jp/sample-questions/) と [栃木県公式過去問](https://www.pref.tochigi.lg.jp/e07/kakomon.html)。試験問題・図表は原本ページ画像で表示し、選択肢ラベルと公式正答を登録します。同じページの隣の問題も画像に表示されます。3択・4択を問題ごとに区別します。製菓実技の和菓子・洋菓子・製パンは別問題として数え、実技を全分野選択する本試験という意味ではありません。理由解説は未収録です。

全1,800候補から12問を除外しました。公式に全員加点・採点除外とされた6問（2026栃木県調理師問1、製菓衛生師問4・46、2025農検2級問8・67、2021農検3級問6）と、公式解答の表の位置を確定できない6問（2023農検2級問40、2021農検3級問18・43、1級問22・27・61）です。曖昧な解答を推測して補っていません。

公式解答はネイティブPDFの文字列とセルの位置を別々に読み、両方の一致を検査します。問題番号の欠落・選択肢の範囲・原本/問題JSON/画像のSHA-256と原本画像の画素一致を検査します。代表ページを目視確認しましたが、全問の目視確認や内容の専門家レビューは行っていません。

## GitHub・外部サイトの調査

- GitHubでは「日本農業検定」「農検」「食生活アドバイザー」「製菓衛生師」「調理師」「chouri-quiz」「seika 試験」を検索しました。新規採用できる問題データを確認できませんでした。既存の `nomu770501-Git/chouri-quiz` は追加取得・再加算しません。
- [食生活アドバイザー公式問題集](https://flanet.jp/shoseki/past.html) は購入案内。公式模範解答の公開だけでは設問を復元せず、2・3級は追加0問です。[外部解説](https://food-education.net/app-past-questions) と無料の独自対策問題も調べましたが、独自問題を過去問として扱っていません。
- [調理師の外部過去問一覧](https://chourishi.kakomonn.com/list)・[コクシメイク](https://kokushimake.com/cook/) も調査しました。解説の転載条件を確認できないため、外部解説を複製せず公式原本を採用しました。
- [北海道製菓衛生師](https://www.pref.hokkaido.lg.jp/hf/kse/sho/kas/194577.html) は解答非公開のため今回未採用。[三重県](https://www.pref.mie.lg.jp/SHOKUSEI/HP/70444044662_00001.htm)、[静岡県](https://www.pref.shizuoka.jp/kenkofukushi/eiseiyakuji/shokuanzen/shokushiken/1024966.html)、[関西広域連合](https://www.kouiki-kansai.jp/koikirengo/jisijimu/shikakumenkyo/seika_top/seikaeiseisisiken/9021.html)、[茨城県](https://www.pref.ibaraki.jp/hokenfukushi/seiei/eisei/syokuhin_seikaeiseishi_shiken.html) にも追加候補あり。今回の28冊には含めず、冊子形式・解答表・訂正の検査は未実施です。全国全年度の網羅は主張しません。

## 保存・再生成

原本・取得URL・ハッシュは `private-data/github-material/food-discovery.json`、変換・非収録理由は `prepared/food-report.json` に保存します。既存キャッシュを再利用します。

```powershell
python scripts/prepare-food-material.py --fetch
python checks/food-material-check.py
node scripts/append-food-material.mjs
npm run inventory:exams
```

`--fetch` なしでは保存済みの取得記録から再生成します。単独検査は原本画像の画素一致を含め、`food-verification.json` を生成します。追加処理は最後に成功した本人用ビルドの既存全パックのハッシュ・件数を検査してから今回の教材だけ追加します。再実行は重複追加せず、同じIDの教材変更は拒否します。他カテゴリの更新中に全体検査で台帳と教材の不一致が見つかったため、今回の追加はこの方法で既存教材を保持しました。全体の再生成時は `python scripts/verify-github-material.py` と `npm run build:private` を使えますが、他カテゴリの未解決の不一致があれば停止します。

本人用教材として保存し、再配布の許諾を取得したと主張しません。[栃木県の利用条件](https://www.pref.tochigi.lg.jp/kensei/kouhou/hp/chosakuken/index.html) と [農検のリンク案内](https://nou-ken.jp/about/link) を確認しました。クラウドや公開サイトへの転載は今回の作業に含めません。
