// Registration destinations only. No questions, official scoring or practical exams are bundled.
// One row per level/type; yearly editions belong to question.year, not new exam IDs.
const groups=[
['IT・AI','https://www.ipa.go.jp/shiken/kubun/index.html',`
ip|ITパスポート
sg|情報セキュリティマネジメント
fe|基本情報技術者
ap|応用情報技術者
st|ITストラテジスト
sa|システムアーキテクト
pm|プロジェクトマネージャ
nw|ネットワークスペシャリスト
db|データベーススペシャリスト
es|エンベデッドシステムスペシャリスト
sm|ITサービスマネージャ
au|システム監査技術者
sc|情報処理安全確保支援士`],
['IT・AI','https://www.jdla.org/certificate/',`
gken|G検定
eken|E資格
jdla-generative|Generative AI Test`],
['IT・AI','https://pythonic-exam.com/exam',`
python-basic|Python 3 エンジニア認定基礎試験
python-practical|Python 3 エンジニア認定実践試験
python-data|Python 3 エンジニア認定データ分析試験
python-data-practical|Python 3 エンジニア認定データ分析実践試験`],
['IT・AI','https://www.lpi.org/our-certifications/summary-of-lpi-certifications/',`
linux-essentials|Linux Essentials
lpic1|LPIC-1
lpic2|LPIC-2
lpic3-300|LPIC-3 Mixed Environments
lpic3-303|LPIC-3 Security
lpic3-305|LPIC-3 Virtualization and Containerization
lpic3-306|LPIC-3 High Availability and Storage Clusters`],
['IT・AI','https://aws.amazon.com/jp/certification/',`
aws-clf|AWS Certified Cloud Practitioner
aws-aif|AWS Certified AI Practitioner
aws-saa|AWS Certified Solutions Architect - Associate
aws-dva|AWS Certified Developer - Associate
aws-sap|AWS Certified Solutions Architect - Professional
aws-dop|AWS Certified DevOps Engineer - Professional`],
['IT・AI','https://mos.odyssey-com.co.jp/outline/',`
mos-word|MOS Word
mos-word-expert|MOS Word Expert
mos-excel|MOS Excel
mos-excel-expert|MOS Excel Expert
mos-powerpoint|MOS PowerPoint
mos-access|MOS Access
mos-outlook|MOS Outlook`],
['IT・AI','https://www.kentei.ne.jp/',`
nissho-pc-doc1|日商PC検定 文書作成1級
nissho-pc-doc2|日商PC検定 文書作成2級
nissho-pc-doc3|日商PC検定 文書作成3級
nissho-pc-data1|日商PC検定 データ活用1級
nissho-pc-data2|日商PC検定 データ活用2級
nissho-pc-data3|日商PC検定 データ活用3級
nissho-pc-slide1|日商PC検定 プレゼン資料作成1級
nissho-pc-slide2|日商PC検定 プレゼン資料作成2級
nissho-pc-slide3|日商PC検定 プレゼン資料作成3級
nissho-program-basic|日商プログラミング検定 BASIC
nissho-program-standard|日商プログラミング検定 STANDARD
nissho-program-expert|日商プログラミング検定 EXPERT`],
['法律・行政','https://www.gyosei-shiken.or.jp/',`gyosei|行政書士試験`],
['法律・行政','https://www.sharosi-siken.or.jp/',`sharosi|社会保険労務士試験`],
['法律・行政','https://www.moj.go.jp/qualification_test.html',`
shiho|司法試験
shiho-yobi|司法試験予備試験
shihoshoshi|司法書士試験
land-surveyor|土地家屋調査士試験`],
['法律・行政','https://kentei.tokyo-cci.or.jp/houmu/',`
business-law1|ビジネス実務法務検定1級
business-law2|ビジネス実務法務検定2級
business-law3|ビジネス実務法務検定3級`],
['会計・金融','https://www.kentei.ne.jp/bookkeeping',`
boki1|日商簿記1級
boki2|日商簿記2級
boki3|日商簿記3級
boki-basic|日商簿記初級
cost-basic|日商原価計算初級`],
['会計・金融','https://www.jafp.or.jp/exam/',`
fp1|FP技能検定1級
fp2|FP技能検定2級
fp3|FP技能検定3級`],
['会計・金融','https://www.nta.go.jp/taxes/zeirishi/zeirishishiken/zeirishi.htm',`zeirishi|税理士試験`],
['会計・金融','https://www.fsa.go.jp/cpaaob/kouninkaikeishi-shiken/',`cpa|公認会計士試験`],
['会計・金融','https://www.jsda.or.jp/gaimuin/',`
securities1|一種外務員資格試験
securities2|二種外務員資格試験`],
['会計・金融','https://www.kentei.ne.jp/abacus',`
abacus1|珠算能力検定1級
abacus2|珠算能力検定2級
abacus3|珠算能力検定3級`],
['経営・事務・販売','https://www.kentei.ne.jp/retailsales',`
retail1|リテールマーケティング（販売士）検定1級
retail2|リテールマーケティング（販売士）検定2級
retail3|リテールマーケティング（販売士）検定3級`],
['経営・事務・販売','https://kentei.tokyo-cci.or.jp/management/',`business-manager|ビジネスマネジャー検定`],
['経営・事務・販売','https://jitsumu-ginou-kentei.jp/',`
secretary1|秘書検定1級
secretary-pre1|秘書検定準1級
secretary2|秘書検定2級
secretary3|秘書検定3級
business-doc1|ビジネス文書検定1級
business-doc2|ビジネス文書検定2級
business-doc3|ビジネス文書検定3級
business-manner1|ビジネス実務マナー検定1級
business-manner2|ビジネス実務マナー検定2級
business-manner3|ビジネス実務マナー検定3級
service1|サービス接遇検定1級
service-pre1|サービス接遇検定準1級
service2|サービス接遇検定2級
service3|サービス接遇検定3級`],
['英語','https://www.eiken.or.jp/eiken/exam/criteria/index.html',`
eiken1|英検1級
eiken-pre1|英検準1級
eiken2|英検2級
eiken-pre2-plus|英検準2級プラス
eiken-pre2|英検準2級
eiken3|英検3級
eiken4|英検4級
eiken5|英検5級`],
['英語','https://www.iibc-global.org/toeic.html',`
toeic-lr|TOEIC Listening & Reading
toeic-sw|TOEIC Speaking & Writing
toeic-bridge-lr|TOEIC Bridge Listening & Reading
toeic-bridge-sw|TOEIC Bridge Speaking & Writing`],
['外国語','https://www.chuken.gr.jp/',`
chuken1|中国語検定1級
chuken-pre1|中国語検定準1級
chuken2|中国語検定2級
chuken3|中国語検定3級
chuken4|中国語検定4級
chuken-pre4|中国語検定準4級`],
['外国語','https://hangul.or.jp/',`
hangul1|ハングル能力検定1級
hangul2|ハングル能力検定2級
hangul-pre2|ハングル能力検定準2級
hangul3|ハングル能力検定3級
hangul4|ハングル能力検定4級
hangul5|ハングル能力検定5級`],
['外国語','https://apefdapf.org/',`
french1|実用フランス語技能検定1級
french-pre1|実用フランス語技能検定準1級
french2|実用フランス語技能検定2級
french-pre2|実用フランス語技能検定準2級
french3|実用フランス語技能検定3級
french4|実用フランス語技能検定4級
french5|実用フランス語技能検定5級`],
['外国語','https://www.dokken.or.jp/',`
german1|ドイツ語技能検定1級
german-pre1|ドイツ語技能検定準1級
german2|ドイツ語技能検定2級
german3|ドイツ語技能検定3級
german4|ドイツ語技能検定4級
german5|ドイツ語技能検定5級`],
['日本語・国語','https://www.jlpt.jp/about/levelsummary.html',`
jlpt-n1|日本語能力試験N1
jlpt-n2|日本語能力試験N2
jlpt-n3|日本語能力試験N3
jlpt-n4|日本語能力試験N4
jlpt-n5|日本語能力試験N5`],
['日本語・国語','https://www.kanken.or.jp/kanken/',`
kanken1|漢検1級
kanken-pre1|漢検準1級
kanken2|漢検2級
kanken-pre2|漢検準2級
kanken3|漢検3級
kanken4|漢検4級
kanken5|漢検5級
kanken6|漢検6級
kanken7|漢検7級
kanken8|漢検8級
kanken9|漢検9級
kanken10|漢検10級`],
['数学・統計','https://www.su-gaku.net/suken/',`
suken1|数学検定1級
suken-pre1|数学検定準1級
suken2|数学検定2級
suken-pre2|数学検定準2級
suken3|数学検定3級
suken4|数学検定4級
suken5|数学検定5級
suken6|算数検定6級
suken7|算数検定7級
suken8|算数検定8級
suken9|算数検定9級
suken10|算数検定10級
suken11|算数検定11級`],
['数学・統計','https://www.toukei-kentei.jp/',`
statistics1|統計検定1級
statistics-pre1|統計検定準1級
statistics2|統計検定2級
statistics3|統計検定3級
statistics4|統計検定4級
statistics-survey|統計検定 統計調査士
statistics-specialist|統計検定 専門統計調査士
statistics-ds-basic|統計検定 データサイエンス基礎
statistics-ds-advanced|統計検定 データサイエンス発展
statistics-ds-expert|統計検定 データサイエンスエキスパート`],
['歴史・地理','https://www.rekiken.gr.jp/',`
rekiken-japan1|歴史能力検定 日本史1級
rekiken-japan2|歴史能力検定 日本史2級
rekiken-japan3|歴史能力検定 日本史3級
rekiken-world1|歴史能力検定 世界史1級
rekiken-world2|歴史能力検定 世界史2級
rekiken-world3|歴史能力検定 世界史3級
rekiken-pre3|歴史能力検定 準3級
rekiken4|歴史能力検定4級
rekiken5|歴史能力検定5級`],
['歴史・地理','https://www.jmc.or.jp/keihatsu-kyouiku/chizuken/about-kentei/',`
map-geography-basic|地図地理検定 基礎
map-geography-specialist|地図地理検定 専門`],
['電気・通信','https://www.shiken.or.jp/',`
electrician1|第一種電気工事士
electrician2|第二種電気工事士
denken1|第一種電気主任技術者
denken2|第二種電気主任技術者
denken3|第三種電気主任技術者`],
['電気・通信','https://www.dekyo.or.jp/shiken/',`
telecom-transmission|電気通信主任技術者 伝送交換主任技術者
telecom-line|電気通信主任技術者 線路主任技術者
telecom-installer-general|工事担任者 総合通信
telecom-installer-analog1|工事担任者 第一級アナログ通信
telecom-installer-analog2|工事担任者 第二級アナログ通信
telecom-installer-digital1|工事担任者 第一級デジタル通信
telecom-installer-digital2|工事担任者 第二級デジタル通信`],
['電気・通信','https://www.nichimu.or.jp/',`
radio-land1|第一級陸上無線技術士
radio-land2|第二級陸上無線技術士
radio-land-special1|第一級陸上特殊無線技士
radio-land-special2|第二級陸上特殊無線技士
radio-land-special3|第三級陸上特殊無線技士
radio-amateur1|第一級アマチュア無線技士
radio-amateur2|第二級アマチュア無線技士
radio-amateur3|第三級アマチュア無線技士
radio-amateur4|第四級アマチュア無線技士
radio-general1|第一級総合無線通信士
radio-general2|第二級総合無線通信士
radio-general3|第三級総合無線通信士
radio-aeronautical|航空無線通信士
radio-maritime4|第四級海上無線通信士`],
['建築・土木','https://www.jaeic.or.jp/',`
architect1|一級建築士
architect2|二級建築士
architect-wood|木造建築士
building-equipment|建築設備士
interior-planner|インテリアプランナー`],
['建築・土木','https://www.jctc.jp/',`
civil-management1|1級土木施工管理技士
civil-management2|2級土木施工管理技士
pipe-management1|1級管工事施工管理技士
pipe-management2|2級管工事施工管理技士
landscape-management1|1級造園施工管理技士
landscape-management2|2級造園施工管理技士
telecom-management1|1級電気通信工事施工管理技士
telecom-management2|2級電気通信工事施工管理技士`],
['不動産','https://www.retio.or.jp/exam/',`takken|宅地建物取引士`],
['不動産','https://www.mankan.org/',`mankan|マンション管理士`],
['不動産','https://www.kanrikyo.or.jp/',`management-chief|管理業務主任者`],
['不動産','https://www.chintaikanrishi.jp/',`rental-manager|賃貸不動産経営管理士`],
['安全・消防・設備','https://www.shoubo-shiken.or.jp/kikenbutsu/',`
hazmat-a|危険物取扱者 甲種
hazmat-b1|危険物取扱者 乙種第1類
hazmat-b2|危険物取扱者 乙種第2類
hazmat-b3|危険物取扱者 乙種第3類
hazmat-b4|危険物取扱者 乙種第4類
hazmat-b5|危険物取扱者 乙種第5類
hazmat-b6|危険物取扱者 乙種第6類
hazmat-c|危険物取扱者 丙種`],
['安全・消防・設備','https://www.shoubo-shiken.or.jp/shoubou/',`
fire-a-special|消防設備士 甲種特類
fire-a1|消防設備士 甲種第1類
fire-a2|消防設備士 甲種第2類
fire-a3|消防設備士 甲種第3類
fire-a4|消防設備士 甲種第4類
fire-a5|消防設備士 甲種第5類
fire-b1|消防設備士 乙種第1類
fire-b2|消防設備士 乙種第2類
fire-b3|消防設備士 乙種第3類
fire-b4|消防設備士 乙種第4類
fire-b5|消防設備士 乙種第5類
fire-b6|消防設備士 乙種第6類
fire-b7|消防設備士 乙種第7類`],
['安全・消防・設備','https://www.exam.or.jp/',`
health1|第一種衛生管理者
health2|第二種衛生管理者
boiler-special|特級ボイラー技士
boiler1|一級ボイラー技士
boiler2|二級ボイラー技士
boiler-maintenance|ボイラー整備士
crane-derrick|クレーン・デリック運転士（限定なし）
mobile-crane|移動式クレーン運転士
lifting-derrick|揚貨装置運転士
diver|潜水士
work-environment1|第一種作業環境測定士
work-environment2|第二種作業環境測定士
health-consultant|労働衛生コンサルタント
safety-consultant|労働安全コンサルタント`],
['医療・健康','https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html',`
doctor|医師国家試験
dentist|歯科医師国家試験
pharmacist|薬剤師国家試験
nurse|看護師国家試験
public-health-nurse|保健師国家試験
midwife|助産師国家試験
clinical-lab|臨床検査技師国家試験
radiological-tech|診療放射線技師国家試験
physical-therapist|理学療法士国家試験
occupational-therapist|作業療法士国家試験
orthoptist|視能訓練士国家試験
clinical-engineer|臨床工学技士国家試験
speech-therapist|言語聴覚士国家試験
dental-hygienist|歯科衛生士国家試験
dental-technician|歯科技工士国家試験
emergency-tech|救急救命士国家試験
nutritionist|管理栄養士国家試験
acupuncturist|はり師国家試験
moxibustion|きゅう師国家試験
massage-therapist|あん摩マッサージ指圧師国家試験
judo-therapist|柔道整復師国家試験
psychologist|公認心理師試験
drug-seller|登録販売者試験`],
['福祉・介護・保育','https://www.sssc.or.jp/',`
social-worker|社会福祉士国家試験
care-worker|介護福祉士国家試験
mental-social-worker|精神保健福祉士国家試験`],
['福祉・介護・保育','https://www.hoyokyo.or.jp/exam/',`childcare|保育士試験`],
['福祉・介護・保育','https://kentei.tokyo-cci.or.jp/fukushi/',`
welfare-housing1|福祉住環境コーディネーター検定1級
welfare-housing2|福祉住環境コーディネーター検定2級
welfare-housing3|福祉住環境コーディネーター検定3級`],
['農業・食品','https://nou-ken.jp/application/individual/',`
agri1|日本農業検定1級
agri2|日本農業検定2級
agri3|日本農業検定3級`],
['農業・食品','https://flanet.jp/',`
food-advisor2|食生活アドバイザー2級
food-advisor3|食生活アドバイザー3級`],
['農業・食品','https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html',`
cook|調理師試験
confectionery-hygiene|製菓衛生師試験`],
['観光・運輸','https://www.jata-net.or.jp/',`travel-general|総合旅行業務取扱管理者`],
['観光・運輸','https://www.anta.or.jp/',`travel-domestic|国内旅行業務取扱管理者`],
['観光・運輸','https://www.jnto.go.jp/projects/visitor-support/interpreter-guide-exams/',`tour-guide|全国通訳案内士試験`],
['観光・運輸','https://www.unkan.or.jp/',`
transport-cargo|運行管理者（貨物）
transport-passenger|運行管理者（旅客）`],
['デザイン・生活','https://www.aft.or.jp/exam-orders',`
color1|色彩検定1級
color2|色彩検定2級
color3|色彩検定3級
color-uc|色彩検定UC級`],
['デザイン・生活','https://kentei.tokyo-cci.or.jp/color/',`
color-coordinator-standard|カラーコーディネーター検定 スタンダードクラス
color-coordinator-advanced|カラーコーディネーター検定 アドバンスクラス`],
['デザイン・生活','https://www.mhlw.go.jp/kouseiroudoushou/shikaku_shiken/index.html',`
barber|理容師国家試験
beautician|美容師国家試験`],
['環境・自然科学','https://kentei.tokyo-cci.or.jp/eco/',`eco|環境社会検定（eco検定）`],
['環境・自然科学','https://www.jmbsc.or.jp/jp/examination/examination-1.html',`weather|気象予報士試験`],
['公務員','https://www.jinji.go.jp/saiyo/siken.html',`
civil-general-grad|国家公務員総合職（院卒者試験）
civil-general-univ|国家公務員総合職（大卒程度試験）
civil-regular-univ|国家公務員一般職（大卒程度試験）
civil-regular-high|国家公務員一般職（高卒者試験）
tax-specialist|国税専門官採用試験
finance-specialist|財務専門官採用試験
labor-inspector|労働基準監督官採用試験`]
];

export const EXAM_CATALOG=groups.flatMap(([field,source,rows])=>rows.trim().split('\n').map(row=>{
  const [id,name]=row.split('|');return {id,name,field,source};
}));
const details=new Map(EXAM_CATALOG.map(e=>[e.id,e]));
export const examField=exam=>exam.id.startsWith('original-')?'自作一般教材':details.get(exam.id)?.field || exam.field || '未分類';
export const examSource=exam=>details.get(exam.id)?.source || '';
export function groupExams(exams) {
  const grouped=new Map();
  for(const exam of exams) {const field=examField(exam);if(!grouped.has(field)) grouped.set(field,[]);grouped.get(field).push(exam);}
  return grouped;
}
