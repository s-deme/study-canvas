// Reuse the existing loopback/auth fixture and isolated Chrome approach with corrected real material.
import assert from 'node:assert/strict';
import {readFileSync,writeFileSync,mkdirSync,existsSync} from 'node:fs';
import {join,resolve,sep} from 'node:path';
import {pathToFileURL} from 'node:url';
import {servePreview} from './cloud-preview.mjs';
import {validateQuestions} from '../web/core.mjs';
import {bundledAsset} from '../scripts/cloud-runtime.mjs';
const read=file=>JSON.parse(readFileSync(file));
const displayed=text=>text.replace(/［(?:上付き|下付き|太字・斜体|太字|斜体|下線|上線)：([^［］]+)］/g,'$1')
  .replace(/^```[^\n]*$/gm,'').replace(/^\s*\|(?:\s*:?-{3,}:?\s*\|)+\s*$/gm,'')
  .replace(/^\s*\|(.+)\|\s*$/gm,(_,cells)=>cells.split('|').map(c=>c.trim()).join(''));
assert.equal(displayed('本文\n```\n値 ← 1\n```\n\n| ［下線：番号］ | 値 |\n| --- | --- |\n| 1 | 2 |').replace(/\s+/g,''),'本文値←1番号値12');
const directory=process.argv[2] || read('build/material-transcription/current.json').directory,root=pathToFileURL(resolve(directory)+sep);
const manifest=read(join(directory,'manifest.json'));
const samples=[['prose','fe::2023r05_fe_kamoku_a-q003','独立して動作'],['table','fe::2023r05_fe_kamoku_a-q002','新たな社員G'],
  ['formula','ap::2023r05a_ap_am-q01','x₁x₂'],['code','fe::2023r05_fe_kamoku_b-q001','findPrimeNumbers'],
  ['scan','nw::2009h21a_nw_am2-q001','0.02'],['multi-page','st::2023r05h_st_pm1-q01-s4','ウォレット機能'],
  ['unreviewed','fe::2023r05_fe_kamoku_a-q013','2023年度 公開問題 基本情報技術者 科目A 問13'],
  ['medical-text','orthoptist::medical-official-tp200414-10b_01-q007','脳圧亢進'],
  ['medical-crop','clinical-lab::expansion-tp170425-07b_01-q097','関連図記号'],
  ['medical-cid-reviewed','orthoptist::medical-official-tp200414-10b_01-q003','人口統計'],
  ['medical-cid-recovered','orthoptist::medical-official-tp200414-10b_01-q004','男性に多い疾患'],
  ['medical-digits-recovered','orthoptist::medical-official-tp200414-10b_01-q021','右外転神経麻痺'],
  ['medical-partial-reviewed','orthoptist::medical-official-tp170425-10a_01-q006','乳児の正常な発達'],
  ['medical-partial','orthoptist::medical-official-tp200414-10b_01-q039','涙液層破壊時間'],
  ['medical-multiple','orthoptist::medical-official-tp200414-10b_01-q019','明所視'],
  ['medical-case','nurse::expansion-tp140512-03-3a-q091','呼吸困難が増悪'],
  ['medical-chemical','clinical-lab::expansion-tp150511-05am_01-q037','（NH₂）₂CO'],
  ['medical-printer-marks','clinical-lab::expansion-tp150511-05am_01-q002','適切でない'],
  ['medical-connectors','clinical-lab::expansion-tp150511-05am_01-q014','血中濃度'],
  ['medical-layout-line','clinical-lab::expansion-tp150511-05am_01-q019','肺気腫'],
  ['medical-comma-case','public-health-nurse::expansion-tp150511-03-1pm-q045','回収率'],
  ['medical-greek-reviewed','clinical-lab::expansion-tp150511-05am_01-q015','腎糸球体障害'],
  ['medical-ruby','nurse::expansion-tp170425-05b_01-q005','業務従事者届'],
  ['accepted-single','nurse::expansion-tp190415-05b_01-q033','2019年度 看護師国家試験 午前 問33'],
  ['accepted-multiple','nurse::expansion-tp210416-05b_01-q086','2021年度 看護師国家試験 午前 問86'],
  ['answer-pending','nurse::expansion-tp190415-05b_01-q005','2019年度 看護師国家試験 午前 問5'],
  ['answer-pending-2018','nurse::expansion-tp180511-05b_01-q083','2018年度 看護師国家試験 午前 問83'],
  ['scoped-answer-table','sme-consultant::business-sme-2012-A-q8','2012年度 中小企業診断士'],
  ['scoped-intent','sme-consultant::business-sme-case-2021-1-q2','先代経営者からの事業承継'],
  ['scoped-case','sme-consultant::business-sme-case-2018-1-q1','研究開発型企業'],
  ['ocr-prose','nw::2023r05h_koudo_am1-q04','動作周波数1.25GHz'],
  ['ocr-piecewise','nw::2023r05h_koudo_am1-q01','255以下の整数'],
  ['ocr-graph','nw::2023r05h_koudo_am1-q02','平均が60'],
  ['ocr-model','nw::2023r05h_koudo_am1-q09','UMLを用いて'],
  ['ocr-answer-table','ap::2023r05a_ap_pm-q06-s2','引当予定'],
  ['ocr-answer-reason','ap::2023r05a_ap_pm-q10-s2','内部供給者との目標の合意'],
  ['bulk-2023-table','au::2023r05a_koudo_am1-q06','問6'],
  ['bulk-2023-circuit','au::2023r05a_koudo_am1-q07','問7'],
  ['bulk-2024a-table-diagram','au::2024r06a_koudo_am1-q28','問28'],
  ['bulk-2024h-formula','nw::2024r06h_koudo_am1-q02','問2'],
  ['bulk-2024h-curves','nw::2024r06h_koudo_am1-q17','問17'],
  ['bulk-2025a-negation','au::2025r07a_koudo_am1-q07','問7'],
  ['bulk-2025h-subscript','nw::2025r07h_koudo_am1-q05','問5'],
  ['bulk-2025h-sql','nw::2025r07h_koudo_am1-q10','問10'],
  ['bulk-ip-roadmap','ip::2017h29a_ip-q018','問18'],
  ['bulk-ip-joined-tables','ip::2017h29a_ip-q060','問60'],
  ['bulk-ip-permission-table','ip::2017h29a_ip-q092','問92'],
  ['bulk-ip-matrix','ip::2017h29a_ip-q097','問97'],
  ['bulk-ip-venn','ip::2017h29a_ip-q098','問98'],
  ['continuation-overline','nw::2023r05h_koudo_am1-q07','NAND素子'],
  ['continuation-work-table','nw::2023r05h_koudo_am1-q19','200本'],
  ['continuation-final-question','st::2023r05h_koudo_am1-q30','労働者派遣法'],
  ['continuation-ip-underline','ip::2013h25a_ip-q004','個人情報に'],
  ['continuation-ip-table','ip::2013h25a_ip-q012','合計4個の資材'],
  ['continuation-ip-process','ip::2013h25a_ip-q037','各矢印は監査対象'],
  ['continuation-ip-ruby','ip::2013h25a_ip-q074','ゼロデイ'],
  ['continuation-ip-shading','ip::2014h26a_ip-q011','会計期間の経常利益'],
  ['continuation-ip-random-table','ip::2014h26a_ip-q051','乱数表'],
  ['continuation-ip-conditions','ip::2014h26a_ip-q075','img.jpg'],
  ['continuation-ip-availability','ip::2014h26a_ip-q084','装置Aの稼働率を0.8'],
  ['ip-next-dfd','ip::2015h27a_ip-q008','図のDFDで示された業務A'],
  ['ip-next-joined-tables','ip::2015h27a_ip-q064','建物名が'],
  ['ip-next-keys','ip::2015h27a_ip-q072','下線のうち実線'],
  ['ip-next-common-sheet','ip::2015h27a_ip-q085','セルB208には'],
  ['ip-next-two-sheets','ip::2015h27a_ip-q086','アンケート抽出表'],
  ['ip-next-common-graph','ip::2015h27a_ip-q088','相関係数を横軸'],
  ['ip-next-text-sheet','ip::2015h27a_ip-q089','セルE2に計算式'],
  ['ip-next-common-arrow','ip::2015h27a_ip-q093','アローダイアグラムを作成する手順'],
  ['ip-next-recycle-policy','ip::2015h27a_ip-q097','内容に絞り込まれた情報'],
  ['ip-next-spring-dfd','ip::2015h27h_ip-q025','伝票つづり'],
  ['ip-next-spring-ruby','ip::2015h27h_ip-q054','虹（こう）彩認証'],
  ['ip-next-spring-primary-key','ip::2015h27h_ip-q086','入退室許可表のレコード'],
  ['ip-next-spring-risk-table','ip::2015h27h_ip-q091','遅延の予測日数'],
  ['ip-next-spring-absolute-reference','ip::2015h27h_ip-q093','セルB5に計算式'],
  ['ip-next-spring-venn','ip::2015h27h_ip-q098','ベン図中の領域'],
  ['ip-next-spring-conditions','ip::2015h27h_ip-q100','同じ結果が得られる命令'],
  ['ip-2016-h-phases','ip::2016h28h_ip-q010','図のソフトウェアライフサイクル'],
  ['ip-2016-h-merged-cost','ip::2016h28h_ip-q022','導入後の運用期間'],
  ['ip-2016-h-route','ip::2016h28h_ip-q033','地点Xから出発して'],
  ['ip-2016-h-redundancy','ip::2016h28h_ip-q060','同じ装置が複数接続'],
  ['ip-2016-h-router','ip::2016h28h_ip-q078','ハブとルータを使用して'],
  ['ip-2016-h-spreadsheet','ip::2016h28h_ip-q080','買い物金額に応じた'],
  ['ip-2016-h-schema','ip::2016h28h_ip-q094','商品の仕入状況'],
  ['ip-2016-h-joined','ip::2016h28h_ip-q095','表1と表2に'],
  ['ip-2016-a-organization','ip::2016h28a_ip-q025','企業の組織形態'],
  ['ip-2016-a-image-options','ip::2016h28a_ip-q050','原因別に不良'],
  ['ip-2016-a-exponent','ip::2016h28a_ip-q061','パスワードの長さが8文字'],
  ['ip-2016-a-conditions','ip::2016h28a_ip-q074','最高気温が35度以上'],
  ['ip-2016-a-directory','ip::2016h28a_ip-q075','階層構造をもつ'],
  ['ip-2016-a-linear','ip::2016h28a_ip-q079','WPA2による暗号化'],
  ['ip-2016-a-spreadsheet','ip::2016h28a_ip-q082','セルB2～C8に'],
  ['ip-2016-a-stack','ip::2016h28a_ip-q092','後に入れたデータ'],
  ['ip-2016-a-ruby','ip::2016h28a_ip-q096','情報セキュリティにおけるリスクマネジメント'],
  ['ip-2016-a-permissions','ip::2016h28a_ip-q099','人事ファイルへのアクセス権'],
  ['ip-2017-next-stock','ip::2017h29h_ip-q032','移動平均法'],
  ['ip-2017-next-schema','ip::2017h29h_ip-q069','社員'],
  ['ip-2017-next-bits','ip::2017h29h_ip-q072','01011010'],
  ['ip-2017-next-sql','ip::2017h29h_ip-q090','S001'],
  ['ip-2017-next-sheet','ip::2017h29h_ip-q091','表計算ソフト'],
  ['ip-2017-next-final','ip::2017h29h_ip-q100','ESSID'],
  ['ip-2017-next-dfd','ip::2018h30h_ip-q005','DFD'],
  ['ip-2017-next-balance','ip::2018h30h_ip-q011','貸借対照表'],
  ['ip-2017-next-sla','ip::2018h30h_ip-q039','SLA'],
  ['ip-2017-next-network','ip::2018h30h_ip-q043','アローダイアグラム'],
  ['ip-2017-next-curves','ip::2018h30h_ip-q054','ウォータフォール'],
  ['ip-2017-next-average','ip::2018h30h_ip-q060','平均'],
  ['ip-2017-next-message','ip::2018h30h_ip-q066','ロック'],
  ['ip-2017-next-key','ip::2018h30h_ip-q081','主キー'],
  ['ip-2017-next-wildcard','ip::2018h30h_ip-q085','ワイルドカード'],
  ['ip-2017-next-essid','ip::2018h30h_ip-q100','ESSID'],
  ['ip-2018-next-schedule','ip::2018h30a_ip-q005','機械'],
  ['ip-2018-next-profit','ip::2018h30a_ip-q006','利益の計画に対する'],
  ['ip-2018-next-ruby','ip::2018h30a_ip-q025','規制'],
  ['ip-2018-next-proxy','ip::2018h30a_ip-q064','プロキシ'],
  ['ip-2018-next-copy','ip::2018h30a_ip-q080','2種類の税率'],
  ['ip-2018-next-foreign-key','ip::2018h30a_ip-q085','結合に用いた“顧客”'],
  ['ip-2018-next-signature','ip::2018h30a_ip-q093','公開鍵の組合せa'],
  ['ip-2018-next-materials','ip::2019h31h_ip-q012','シュウマイ'],
  ['ip-2018-next-ppm','ip::2019h31h_ip-q026','PPMを作図した'],
  ['ip-2018-next-gateway','ip::2019h31h_ip-q058','PC1をインターネットに接続'],
  ['ip-2018-next-prefix','ip::2019h31h_ip-q066','接頭語'],
  ['ip-2018-next-box','ip::2019h31h_ip-q071','ボックス'],
  ['ip-2018-next-join','ip::2019h31h_ip-q078','住所と所属する部署'],
  ['ip-2018-next-mail','ip::2019h31h_ip-q082','PC1のメールクライアント'],
  ['ip-2018-next-negation','ip::2019h31h_ip-q084','オンラインストレージ'],
  ['ip-2018-next-directory','ip::2019h31h_ip-q096','Webページファイルf2.html'],
  ['ip-2018-next-logic','ip::2019h31h_ip-q098','合否'],
  ['ip-2019-next-inventory','ip::2019r01a_ip-q026','部品Bの発注量a'],
  ['ip-2019-next-stack','ip::2019r01a_ip-q062','上にある品物から順に取り出す装置'],
  ['ip-2019-next-cipher','ip::2019r01a_ip-q070','大文字の英字から成る文字列の暗号化'],
  ['ip-2019-next-sum-count','ip::2019r01a_ip-q076','セルB3～B7に各月'],
  ['ip-2019-next-ruby','ip::2019r01a_ip-q100','脆（ぜい）弱性のあるIoT機器'],
  ['ip-2019-next-parallel','ip::2021r03_ip-q050','自分のデスクにあるPCと共有スペース'],
  ['ip-2019-next-relations','ip::2021r03_ip-q070','出版社と著者と本の関係'],
  ['ip-2019-next-flow','ip::2021r03_ip-q074','流れ図Xで示す処理'],
  ['ip-2019-next-risk-ruby','ip::2021r03_ip-q091','リスクアセスメントに含まれるもの'],
  ['ip-2019-next-sales','ip::2021r03_ip-q095','商品ごとの合計額が20,000円以上'],
  ['ip-2019-next-appendix-excluded','ip::2021r03_ip-q100','TCOの概念が重要視'],
  ['ip-2023-next-profit','ip::2023r05_ip-q013','販売単価を1,000円から800円'],
  ['ip-2023-next-inventory','ip::2023r05_ip-q033','製品Aを1個生産する'],
  ['ip-2023-next-arrow','ip::2023r05_ip-q041','作業Dが2日遅延'],
  ['ip-2023-next-code-reference','ip::2023r05_ip-q060','手続printArray'],
  ['ip-2023-next-if-reference','ip::2023r05_ip-q075','二つの科目X'],
  ['ip-2023-next-hybrid','ip::2023r05_ip-q086','ハイブリッド暗号方式'],
  ['ip-2023-next-underline','ip::2023r05_ip-q095','確保されなかった例'],
  ['ip-2025-next-ruby','ip::2025r07_ip-q014','俯瞰（ふかん）'],
  ['ip-2025-next-transactions','ip::2025r07_ip-q026','売掛金は何万円'],
  ['ip-2025-next-formulas','ip::2025r07_ip-q045','40日間で100本'],
  ['ip-2025-next-login-table','ip::2025r07_ip-q066','ログイン記録'],
  ['ip-2025-next-cell-reference','ip::2025r07_ip-q076','セルB1には消費税率'],
  ['ip-2025-next-code','ip::2025r07_ip-q099','calculateAmountOfPrize'],
  ['ip-2025-next-footer-excluded','ip::2025r07_ip-q100','所有物を要素として'],
  ["ip-2026-next-suit","ip::2026r08_ip-q011","プロサッカーチームのファンの集いで，人気のある選"],
  ["ip-2026-next-balance","ip::2026r08_ip-q026","表はA社の貸借対照表である。A社の自己資本比率は"],
  ["ip-2026-next-assignment","ip::2026r08_ip-q044","あるサービスデスクでは，電子メールによる問合せに"],
  ["ip-2026-next-resources","ip::2026r08_ip-q050","次の表の作業を3名で実施するとき，全ての作業を終"],
  ["ip-2026-next-primary","ip::2026r08_ip-q057","関係データベースで管理している“学生”表，“科目"],
  ["ip-2026-next-sort","ip::2026r08_ip-q067","手続sortは，要素数が2以上の整数型の配列を引"],
  ["ip-2026-next-keys","ip::2026r08_ip-q072","関係データベースで管理している“口座”表，“顧客"],
  ["ip-2026-next-sheet","ip::2026r08_ip-q074","表計算ソフトを用いて，二つの2進数α，βの和を求"],
  ["ip-2026-next-prime","ip::2026r08_ip-q085","関数isPrimeは，引数として与えられた正の整"],
  ["ip-2026-next-ruby","ip::2014h26h_ip-q050","システム監査に必要なプロセスのうち，システム監査"],
  ["ip-2026-next-box","ip::2014h26h_ip-q057","図1のように二つの入力に対し，一つの出力を行うボ"],
  ["ip-2026-next-normalization","ip::2014h26h_ip-q060","ファイルで管理されていた受注データを，受注に関す"],
  ["ip-2026-next-tree","ip::2014h26h_ip-q068","図に示す階層構造において，カレントディレクトリが"],
  ["ip-2026-next-common-a","ip::2014h26h_ip-q085","運用管理部門，販売部門から受領したデータを〔デー"],
  ["ip-2026-next-staff","ip::2014h26h_ip-q086","Yさんは，電話受付センタにおける時間別の電話受付"],
  ["ip-2026-next-gray","ip::2014h26h_ip-q087","電話受付センタのオペレータの勤務形態は，図2に示"],
  ["ip-2026-next-common-b","ip::2014h26h_ip-q090","製品Hには，社外から仕入れている部品Jが使われて"],
  ["ip-2026-next-common-c","ip::2014h26h_ip-q093","入力項目“種別”の入力に使用するGUI（Grap"],
  ["ip-2026-next-common-d","ip::2014h26h_ip-q097","図1の移行作業のアローダイアグラムに基づいて作業"],
  ["ip-2026-next-recovery","ip::2014h26h_ip-q099","移行プロジェクトで作成した図1に示す移行作業のア"],
  ['ip-2011-bidding','ip::2011h23a_ip-q007','問7'],
  ['ip-2011-wbs','ip::2011h23a_ip-q042','問42'],
  ['ip-2011-state','ip::2011h23a_ip-q064','問64'],
  ['ip-2011-countif','ip::2011h23a_ip-q069','問69'],
  ['ip-2011-common-a','ip::2011h23a_ip-q089','問89'],
  ['ip-2011-grid','ip::2011h23a_ip-q090','問90'],
  ['ip-2011-flow','ip::2011h23a_ip-q091','問91'],
  ['ip-2011-hidden','ip::2011h23a_ip-q093','問93'],
  ['ip-2011-work-table','ip::2011h23a_ip-q095','問95'],
  ['ip-2011-probability','ip::2011h23a_ip-q100','問100'],
  ['ip-2012-dfd','ip::2012h24a_ip-q002','問2'],
  ['ip-2012-org','ip::2012h24a_ip-q021','問21'],
  ['ip-2012-directory','ip::2012h24a_ip-q063','問63'],
  ['ip-2012-binary-table','ip::2012h24a_ip-q072','問72'],
  ['ip-2012-concurrent','ip::2012h24a_ip-q080','問80'],
  ['ip-2012-sum-spec','ip::2012h24a_ip-q086','問86'],
  ['ip-2012-if-spec','ip::2012h24a_ip-q088','問88'],
  ['ip-2012-common-b','ip::2012h24a_ip-q089','問89'],
  ['ip-2012-run-length','ip::2012h24a_ip-q096','問96'],
  ['ip-2012-common-d','ip::2012h24a_ip-q098','問98'],
  ['ip-2011-wildcard','ip::2011h23a_ip-q073','問73'],
  ['ip-2012-negation','ip::2012h24a_ip-q062','問62'],
  ['ip-2012-inappropriate','ip::2012h24a_ip-q097','問97'],
  ["ip-2013-common-2013h25a_ip-q085", "ip::2013h25a_ip-q085", "N社内のプロジェクトは，構成員全員が相互にコミュニケーションをと"],
  ["ip-2013-common-2013h25a_ip-q086", "ip::2013h25a_ip-q086", "N社が，見積依頼先のB社及びC社と守秘義務契約を締結した理由とし"],
  ["ip-2013-common-2013h25a_ip-q087", "ip::2013h25a_ip-q087", "N社とB社は，ソフトウェア開発の期間短縮を実現するために，締結し"],
  ["ip-2013-common-2013h25a_ip-q088", "ip::2013h25a_ip-q088", "N社は，7月1日から図1のガントチャートの変更計画に従って工程管"],
  ["ip-2013-common-2013h25a_ip-q089", "ip::2013h25a_ip-q089", "Mさんが担当することになった“事務担当者の残業増加”に該当する損"],
  ["ip-2013-common-2013h25a_ip-q090", "ip::2013h25a_ip-q090", "Mさんは，改善案を検討する前に〔業務改善の企画書作成に関する上司"],
  ["ip-2013-common-2013h25a_ip-q091", "ip::2013h25a_ip-q091", "Mさんは，〔業務改善の企画書作成に関する上司からの指示〕の(2)"],
  ["ip-2013-common-2013h25a_ip-q092", "ip::2013h25a_ip-q092", "Mさんは複数のアイデアを，評価軸ごとに5点満点で評価した。関係者"],
  ["ip-2013-common-2013h25a_ip-q093", "ip::2013h25a_ip-q093", "総務部の情報太郎さんが，2010年9月第2週の業務報告書を作成し"],
  ["ip-2013-common-2013h25a_ip-q094", "ip::2013h25a_ip-q094", "ひな形ファイルを用いて，新たに業務報告書をワープロソフトで作成す"],
  ["ip-2013-common-2013h25a_ip-q095", "ip::2013h25a_ip-q095", "“報告書”フォルダのファイルをファイル名で整列したときに，関連資"],
  ["ip-2013-common-2013h25a_ip-q096", "ip::2013h25a_ip-q096", "機密度の高い関連資料のファイルに設定するパスワードとして，適切な"],
  ["ip-2013-common-2013h25a_ip-q097", "ip::2013h25a_ip-q097", "Bさんは，RFIDを内蔵した利用者カードを発行し，書籍にはシート"],
  ["ip-2013-common-2013h25a_ip-q098", "ip::2013h25a_ip-q098", "A図書館には数十万冊の蔵書があり，新システムに移行するためには，"],
  ["ip-2013-common-2013h25a_ip-q099", "ip::2013h25a_ip-q099", "Bさんは〔要望事項〕を実現するために，市販されているRFIDを用"],
  ["ip-2013-common-2013h25a_ip-q100", "ip::2013h25a_ip-q100", "A図書館では，書籍の他に雑誌も閲覧に供している。ただし，貸出しは"],
  ["ip-2014-common-2014h26a_ip-q085", "ip::2014h26a_ip-q085", "Xソフトの開発が終了する日は，開始から最短で何日目か。"],
  ["ip-2014-common-2014h26a_ip-q086", "ip::2014h26a_ip-q086", "Xソフトの開発が表1のとおりに進んだ場合，開始してから10日目の"],
  ["ip-2014-common-2014h26a_ip-q087", "ip::2014h26a_ip-q087", "作業Hは，他の作業に比べて日数が多い。作業Hの内容を確認したとこ"],
  ["ip-2014-common-2014h26a_ip-q088", "ip::2014h26a_ip-q088", "前作業が終了していないことが原因で，作業Hの開始が1日遅れるとい"],
  ["ip-2014-common-2014h26a_ip-q089", "ip::2014h26a_ip-q089", "Sさんが，現PCと旧PCを無線LANに接続してファイルをコピーす"],
  ["ip-2014-common-2014h26a_ip-q090", "ip::2014h26a_ip-q090", "旧PCに保管してある画像ファイルを現PCに転送するのに要した時間"],
  ["ip-2014-common-2014h26a_ip-q091", "ip::2014h26a_ip-q091", "Sさんは，画像ファイルを復旧した後に，現PCに保管している画像フ"],
  ["ip-2014-common-2014h26a_ip-q092", "ip::2014h26a_ip-q092", "Sさんは，現PCに保管した画像ファイルに色調補正などの加工をする"],
  ["ip-2014-common-2014h26a_ip-q093", "ip::2014h26a_ip-q093", "図2のテストの採点結果入力のワークシートに，組別の得点分布表を作"],
  ["ip-2014-common-2014h26a_ip-q094", "ip::2014h26a_ip-q094", "図3のテストの採点結果入力のワークシートのセルH53に，全受講生"],
  ["ip-2014-common-2014h26a_ip-q095", "ip::2014h26a_ip-q095", "T組とU組の得点分布は，図4のとおりであった。この二つの組の平均"],
  ["ip-2014-common-2014h26a_ip-q096", "ip::2014h26a_ip-q096", "P～S組の平均点と標準偏差は，表2のとおりであった。この四つの組"],
  ["ip-2014-common-2014h26a_ip-q097", "ip::2014h26a_ip-q097", "交通費精算業務の流れを示す図を作成した。流れ図中のa～cに入れる"],
  ["ip-2014-common-2014h26a_ip-q098", "ip::2014h26a_ip-q098", "精算システムを導入しても，事務担当者が精査する現在の申請内容のう"],
  ["ip-2014-common-2014h26a_ip-q099", "ip::2014h26a_ip-q099", "精算システムのデータベースを使って，図1に示す顧客別社員別交通費"],
  ["ip-2014-common-2014h26a_ip-q100", "ip::2014h26a_ip-q100", "精算システムの導入前と導入後について，各担当者の作業時間をサンプ"],
  ["shared-medical-medical-official-tp200414-08b_01-q057", "physical-therapist::medical-official-tp200414-08b_01-q057", "胃について正しいのはどれか。"],
  ["shared-medical-medical-official-tp200414-08b_01-q061", "physical-therapist::medical-official-tp200414-08b_01-q061", "細胞について［太字：誤っている］のはどれか。"],
  ["shared-medical-medical-official-tp200414-08b_01-q067", "physical-therapist::medical-official-tp200414-08b_01-q067", "排尿に関与する神経で正しいのはどれか。"],
  ["shared-medical-medical-official-tp200414-08b_01-q068", "physical-therapist::medical-official-tp200414-08b_01-q068", "男性生殖器系で正しいのはどれか。"],
  ["shared-medical-medical-official-tp200414-08b_01-q072", "physical-therapist::medical-official-tp200414-08b_01-q072", "股関節伸展、内転、内旋および膝関節屈曲に作用する筋はどれか。"],
  ["shared-medical-medical-official-tp200414-08b_01-q083", "physical-therapist::medical-official-tp200414-08b_01-q083", "Brown-Séquard症候群で損傷髄節よりも下位の反対側に現"],
  ["shared-medical-medical-official-tp200414-08b_01-q089", "physical-therapist::medical-official-tp200414-08b_01-q089", "筋強直性ジストロフィーで正しいのはどれか。"],
  ["shared-medical-medical-official-tp200414-09b_01-q057", "occupational-therapist::medical-official-tp200414-09b_01-q057", "胃について正しいのはどれか。"],
  ["shared-medical-medical-official-tp200414-09b_01-q061", "occupational-therapist::medical-official-tp200414-09b_01-q061", "細胞について［太字：誤っている］のはどれか。"],
  ["shared-medical-medical-official-tp200414-09b_01-q067", "occupational-therapist::medical-official-tp200414-09b_01-q067", "排尿に関与する神経で正しいのはどれか。"],
  ["shared-medical-medical-official-tp200414-09b_01-q068", "occupational-therapist::medical-official-tp200414-09b_01-q068", "男性生殖器系で正しいのはどれか。"],
  ["shared-medical-medical-official-tp200414-09b_01-q072", "occupational-therapist::medical-official-tp200414-09b_01-q072", "股関節伸展、内転、内旋および膝関節屈曲に作用する筋はどれか。"],
  ["shared-medical-medical-official-tp200414-09b_01-q083", "occupational-therapist::medical-official-tp200414-09b_01-q083", "Brown-Séquard症候群で損傷髄節よりも下位の反対側に現"],
  ["shared-medical-medical-official-tp200414-09b_01-q089", "occupational-therapist::medical-official-tp200414-09b_01-q089", "筋強直性ジストロフィーで正しいのはどれか。"],
  ["shared-medical-medical-official-tp200414-08a_01-q055", "physical-therapist::medical-official-tp200414-08a_01-q055", "腰神経叢に含まれるのはどれか。"],
  ["shared-medical-medical-official-tp200414-08a_01-q057", "physical-therapist::medical-official-tp200414-08a_01-q057", "気管支について正しいのはどれか。"],
  ["shared-medical-medical-official-tp200414-08a_01-q068", "physical-therapist::medical-official-tp200414-08a_01-q068", "体温調節の中枢で正しいのはどれか。"],
  ["shared-medical-medical-official-tp200414-08a_01-q076", "physical-therapist::medical-official-tp200414-08a_01-q076", "小脳橋角部に最も多い脳腫瘍はどれか。"],
  ["shared-medical-medical-official-tp200414-08a_01-q087", "physical-therapist::medical-official-tp200414-08a_01-q087", "視床痛で正しいのはどれか。"],
  ["shared-medical-medical-official-tp200414-08a_01-q092", "physical-therapist::medical-official-tp200414-08a_01-q092", "食道癌で正しいのはどれか。"],
  ["shared-medical-medical-official-tp200414-09a_01-q055", "occupational-therapist::medical-official-tp200414-09a_01-q055", "腰神経叢に含まれるのはどれか。"],
  ["shared-medical-medical-official-tp200414-09a_01-q057", "occupational-therapist::medical-official-tp200414-09a_01-q057", "気管支について正しいのはどれか。"],
  ["shared-medical-medical-official-tp200414-09a_01-q068", "occupational-therapist::medical-official-tp200414-09a_01-q068", "体温調節の中枢で正しいのはどれか。"],
  ["shared-medical-medical-official-tp200414-09a_01-q076", "occupational-therapist::medical-official-tp200414-09a_01-q076", "小脳橋角部に最も多い脳腫瘍はどれか。"],
  ["shared-medical-medical-official-tp200414-09a_01-q087", "occupational-therapist::medical-official-tp200414-09a_01-q087", "視床痛で正しいのはどれか。"],
  ["shared-medical-medical-official-tp200414-09a_01-q092", "occupational-therapist::medical-official-tp200414-09a_01-q092", "食道癌で正しいのはどれか。"],
  ["shared-medical-medical-official-tp170425-08a_01-q052", "physical-therapist::medical-official-tp170425-08a_01-q052", "体表から触知できるのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp170425-09a_01-q052", "occupational-therapist::medical-official-tp170425-09a_01-q052", "体表から触知できるのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp170425-08a_01-q053", "physical-therapist::medical-official-tp170425-08a_01-q053", "回旋筋腱板を構成する筋はどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp170425-09a_01-q053", "occupational-therapist::medical-official-tp170425-09a_01-q053", "回旋筋腱板を構成する筋はどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp170425-08a_01-q062", "physical-therapist::medical-official-tp170425-08a_01-q062", "運動単位について［太字：誤っている］のはどれか。"],
  ["shared-medical-medical-official-tp170425-09a_01-q062", "occupational-therapist::medical-official-tp170425-09a_01-q062", "運動単位について［太字：誤っている］のはどれか。"],
  ["shared-medical-medical-official-tp170425-08a_01-q082", "physical-therapist::medical-official-tp170425-08a_01-q082", "中心性脊髄損傷について正しいのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp170425-09a_01-q082", "occupational-therapist::medical-official-tp170425-09a_01-q082", "中心性脊髄損傷について正しいのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp170425-08a_01-q086", "physical-therapist::medical-official-tp170425-08a_01-q086", "変形性膝関節症について正しいのはどれか。"],
  ["shared-medical-medical-official-tp170425-09a_01-q086", "occupational-therapist::medical-official-tp170425-09a_01-q086", "変形性膝関節症について正しいのはどれか。"],
  ["shared-medical-medical-official-tp170425-08a_01-q088", "physical-therapist::medical-official-tp170425-08a_01-q088", "脳血管障害について［太字：誤っている］のはどれか。"],
  ["shared-medical-medical-official-tp170425-09a_01-q088", "occupational-therapist::medical-official-tp170425-09a_01-q088", "脳血管障害について［太字：誤っている］のはどれか。"],
  ["shared-medical-medical-official-tp170425-08a_01-q098", "physical-therapist::medical-official-tp170425-08a_01-q098", "アルコールの離脱症候群はどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp170425-09a_01-q098", "occupational-therapist::medical-official-tp170425-09a_01-q098", "アルコールの離脱症候群はどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp170425-08b_01-q060", "physical-therapist::medical-official-tp170425-08b_01-q060", "細胞分裂の開始に関わるのはどれか。"],
  ["shared-medical-medical-official-tp170425-09b_01-q060", "occupational-therapist::medical-official-tp170425-09b_01-q060", "細胞分裂の開始に関わるのはどれか。"],
  ["shared-medical-medical-official-tp170425-08b_01-q061", "physical-therapist::medical-official-tp170425-08b_01-q061", "1本の神経線維を電気刺激した場合の興奮伝導の説明で正しいのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp170425-09b_01-q061", "occupational-therapist::medical-official-tp170425-09b_01-q061", "1本の神経線維を電気刺激した場合の興奮伝導の説明で正しいのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp170425-08b_01-q065", "physical-therapist::medical-official-tp170425-08b_01-q065", "右心不全の症候として正しいのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp170425-09b_01-q065", "occupational-therapist::medical-official-tp170425-09b_01-q065", "右心不全の症候として正しいのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp170425-08b_01-q069", "physical-therapist::medical-official-tp170425-08b_01-q069", "代謝について正しいのはどれか。"],
  ["shared-medical-medical-official-tp170425-09b_01-q069", "occupational-therapist::medical-official-tp170425-09b_01-q069", "代謝について正しいのはどれか。"],
  ["shared-medical-medical-official-tp170425-08b_01-q072", "physical-therapist::medical-official-tp170425-08b_01-q072", "膝関節半月板について正しいのはどれか。"],
  ["shared-medical-medical-official-tp170425-09b_01-q072", "occupational-therapist::medical-official-tp170425-09b_01-q072", "膝関節半月板について正しいのはどれか。"],
  ["shared-medical-medical-official-tp170425-08b_01-q073", "physical-therapist::medical-official-tp170425-08b_01-q073", "足部の内がえしに作用する筋はどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp170425-09b_01-q073", "occupational-therapist::medical-official-tp170425-09b_01-q073", "足部の内がえしに作用する筋はどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp170425-08b_01-q074", "physical-therapist::medical-official-tp170425-08b_01-q074", "成人の安静開脚立位で正しいのはどれか。"],
  ["shared-medical-medical-official-tp170425-09b_01-q074", "occupational-therapist::medical-official-tp170425-09b_01-q074", "成人の安静開脚立位で正しいのはどれか。"],
  ["shared-medical-medical-official-tp170425-08b_01-q082", "physical-therapist::medical-official-tp170425-08b_01-q082", "脊髄損傷の自律神経過反射でみられるのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp170425-09b_01-q082", "occupational-therapist::medical-official-tp170425-09b_01-q082", "脊髄損傷の自律神経過反射でみられるのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp170425-08b_01-q083", "physical-therapist::medical-official-tp170425-08b_01-q083", "老研式活動能力指標の質問項目のうち、手段的ADL に該当するのはどれか。"],
  ["shared-medical-medical-official-tp170425-09b_01-q083", "occupational-therapist::medical-official-tp170425-09b_01-q083", "老研式活動能力指標の質問項目のうち、手段的ADL に該当するのはどれか。"],
  ["shared-medical-medical-official-tp170425-08b_01-q086", "physical-therapist::medical-official-tp170425-08b_01-q086", "特発性大腿骨頭壊死症について正しいのはどれか。"],
  ["shared-medical-medical-official-tp170425-09b_01-q086", "occupational-therapist::medical-official-tp170425-09b_01-q086", "特発性大腿骨頭壊死症について正しいのはどれか。"],
  ["shared-medical-medical-official-tp170425-08b_01-q092", "physical-therapist::medical-official-tp170425-08b_01-q092", "高齢者にみられる病態のうち、低栄養の関与が［太字：低い］のはどれか。"],
  ["shared-medical-medical-official-tp170425-09b_01-q092", "occupational-therapist::medical-official-tp170425-09b_01-q092", "高齢者にみられる病態のうち、低栄養の関与が［太字：低い］のはどれか。"],
  ["shared-medical-medical-official-tp170425-08b_01-q095", "physical-therapist::medical-official-tp170425-08b_01-q095", "リンパ浮腫について正しいのはどれか。"],
  ["shared-medical-medical-official-tp170425-09b_01-q095", "occupational-therapist::medical-official-tp170425-09b_01-q095", "リンパ浮腫について正しいのはどれか。"],
  ["shared-medical-medical-official-tp170425-08b_01-q099", "physical-therapist::medical-official-tp170425-08b_01-q099", "てんかんについて正しいのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp170425-09b_01-q099", "occupational-therapist::medical-official-tp170425-09b_01-q099", "てんかんについて正しいのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp210416-08a_01-q054", "physical-therapist::medical-official-tp210416-08a_01-q054", "健常成人において脊椎に対する脊髄最下端の位置はどれか。"],
  ["shared-medical-medical-official-tp210416-09a_01-q054", "occupational-therapist::medical-official-tp210416-09a_01-q054", "健常成人において脊椎に対する脊髄最下端の位置はどれか。"],
  ["shared-medical-medical-official-tp210416-08a_01-q062", "physical-therapist::medical-official-tp210416-08a_01-q062", "骨格筋について正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-09a_01-q062", "occupational-therapist::medical-official-tp210416-09a_01-q062", "骨格筋について正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-08a_01-q065", "physical-therapist::medical-official-tp210416-08a_01-q065", "心臓について正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-09a_01-q065", "occupational-therapist::medical-official-tp210416-09a_01-q065", "心臓について正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-08a_01-q066", "physical-therapist::medical-official-tp210416-08a_01-q066", "膵液について正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-09a_01-q066", "occupational-therapist::medical-official-tp210416-09a_01-q066", "膵液について正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-08a_01-q075", "physical-therapist::medical-official-tp210416-08a_01-q075", "心電図の房室ブロックの所見で正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-09a_01-q075", "occupational-therapist::medical-official-tp210416-09a_01-q075", "心電図の房室ブロックの所見で正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-08a_01-q079", "physical-therapist::medical-official-tp210416-08a_01-q079", "イラスト風に描かれた人物のセリフを書き込む形式の心理検査はどれか。"],
  ["shared-medical-medical-official-tp210416-09a_01-q079", "occupational-therapist::medical-official-tp210416-09a_01-q079", "イラスト風に描かれた人物のセリフを書き込む形式の心理検査はどれか。"],
  ["shared-medical-medical-official-tp210416-08a_01-q081", "physical-therapist::medical-official-tp210416-08a_01-q081", "老年期における精神保健上の問題として正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-09a_01-q081", "occupational-therapist::medical-official-tp210416-09a_01-q081", "老年期における精神保健上の問題として正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-08a_01-q084", "physical-therapist::medical-official-tp210416-08a_01-q084", "切断について正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-09a_01-q084", "occupational-therapist::medical-official-tp210416-09a_01-q084", "切断について正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-08a_01-q085", "physical-therapist::medical-official-tp210416-08a_01-q085", "悪性リンパ腫について正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-09a_01-q085", "occupational-therapist::medical-official-tp210416-09a_01-q085", "悪性リンパ腫について正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-08a_01-q087", "physical-therapist::medical-official-tp210416-08a_01-q087", "視床痛について正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-09a_01-q087", "occupational-therapist::medical-official-tp210416-09a_01-q087", "視床痛について正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-08a_01-q091", "physical-therapist::medical-official-tp210416-08a_01-q091", "急性心筋梗塞の発症後の血液検査所見で上昇が［太字：みられない］のはどれか。"],
  ["shared-medical-medical-official-tp210416-09a_01-q091", "occupational-therapist::medical-official-tp210416-09a_01-q091", "急性心筋梗塞の発症後の血液検査所見で上昇が［太字：みられない］のはどれか。"],
  ["shared-medical-medical-official-tp210416-08a_01-q093", "physical-therapist::medical-official-tp210416-08a_01-q093", "COPD について正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-09a_01-q093", "occupational-therapist::medical-official-tp210416-09a_01-q093", "COPD について正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-08a_01-q094", "physical-therapist::medical-official-tp210416-08a_01-q094", "介護保険制度について正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-09a_01-q094", "occupational-therapist::medical-official-tp210416-09a_01-q094", "介護保険制度について正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-08a_01-q098", "physical-therapist::medical-official-tp210416-08a_01-q098", "曝露反応妨害法が有効なのはどれか。"],
  ["shared-medical-medical-official-tp210416-09a_01-q098", "occupational-therapist::medical-official-tp210416-09a_01-q098", "曝露反応妨害法が有効なのはどれか。"],
  ["shared-medical-medical-official-tp190415-08a_01-q055", "physical-therapist::medical-official-tp190415-08a_01-q055", "問55　消化器の解剖で正しいのはどれか。"],
  ["shared-medical-medical-official-tp190415-09a_01-q055", "occupational-therapist::medical-official-tp190415-09a_01-q055", "問55　消化器の解剖で正しいのはどれか。"],
  ["shared-medical-medical-official-tp190415-08a_01-q059", "physical-therapist::medical-official-tp190415-08a_01-q059", "問59　ホルモンの産生で正しいのはどれか。"],
  ["shared-medical-medical-official-tp190415-09a_01-q059", "occupational-therapist::medical-official-tp190415-09a_01-q059", "問59　ホルモンの産生で正しいのはどれか。"],
  ["shared-medical-medical-official-tp190415-08a_01-q061", "physical-therapist::medical-official-tp190415-08a_01-q061", "問61　遺伝情報伝達で正しいのはどれか。"],
  ["shared-medical-medical-official-tp190415-09a_01-q061", "occupational-therapist::medical-official-tp190415-09a_01-q061", "問61　遺伝情報伝達で正しいのはどれか。"],
  ["shared-medical-medical-official-tp190415-08a_01-q062", "physical-therapist::medical-official-tp190415-08a_01-q062", "問62　骨格筋の筋収縮で正しいのはどれか。"],
  ["shared-medical-medical-official-tp190415-09a_01-q062", "occupational-therapist::medical-official-tp190415-09a_01-q062", "問62　骨格筋の筋収縮で正しいのはどれか。"],
  ["shared-medical-medical-official-tp190415-08a_01-q065", "physical-therapist::medical-official-tp190415-08a_01-q065", "問65　心筋の再分極に最も影響するのはどれか。"],
  ["shared-medical-medical-official-tp190415-09a_01-q065", "occupational-therapist::medical-official-tp190415-09a_01-q065", "問65　心筋の再分極に最も影響するのはどれか。"],
  ["shared-medical-medical-official-tp190415-08a_01-q069", "physical-therapist::medical-official-tp190415-08a_01-q069", "問69　代謝で［太字：誤っている］のはどれか。"],
  ["shared-medical-medical-official-tp190415-09a_01-q069", "occupational-therapist::medical-official-tp190415-09a_01-q069", "問69　代謝で［太字：誤っている］のはどれか。"],
  ["shared-medical-medical-official-tp190415-08a_01-q072", "physical-therapist::medical-official-tp190415-08a_01-q072", "問72　膝関節の運動で正しいのはどれか。"],
  ["shared-medical-medical-official-tp190415-09a_01-q072", "occupational-therapist::medical-official-tp190415-09a_01-q072", "問72　膝関節の運動で正しいのはどれか。"],
  ["shared-medical-medical-official-tp190415-08a_01-q079", "physical-therapist::medical-official-tp190415-08a_01-q079", "問79　ライフステージにおける成人期後期（50〜60歳ころ）の特徴で適切なのはどれか。"],
  ["shared-medical-medical-official-tp190415-09a_01-q079", "occupational-therapist::medical-official-tp190415-09a_01-q079", "問79　ライフステージにおける成人期後期（50〜60歳ころ）の特徴で適切なのはどれか。"],
  ["shared-medical-medical-official-tp190415-08a_01-q086", "physical-therapist::medical-official-tp190415-08a_01-q086", "問86　改訂日本版デンバー式発達スクリーニング検査〈JDDST-R〉の個人－社会領域で最も早く可能になるのはどれか。"],
  ["shared-medical-medical-official-tp190415-09a_01-q086", "occupational-therapist::medical-official-tp190415-09a_01-q086", "問86　改訂日本版デンバー式発達スクリーニング検査〈JDDST-R〉の個人－社会領域で最も早く可能になるのはどれか。"],
  ["shared-medical-medical-official-tp190415-08a_01-q089", "physical-therapist::medical-official-tp190415-08a_01-q089", "問89　脳血管障害に対して行われる検査で、［太字：誤っている］のはどれか。"],
  ["shared-medical-medical-official-tp190415-09a_01-q089", "occupational-therapist::medical-official-tp190415-09a_01-q089", "問89　脳血管障害に対して行われる検査で、［太字：誤っている］のはどれか。"],
  ["shared-medical-medical-official-tp190415-08a_01-q094", "physical-therapist::medical-official-tp190415-08a_01-q094", "問94　熱傷で正しいのはどれか。"],
  ["shared-medical-medical-official-tp190415-09a_01-q094", "occupational-therapist::medical-official-tp190415-09a_01-q094", "問94　熱傷で正しいのはどれか。"],
  ["shared-medical-medical-official-tp190415-08a_01-q099", "physical-therapist::medical-official-tp190415-08a_01-q099", "問99　神経性無食欲症で正しいのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp190415-09a_01-q099", "occupational-therapist::medical-official-tp190415-09a_01-q099", "問99　神経性無食欲症で正しいのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp190415-08b_01-q052", "physical-therapist::medical-official-tp190415-08b_01-q052", "問52　視覚伝導路に含まれるのはどれか。"],
  ["shared-medical-medical-official-tp190415-09b_01-q052", "occupational-therapist::medical-official-tp190415-09b_01-q052", "問52　視覚伝導路に含まれるのはどれか。"],
  ["shared-medical-medical-official-tp190415-08b_01-q056", "physical-therapist::medical-official-tp190415-08b_01-q056", "問56　心臓で正しいのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp190415-09b_01-q056", "occupational-therapist::medical-official-tp190415-09b_01-q056", "問56　心臓で正しいのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp190415-08b_01-q057", "physical-therapist::medical-official-tp190415-08b_01-q057", "問57　口腔で正しいのはどれか。"],
  ["shared-medical-medical-official-tp190415-09b_01-q057", "occupational-therapist::medical-official-tp190415-09b_01-q057", "問57　口腔で正しいのはどれか。"],
  ["shared-medical-medical-official-tp190415-08b_01-q062", "physical-therapist::medical-official-tp190415-08b_01-q062", "問62　副交感神経線維を含むのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp190415-09b_01-q062", "occupational-therapist::medical-official-tp190415-09b_01-q062", "問62　副交感神経線維を含むのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp190415-08b_01-q069", "physical-therapist::medical-official-tp190415-08b_01-q069", "問69　通常歩行（4km/h）の代謝当量（METs）はどれか。"],
  ["shared-medical-medical-official-tp190415-09b_01-q069", "occupational-therapist::medical-official-tp190415-09b_01-q069", "問69　通常歩行（4km/h）の代謝当量（METs）はどれか。"],
  ["shared-medical-medical-official-tp190415-08b_01-q084", "physical-therapist::medical-official-tp190415-08b_01-q084", "問84　高齢者の長期の安静臥床の影響で正しいのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp190415-09b_01-q084", "occupational-therapist::medical-official-tp190415-09b_01-q084", "問84　高齢者の長期の安静臥床の影響で正しいのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp190415-08b_01-q088", "physical-therapist::medical-official-tp190415-08b_01-q088", "問88　骨肉腫で正しいのはどれか。"],
  ["shared-medical-medical-official-tp190415-09b_01-q088", "occupational-therapist::medical-official-tp190415-09b_01-q088", "問88　骨肉腫で正しいのはどれか。"],
  ["shared-medical-medical-official-tp190415-08b_01-q093", "physical-therapist::medical-official-tp190415-08b_01-q093", "問93　急性膵炎で正しいのはどれか。"],
  ["shared-medical-medical-official-tp190415-09b_01-q093", "occupational-therapist::medical-official-tp190415-09b_01-q093", "問93　急性膵炎で正しいのはどれか。"],
  ["shared-medical-medical-official-tp190415-08b_01-q097", "physical-therapist::medical-official-tp190415-08b_01-q097", "問97　てんかんで正しいのはどれか。"],
  ["shared-medical-medical-official-tp190415-09b_01-q097", "occupational-therapist::medical-official-tp190415-09b_01-q097", "問97　てんかんで正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-08b_01-q053", "physical-therapist::medical-official-tp210416-08b_01-q053", "骨について正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-09b_01-q053", "occupational-therapist::medical-official-tp210416-09b_01-q053", "骨について正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-08b_01-q055", "physical-therapist::medical-official-tp210416-08b_01-q055", "足関節外側面において、外果の前方を走行する筋はどれか。"],
  ["shared-medical-medical-official-tp210416-09b_01-q055", "occupational-therapist::medical-official-tp210416-09b_01-q055", "足関節外側面において、外果の前方を走行する筋はどれか。"],
  ["shared-medical-medical-official-tp210416-08b_01-q064", "physical-therapist::medical-official-tp210416-08b_01-q064", "心筋について正しいのはどれか。"],
  ["shared-medical-medical-official-tp210416-09b_01-q064", "occupational-therapist::medical-official-tp210416-09b_01-q064", "心筋について正しいのはどれか。"],
  ["shared-medical-medical-official-tp220421-08a_01-q056", "physical-therapist::medical-official-tp220421-08a_01-q056", "心臓について正しいのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp220421-09a_01-q056", "occupational-therapist::medical-official-tp220421-09a_01-q056", "心臓について正しいのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp220421-08a_01-q067", "physical-therapist::medical-official-tp220421-08a_01-q067", "排便機構で正しいのはどれか。"],
  ["shared-medical-medical-official-tp220421-09a_01-q067", "occupational-therapist::medical-official-tp220421-09a_01-q067", "排便機構で正しいのはどれか。"],
  ["shared-medical-medical-official-tp220421-08a_01-q068", "physical-therapist::medical-official-tp220421-08a_01-q068", "月経について［太字：誤っている］のはどれか。"],
  ["shared-medical-medical-official-tp220421-09a_01-q068", "occupational-therapist::medical-official-tp220421-09a_01-q068", "月経について［太字：誤っている］のはどれか。"],
  ["shared-medical-medical-official-tp220421-08a_01-q069", "physical-therapist::medical-official-tp220421-08a_01-q069", "エネルギー代謝で［太字：誤っている］のはどれか。"],
  ["shared-medical-medical-official-tp220421-09a_01-q069", "occupational-therapist::medical-official-tp220421-09a_01-q069", "エネルギー代謝で［太字：誤っている］のはどれか。"],
  ["shared-medical-medical-official-tp220421-08a_01-q072", "physical-therapist::medical-official-tp220421-08a_01-q072", "膝関節屈曲運動の制限に関与するのはどれか。"],
  ["shared-medical-medical-official-tp220421-09a_01-q072", "occupational-therapist::medical-official-tp220421-09a_01-q072", "膝関節屈曲運動の制限に関与するのはどれか。"],
  ["shared-medical-medical-official-tp220421-08a_01-q074", "physical-therapist::medical-official-tp220421-08a_01-q074", "10m歩行において歩幅45cm、歩行率80歩/分を示す。\nこのときの歩行速度（m/秒）はどれか。"],
  ["shared-medical-medical-official-tp220421-09a_01-q074", "occupational-therapist::medical-official-tp220421-09a_01-q074", "10m歩行において歩幅45cm、歩行率80歩/分を示す。\nこのときの歩行速度（m/秒）はどれか。"],
  ["shared-medical-medical-official-tp220421-08a_01-q086", "physical-therapist::medical-official-tp220421-08a_01-q086", "FIMについて正しいのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp220421-09a_01-q086", "occupational-therapist::medical-official-tp220421-09a_01-q086", "FIMについて正しいのはどれか。［太字：2つ選べ］。"],
  ["shared-medical-medical-official-tp220421-08a_01-q088", "physical-therapist::medical-official-tp220421-08a_01-q088", "骨形成不全症で正しいのはどれか。"],
  ["shared-medical-medical-official-tp220421-09a_01-q088", "occupational-therapist::medical-official-tp220421-09a_01-q088", "骨形成不全症で正しいのはどれか。"],
  ["shared-medical-medical-official-tp220421-08b_01-q057", "physical-therapist::medical-official-tp220421-08b_01-q057", "腎臓について正しいのはどれか。"],
  ["shared-medical-medical-official-tp220421-09b_01-q057", "occupational-therapist::medical-official-tp220421-09b_01-q057", "腎臓について正しいのはどれか。"],
  ["shared-medical-medical-official-tp220421-08b_01-q058", "physical-therapist::medical-official-tp220421-08b_01-q058", "胸部の解剖について正しいのはどれか。"],
  ["shared-medical-medical-official-tp220421-09b_01-q058", "occupational-therapist::medical-official-tp220421-09b_01-q058", "胸部の解剖について正しいのはどれか。"],
  ["shared-medical-medical-official-tp220421-08b_01-q061", "physical-therapist::medical-official-tp220421-08b_01-q061", "遺伝情報伝達について正しいのはどれか。"],
  ["shared-medical-medical-official-tp220421-09b_01-q061", "occupational-therapist::medical-official-tp220421-09b_01-q061", "遺伝情報伝達について正しいのはどれか。"],
  ["shared-medical-medical-official-tp220421-08b_01-q065", "physical-therapist::medical-official-tp220421-08b_01-q065", "唾液分泌について正しいのはどれか。"],
  ["shared-medical-medical-official-tp220421-09b_01-q065", "occupational-therapist::medical-official-tp220421-09b_01-q065", "唾液分泌について正しいのはどれか。"],
  ["shared-medical-medical-official-tp220421-08b_01-q074", "physical-therapist::medical-official-tp220421-08b_01-q074", "正常歩行について正しいのはどれか。"],
  ["shared-medical-medical-official-tp220421-09b_01-q074", "occupational-therapist::medical-official-tp220421-09b_01-q074", "正常歩行について正しいのはどれか。"],
  ["shared-medical-medical-official-tp220421-08b_01-q077", "physical-therapist::medical-official-tp220421-08b_01-q077", "呼吸機能検査について正しいのはどれか。"],
  ["shared-medical-medical-official-tp220421-09b_01-q077", "occupational-therapist::medical-official-tp220421-09b_01-q077", "呼吸機能検査について正しいのはどれか。"],
  ["shared-medical-medical-official-tp220421-08b_01-q082", "physical-therapist::medical-official-tp220421-08b_01-q082", "リハビリテーション室で訓練中に意識を失った患者への対応としてまず行うのはどれか。"],
  ["shared-medical-medical-official-tp220421-09b_01-q082", "occupational-therapist::medical-official-tp220421-09b_01-q082", "リハビリテーション室で訓練中に意識を失った患者への対応としてまず行うのはどれか。"],
  ["shared-medical-medical-official-tp220421-08b_01-q085", "physical-therapist::medical-official-tp220421-08b_01-q085", "発達評価はどれか。"],
  ["shared-medical-medical-official-tp220421-09b_01-q085", "occupational-therapist::medical-official-tp220421-09b_01-q085", "発達評価はどれか。"],
  ["shared-medical-medical-official-tp220421-08b_01-q088", "physical-therapist::medical-official-tp220421-08b_01-q088", "二分脊椎で正しいのはどれか。"],
  ["shared-medical-medical-official-tp220421-09b_01-q088", "occupational-therapist::medical-official-tp220421-09b_01-q088", "二分脊椎で正しいのはどれか。"],
  ["shared-medical-medical-official-tp220421-08b_01-q090", "physical-therapist::medical-official-tp220421-08b_01-q090", "悪性腫瘍はどれか。"],
  ["shared-medical-medical-official-tp220421-09b_01-q090", "occupational-therapist::medical-official-tp220421-09b_01-q090", "悪性腫瘍はどれか。"],
  ["shared-medical-medical-official-tp250428-08a_01-q065", "physical-therapist::medical-official-tp250428-08a_01-q065", "心臓の刺激伝導系で正しいのはどれか。"],
  ["shared-medical-medical-official-tp250428-09a_01-q065", "occupational-therapist::medical-official-tp250428-09a_01-q065", "心臓の刺激伝導系で正しいのはどれか。"],
["verified-next-medical-official-tp190415-08b_01-q072", "physical-therapist::medical-official-tp190415-08b_01-q072", "右膝の内側面を図に示す。"],
["verified-next-medical-official-tp190415-09b_01-q072", "occupational-therapist::medical-official-tp190415-09b_01-q072", "右膝の内側面を図に示す。"],
["verified-next-medical-official-tp210416-08a_01-q060", "physical-therapist::medical-official-tp210416-08a_01-q060", "右下腿後面を図に示す。"],
["verified-next-medical-official-tp210416-09a_01-q060", "occupational-therapist::medical-official-tp210416-09a_01-q060", "右下腿後面を図に示す。"],
["verified-next-medical-official-tp210416-08b_01-q071", "physical-therapist::medical-official-tp210416-08b_01-q071", "右下腿の外側面を図に示す。矢印の筋の作用で正しい"],
["verified-next-medical-official-tp210416-09b_01-q071", "occupational-therapist::medical-official-tp210416-09b_01-q071", "右下腿の外側面を図に示す。矢印の筋の作用で正しい"],
["verified-next-medical-official-tp220421-08a_01-q070", "physical-therapist::medical-official-tp220421-08a_01-q070", "右下肢の運動の様子を図に示す。"],
["verified-next-medical-official-tp220421-09a_01-q070", "occupational-therapist::medical-official-tp220421-09a_01-q070", "右下肢の運動の様子を図に示す。"],
["verified-next-medical-official-tp240424-08b_01-q072", "physical-therapist::medical-official-tp240424-08b_01-q072", "距骨上面の高さの足関節部と下腿筋との位置関係を図"],
["verified-next-medical-official-tp240424-09b_01-q072", "occupational-therapist::medical-official-tp240424-09b_01-q072", "距骨上面の高さの足関節部と下腿筋との位置関係を図"],
["verified-next-medical-official-tp170425-08a_01-q100", "physical-therapist::medical-official-tp170425-08a_01-q100", "再発に高EE〈Expressed Emotion"],
["verified-next-medical-official-tp170425-09a_01-q100", "occupational-therapist::medical-official-tp170425-09a_01-q100", "再発に高EE〈Expressed Emotion"],
["verified-next-medical-official-tp200414-08a_01-q100", "physical-therapist::medical-official-tp200414-08a_01-q100", "概日リズムの障害による疾患はどれか。"],
["verified-next-medical-official-tp200414-09a_01-q100", "occupational-therapist::medical-official-tp200414-09a_01-q100", "概日リズムの障害による疾患はどれか。"],
["verified-next-medical-official-tp200414-08b_01-q100", "physical-therapist::medical-official-tp200414-08b_01-q100", "てんかんに伴う精神症状として［太字：適切でない］"],
["verified-next-medical-official-tp200414-09b_01-q100", "occupational-therapist::medical-official-tp200414-09b_01-q100", "てんかんに伴う精神症状として［太字：適切でない］"],
["verified-next-medical-official-tp210416-08a_01-q100", "physical-therapist::medical-official-tp210416-08a_01-q100", "てんかんについて正しいのはどれか。"],
["verified-next-medical-official-tp210416-09a_01-q100", "occupational-therapist::medical-official-tp210416-09a_01-q100", "てんかんについて正しいのはどれか。"],
["verified-next-medical-official-tp210416-08b_01-q100", "physical-therapist::medical-official-tp210416-08b_01-q100", "うつ病について正しいのはどれか。"],
["verified-next-medical-official-tp210416-09b_01-q100", "occupational-therapist::medical-official-tp210416-09b_01-q100", "うつ病について正しいのはどれか。"],
["verified-next-medical-official-tp230524-08a_01-q100", "physical-therapist::medical-official-tp230524-08a_01-q100", "強迫性障害で正しいのはどれか。"],
["verified-next-medical-official-tp230524-09a_01-q100", "occupational-therapist::medical-official-tp230524-09a_01-q100", "強迫性障害で正しいのはどれか。"],
["verified-next-medical-official-tp230524-08b_01-q100", "physical-therapist::medical-official-tp230524-08b_01-q100", "神経性無食欲症で生じやすいのはどれか。"],
["verified-next-medical-official-tp230524-09b_01-q100", "occupational-therapist::medical-official-tp230524-09b_01-q100", "神経性無食欲症で生じやすいのはどれか。"],
["verified-next-business-sme-2026-G-q11", "sme-consultant::business-sme-2026-G-q11", "第11問"],
["verified-next-business-sme-2026-G-q12", "sme-consultant::business-sme-2026-G-q12", "第12問"],
["verified-next-business-sme-2026-G-q17", "sme-consultant::business-sme-2026-G-q17", "第17問"],
["verified-next-business-sme-2026-G-q20", "sme-consultant::business-sme-2026-G-q20", "第20問"],
["verified-next-business-sme-2026-G-q25", "sme-consultant::business-sme-2026-G-q25", "第25問"],
["verified-next-business-sme-2026-G-q26", "sme-consultant::business-sme-2026-G-q26", "第26問"],
["verified-next-business-sme-2026-G-q30", "sme-consultant::business-sme-2026-G-q30", "第30問"],
["verified-next-business-sme-2024-F-q9", "sme-consultant::business-sme-2024-F-q9", "第9問"],
["verified-next-business-sme-2025-F-q10", "sme-consultant::business-sme-2025-F-q10", "第10問"],
["verified-next-business-sme-2026-E-q9", "sme-consultant::business-sme-2026-E-q9", "第9問"],
["verified-next-business-sme-2025-B-q11", "sme-consultant::business-sme-2025-B-q11", "第11問"],
["verified-next-business-sme-2026-B-q12", "sme-consultant::business-sme-2026-B-q12", "第12問"],
["verified-next-business-sme-2024-C-q15", "sme-consultant::business-sme-2024-C-q15", "第15問"],
["verified-next-business-sme-2025-C-q11", "sme-consultant::business-sme-2025-C-q11", "第11問"],
["verified-next-business-sme-2026-C-q11", "sme-consultant::business-sme-2026-C-q11", "第11問"],
["verified-next-business-sme-2026-A-q9", "sme-consultant::business-sme-2026-A-q9", "第9問"],
["verified-next-business-sme-2026-D-q10", "sme-consultant::business-sme-2026-D-q10", "第10問"],
["verified-next-business-sme-2024-D-q10", "sme-consultant::business-sme-2024-D-q10", "第10問"],
["verified-next-business-sme-2023-F-q10", "sme-consultant::business-sme-2023-F-q10", "第10問"],
["verified-next-business-sme-2025-E-q8", "sme-consultant::business-sme-2025-E-q8", "第8問"],
["verified-next-business-sme-2023-C-q13", "sme-consultant::business-sme-2023-C-q13", "第13問"],
["verified-next-business-sme-2023-D-q10", "sme-consultant::business-sme-2023-D-q10", "第10問"],
["verified-next-business-sme-2024-A-q10", "sme-consultant::business-sme-2024-A-q10", "第10問"],
["official-solution-business-sme-2023-D-q1", "sme-consultant::business-sme-2023-D-q1", "第1問"],
["official-solution-business-sme-2023-D-q2", "sme-consultant::business-sme-2023-D-q2", "第2問"],
["official-solution-business-sme-2023-D-q3", "sme-consultant::business-sme-2023-D-q3", "第3問"],
["official-solution-business-sme-2023-D-q4", "sme-consultant::business-sme-2023-D-q4", "第4問"],
["official-solution-business-sme-2023-D-q5", "sme-consultant::business-sme-2023-D-q5", "第5問"],
["official-solution-business-sme-2023-D-q6", "sme-consultant::business-sme-2023-D-q6", "第6問"],
["official-solution-business-sme-2023-D-q7", "sme-consultant::business-sme-2023-D-q7", "第7問"],
["official-solution-business-sme-2023-D-q8", "sme-consultant::business-sme-2023-D-q8", "第8問"],
["official-solution-business-sme-2023-D-q9", "sme-consultant::business-sme-2023-D-q9", "第9問"],
["official-solution-business-sme-2023-D-q11", "sme-consultant::business-sme-2023-D-q11", "第11問"],
["official-solution-business-sme-2023-D-q12", "sme-consultant::business-sme-2023-D-q12", "第12問"],
["official-solution-business-sme-2023-D-q13", "sme-consultant::business-sme-2023-D-q13", "第13問"],
["official-solution-business-sme-2023-D-q15", "sme-consultant::business-sme-2023-D-q15", "第15問"],
["official-solution-business-sme-2023-D-q16", "sme-consultant::business-sme-2023-D-q16", "第16問"],
["official-solution-business-sme-2023-D-q17", "sme-consultant::business-sme-2023-D-q17", "第17問"],
["official-solution-business-sme-2023-D-q18", "sme-consultant::business-sme-2023-D-q18", "第18問"],
["official-solution-business-sme-2023-D-q19", "sme-consultant::business-sme-2023-D-q19", "第19問"],
["official-solution-business-sme-2023-D-q20", "sme-consultant::business-sme-2023-D-q20", "第20問"],
["official-solution-business-sme-2023-D-q21", "sme-consultant::business-sme-2023-D-q21", "第21問"],
["official-solution-business-sme-2023-D-q22", "sme-consultant::business-sme-2023-D-q22", "第22問"],
["official-solution-business-sme-2023-D-q23", "sme-consultant::business-sme-2023-D-q23", "第23問"],
["official-solution-business-sme-2023-D-q24", "sme-consultant::business-sme-2023-D-q24", "第24問"],
["official-solution-business-sme-2023-D-q25", "sme-consultant::business-sme-2023-D-q25", "第25問"],
["official-solution-business-sme-2023-D-q26", "sme-consultant::business-sme-2023-D-q26", "第26問"],
["official-solution-business-sme-2023-D-q27", "sme-consultant::business-sme-2023-D-q27", "第27問"],
["official-solution-business-sme-2023-D-q28", "sme-consultant::business-sme-2023-D-q28", "第28問"],
["official-solution-business-sme-2023-D-q29", "sme-consultant::business-sme-2023-D-q29", "第29問"],
["official-solution-business-sme-2023-D-q30", "sme-consultant::business-sme-2023-D-q30", "第30問"],
["official-solution-business-sme-2023-D-q32", "sme-consultant::business-sme-2023-D-q32", "第32問"],
["official-solution-business-sme-2023-D-q33", "sme-consultant::business-sme-2023-D-q33", "第33問"],
["official-solution-business-sme-2023-D-q34", "sme-consultant::business-sme-2023-D-q34", "第34問"],
["official-solution-business-sme-2023-D-q35", "sme-consultant::business-sme-2023-D-q35", "第35問"],
["official-solution-business-sme-2023-D-q36", "sme-consultant::business-sme-2023-D-q36", "第36問"],
["official-solution-business-sme-2023-D-q37", "sme-consultant::business-sme-2023-D-q37", "第37問"],
["official-solution-business-sme-2023-D-q38", "sme-consultant::business-sme-2023-D-q38", "第38問"],
["official-solution-business-sme-2023-D-q39", "sme-consultant::business-sme-2023-D-q39", "第39問"],
["official-solution-business-sme-2023-D-q40", "sme-consultant::business-sme-2023-D-q40", "第40問"],
["verified-font-sme-consultant-business-sme-2023-F-q1","sme-consultant::business-sme-2023-F-q1",""],
["verified-font-sme-consultant-business-sme-2023-F-q2","sme-consultant::business-sme-2023-F-q2",""],
["verified-font-sme-consultant-business-sme-2023-F-q3","sme-consultant::business-sme-2023-F-q3",""],
["verified-font-sme-consultant-business-sme-2023-F-q4","sme-consultant::business-sme-2023-F-q4",""],
["verified-font-sme-consultant-business-sme-2023-F-q5","sme-consultant::business-sme-2023-F-q5",""],
["verified-font-sme-consultant-business-sme-2023-F-q6","sme-consultant::business-sme-2023-F-q6",""],
["verified-font-sme-consultant-business-sme-2023-F-q7","sme-consultant::business-sme-2023-F-q7",""],
["verified-font-sme-consultant-business-sme-2023-F-q8","sme-consultant::business-sme-2023-F-q8",""],
["verified-font-sme-consultant-business-sme-2023-F-q11","sme-consultant::business-sme-2023-F-q11",""],
["verified-font-sme-consultant-business-sme-2023-F-q12","sme-consultant::business-sme-2023-F-q12",""],
["verified-font-sme-consultant-business-sme-2023-F-q13","sme-consultant::business-sme-2023-F-q13",""],
["verified-font-sme-consultant-business-sme-2023-F-q15","sme-consultant::business-sme-2023-F-q15",""],
["verified-font-sme-consultant-business-sme-2023-F-q14","sme-consultant::business-sme-2023-F-q14",""],
["verified-font-sme-consultant-business-sme-2023-F-q16","sme-consultant::business-sme-2023-F-q16",""],
["verified-font-sme-consultant-business-sme-2023-F-q17","sme-consultant::business-sme-2023-F-q17",""],
["verified-font-sme-consultant-business-sme-2023-F-q18","sme-consultant::business-sme-2023-F-q18",""],
["verified-font-sme-consultant-business-sme-2023-F-q19","sme-consultant::business-sme-2023-F-q19",""],
["verified-font-sme-consultant-business-sme-2023-F-q20","sme-consultant::business-sme-2023-F-q20",""],
["verified-font-sme-consultant-business-sme-2023-F-q21","sme-consultant::business-sme-2023-F-q21",""],
["verified-font-sme-consultant-business-sme-2023-F-q22","sme-consultant::business-sme-2023-F-q22",""],
["verified-font-sme-consultant-business-sme-2023-F-q23","sme-consultant::business-sme-2023-F-q23",""],
["verified-font-sme-consultant-business-sme-2023-F-q24","sme-consultant::business-sme-2023-F-q24",""],
["verified-font-sme-consultant-business-sme-2023-F-q25","sme-consultant::business-sme-2023-F-q25",""],
["verified-font-sme-consultant-business-sme-2023-F-q9","sme-consultant::business-sme-2023-F-q9",""],
["verified-font-physical-therapist-medical-official-tp170425-08a_01-q087","physical-therapist::medical-official-tp170425-08a_01-q087",""],
["verified-font-occupational-therapist-medical-official-tp170425-09a_01-q087","occupational-therapist::medical-official-tp170425-09a_01-q087",""],
["verified-font-pair-physical-therapist-medical-official-tp170425-08a_01-q054", "physical-therapist::medical-official-tp170425-08a_01-q054", ""],
["verified-font-pair-occupational-therapist-medical-official-tp170425-09a_01-q054", "occupational-therapist::medical-official-tp170425-09a_01-q054", ""],
["verified-font-pair-physical-therapist-medical-official-tp170425-08a_01-q058", "physical-therapist::medical-official-tp170425-08a_01-q058", ""],
["verified-font-pair-occupational-therapist-medical-official-tp170425-09a_01-q058", "occupational-therapist::medical-official-tp170425-09a_01-q058", ""],
["verified-font-pair-physical-therapist-medical-official-tp170425-08a_01-q066", "physical-therapist::medical-official-tp170425-08a_01-q066", ""],
["verified-font-pair-occupational-therapist-medical-official-tp170425-09a_01-q066", "occupational-therapist::medical-official-tp170425-09a_01-q066", ""],
["verified-font-pair-physical-therapist-medical-official-tp170425-08b_01-q066", "physical-therapist::medical-official-tp170425-08b_01-q066", ""],
["verified-font-pair-occupational-therapist-medical-official-tp170425-09b_01-q066", "occupational-therapist::medical-official-tp170425-09b_01-q066", ""],
["verified-font-pair-physical-therapist-medical-official-tp170425-08b_01-q093", "physical-therapist::medical-official-tp170425-08b_01-q093", ""],
["verified-font-pair-occupational-therapist-medical-official-tp170425-09b_01-q093", "occupational-therapist::medical-official-tp170425-09b_01-q093", ""],
["verified-font-pair-physical-therapist-medical-official-tp190415-08a_01-q051", "physical-therapist::medical-official-tp190415-08a_01-q051", ""],
["verified-font-pair-occupational-therapist-medical-official-tp190415-09a_01-q051", "occupational-therapist::medical-official-tp190415-09a_01-q051", ""],
["verified-font-pair-physical-therapist-medical-official-tp190415-08a_01-q052", "physical-therapist::medical-official-tp190415-08a_01-q052", ""],
["verified-font-pair-occupational-therapist-medical-official-tp190415-09a_01-q052", "occupational-therapist::medical-official-tp190415-09a_01-q052", ""],
["verified-font-pair-physical-therapist-medical-official-tp190415-08a_01-q054", "physical-therapist::medical-official-tp190415-08a_01-q054", ""],
["verified-font-pair-occupational-therapist-medical-official-tp190415-09a_01-q054", "occupational-therapist::medical-official-tp190415-09a_01-q054", ""],
["verified-font-pair-physical-therapist-medical-official-tp190415-08a_01-q060", "physical-therapist::medical-official-tp190415-08a_01-q060", ""],
["verified-font-pair-occupational-therapist-medical-official-tp190415-09a_01-q060", "occupational-therapist::medical-official-tp190415-09a_01-q060", ""],
["verified-font-pair-physical-therapist-medical-official-tp190415-08a_01-q066", "physical-therapist::medical-official-tp190415-08a_01-q066", ""],
["verified-font-pair-occupational-therapist-medical-official-tp190415-09a_01-q066", "occupational-therapist::medical-official-tp190415-09a_01-q066", ""],
["verified-font-pair-physical-therapist-medical-official-tp190415-08a_01-q074", "physical-therapist::medical-official-tp190415-08a_01-q074", ""],
["verified-font-pair-occupational-therapist-medical-official-tp190415-09a_01-q074", "occupational-therapist::medical-official-tp190415-09a_01-q074", ""],
["verified-font-pair-physical-therapist-medical-official-tp190415-08a_01-q077", "physical-therapist::medical-official-tp190415-08a_01-q077", ""],
["verified-font-pair-occupational-therapist-medical-official-tp190415-09a_01-q077", "occupational-therapist::medical-official-tp190415-09a_01-q077", ""],
["verified-font-pair-physical-therapist-medical-official-tp190415-08a_01-q082", "physical-therapist::medical-official-tp190415-08a_01-q082", ""],
["verified-font-pair-occupational-therapist-medical-official-tp190415-09a_01-q082", "occupational-therapist::medical-official-tp190415-09a_01-q082", ""],
["verified-font-pair-physical-therapist-medical-official-tp190415-08a_01-q083", "physical-therapist::medical-official-tp190415-08a_01-q083", ""],
["verified-font-pair-occupational-therapist-medical-official-tp190415-09a_01-q083", "occupational-therapist::medical-official-tp190415-09a_01-q083", ""],
["verified-font-pair-physical-therapist-medical-official-tp190415-08a_01-q085", "physical-therapist::medical-official-tp190415-08a_01-q085", ""],
["verified-font-pair-occupational-therapist-medical-official-tp190415-09a_01-q085", "occupational-therapist::medical-official-tp190415-09a_01-q085", ""],
["verified-font-pair-physical-therapist-medical-official-tp190415-08a_01-q081", "physical-therapist::medical-official-tp190415-08a_01-q081", ""],
["verified-font-pair-occupational-therapist-medical-official-tp190415-09a_01-q081", "occupational-therapist::medical-official-tp190415-09a_01-q081", ""],
["verified-font-pair-physical-therapist-medical-official-tp190415-08a_01-q088", "physical-therapist::medical-official-tp190415-08a_01-q088", ""],
["verified-font-pair-occupational-therapist-medical-official-tp190415-09a_01-q088", "occupational-therapist::medical-official-tp190415-09a_01-q088", ""],
["verified-font-pair-physical-therapist-medical-official-tp190415-08a_01-q091", "physical-therapist::medical-official-tp190415-08a_01-q091", ""],
["verified-font-pair-occupational-therapist-medical-official-tp190415-09a_01-q091", "occupational-therapist::medical-official-tp190415-09a_01-q091", ""],
["verified-font-pair-physical-therapist-medical-official-tp190415-08b_01-q051", "physical-therapist::medical-official-tp190415-08b_01-q051", ""],
["verified-font-pair-occupational-therapist-medical-official-tp190415-09b_01-q051", "occupational-therapist::medical-official-tp190415-09b_01-q051", ""],
["verified-font-pair-physical-therapist-medical-official-tp190415-08b_01-q055", "physical-therapist::medical-official-tp190415-08b_01-q055", ""],
["verified-font-pair-occupational-therapist-medical-official-tp190415-09b_01-q055", "occupational-therapist::medical-official-tp190415-09b_01-q055", ""],
["verified-font-pair-physical-therapist-medical-official-tp190415-08b_01-q092", "physical-therapist::medical-official-tp190415-08b_01-q092", ""],
["verified-font-pair-occupational-therapist-medical-official-tp190415-09b_01-q092", "occupational-therapist::medical-official-tp190415-09b_01-q092", ""]
];
samples.push(["verified-font-batch-physical-therapist-medical-official-tp200414-08a_01-q056", "physical-therapist::medical-official-tp200414-08a_01-q056", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09a_01-q056", "occupational-therapist::medical-official-tp200414-09a_01-q056", ""],
["verified-font-batch-physical-therapist-medical-official-tp200414-08a_01-q061", "physical-therapist::medical-official-tp200414-08a_01-q061", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09a_01-q061", "occupational-therapist::medical-official-tp200414-09a_01-q061", ""],
["verified-font-batch-physical-therapist-medical-official-tp200414-08a_01-q062", "physical-therapist::medical-official-tp200414-08a_01-q062", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09a_01-q062", "occupational-therapist::medical-official-tp200414-09a_01-q062", ""],
["verified-font-batch-physical-therapist-medical-official-tp200414-08a_01-q065", "physical-therapist::medical-official-tp200414-08a_01-q065", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09a_01-q065", "occupational-therapist::medical-official-tp200414-09a_01-q065", ""],
["verified-font-batch-physical-therapist-medical-official-tp200414-08a_01-q067", "physical-therapist::medical-official-tp200414-08a_01-q067", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09a_01-q067", "occupational-therapist::medical-official-tp200414-09a_01-q067", ""],
["verified-font-batch-physical-therapist-medical-official-tp200414-08a_01-q073", "physical-therapist::medical-official-tp200414-08a_01-q073", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09a_01-q073", "occupational-therapist::medical-official-tp200414-09a_01-q073", ""],
["verified-font-batch-physical-therapist-medical-official-tp200414-08a_01-q074", "physical-therapist::medical-official-tp200414-08a_01-q074", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09a_01-q074", "occupational-therapist::medical-official-tp200414-09a_01-q074", ""],
["verified-font-batch-physical-therapist-medical-official-tp200414-08a_01-q079", "physical-therapist::medical-official-tp200414-08a_01-q079", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09a_01-q079", "occupational-therapist::medical-official-tp200414-09a_01-q079", ""],
["verified-font-batch-physical-therapist-medical-official-tp200414-08a_01-q082", "physical-therapist::medical-official-tp200414-08a_01-q082", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09a_01-q082", "occupational-therapist::medical-official-tp200414-09a_01-q082", ""],
["verified-font-batch-physical-therapist-medical-official-tp200414-08b_01-q052", "physical-therapist::medical-official-tp200414-08b_01-q052", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09b_01-q052", "occupational-therapist::medical-official-tp200414-09b_01-q052", ""],
["verified-font-batch-physical-therapist-medical-official-tp200414-08b_01-q054", "physical-therapist::medical-official-tp200414-08b_01-q054", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09b_01-q054", "occupational-therapist::medical-official-tp200414-09b_01-q054", ""],
["verified-font-batch-physical-therapist-medical-official-tp200414-08b_01-q056", "physical-therapist::medical-official-tp200414-08b_01-q056", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09b_01-q056", "occupational-therapist::medical-official-tp200414-09b_01-q056", ""],
["verified-font-batch-physical-therapist-medical-official-tp200414-08b_01-q060", "physical-therapist::medical-official-tp200414-08b_01-q060", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09b_01-q060", "occupational-therapist::medical-official-tp200414-09b_01-q060", ""],
["verified-font-batch-physical-therapist-medical-official-tp200414-08b_01-q064", "physical-therapist::medical-official-tp200414-08b_01-q064", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09b_01-q064", "occupational-therapist::medical-official-tp200414-09b_01-q064", ""],
["verified-font-batch-physical-therapist-medical-official-tp200414-08b_01-q065", "physical-therapist::medical-official-tp200414-08b_01-q065", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09b_01-q065", "occupational-therapist::medical-official-tp200414-09b_01-q065", ""],
["verified-font-batch-physical-therapist-medical-official-tp200414-08b_01-q070", "physical-therapist::medical-official-tp200414-08b_01-q070", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09b_01-q070", "occupational-therapist::medical-official-tp200414-09b_01-q070", ""],
["verified-font-batch-physical-therapist-medical-official-tp200414-08b_01-q071", "physical-therapist::medical-official-tp200414-08b_01-q071", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09b_01-q071", "occupational-therapist::medical-official-tp200414-09b_01-q071", ""],
["verified-font-batch-physical-therapist-medical-official-tp200414-08b_01-q082", "physical-therapist::medical-official-tp200414-08b_01-q082", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09b_01-q082", "occupational-therapist::medical-official-tp200414-09b_01-q082", ""],
["verified-font-batch-physical-therapist-medical-official-tp200414-08b_01-q094", "physical-therapist::medical-official-tp200414-08b_01-q094", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09b_01-q094", "occupational-therapist::medical-official-tp200414-09b_01-q094", ""],
["verified-font-batch-physical-therapist-medical-official-tp200414-08b_01-q096", "physical-therapist::medical-official-tp200414-08b_01-q096", ""],
["verified-font-batch-occupational-therapist-medical-official-tp200414-09b_01-q096", "occupational-therapist::medical-official-tp200414-09b_01-q096", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08a_01-q058", "physical-therapist::medical-official-tp210416-08a_01-q058", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09a_01-q058", "occupational-therapist::medical-official-tp210416-09a_01-q058", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08a_01-q072", "physical-therapist::medical-official-tp210416-08a_01-q072", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09a_01-q072", "occupational-therapist::medical-official-tp210416-09a_01-q072", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08a_01-q078", "physical-therapist::medical-official-tp210416-08a_01-q078", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09a_01-q078", "occupational-therapist::medical-official-tp210416-09a_01-q078", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08a_01-q083", "physical-therapist::medical-official-tp210416-08a_01-q083", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09a_01-q083", "occupational-therapist::medical-official-tp210416-09a_01-q083", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08a_01-q086", "physical-therapist::medical-official-tp210416-08a_01-q086", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09a_01-q086", "occupational-therapist::medical-official-tp210416-09a_01-q086", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08a_01-q092", "physical-therapist::medical-official-tp210416-08a_01-q092", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09a_01-q092", "occupational-therapist::medical-official-tp210416-09a_01-q092", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08a_01-q095", "physical-therapist::medical-official-tp210416-08a_01-q095", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09a_01-q095", "occupational-therapist::medical-official-tp210416-09a_01-q095", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08a_01-q096", "physical-therapist::medical-official-tp210416-08a_01-q096", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09a_01-q096", "occupational-therapist::medical-official-tp210416-09a_01-q096", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08a_01-q097", "physical-therapist::medical-official-tp210416-08a_01-q097", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09a_01-q097", "occupational-therapist::medical-official-tp210416-09a_01-q097", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08b_01-q051", "physical-therapist::medical-official-tp210416-08b_01-q051", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09b_01-q051", "occupational-therapist::medical-official-tp210416-09b_01-q051", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08b_01-q057", "physical-therapist::medical-official-tp210416-08b_01-q057", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09b_01-q057", "occupational-therapist::medical-official-tp210416-09b_01-q057", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08b_01-q058", "physical-therapist::medical-official-tp210416-08b_01-q058", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09b_01-q058", "occupational-therapist::medical-official-tp210416-09b_01-q058", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08b_01-q066", "physical-therapist::medical-official-tp210416-08b_01-q066", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09b_01-q066", "occupational-therapist::medical-official-tp210416-09b_01-q066", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08b_01-q068", "physical-therapist::medical-official-tp210416-08b_01-q068", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09b_01-q068", "occupational-therapist::medical-official-tp210416-09b_01-q068", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08b_01-q072", "physical-therapist::medical-official-tp210416-08b_01-q072", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09b_01-q072", "occupational-therapist::medical-official-tp210416-09b_01-q072", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08b_01-q074", "physical-therapist::medical-official-tp210416-08b_01-q074", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09b_01-q074", "occupational-therapist::medical-official-tp210416-09b_01-q074", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08b_01-q075", "physical-therapist::medical-official-tp210416-08b_01-q075", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09b_01-q075", "occupational-therapist::medical-official-tp210416-09b_01-q075", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08b_01-q079", "physical-therapist::medical-official-tp210416-08b_01-q079", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09b_01-q079", "occupational-therapist::medical-official-tp210416-09b_01-q079", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08b_01-q086", "physical-therapist::medical-official-tp210416-08b_01-q086", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09b_01-q086", "occupational-therapist::medical-official-tp210416-09b_01-q086", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08b_01-q093", "physical-therapist::medical-official-tp210416-08b_01-q093", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09b_01-q093", "occupational-therapist::medical-official-tp210416-09b_01-q093", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08b_01-q095", "physical-therapist::medical-official-tp210416-08b_01-q095", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09b_01-q095", "occupational-therapist::medical-official-tp210416-09b_01-q095", ""],
["verified-font-batch-physical-therapist-medical-official-tp210416-08b_01-q096", "physical-therapist::medical-official-tp210416-08b_01-q096", ""],
["verified-font-batch-occupational-therapist-medical-official-tp210416-09b_01-q096", "occupational-therapist::medical-official-tp210416-09b_01-q096", ""],
["retained-neighbor-physical-therapist", "physical-therapist::medical-official-tp210416-08b_01-q071", ""],
["retained-neighbor-occupational-therapist", "occupational-therapist::medical-official-tp210416-09b_01-q071", ""]);
const selected=new Map();
for(const pack of manifest.packs.filter(p=>['fe','ap','ip','au','nw','st','orthoptist','clinical-lab','nurse','public-health-nurse','sme-consultant','physical-therapist','occupational-therapist'].includes(p.examId))) for(const q of validateQuestions(read(join(directory,'web',pack.url)))) {
  const key=q.examId+'::'+q.id;if(samples.some(s=>s[1]===key)) selected.set(key,q);
}
for(const [,key] of samples) assert.ok(selected.has(key),'Browser sample must exist in the selected source: '+key);
const {onRequestGet,onRequestPut}=await import(new URL('functions/api/state.js',root));
const stateTrace=[];
const tracedGet=async context=>{const response=await onRequestGet(context),value=await response.clone().json();stateTrace.push({method:'GET',status:response.status,revision:value.revision,mutationId:value.mutationId});return response;};
const tracedPut=async context=>{const input=await context.request.clone().json(),response=await onRequestPut(context),value=await response.clone().json();stateTrace.push({method:'PUT',status:response.status,sentRevision:input.revision,sentMutationId:input.mutationId,revision:value.revision,error:value.error});return response;};
// An interrupted browser context must not reach a later fixture's database.
const preview=await servePreview(0,{webRoot:new URL('web/',root),getState:tracedGet,putState:tracedPut,assetHandler:manifest.packagedAt?bundledAsset:null});
const previewURL=`http://127.0.0.1:${preview.server.address().port}/#home`;
const browser=await(await fetch('http://127.0.0.1:9238/json/version')).json();
const ws=new WebSocket(browser.webSocketDebuggerUrl);await new Promise((ok,fail)=>{ws.onopen=ok;ws.onerror=fail;});
let id=0,context;const pending=new Map(),errors=[];
ws.onmessage=e=>{const r=JSON.parse(e.data),p=pending.get(r.id);if(p){pending.delete(r.id);r.error?p.reject(new Error(r.error.message)):p.resolve(r.result);}if(r.method==='Runtime.exceptionThrown') errors.push(r.params.exceptionDetails);};
const send=(method,params={},sessionId)=>new Promise((resolve,reject)=>{const key=++id;pending.set(key,{resolve,reject});ws.send(JSON.stringify({id:key,method,params,...(sessionId?{sessionId}:{})}));});
async function evaluate(s,expression) {const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true},s);if(r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails));return r.result.value;}
async function until(s,expression) {const end=Date.now()+60000;while(Date.now()<end){if(await evaluate(s,expression)) return;await new Promise(ok=>setTimeout(ok,100));}const diagnostic=await evaluate(s,"({route:location.hash,syncKind:document.querySelector('#sync-panel')?.dataset.kind,syncText:document.querySelector('#sync-panel')?.textContent,feedback:!!document.querySelector('.feedback'),next:!!document.querySelector('[data-action=next]')})");throw new Error('Timed out: '+expression+'; UI diagnostic: '+JSON.stringify(diagnostic));}
const click=(s,selector)=>evaluate(s,`document.querySelector(${JSON.stringify(selector)}).click()`);
const field=(s,selector,value,event='change')=>evaluate(s,`(()=>{const el=document.querySelector(${JSON.stringify(selector)});el.value=${JSON.stringify(value)};el.dispatchEvent(new Event(${JSON.stringify(event)},{bubbles:true}));})()`);
const screenshots=resolve(process.env.STUDY_CANVAS_SCREENSHOT_DIR || 'tmp/transcription/screenshots');
mkdirSync(screenshots,{recursive:true});
try {
  context=(await send('Target.createBrowserContext')).browserContextId;
  const t=await send('Target.createTarget',{url:'about:blank',browserContextId:context});
  const {sessionId:s}=await send('Target.attachToTarget',{targetId:t.targetId,flatten:true});
  await send('Page.enable',{},s);await send('Runtime.enable',{},s);
  await send('Emulation.setDeviceMetricsOverride',{width:1100,height:1000,deviceScaleFactor:1,mobile:false},s);
  await send('Page.navigate',{url:previewURL},s);
  await until(s,"!!document.querySelector('#exam-select') && document.querySelector('#sync-panel')?.dataset.kind==='synced'");
  await evaluate(s,'window.confirm=()=>true');
  for(const [name,key,query] of samples) {
    const q=selected.get(key);assert.ok(q,key);
    await field(s,'#exam-select',q.examId);
    await until(s,`JSON.parse(localStorage.getItem('gstudy.web.v1')).selectedExam===${JSON.stringify(q.examId)}`);
    await evaluate(s,"location.hash='#search'");await until(s,"!!document.querySelector('#search-input')");
    await field(s,'#search-input',q.topic,'input');
    const selector=`[data-question="${key}"]`;await until(s,`!!document.querySelector(${JSON.stringify(selector)})`);
    const lookup=/^(official-solution-|verified-font-|retained-neighbor-)/.test(name)?q.topic:name.startsWith('verified-next-')?q.prompt.replace(/^(?:問\d+[ 　]+|第\d+問\s*)/,'').split(/\r?\n/)[0].slice(0,24):/^(ip-201[1-4]-|shared-medical-)/.test(name)?q.prompt.replace(/^問\d+[ 　]+/,'').split(/\r?\n/)[0].slice(0,32):query;
    assert.ok(lookup.trim(),name+' search query must contain source text');
    await field(s,'#search-input',lookup,'input');await until(s,`!!document.querySelector(${JSON.stringify(selector)})`);
    if(name==='multi-page') {
      // These phrases occur in official answer/purpose, not in the question or commentary.
      for(const query of ['NFTの二次流通においてもその収益の一部を著作者に還元させる','構想・計画の実行と評価・改善']) {
        await field(s,'#search-input',query,'input');await until(s,`!!document.querySelector(${JSON.stringify(selector)})`);
      }
    }
    await click(s,selector);await until(s,"location.hash==='#quiz' && !!document.querySelector('[data-action=answer]')");
    await evaluate(s,"document.querySelectorAll('.question-image').forEach(i=>i.loading='eager')");
    await until(s,"[...document.querySelectorAll('.question-image')].every(i=>i.complete&&i.naturalWidth>0)");
    assert.equal(await evaluate(s,"document.querySelectorAll('.question-image').length"),q.images.length);
    if(name==='medical-text') {assert.equal(q.images.length,0);assert.deepEqual(q.options,['1　頭痛','2　高眼圧','3　うっ血乳頭','4　視神経萎縮','5　外転神経麻痺']);}
    if(name==='medical-crop') assert.ok(q.images.length && q.images.every(i=>i.src.startsWith('assets/transcription/')));
    if(name==='medical-cid-reviewed') {assert.equal(q.images.length,0);assert.ok(q.prompt.includes('(2018年)') && q.options[2].includes('2億2600万人'));}
    if(name==='medical-cid-recovered') {assert.equal(q.images.length,0);assert.ok(q.options[3].includes('抗アクアポリン4抗体') && q.options[4].includes('〈AZOOR〉'));}
    if(name==='medical-digits-recovered') {assert.equal(q.images.length,0);assert.ok(q.options[1].includes('第1眼位') && q.options[2].includes('3step'));}
    if(name==='medical-partial') {assert.ok(q.options.some(o=>o.includes('判読保留')) && q.images.length && q.images.every(i=>i.src.startsWith('assets/transcription/')));}
    if(name==='medical-partial-reviewed') {assert.equal(q.images.length,0);assert.equal(q.textReview.options,'source-verified');assert.ok(q.options[1].includes('5か月で寝返り'));}
    if(name==='medical-case') {assert.ok(q.passage.includes('次の文を読み91～93') && q.passage.includes('25 歳'));assert.ok(!q.options.some(o=>o.includes('93') || o.includes('次の文を読み')));assert.ok(await evaluate(s,"document.querySelector('.passage')?.textContent.includes('25 歳') && !document.querySelector('.passage').closest('details')"));}
    if(name==='medical-connectors') {assert.equal(q.images.length,0);assert.equal(q.options[0],'1．Addison 病 — 副腎皮質刺激ホルモン');assert.equal(q.options[4],'5．副腎性Cushing 症候群 — アルドステロン');}
    if(name==='medical-layout-line') {assert.equal(q.images.length,0);assert.equal(q.options[0],'1．1 秒量〈FEV［下付き：1.0］〉');assert.equal(q.options[3],'4．機能的残気量〈FRC〉');assert.ok(await evaluate(s,"[...document.querySelectorAll('.option sub')].some(e=>e.textContent==='1.0')"));}
    if(name==='medical-comma-case') {assert.equal(q.images.length,0);assert.ok(q.passage.includes('次の文を読み45、46') && q.passage.includes('人口8 万人'));assert.deepEqual(q.options,['1．自治会','2．シルバー人材センター','3．指定居宅介護支援事業所','4．指定居宅サービス事業所']);}
    if(name==='medical-greek-reviewed') {assert.equal(q.images.length,0);assert.equal(q.options[4],'5．尿中［斜体：β］₂-ミクログロブリン');assert.ok(await evaluate(s,"[...document.querySelectorAll('.option i')].some(e=>e.textContent==='β')"));}
    if(name==='medical-ruby') {assert.equal(q.answer,1);assert.equal(q.subject,'午前');assert.equal(q.images.length,0);assert.equal(q.textReview.prompt,'source-verified');assert.equal(q.textReview.options,'source-verified');assert.ok(q.prompt.includes('看護師の業務従事者届') && !q.prompt.includes('かんご'));assert.ok(q.options[3].startsWith('4．10 年'));}
    if(name.startsWith('shared-medical-')) {
      assert.equal(q.images.length,0);assert.equal(q.options.length,5);assert.equal(q.textReview.prompt,'source-verified');assert.equal(q.textReview.options,'source-verified');
      assert.ok(!/判読保留|未照合/.test(q.prompt+q.options.join('')));
      if(q.id.includes('tp200414-') && q.id.includes('b_01-q061')) {assert.equal(await evaluate(s,"[...document.querySelectorAll('.option sup')].filter(e=>e.textContent==='+').length"),3);assert.equal(await evaluate(s,"document.querySelector('main strong')?.textContent"),'誤っている');}
      if(q.id.includes('tp200414-') && q.id.includes('a_01-q087')) assert.equal(q.options[0],'1．CRPS〈複合性局所疼痛症候群〉Ⅰ型に分類される。');
      if(q.id.includes('tp210416-') && q.id.includes('a_01-q062')) assert.equal(await evaluate(s,"[...document.querySelectorAll('.option sup')].filter(e=>e.textContent==='+').length"),1);
      if(q.id.includes('tp210416-') && q.id.includes('a_01-q065')) assert.equal(await evaluate(s,"[...document.querySelectorAll('.option sup')].filter(e=>e.textContent==='+').length"),1);
      if(q.id.includes('tp210416-') && q.id.includes('a_01-q087')) assert.ok(q.options[0].includes('CRPS〈複合性局所疼痛症候群〉typeⅠ'));
      if(q.id.includes('tp170425-') && q.id.includes('a_01-q088')) assert.ok(q.options[4].includes('慢性腎臓病〈CKD〉'));
      if(q.id.includes('tp170425-') && q.id.includes('b_01-q061')) assert.ok(q.prompt.includes('2つ選べ') && q.options[4].includes('髄鞘'));
      if(q.id.includes('tp190415-') && q.id.includes('a_01-q062')) assert.deepEqual(await evaluate(s,"[...document.querySelectorAll('.option sup')].map(e=>e.textContent).sort()"),['+','2+']);
      if(q.id.includes('tp190415-') && q.id.includes('a_01-q065')) assert.deepEqual(await evaluate(s,"[...document.querySelectorAll('.option sup')].map(e=>e.textContent).sort()"),['+','+','2+']);
      if(q.id.includes('tp190415-') && q.id.includes('a_01-q086')) assert.ok(q.prompt.includes('個人－社会'));
      if(q.id.includes('tp190415-') && q.id.includes('a_01-q089')) assert.equal(await evaluate(s,"[...document.querySelectorAll('.option sup')].filter(e=>e.textContent==='*').length"),1);
      if(q.id.includes('tp220421-') && q.id.includes('b_01-q077')) assert.ok(q.options[4].includes('肺胞気－動脈血'));
      if(q.id.includes('tp220421-') && q.id.includes('b_01-q085')) assert.ok(q.options[4].includes('WPPISI-Ⅲ〈Wechsler Preschool and Primary Scale of Intelligence-Ⅲ〉'));
      if(q.id.includes('tp250428-') && q.id.includes('a_01-q065')) assert.equal(await evaluate(s,"[...document.querySelectorAll('.option sup')].filter(e=>e.textContent==='+').length"),1);
    }
    if(name.startsWith('verified-font-')) {
      for(const field of ['prompt','options','passage']) assert.equal(q.textReview[field],'source-verified');
      assert.equal(q.images.length,0);assert.equal(q.options.length,5);
      if(q.id==='business-sme-2023-F-q2') assert.equal(await evaluate(s,"document.querySelector('main u')?.textContent"),'最も不適切なものはどれか');
      if(q.id==='business-sme-2023-F-q8') assert.equal(await evaluate(s,"document.querySelectorAll('.question table').length"),1);
      if(q.id==='business-sme-2023-F-q9') {assert.equal(await evaluate(s,"document.querySelectorAll('.question table').length"),2);assert.ok(await evaluate(s,"document.querySelector('.question pre')?.textContent.includes('COUNT(*)')"));}
      if(q.id==='business-sme-2023-F-q24') assert.equal(await evaluate(s,"document.querySelectorAll('.question table').length"),1);
      if(q.id.endsWith('-q087')) {assert.ok(q.prompt.includes('症候'));assert.equal(await evaluate(s,"document.querySelector('main strong')?.textContent"),'誤っている');}
    }
    if(name.startsWith('verified-font-batch-')) {
      if(q.type==='multiple') assert.equal(await evaluate(s,"document.querySelectorAll('main strong').length"),1);
      if(q.id.startsWith('medical-official-tp200414-') && q.id.includes('a_01-q062')) assert.ok(await evaluate(s,"[...document.querySelectorAll('main sup')].some(e=>e.textContent==='2+')"));
      if(q.id.startsWith('medical-official-tp200414-') && q.id.includes('a_01-q067')) assert.ok(await evaluate(s,"[...document.querySelectorAll('.option sup')].some(e=>e.textContent==='+')"));
      if(q.id.startsWith('medical-official-tp200414-') && q.id.includes('b_01-q064')) assert.ok(q.options[0].includes('Ⅰa') && q.options[1].includes('Ⅰb') && q.options[2].includes('Ⅱ') && q.options[3].includes('α') && q.options[4].includes('γ'));
      if(q.id.startsWith('medical-official-tp210416-') && q.id.includes('b_01-q068')) assert.ok(q.options[4].includes('バゾプレッシン'));
      if(q.id.startsWith('medical-official-tp210416-') && q.id.includes('b_01-q072')) assert.equal(q.images.length,0);
    }
    if(name.startsWith('retained-neighbor-')) {
      assert.ok(q.images.length>0);await click(s,'.question-image');await until(s,"document.querySelector('#image-dialog').open && document.querySelector('#image-view').complete && document.querySelector('#image-view').naturalWidth>0");await click(s,'#image-close');
    }
    if(name.startsWith('verified-font-pair-')) {
      if(q.type==='multiple') assert.equal(await evaluate(s,"document.querySelectorAll('main strong').length"),1);
      if(q.id.startsWith('medical-official-tp190415-') && q.id.includes('a_01-q066')) assert.ok(await evaluate(s,"[...document.querySelectorAll('.option sub')].some(e=>e.textContent==='2')"));
      if(q.id.startsWith('medical-official-tp190415-') && q.id.includes('a_01-q077')) assert.ok(q.options[0].includes('÷％肺活量'));
      if(q.id.startsWith('medical-official-tp190415-') && q.id.includes('a_01-q085')) assert.ok(q.options[4].includes('Kleinfelter'));
      if(q.id.startsWith('medical-official-tp190415-') && q.id.includes('a_01-q081')) {assert.equal(await evaluate(s,"document.querySelectorAll('.question table').length"),1);assert.equal(await evaluate(s,"document.querySelectorAll('.question table tbody tr').length"),4);assert.equal(await evaluate(s,"document.querySelectorAll('.question table strong').length"),4);}
    }
    if(name.startsWith('verified-next-')) {
      assert.equal(q.textReview.prompt,'source-verified');assert.equal(q.textReview.options,'source-verified');assert.equal(q.textReview.passage,'source-verified');
      assert.ok(!/原本未照合|判読保留|補助テキスト/.test(q.prompt+q.passage+q.options.join('')));
      assert.ok(q.images.every(i=>i.src.startsWith('assets/transcription/')));assert.ok(q.images.length<=1);
      if(q.id.startsWith('medical-official-')) assert.equal(q.images.length,q.id.endsWith('-q100')?0:1);
      if(q.id==='business-sme-2024-A-q10') assert.equal(q.images.length,1);
      if(q.id==='business-sme-2025-C-q11') assert.equal(await evaluate(s,"document.querySelector('main u')?.textContent"),'最も不適切なものはどれか');
      if(q.id==='business-sme-2024-D-q10') assert.ok(q.prompt.includes('Vender Managed Inventory'));
      if(q.id==='business-sme-2026-G-q20') assert.equal(await evaluate(s,"document.querySelector('main u')?.textContent"),'制度の対象となる者');
      if(q.id==='business-sme-2026-G-q25') {assert.equal(await evaluate(s,"[...document.querySelectorAll('.passage sub')].map(e=>e.textContent).join('')"),'①②');assert.equal(await evaluate(s,"document.querySelectorAll('.passage u').length"),2);}
      if(q.id==='business-sme-2023-D-q10') {assert.equal(q.type,'written');assert.equal(q.options.length,0);assert.equal(q.answer,null);assert.ok(q.prompt.includes('工数の山積山崩'));}
      if(q.images.length) {await click(s,'.question-image');await until(s,"document.querySelector('#image-dialog').open && document.querySelector('#image-view').complete && document.querySelector('#image-view').naturalWidth>0");assert.equal(await evaluate(s,"document.querySelector('#image-view').alt"),q.images[0].alt);await click(s,'#image-close');}
    }
    if(/^ip-201[34]-common-/.test(name)) {
      assert.equal(q.textReview.passage,'source-verified');assert.ok(!/原本未照合|判読保留/.test(q.passage));
      assert.equal(await evaluate(s,"(()=>{const el=document.querySelector('.passage').cloneNode(true);el.querySelector(':scope > .muted')?.remove();return el.textContent.replace(/\\s+/g,'');})()"),displayed(q.passage).replace(/\s+/g,''));
      if(q.id==='2014h26a_ip-q093') {assert.ok(q.passage.includes('条件付個数'));assert.ok(!q.passage.includes('数値以外の値は処理の対象としない'));}
      if(q.id==='2014h26a_ip-q094') assert.ok(q.passage.includes('数値以外の値は処理の対象としない'));
    }
    if(name==='ip-2011-countif') {assert.ok(q.passage.includes('条件付個数') && q.passage.includes('10,000'));assert.ok(!q.passage.includes('数値以外の値は処理の対象としない'));assert.equal(q.images.length,0);}
    if(name==='ip-2012-sum-spec') {assert.ok(q.passage.includes('数値以外の値は処理の対象としない'));assert.equal(q.options[2],'ウ　F2／F$6');assert.equal(q.images.length,0);}
    if(name==='ip-2012-if-spec') {assert.ok(q.passage.includes('北海道') && q.passage.includes('IF（論理式，式1，式2）'));assert.ok(!q.passage.includes('数値以外の値は処理の対象としない'));assert.ok(q.options[2].includes('C$12') && q.options[2].includes('$B13'));assert.equal(q.images.length,0);}
    if(name==='ip-2012-run-length') {assert.equal(q.images.length,1);assert.ok(q.passage.includes('00111111'));assert.ok(q.prompt.includes('111010100') && q.prompt.includes('先頭に“000”'));}
    if(name==='ip-2012-directory') {assert.equal(q.images.length,1);assert.equal(q.options[3],'エ　..¥..¥..¥B¥f');}
    if(name==='ip-2011-flow') {assert.ok(!q.passage.includes('`'));assert.ok(q.passage.includes('w2,b3,w3,b,w3,b'));}
    if(name==='ip-2011-wildcard') {assert.ok(q.prompt.includes('%イ%ン_') && !q.prompt.includes('`'));}
    if(name==='ip-2012-negation') assert.equal(await evaluate(s,"document.querySelector('main u')?.textContent"),'ではないもの');
    if(name==='ip-2012-inappropriate') assert.equal(await evaluate(s,"document.querySelector('main u')?.textContent"),'不適切な点がある');
    assert.ok(await evaluate(s,`document.querySelector('main').textContent.replace(/\\s+/g,'').includes(${JSON.stringify(displayed(q.prompt).replace(/\s+/g,''))})`));
    if(q.textReview?.passage==='source-verified' && q.passage) assert.ok(await evaluate(s,"!!document.querySelector('section.passage') && !document.querySelector('section.passage').closest('details')"));
    if(name==='table') assert.equal(await evaluate(s,"document.querySelectorAll('.passage table').length"),2);
    if(name==='ocr-prose') {assert.equal(q.images.length,0);assert.deepEqual(q.options,['ア　0.8','イ　1.25','ウ　2.5','エ　10']);}
    if(name==='ocr-piecewise') {assert.equal(q.images.length,0);assert.ok(await evaluate(s,"document.querySelector('.passage table').textContent.includes('0≦n＜255')"));}
    if(name==='ocr-graph') {assert.equal(q.images.length,1);assert.ok(q.prompt.includes('平均が60'));assert.deepEqual(q.options,['ア','イ','ウ','エ']);}
    if(name==='ocr-model') {assert.equal(q.images.length,1);assert.equal(await evaluate(s,"document.querySelectorAll('.passage tbody tr').length"),4);}
    if(name.startsWith('bulk-')) {
      assert.equal(q.textReview.prompt,'source-verified');assert.equal(q.textReview.options,'source-verified');
      assert.ok(!q.passage.includes('原本未照合'));
      if(q.images.length) assert.ok(q.images.every(i=>i.src.startsWith('assets/transcription/')));
    }
    if(name==='bulk-2025a-negation') assert.ok(await evaluate(s,"document.querySelector('main').textContent.includes('b̅') && document.querySelector('main').textContent.includes('a̅')"));
    if(name==='bulk-2025h-subscript') assert.ok(await evaluate(s,"document.querySelector('main sub')?.textContent==='A'"));
    if(name==='bulk-ip-joined-tables') assert.equal(await evaluate(s,"document.querySelectorAll('.passage table').length"),2);
    if(name==='bulk-ip-permission-table') assert.equal(await evaluate(s,"document.querySelectorAll('.passage tbody tr').length"),4);
    if(name==='continuation-overline') assert.equal(await evaluate(s,"[...document.querySelectorAll('.option > span span')].filter(e=>getComputedStyle(e).textDecorationLine==='overline').length"),2);
    if(name==='continuation-work-table') assert.equal(await evaluate(s,"document.querySelectorAll('.passage tbody tr').length"),2);
    if(name==='continuation-final-question') assert.ok(!q.passage.includes('メモ用紙') && !q.passage.includes('監督員'));
    if(name==='continuation-ip-random-table') assert.equal(await evaluate(s,"document.querySelectorAll('.passage tbody tr').length"),5);
    if(name.startsWith('ip-next-') || name.startsWith('ip-2016-') || name.startsWith('ip-2017-next-') || name.startsWith('ip-2018-next-') || name.startsWith('ip-2019-next-')) {
      assert.equal(q.textReview.prompt,'source-verified');assert.equal(q.textReview.options,'source-verified');
      assert.ok(!/原本未照合|補助テキスト/.test(q.passage));
      assert.ok(q.images.every(i=>i.src.startsWith('assets/transcription/')));
    }
    if(['ip-2017-next-dfd','ip-2017-next-network','ip-2017-next-curves'].includes(name)) assert.equal(q.images.length,1);
    if(name==='ip-2017-next-dfd') assert.deepEqual(q.options,['ア','イ','ウ','エ']);
    if(name==='ip-2017-next-message') {assert.equal(q.images.length,0);assert.ok(q.passage.includes('48時間以内') && q.options[3].includes('ランサムウェア'));}
    if(name==='ip-2017-next-key') {assert.equal(q.images.length,0);assert.equal(await evaluate(s,"document.querySelectorAll('.option u').length"),10);}
    if(name==='ip-2017-next-average') {assert.equal(q.images.length,0);assert.ok(q.options[3].includes('平均($C2：$E2)'));assert.ok(q.passage.includes('数値以外の値は処理の対象としない'));assert.equal(await evaluate(s,"document.querySelector('.passage table tbody').rows.length"),7);}
    if(name==='ip-2017-next-bits') {assert.equal(q.images.length,0);assert.ok(q.prompt.includes('01011010') || q.passage.includes('01011010'));}
    if(['ip-2018-next-schedule','ip-2018-next-ppm','ip-2018-next-gateway','ip-2018-next-box','ip-2018-next-mail'].includes(name)) assert.equal(q.images.length,1);
    if(name==='ip-2018-next-proxy') assert.ok(q.options[3].includes('相互変換'));
    if(['ip-2019-next-stack','ip-2019-next-flow'].includes(name)) assert.equal(q.images.length,1);
    if(name==='ip-2019-next-inventory') {assert.equal(q.images.length,0);assert.equal(await evaluate(s,"document.querySelectorAll('.passage tbody tr').length"),4);assert.ok(q.passage.includes('安全在庫') && q.passage.includes('網掛け'));}
    if(name==='ip-2019-next-sum-count') {assert.equal(q.images.length,0);assert.ok(q.passage.includes('数値以外の値は処理の対象としない') && q.passage.includes('空白セルでないセルの個数'));assert.equal(await evaluate(s,"document.querySelectorAll('.passage table').length"),3);}
    if(name==='ip-2019-next-parallel') {assert.equal(q.images.length,0);assert.equal(await evaluate(s,"document.querySelectorAll('.passage table').length"),2);assert.ok(q.passage.includes('片道60秒') && q.passage.includes('150秒'));}
    if(name==='ip-2019-next-relations') {assert.equal(q.images.length,0);assert.ok(await evaluate(s,"document.querySelector('.passage pre').textContent.includes('［a］→［b］')"));assert.ok(q.options[1].includes('→［著者］←'));}
    if(name==='ip-2019-next-sales') {assert.equal(q.images.length,0);assert.equal(await evaluate(s,"document.querySelectorAll('.passage table').length"),2);assert.equal(await evaluate(s,"document.querySelectorAll('.passage tbody tr').length"),12);assert.ok(q.passage.includes('Z00005') && q.passage.includes('6/10'));}
    if(name==='ip-2019-next-appendix-excluded') {assert.equal(q.images.length,0);assert.equal(q.passage,'');assert.ok(!q.prompt.includes('表計算ソフト'));}
    if(name==='ip-2018-next-materials') {assert.equal(q.images.length,0);assert.equal(await evaluate(s,"document.querySelectorAll('.passage table').length"),3);assert.equal(await evaluate(s,"document.querySelectorAll('.passage tbody tr').length"),6);}
    if(name==='ip-2018-next-negation') assert.equal(await evaluate(s,"document.querySelectorAll('.question u').length"),1);
    if(name==='ip-2018-next-directory') {assert.equal(q.images.length,0);assert.ok(await evaluate(s,"document.querySelector('.passage pre').textContent.includes('f2.html')"));}
    if(name==='ip-2018-next-logic') {assert.equal(q.images.length,0);assert.ok(q.passage.includes('式の個数は，1以上') && q.passage.includes('論理積') && q.passage.includes('論理和'));assert.equal(await evaluate(s,"document.querySelector('.passage table tbody').rows.length"),2);}
    if(['ip-next-two-sheets','ip-next-common-graph'].includes(name)) assert.equal(q.images.length,2);
    if(name==='ip-next-spring-absolute-reference') {
      assert.equal(q.images.length,0);assert.equal(q.options[2],'ウ　A5＊B$1＋B$2');
      assert.ok(q.passage.includes('－1,850') && q.passage.includes('5,286'));
      assert.equal(await evaluate(s,"document.querySelector('.passage table tbody').rows.length"),17);
    }
    if(name==='ip-next-spring-conditions') {assert.equal(q.images.length,0);assert.ok(q.options[0].includes('[性能=0] and [価格=1] and [デザイン=0]'));}
    if(name==='ip-2016-a-exponent') {assert.equal(q.images.length,0);assert.equal(await evaluate(s,"document.querySelectorAll('.option sup').length"),3);assert.deepEqual(q.options,['ア　8×M','イ　8［上付き：M］','ウ　M［上付き：8］－1','エ　M［上付き：8］']);}
    if(name==='ip-2016-h-router') assert.equal(q.images.length,1);
    if(['ip-2026-next-box','ip-2026-next-tree','ip-2026-next-common-d','ip-2026-next-recovery'].includes(name)) assert.equal(q.images.length,1);
    if(name==='ip-2026-next-common-b') {assert.equal(q.images.length,2);assert.deepEqual(q.options,['ア','イ','ウ','エ']);assert.ok(q.passage.includes('固定費（万円／月）'));}
    if(['ip-2026-next-sort','ip-2026-next-prime'].includes(name)) {assert.equal(q.images.length,0);assert.ok(q.passage.includes('擬似言語の記述形式'));assert.ok(await evaluate(s,"document.querySelector('pre')?.textContent.length>100"));}
    if(name==='ip-2026-next-sheet') {assert.equal(q.images.length,0);assert.ok(q.passage.includes('数値以外の値は処理の対象としない'));assert.ok(q.options.every(o=>o.includes('合計(B2:B4)')));}
    if(name==='ip-2026-next-staff') {assert.equal(q.images.length,0);assert.ok(q.passage.includes('1日の平均電話受付件数'));assert.ok(q.passage.includes('B5～G10'));assert.ok(!q.passage.includes('B5：G10'));assert.equal(await evaluate(s,"document.querySelector('table tbody').rows.length"),13);}
    if(name==='ip-2026-next-gray') {assert.equal(q.images.length,0);assert.ok(q.prompt.includes('P1＋P2＋P3') && q.prompt.includes('P2＋P3＋P4'));assert.equal(await evaluate(s,"document.querySelectorAll('.question u').length"),1);}
    if(name==='ip-2026-next-common-c') {assert.equal(q.images.length,0);assert.ok(q.passage.includes('申請前の入力情報は，履歴としては保存しない'));assert.equal(await evaluate(s,"document.querySelector('table tbody').rows.length"),9);}
    if(name==='ip-2016-a-image-options') {assert.equal(q.images.length,1);assert.deepEqual(q.options,['ア','イ','ウ','エ']);}
    if(name==='ip-2016-h-joined') {assert.equal(q.images.length,0);assert.equal(await evaluate(s,"document.querySelectorAll('.passage table').length"),3);}
    if(name==='ip-2016-h-schema') assert.equal(await evaluate(s,"document.querySelectorAll('.passage table th').length"),7);
    if(name==='ip-2016-a-spreadsheet') {assert.equal(q.images.length,0);assert.equal(await evaluate(s,"document.querySelector('.passage table tbody').rows.length"),8);assert.ok(q.prompt.includes("IF(B2≧50，’合格’，IF(C2≧50，’合格’，’不合格’))"));assert.ok(q.passage.includes('セルC4には式$A$1＋$A5＋B$5'));
    }
    if(['ocr-graph','ocr-model'].includes(name)) {
      await click(s,'.question-image');await until(s,"document.querySelector('#image-dialog').open && document.querySelector('#image-view').complete && document.querySelector('#image-view').naturalWidth>0");
      assert.equal(await evaluate(s,"document.querySelector('#image-view').alt"),q.images[0].alt);
      await click(s,'#image-close');assert.equal(await evaluate(s,"document.querySelector('#image-dialog').open"),false);
    }
    if(name==='code') assert.ok(await evaluate(s,"document.querySelector('.passage pre code').textContent.includes('      if (［b］)\\n          divideFlag ← false')"));
    if(name==='unreviewed') {
      if(q.images.some(i=>i.src.startsWith('assets/transcription/'))) {
        assert.ok(await evaluate(s,"!!document.querySelector('.passage') && !document.querySelector('.passage').closest('details')"));
        assert.ok(await evaluate(s,"document.querySelector('main').textContent.includes('原本未照合')"));
        assert.ok(await evaluate(s,"!!(document.querySelector('.passage').compareDocumentPosition(document.querySelector('.question-image')) & Node.DOCUMENT_POSITION_FOLLOWING)"));
      }else assert.ok(await evaluate(s,"[...document.querySelectorAll('details summary')].some(e=>e.textContent.includes('原本未照合'))"));
    }
    const chosen=q.answerPending?0:q.acceptedAnswers?.at(-1) ?? q.answer;
    const statsBefore=await evaluate(s,"JSON.parse(localStorage.getItem('gstudy.web.v1')).stats");
    if(['single','multiple'].includes(q.type)) {assert.deepEqual(await evaluate(s,"[...document.querySelectorAll('.option > span')].map(e=>e.textContent).sort()"),q.options.map(displayed).sort());for(const answer of [chosen].flat()) await click(s,`input[name=answer][value="${answer}"]`);}
    else await field(s,'#written-answer','原本との比較のためのテスト回答','input');
    await click(s,'[data-action=answer]');await until(s,"!!document.querySelector('.feedback')");
    if(['single','multiple'].includes(q.type) && !q.answerPending) for(const answer of [chosen].flat()) assert.ok(await evaluate(s,`document.querySelector('.feedback').textContent.includes(${JSON.stringify(displayed(q.options[answer]))})`));
    if(q.acceptedAnswers) {assert.ok(await evaluate(s,"document.querySelector('.feedback .correct')?.textContent==='正解！'"));assert.ok(await evaluate(s,"document.querySelector('.feedback').textContent.includes('または')"));}
    if(q.answerPending) {assert.ok(await evaluate(s,"document.querySelector('.feedback').textContent.includes('採点保留') && !document.querySelector('.feedback .incorrect') && !document.querySelector('.feedback .correct')"));assert.deepEqual(await evaluate(s,"JSON.parse(localStorage.getItem('gstudy.web.v1')).stats"),statsBefore);}
    if(name.startsWith('official-solution-') || q.id==='business-sme-2023-D-q10') {
      assert.equal(q.type,'written');assert.equal(q.answer,null);assert.equal(q.options.length,0);assert.equal(q.solutionImages.length,0);
      assert.equal(q.textReview.modelAnswer,'source-verified');assert.equal(q.textReview.evaluationGuide,'source-verified');assert.equal(q.textReview.explanation,'source-verified');
      assert.equal(q.evaluationGuide,'');assert.equal(q.explanation,'');
      const number=Number(q.id.split('-q')[1]);assert.ok(![14,31].includes(number));
      assert.ok(await evaluate(s,`document.querySelector('.feedback').textContent.replace(/\\s+/g,'').includes(${JSON.stringify(displayed(q.modelAnswer).replace(/\s+/g,''))})`));
      assert.equal(await evaluate(s,"document.querySelector('.feedback table tbody').rows.length"),[15,28,29,38].includes(number)?2:1);
      assert.ok(await evaluate(s,`[...document.querySelectorAll('.feedback table tbody tr')].every(r=>r.cells[0].textContent==='第${number}問')`));
      assert.equal(await evaluate(s,"!!document.querySelector('.feedback .correct') || !!document.querySelector('.feedback .incorrect')"),false);
    }
    if(name==='scoped-answer-table') {
      assert.equal(q.solutionImages.length,0);
      assert.ok(await evaluate(s,"document.querySelector('.feedback table')?.textContent.includes('設問1') && document.querySelector('.feedback table')?.textContent.includes('設問2')"));
      assert.ok(!q.modelAnswer.includes('第7問') && !q.modelAnswer.includes('第9問'));
    }
    if(name==='scoped-intent') {assert.equal(q.solutionImages.length,0);assert.ok(q.evaluationGuide.includes('第2 問') && !q.evaluationGuide.includes('第1 問') && !q.evaluationGuide.includes('第3 問'));assert.ok(await evaluate(s,"document.querySelector('.feedback').textContent.includes('先代経営者からの事業承継')"));}
    if(name==='scoped-case') {assert.ok(q.images.length && q.images.every(i=>i.src.startsWith('assets/transcription/')));assert.ok(q.prompt.includes('100 字以内') && !q.prompt.includes('第2 問'));}
    if(name==='ocr-answer-table') {assert.equal(q.solutionImages.length,0);assert.ok(await evaluate(s,"document.querySelector('.feedback table u')?.textContent==='日' && document.querySelector('.feedback table').textContent.includes('入荷済数')"));assert.ok(!q.modelAnswer.includes('OVER'));}
    if(name==='ocr-answer-reason') {assert.equal(q.solutionImages.length,0);assert.ok(await evaluate(s,"document.querySelector('.feedback table').textContent.includes('サービス回復時間にはシステム開発課以外')"));assert.ok(!q.modelAnswer.includes('サービスデスク要員'));}
    if(name==='multi-page') for(const expected of ['公式解答例・解答の要点','出題趣旨・自己評価資料','採点講評',q.modelAnswer.split('\n')[1]]) assert.ok(await evaluate(s,`document.querySelector('.feedback').textContent.includes(${JSON.stringify(expected)})`));
    if(!['single','multiple'].includes(q.type)) await click(s,'[data-action=self-done]');
    await until(s,"!!document.querySelector('[data-action=next]') && document.querySelector('#sync-panel')?.dataset.kind==='synced'");
    const state=await evaluate(s,"JSON.parse(localStorage.getItem('gstudy.web.v1'))");
    if(name.startsWith('official-solution-') || q.id==='business-sme-2023-D-q10') {
      assert.equal(state.stats[key].correct,statsBefore[key]?.correct || 0);
      assert.equal(state.stats[key].gradedAttempts,statsBefore[key]?.gradedAttempts ?? statsBefore[key]?.attempts ?? 0);
      assert.equal(state.stats[key].self.done,(statsBefore[key]?.self?.done || 0)+1);
    }
    await evaluate(s,'window.transcriptionBeforeReload=true');
    await send('Page.reload',{},s);await until(s,"!window.transcriptionBeforeReload && !!document.querySelector('.feedback') && !!document.querySelector('[data-action=next]') && document.querySelector('#sync-panel')?.dataset.kind==='synced'");
    await evaluate(s,"document.querySelectorAll('.question-image').forEach(i=>i.loading='eager')");
    await until(s,"[...document.querySelectorAll('.question-image')].every(i=>i.complete&&i.naturalWidth>0)");
    assert.deepEqual((await evaluate(s,"JSON.parse(localStorage.getItem('gstudy.web.v1'))")).session,state.session);
    for(const width of [320,390,1100]) {
      await send('Emulation.setDeviceMetricsOverride',{width,height:1000,deviceScaleFactor:1,mobile:width<500},s);
      assert.equal(await evaluate(s,'document.documentElement.scrollWidth<=innerWidth'),true,name+' '+width);
      if(width===320 && (name.startsWith('official-solution-') || q.id==='business-sme-2023-D-q10')) assert.ok(await evaluate(s,"[...document.querySelectorAll('.feedback .table-scroll')].every(e=>{if(e.tabIndex!==0) return false;if(e.scrollWidth<=e.clientWidth) return true;e.scrollLeft=30;const moved=e.scrollLeft>0;e.scrollLeft=0;return moved;})"),name+' official table narrow scrolling');
      if(width===320 && name.startsWith('verified-font-')) assert.ok(await evaluate(s,"[...document.querySelectorAll('.question .table-scroll, .question pre')].every(e=>{if(e.tabIndex!==0) return false;if(e.scrollWidth<=e.clientWidth) return true;e.scrollLeft=30;const moved=e.scrollLeft>0;e.scrollLeft=0;return moved;})"),name+' tables and SQL narrow scrolling');
      if(width===320 && /^ip-201[34]-common-/.test(name)) assert.ok(await evaluate(s,"[...document.querySelectorAll('.passage .table-scroll')].every(e=>{if(e.tabIndex!==0) return false;if(e.scrollWidth<=e.clientWidth) return true;e.scrollLeft=30;const moved=e.scrollLeft>0;e.scrollLeft=0;return moved;})"),name+' common tables scroll');
      if(name==='table' && width===320) assert.ok(await evaluate(s,"[...document.querySelectorAll('.passage .table-scroll')].every(e=>e.scrollWidth>e.clientWidth && e.tabIndex===0)"));
      if(name==='scoped-answer-table' && width===320) assert.ok(await evaluate(s,"document.querySelector('.feedback .table-scroll').scrollWidth>document.querySelector('.feedback .table-scroll').clientWidth && document.querySelector('.feedback .table-scroll').tabIndex===0"));
      if(name==='code') assert.equal(await evaluate(s,"document.querySelector('.passage pre').tabIndex"),0);
      if(width===320 && ['table','code','scoped-answer-table','ocr-answer-table'].includes(name)) {
        const selector=name==='table'?'.passage .table-scroll':['scoped-answer-table','ocr-answer-table'].includes(name)?'.feedback .table-scroll':'.passage pre';
        await evaluate(s,`document.querySelector(${JSON.stringify(selector)}).focus()`);
        await send('Input.dispatchKeyEvent',{type:'keyDown',key:'ArrowRight',code:'ArrowRight',windowsVirtualKeyCode:39},s);
        await send('Input.dispatchKeyEvent',{type:'keyUp',key:'ArrowRight',code:'ArrowRight',windowsVirtualKeyCode:39},s);
        await until(s,`document.querySelector(${JSON.stringify(selector)}).scrollLeft>0`);
        await evaluate(s,`document.querySelector(${JSON.stringify(selector)}).scrollLeft=0`);
      }
      const size=await send('Page.getLayoutMetrics',{},s);
      const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:{x:0,y:0,width,height:Math.min(15000,size.cssContentSize.height),scale:1}},s);
      writeFileSync(join(screenshots,`${name}-${width}.png`),Buffer.from(shot.data,'base64'));
      if(width===320) for(const selector of ['.passage','.feedback']) {
        const rect=await evaluate(s,`(()=>{const e=document.querySelector(${JSON.stringify(selector)});if(!e) return null;const r=e.getBoundingClientRect();return {x:0,y:r.top+scrollY,width:innerWidth,height:Math.min(1300,r.height),scale:1};})()`);
        if(rect) {const part=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:true,clip:rect},s);writeFileSync(join(screenshots,`${name}-${selector.slice(1)}.png`),Buffer.from(part.data,'base64'));}
      }
    }
    await click(s,'[data-action=pause-dialog]');await click(s,'#finish');await until(s,"location.hash==='#results'");
    console.log('PASS: search/question/graded solution/resume/narrow widths '+name+' '+key);
  }
  const edited=selected.get('nw::2009h21a_nw_am2-q001');
  await field(s,'#exam-select','nw');await evaluate(s,"location.hash='#manage'");await until(s,"!!document.querySelector('#manage-search')");
  await field(s,'#manage-search',edited.id,'input');await until(s,"!!document.querySelector('[data-edit-question]')");await click(s,'[data-edit-question]');await until(s,"!!document.querySelector('#question-form')");
  await field(s,'textarea[name=prompt]',edited.prompt+'（編集テスト）','input');
  await evaluate(s,"document.querySelector('#question-form').requestSubmit()");await until(s,"location.hash==='#manage'");
  const custom=await evaluate(s,`JSON.parse(localStorage.getItem('gstudy.web.v1')).custom.find(q=>q.id===${JSON.stringify(edited.id)} && q.examId==='nw')`);
  assert.ok(custom);assert.equal(custom.textReview?.prompt,undefined);assert.equal(custom.textReview?.options,'source-verified');assert.equal(custom.textReview?.answer,undefined);assert.equal(custom.answerKind,undefined);
  console.log('PASS: editing only the prompt clears dependent official answer review; unchanged option text remains source-verified');
  for(const key of ['nurse::expansion-tp190415-05b_01-q005','nurse::expansion-tp190415-05b_01-q033']) {
    const original=selected.get(key);await field(s,'#exam-select','nurse');await evaluate(s,"location.hash='#manage'");await until(s,"!!document.querySelector('#manage-search')");
    await field(s,'#manage-search',original.id,'input');await until(s,"!!document.querySelector('[data-edit-question]')");await click(s,'[data-edit-question]');await until(s,"!!document.querySelector('#question-form')");
    if(original.answerPending) assert.equal(await evaluate(s,"document.querySelector('[name=correct-answer]').value"),'');
    await field(s,'textarea[name=prompt]',original.prompt+'（編集テスト）','input');await evaluate(s,"document.querySelector('#question-form').requestSubmit()");await until(s,"location.hash==='#manage'");
    const saved=await evaluate(s,`JSON.parse(localStorage.getItem('gstudy.web.v1')).custom.find(q=>q.examId==='nurse' && q.id===${JSON.stringify(original.id)})`);
    assert.equal(saved.answerPending,original.answerPending);assert.deepEqual(saved.acceptedAnswers,original.acceptedAnswers);assert.deepEqual(saved.answer,original.answer);
  }
  console.log('PASS: editing preserves blank-answer hold and unchanged accepted answer alternatives');
  assert.deepEqual(errors,[]);
  writeFileSync(join(directory,'browser-verification.json'),JSON.stringify({passed:true,samples:samples.map(s=>s[0]),widths:[320,390,1100],screenshots,at:new Date().toISOString()},null,2));
  const reportFile=join(directory,'transcription-report.json');
  if(existsSync(reportFile)) {const report=read(reportFile);report.checks.browser='pass';writeFileSync(reportFile,JSON.stringify(report,null,2));}
} finally {
  writeFileSync(join(screenshots,'sync-request-trace.json'),JSON.stringify(stateTrace,null,2));
  if(context) await send('Target.disposeBrowserContext',{browserContextId:context});ws.close();
  await new Promise(ok=>preview.server.close(ok));preview.fixture.restore();
}
