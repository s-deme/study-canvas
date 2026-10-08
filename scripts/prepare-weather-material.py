"""Import JMBSC's released papers into the personal, local-only collection."""
import importlib.util, json, re, sys, zipfile
from urllib.parse import urljoin, quote
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('archive', ROOT/'scripts/prepare-github-material.py')
archive = importlib.util.module_from_spec(spec); spec.loader.exec_module(archive)
spec = importlib.util.spec_from_file_location('fetcher', ROOT/'scripts/fetch-github-material.py')
fetcher = importlib.util.module_from_spec(spec); spec.loader.exec_module(fetcher)
SRC, OUT, fitz = archive.SRC, archive.OUT, archive.fitz
SUBJECTS = ['予報業務に関する一般知識', '予報業務に関する専門知識']

def labels(text):
    return archive.norm(''.join('問' if c == '໲' else chr(ord(c)+29) if '\x13' <= c <= '\x1c' else str(ord(c)-0x1d84) if 'ᶅ' <= c <= 'ᶉ' else str(ord(c)-0x30e) if '\u030f' <= c <= '\u0317' else ' ' if c == '\x03' else c for c in text))

def official_keys(doc, task):
    column = SUBJECTS.index(task['subject'])
    pages=[p for p in doc if len(re.findall(r'問\s*\d+',labels(p.get_text())))>=30]
    assert len(pages)==1, '学科正答表を一意に特定できません'
    page = pages[0]
    words = [(*line['bbox'],labels(''.join(s['text'] for s in line['spans']))) for line in archive.lines(page.get_text('dict'))]
    words = [w for w in words if (w[0] < page.rect.width/2) == (column == 0)]
    keys = {}
    for w in words:
        complete=re.fullmatch(r'問\s*(\d+)\s+([1-5])',w[4].strip())
        if complete:
            number=int(complete[1]);assert number not in keys
            keys[number]=int(complete[2])-1
            continue
        if not re.fullmatch(r'問\s*\d*', w[4].strip()): continue
        cells = sorted((v for v in words if abs(v[1]-w[1]) < 4 and 0 < v[0]-w[2] < 100), key=lambda v:v[0])
        values = [v[4].strip() for v in cells if v[4].strip()]
        number = re.search(r'\d+', w[4])
        if number: values.insert(0,number[0])
        if task['term']=='第60回' and column==0 and values[0] in ('3','8'):
            assert '全て正解として採点' in archive.norm(page.get_text())
            keys[int(values[0])] = None
            continue
        if task['term']=='第59回' and column==1 and values[0]=='8':
            assert '5または4' in archive.norm(page.get_text())
            keys[8] = None
            continue
        if task['term']=='第57回' and column==0 and values[0]=='3':
            assert archive.norm('સҽਜ਼մ') in labels(page.get_text())
            keys[3] = None
            continue
        assert len(values) == 2 and values[0].isdigit() and values[1] in '12345', values
        number = int(values[0]); assert number not in keys
        keys[number] = int(values[1])-1
    assert sorted(keys) == list(range(1,16)), keys
    # Independent reading-order check of the two parallel answer columns.
    text = labels(page.get_text())
    pairs = re.findall(archive.norm(r'問\s*(\d+)\s*([1-5]または[1-5]|[1-5]|全て正解として採点|સҽਜ਼մͳ͢\s*ͱࡀ఼)'), text)
    assert len(pairs) == 30
    ordered=pairs[column*15:(column+1)*15] if [int(n) for n,a in pairs[:15]]==list(range(1,16)) else pairs[column::2]
    assert keys == {int(n):int(a)-1 if a.isdigit() else None for n,a in ordered}
    return keys

def question_starts(doc):
    starts = []
    for pn in range(len(doc)):
        for line in archive.lines(doc[pn].get_text('dict')):
            text = ''.join(s['text'] for s in line['spans'])
            # Some official PDFs lack a correct ToUnicode map. Decode only
            # their fixed heading glyphs; never expose corrupted body text.
            if text.startswith('໲'):
                text = '問' + ''.join(chr(ord(c)+29) if '\x13' <= c <= '\x1c' else str(ord(c)-0x30e) if '\u030f' <= c <= '\u0317' else c for c in text[1:])
            match = re.match(r'^問\s*(\d+)', archive.norm(text))
            if match and line['bbox'][0] < 100:
                starts.append((int(match[1]),pn,line['bbox'][1]))
    starts.sort(key=lambda s:(s[1],s[2]))
    assert [n for n,_,_ in starts] == list(range(1,16)), starts
    return starts

def mirror_papers(acquired):
    source = fetcher.fetch('https://www.team-saboten.com/school/kakomon-kaisetsu','weather-mirror-index.html')
    acquired.append(source)
    class Links(HTMLParser):
        def __init__(self): super().__init__(); self.session=None; self.papers={}
        def handle_data(self,text):
            match=re.fullmatch(r'.*第(\d+)回試験問題.*',text)
            if match:self.session=int(match[1])
        def handle_starttag(self,tag,attrs):
            url=dict(attrs).get('href','')
            if tag=='a' and '.pdf' in url and self.session:
                self.papers.setdefault(self.session,[]).append(url)
    parser=Links();parser.feed((SRC/source['file']).read_text(encoding='utf-8'))
    # These nine sessions have no correction link in the mirror index.
    # Papers with correction links require reviewing that correction first.
    for session in [55,54,53,51,50,49,46,45,44]:
        urls=list(dict.fromkeys(parser.papers[session]));assert len(urls)==7
        papers={}
        for key,index in [('ippan',0),('senmon',1),('answer',6)]:
            assert urls[index].startswith('https://www.team-saboten.com/_files/ugd/'), 'Unexpected mirror host'
            record=fetcher.fetch(urls[index],f'weather-{session}-{key}.pdf')
            acquired.append(record);papers[key]=record
        yield session,papers

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    index = fetcher.fetch('https://www.jmbsc.or.jp/jp/examination/examination-7.html','weather-index.html')
    text = (SRC/index['file']).read_bytes().decode('utf-8')
    links = re.findall(r'href=["\']([^"\']+\.zip)',text)
    assert len(links) >= 10
    packs, acquired = [], [index]
    (OUT/'assets').mkdir(exist_ok=True)
    tasks=[]
    for link in links:
        session = int(re.search(r'cwfe_(\d+)',link)[1])
        assert urljoin(index['url'],link).startswith('https://www.jmbsc.or.jp/jp/examination/z/'), 'Unexpected official archive host'
        source = fetcher.fetch(urljoin(index['url'],link),f'weather-{session}.zip')
        acquired.append(source);papers = {}
        with zipfile.ZipFile(SRC/source['file']) as z:
            for member in z.namelist():
                if not member.lower().endswith('.pdf'): continue
                base = Path(member).name;stem = f'weather-{session}-' + archive.sha(base.encode())[:12]
                data = z.read(member); (SRC/(stem+'.pdf')).write_bytes(data)
                record = dict(file=stem+'.pdf',url=source['url']+'#'+quote(base),sha256=archive.sha(data),bytes=len(data),archive=source['file'],member=member)
                acquired.append(record)
                if 'ippan' in base: papers['ippan'] = record
                elif 'senmon' in base: papers['senmon'] = record
                elif 'kaitourei' in base or base.startswith('cwfe_') and '_a' in base: papers['answer'] = record
        tasks.append((session,papers))
    if '--mirrors' in sys.argv:tasks.extend(mirror_papers(acquired))
    for session,papers in tasks:
        assert set(papers) == {'ippan','senmon','answer'}, papers
        answer = papers['answer']
        for column,kind in enumerate(['ippan','senmon']):
            qsource = papers[kind]; stem = Path(qsource['file']).stem
            year = str(2026-(66-session+1)//2)
            task = dict(provider='JMBSC',examId='weather',year=year,term=f'第{session}回',subject=SUBJECTS[column],
                        sourceFile=qsource['file'],answerFile=answer['file'],url=qsource['url'],sources=[qsource,answer],localOnly=True)
            with fitz.open(SRC/qsource['file']) as doc, fitz.open(SRC/answer['file']) as ans:
                keys = official_keys(ans,task); starts = question_starts(doc)
                rows, evidence, pictures = [], [], {}
                for i,(number,pn,y) in enumerate(starts):
                    if keys[number] is None: continue
                    end = starts[i+1][1] if i+1<len(starts) else len(doc)-1
                    if i+1<len(starts) and starts[i+1][2]<65: end -= 1
                    images, records = [], []
                    for p in range(pn,end+1):
                        if p not in pictures:
                            name = stem+f'-p{p+1}.png'; path=OUT/'assets'/name
                            doc[p].get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(path)
                            pictures[p] = ({'src':'assets/github-material/'+name,'alt':f'第{session}回 {SUBJECTS[column]} 原本{p+1}ページ'},
                                           {'file':name,'sha256':archive.sha(path.read_bytes()),'page':p,'rect':list(doc[p].rect)})
                        image,record = pictures[p]; images.append(image); records.append(record)
                    title = f'第{session}回 気象予報士試験 {SUBJECTS[column]} 問{number}'
                    q = dict(id=stem+f'-q{number:03}',examId='weather',type='single',year=year,term=task['term'],subject=task['subject'],category='過去問',topic=title,
                             prompt=title+'\n原本ページの該当する問題番号を解答してください。',options=list('12345'),answer=keys[number],images=images,
                             explanation=f'公式解答：{keys[number]+1}。理由解説は未収録です。実施当時の制度を前提とします。',
                             source='気象業務支援センター '+title+'（個人利用・原本ページ）',sourceUrl=qsource['url'],explanationSource='気象業務支援センター公式解答')
                    rows.append(q); evidence.append(dict(id=q['id'],number=number,answer=q['answer'],images=records))
                raw=archive.encode(rows); (OUT/(stem+'.json')).write_bytes(raw)
                packs.append(dict(**task,file=stem+'.json',status='prepared',count=len(rows),sha256=archive.sha(raw),questions=evidence))
        print('Prepared',session,sum(p['count'] for p in packs if p['term']==f'第{session}回'),flush=True)
    report = {'packs':packs,'sources':acquired,'unregistered':'実技問題・解答用紙は原本保存のみ。小問と模範解答の対応は未検証。'}
    (OUT/'weather-report.json').write_bytes(archive.encode(report))

if __name__ == '__main__': main()
