"""Verify source hashes, official answer cells and every archived PDF pixel."""
import importlib.util,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('business',ROOT/'scripts/prepare-business-material.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
sys.stdout.reconfigure(encoding='utf-8')
raw=(b.OUT/'business-report.json').read_bytes();report=json.loads(raw);seen=set();total=0
html_packs={p['file']:p for p in b.examples()+b.commercial_examples()}
for index,pack in enumerate(report['packs']):
    if pack['status']!='prepared':continue
    assert pack['localOnly']
    for source in pack['sources']:assert b.b.ipa.sha((b.SRC/source['file']).read_bytes())==source['sha256']
    data=(b.OUT/pack['file']).read_bytes();assert b.b.ipa.sha(data)==pack['sha256']
    rows=json.loads(data);assert len(rows)==pack['count']==len(pack['questions'])
    if pack.get('kind')=='case':
        with b.fitz.open(b.SRC/pack['answerFile']) as doc:
            expected=sorted({int(n) for p in doc for n in re.findall(r'第\s*(\d+)\s*問',b.norm(p.get_text()))})
        assert [int(e['number']) for e in pack['questions']]==expected
        with b.fitz.open(b.SRC/pack['sourceFile']) as doc:
            assert all([r['page'] for r in e['images']]==list(range(len(doc))) for e in pack['questions'])
    official={}
    if pack.get('answerFile') and rows[0]['type']=='single':
        with b.fitz.open(b.SRC/pack['answerFile']) as doc:
            for page in doc:
                lines=b.b.native_lines(page)
                centers=sorted((r[0]+r[2])/2 for t,r in lines if t=='正解')
                for x in centers:
                    column=max((r[0]+r[2])/2 for t,r in lines if t=='問題' and (r[0]+r[2])/2<x)
                    subcolumn=max((r[0]+r[2])/2 for t,r in lines if t=='設問' and (r[0]+r[2])/2<x)
                    problems=[(int(re.search(r'\d+',t)[0]),r) for t,r in lines if re.fullmatch(r'第\d+問',t) and abs(column-(r[0]+r[2])/2)<15]
                    for t,r in lines:
                        if t not in list('アイウエオカキ') or abs((r[0]+r[2])/2-x)>12:continue
                        parents=[(n,p) for n,p in problems if p[1]<=r[1]+2]
                        earlier=[int(re.search(r'\d+',u)[0]) for u,c in lines if re.fullmatch(r'第\d+問',u) and (c[0]+c[2])/2<column-15]
                        assert parents or earlier
                        number=max(parents,key=lambda p:p[1][1])[0] if parents else max(earlier)
                        sub=[u for u,c in lines if re.fullmatch(r'設問\d+',u) and abs(c[1]-r[1])<2 and abs(subcolumn-(c[0]+c[2])/2)<15]
                        key=str(number)+('-'+re.search(r'\d+',sub[0])[0] if sub else '')
                        assert key not in official
                        official[key]='アイウエオカキ'.index(t)
    for q,e in zip(rows,pack['questions']):
        assert q['id']==e['id'] and q['answer']==e['answer'] and q['sourceUrl']==pack['url']
        if official:assert q['answer']==official[e['number']]
        if q['type']=='written':assert q['answer'] is None and q['modelAnswer']
        for field,source in [('images',pack.get('sourceFile')),('solutionImages',pack.get('answerFile'))]:
            refs=q.get(field,[]);records=e.get(field,[]);assert len(refs)==len(records)
            for ref,r in zip(refs,records):
                assert ref['src']=='assets/github-material/'+r['file']
                if r['file'] in seen:continue
                file=b.OUT/'assets'/r['file'];assert b.b.ipa.sha(file.read_bytes())==r['sha256']
                with b.fitz.open(b.SRC/source) as doc:
                    page=doc[r['page']];assert list(page.rect)==r['rect']
                    pix=page.get_pixmap(matrix=b.fitz.Matrix(1.5,1.5),alpha=False)
                    with b.b.ipa.Image.open(file) as image:assert image.size==(pix.width,pix.height) and image.convert('RGB').tobytes()==pix.samples
                seen.add(r['file'])
    if not pack.get('sourceFile'):
        regenerated=html_packs[pack['file']]
        assert regenerated['sha256']==pack['sha256']
    if pack['examId'].startswith('retail'):assert html_packs[pack['file']]['sha256']==pack['sha256']
    total+=len(rows)
    if index%15==0:print(index+1,'packs checked;',total,'items;',len(seen),'pages',flush=True)
assert total>2000
(b.OUT/'business-verification.json').write_bytes(b.b.ipa.encode(dict(reportSha256=b.b.ipa.sha(raw),questions=total,officialAnswers='pass',originalPixels='pass',method='Independent spatial answer-cell matching, source hashes, HTML extraction and every original question/solution pixel. Legacy papers use written self grading.')))
print(f'PASS: {total} business items, {len(seen)} original PDF page images')
