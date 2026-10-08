"""Check keys by row grouping (independent of the importer's nearest-cell parser)."""
import importlib.util,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('finance',ROOT/'scripts/prepare-finance-material.py')
f=importlib.util.module_from_spec(spec);spec.loader.exec_module(f)
from PIL import Image
report_file=f.OUT/'finance-report.json'
raw=report_file.read_bytes();report=json.loads(raw);count=0;checked=set();keys_cache={}
for pack_index,pack in enumerate(report['packs']):
    if pack['status']!='prepared':continue
    cache_key=(pack['answerFile'],pack['subject'])
    if cache_key not in keys_cache:
        keys={}
        if pack['answerFile'].endswith('.html'):
            soup=f.BeautifulSoup((f.SRC/pack['answerFile']).read_bytes(),'html.parser')
            tables=[t for t in soup.find_all('table') if not t.find('table')]
            selected=False
            for table in tables:
                text=f.ipa.norm(table.get_text(' ',strip=True))
                if '【' in text:selected='【'+pack['subject']+'】' in text
                if not selected:continue
                for tr in table.find_all('tr'):
                    cells=[f.ipa.norm(td.get_text(' ',strip=True)) for td in tr.find_all(['td','th'])]
                    if len(cells)!=2 or not re.fullmatch(r'問題\s*\d+',cells[0]):continue
                    n=str(int(re.search(r'\d+',cells[0])[0]));keys[n]=int(cells[1])-1 if cells[1].isdigit() else None
        elif pack['examId']=='fp3':
            doc=f.fitz.open(f.SRC/pack['answerFile'])
            text=f.ipa.norm('\n'.join(p.get_text() for p in doc))
            cells=[t.strip() for t in text.splitlines() if re.fullmatch(r'問\s*\d+|[1-3]',t.strip())]
            assert len(cells)==40
            for offset in (0,20):
                for j in range(10):keys[str(int(re.search(r'\d+',cells[offset+j])[0]))]=int(cells[offset+10+j])-1
        else:
            doc=f.fitz.open(f.SRC/pack['answerFile'])
            page=next(p for p in doc if pack['subject'] in f.ipa.norm(p.get_text()))
            lines=f.tour.native_lines(page)
            headers=[((b[0]+b[2])/2,t.strip('【】[] '),b[1]) for t,b in lines if t.strip('【】[] ') in f.SUBJECTS]
            # Group all cells along each horizontal table row, then pair numbers and answers in x order.
            table=[(t,b) for t,b in lines if re.fullmatch(r'問題\s*\d+|[1-9](?:[,、・\s]+[1-9])*|[-−―ー]',t)]
            for y in sorted({round(b[1],0) for t,b in table if t.startswith('問題')}):
                row=sorted((b[0],t,b) for t,b in table if abs(b[1]-y)<.6)
                for i,(x,t,b) in enumerate(row):
                    if not t.startswith('問題'):continue
                    if min(headers,key=lambda h:abs(h[0]-(b[0]+b[2])/2))[1]!=pack['subject']:continue
                    assert i+1<len(row) and not row[i+1][1].startswith('問題')
                    symbol=row[i+1][1];values=sorted({int(v)-1 for v in re.findall('[1-9]',symbol)})
                    keys[str(int(re.search(r'\d+',t)[0]))]=values[0] if len(values)==1 else None
        assert set(map(int,keys))==set(range(1,len(keys)+1))
        keys_cache[cache_key]=keys
    keys=keys_cache[cache_key];rows=json.loads((f.OUT/pack['file']).read_bytes())
    assert f.ipa.sha((f.OUT/pack['file']).read_bytes())==pack['sha256']
    assert len(rows)==pack['count']==len(pack['questions'])
    assert len(rows)+len(pack['excludedQuestions'])==len(keys)
    for source in pack['sources']:assert f.ipa.sha((f.SRC/source['file']).read_bytes())==source['sha256']
    source_doc=f.fitz.open(f.SRC/pack['sourceFile'])
    for q,e in zip(rows,pack['questions']):
        assert q['id']==e['id'] and q['answer']==e['answer']==keys[e['number']]
        assert 0<=q['answer']<len(q['options']) and q['sourceUrl']==pack['url']
        assert len(q['images'])==len(e['images'])>0
        for image,record in zip(q['images'],e['images']):
            assert image['src']=='assets/github-material/'+record['file']
            if record['file'] in checked:continue
            expected=source_doc[record['page']].get_pixmap(matrix=f.fitz.Matrix(1.5,1.5),clip=f.fitz.Rect(record['rect']),alpha=False)
            with Image.open(f.OUT/'assets'/record['file']) as stored:
                assert stored.size==(expected.width,expected.height) and stored.convert('RGB').tobytes()==expected.samples
            assert f.ipa.sha((f.OUT/'assets'/record['file']).read_bytes())==record['sha256']
            checked.add(record['file'])
        count+=1
    if (pack_index+1)%20==0:print(f'Checked {pack_index+1}/{len(report["packs"])} papers, {count} questions',flush=True)
assert count>0
assert report_file.read_bytes()==raw,'Report changed during verification'
(f.OUT/'finance-verification.json').write_bytes(f.ipa.encode(dict(reportSha256=f.ipa.sha(raw),questions=count,officialAnswers='pass',originalPixels='pass',visualReview='representative pages only; not all questions')))
print(f'PASS: {count} questions, {len(checked)} original page images; independent official-key check')
