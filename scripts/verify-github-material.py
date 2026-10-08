"""Verify every archived source, official key and generated image before a build."""
import hashlib, importlib.util, json, re, sys, unicodedata
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'build/python-deps'))
import pymupdf as fitz
from PIL import Image
SRC=ROOT/'private-data/github-material';OUT=SRC/'prepared'
sha=lambda b:hashlib.sha256(b).hexdigest()
norm=lambda t:unicodedata.normalize('NFKC',t)
spec=importlib.util.spec_from_file_location('nonit',ROOT/'scripts/prepare-nonit-material.py')
nonit=importlib.util.module_from_spec(spec);spec.loader.exec_module(nonit)
spec=importlib.util.spec_from_file_location('expansion',ROOT/'scripts/expand-github-material.py')
expansion=importlib.util.module_from_spec(spec);spec.loader.exec_module(expansion)

spec=importlib.util.spec_from_file_location('jlpt',ROOT/'scripts/prepare-jlpt-material.py')
jlpt=importlib.util.module_from_spec(spec);spec.loader.exec_module(jlpt)
spec=importlib.util.spec_from_file_location('design',ROOT/'scripts/prepare-design-material.py')
design=importlib.util.module_from_spec(spec);spec.loader.exec_module(design)
spec=importlib.util.spec_from_file_location('weather',ROOT/'scripts/prepare-weather-material.py')
weather=importlib.util.module_from_spec(spec);spec.loader.exec_module(weather)
spec=importlib.util.spec_from_file_location('food',ROOT/'scripts/prepare-food-material.py')
food=importlib.util.module_from_spec(spec);spec.loader.exec_module(food)
spec=importlib.util.spec_from_file_location('civil',ROOT/'scripts/prepare-civil-material.py')
civil=importlib.util.module_from_spec(spec);spec.loader.exec_module(civil)
spec=importlib.util.spec_from_file_location('tourism',ROOT/'scripts/prepare-tourism-material.py')
tourism=importlib.util.module_from_spec(spec);spec.loader.exec_module(tourism)
spec=importlib.util.spec_from_file_location('estate',ROOT/'scripts/prepare-estate-material.py')
estate=importlib.util.module_from_spec(spec);spec.loader.exec_module(estate)
spec=importlib.util.spec_from_file_location('medical_council',ROOT/'scripts/prepare-medical-council.py')
medical_council=importlib.util.module_from_spec(spec);spec.loader.exec_module(medical_council)

def ipa_keys(doc):
    keys={}
    for page in doc:
        words=page.get_text('words')
        for word in words:
            match=re.fullmatch(r'問(\d+)',norm(word[4]))
            label_end=word[2]
            if not match and norm(word[4])=='問':
                following=[w for w in words if abs((w[1]+w[3]-word[1]-word[3])/2)<3.5 and 0<w[0]-word[2]<20 and re.fullmatch(r'\d+',norm(w[4]))]
                if not following:continue  # Decorative vertical 問A headings are not table cells.
                assert len(following)==1
                match=re.fullmatch(r'(\d+)',norm(following[0][4]));label_end=following[0][2]
            if not match:continue
            candidates=[w for w in words if abs((w[1]+w[3]-word[1]-word[3])/2)<3.5 and 0<w[0]-label_end<85 and norm(w[4]) in 'アイウエオカキクケコ' and len(norm(w[4]))==1]
            assert len(candidates)==1,(word,candidates)
            keys[int(match[1])]='アイウエオカキクケコ'.index(norm(candidates[0][4]))
    assert sorted(keys)==list(range(1,max(keys)+1))
    return keys

def main():
    report=json.loads((OUT/'report.json').read_bytes());count=0;checked_images=set();image_hashes={}
    medical_only='--medical' in sys.argv
    report_name='medical-verified-report.json' if medical_only else 'report.json'
    verification_name='medical-verification.json' if medical_only else 'verification.json'
    cache_file=OUT/('medical-verification-cache.json' if medical_only else 'verification-cache.json')
    cache=json.loads(cache_file.read_bytes()) if cache_file.exists() else {}
    if (OUT/'gsi-report.json').exists():
        report['packs']=[p for p in report['packs'] if p.get('provider')!='GSI']+json.loads((OUT/'gsi-report.json').read_bytes())['packs']
    if (OUT/'nonit-report.json').exists():
        report['packs']=[p for p in report['packs'] if p.get('provider') not in ('ECEE','MHLW','MHLW-PHARM')]+json.loads((OUT/'nonit-report.json').read_bytes())['packs']
    if (OUT/'expansion-report.json').exists():
        report['packs']=[p for p in report['packs'] if p.get('provider')!='MHLW-NUMERIC']+json.loads((OUT/'expansion-report.json').read_bytes())['packs']
    if (OUT/'jlpt-report.json').exists():
        report['packs']=[p for p in report['packs'] if p.get('provider')!='JLPT']+json.loads((OUT/'jlpt-report.json').read_bytes())['packs']
    if (OUT/'design-report.json').exists():
        report['packs']=[p for p in report['packs'] if p.get('provider')!='RBC']+json.loads((OUT/'design-report.json').read_bytes())['packs']
    if (OUT/'food-report.json').exists():
        report['packs']=[p for p in report['packs'] if p.get('provider')!='FOOD']+json.loads((OUT/'food-report.json').read_bytes())['packs']
    if (OUT/'civil-report.json').exists():
        report['packs']=[p for p in report['packs'] if p.get('provider')!='JINJI']+json.loads((OUT/'civil-report.json').read_bytes())['packs']
    if (OUT/'weather-report.json').exists():
        report['packs']=[p for p in report['packs'] if p.get('provider')!='JMBSC']+json.loads((OUT/'weather-report.json').read_bytes())['packs']
    if (OUT/'tourism-report.json').exists():
        report['packs']=[p for p in report['packs'] if p.get('provider')!='TOURISM']+json.loads((OUT/'tourism-report.json').read_bytes())['packs']
    report['packs']=[p for p in report['packs'] if p.get('provider')!='SAFETY']
    if (OUT/'estate-report.json').exists():
        report['packs']=[p for p in report['packs'] if p.get('provider')!='ESTATE']+json.loads((OUT/'estate-report.json').read_bytes())['packs']
    report['packs']=[p for p in report['packs'] if p.get('provider') not in ('MHLW-MEDICAL','MEDICAL-COUNCIL')]
    if medical_only:
        report={'packs':sum((json.loads((OUT/name).read_bytes())['packs'] for name in ['medical-official-report.json','medical-council-report.json']),[])}
    raw=json.dumps(report,ensure_ascii=False,indent=2).encode('utf-8');(OUT/report_name).write_bytes(raw)
    prepared_count=0
    for pack in sorted(report['packs'],key=lambda p:p.get('provider') not in ('ECEE','MHLW','MHLW-PHARM')):
        if pack['status']!='prepared':continue
        for source in pack['sources']:assert sha((SRC/source['file']).read_bytes())==source['sha256']
        fingerprint=sha(json.dumps(pack,ensure_ascii=False,sort_keys=True).encode('utf-8'))
        if cache.get(pack['file'])==fingerprint:
            assert sha((OUT/pack['file']).read_bytes())==pack['sha256'],pack['file']
            for item in pack['questions']:
                for record in item['images']+item.get('solutionImages',[]):
                    file=record['file']
                    if file not in image_hashes:image_hashes[file]=sha((OUT/'assets'/file).read_bytes())
                    assert image_hashes[file]==record['sha256'],file
                for audio in item.get('audio',[]):
                    file=audio['src'].removeprefix('assets/github-material/')
                    assert (OUT/'assets'/file).read_bytes()==(SRC/file).read_bytes()
            count+=pack['count'];prepared_count+=1
            continue
        docs={s['file']:fitz.open(SRC/s['file']) for s in pack['sources'] if s['file'].endswith('.pdf')};answer=docs.get(pack['answerFile'])
        assert answer is not None or pack.get('provider')=='MEDICAL-COUNCIL'
        answer_text=norm('\n'.join(p.get_text() for p in answer)) if answer is not None else ''
        provider=pack.get('provider')
        if provider=='MEDICAL-COUNCIL':
            keys=medical_council.official_keys(pack)
            starts=medical_council.question_starts(docs[pack['sourceFile']])
            assert pack['localOnly'] and all(str(n) in keys for n,p,y in starts)
        elif provider=='ESTATE':
            keys=estate.official_keys(answer,pack)
            starts=estate.question_starts(docs[pack['sourceFile']],pack)
            assert pack['localOnly'] and len(starts)==50
        elif provider=='TOURISM':
            keys=tourism.official_keys(answer,pack)
            if pack['kind']!='jnto':
                starts=tourism.question_starts(docs[pack['sourceFile']],pack)
                assert set(keys)=={n for n,p,y in starts}
            assert pack['localOnly']
        elif provider=='FOOD':
            keys=food.official_keys(answer,pack)
            textual={};occurrences={}
            label=r'(\d+)' if pack['examId'].startswith('agri') and pack['year']=='2020' else r'問\s*(\d+)'
            text=norm('\n'.join(p.get_text() for p in answer))
            symbols={'ア':0,'イ':1,'ウ':2,'エ':3,'1':0,'2':1,'3':2,'4':3,'➀':0,'➁':1,'➂':2,'➃':3}
            for n,symbol in re.findall(label+r'\s*\n\s*([アイウエ1234➀➁➂➃])\s*(?:\n|$)',text):
                index=occurrences.get(n,0);occurrences[n]=index+1;textual[f'{int(n)}:{index}']=symbols[symbol]
            assert all(textual.get(n)==a for n,a in keys.items() if a is not None), 'Food answer text/geometry mismatch'
            starts=food.question_starts(docs[pack['sourceFile']],pack)
            assert set(keys)=={n for n,p,y in starts} and len(keys)==len(starts)
            assert {q['number'] for q in pack['questions']}=={n for n,a in keys.items() if a is not None}
        elif provider=='JMBSC':
            keys=weather.official_keys(answer,pack)
            starts=weather.question_starts(docs[pack['sourceFile']])
        elif provider=='JINJI':
            keys=civil.official_keys(answer)
            starts=civil.question_starts(docs[pack['sourceFile']])
        elif provider=='RBC':keys={item['number']:item['answer'] for item in design.items(answer,pack['sourceFile'])}
        elif provider=='JLPT':keys=jlpt.official_keys(answer,pack)
        elif provider in ('MHLW-NUMERIC','MHLW-MEDICAL'):keys=expansion.official_keys(answer,pack)
        elif provider in ('ECEE','MHLW','MHLW-PHARM'):keys=nonit.official_keys(answer,pack)
        elif provider=='GSI':keys={int(n):int(a)-1 for n,a in re.findall(r'No\.?\s*(\d+)\s*([1-5])',answer_text)}
        else:keys=ipa_keys(answer)
        if provider=='MHLW':
            page_texts=[nonit.tidy(p.get_text()) for p in docs[pack['sourceFile']]];text=''.join(page_texts)
        if provider in ('ECEE','MHLW-PHARM'):
            starts=nonit.question_starts(docs[pack['sourceFile']],pack)
            parents={n for n,p,y in starts}
            assert all(int(re.match(r'\d+',e['number'])[0]) in parents for e in pack['questions'])
        if provider in ('MHLW-NUMERIC','MHLW-MEDICAL'):
            starts=expansion.question_starts(docs[pack['sourceFile']],pack)
            assert [n for n,p,y in starts]==list(range(1,len(keys)+1))
        if provider=='MHLW-PHARM':
            source_doc=docs[pack['sourceFile']]
            page_lines=[nonit.ipa.lines(p.get_text('dict',flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)) for p in source_doc]
            option_review={r['number']:r for r in json.loads((SRC/'pharmacist-option-counts-verified.json').read_bytes())}
        data=(OUT/pack['file']).read_bytes();assert sha(data)==pack['sha256'],pack['file'];rows=json.loads(data)
        assert len(rows)==pack['count']==len(pack['questions'])
        for q,evidence in zip(rows,pack['questions']):
            official=keys[evidence['number']]
            if isinstance(official,list) and len(official)==1:official=official[0]
            assert q['id']==evidence['id'] and q['answer']==evidence['answer']==official,(pack['file'],q['id'],q['answer'],evidence['answer'],official)
            assert q['sourceUrl']==evidence.get('sourceUrl',pack['url']) and q['examId']==pack['examId'] and q['year']==pack['year']
            if provider=='MEDICAL-COUNCIL':
                index=next(i for i,s in enumerate(starts) if str(s[0])==evidence['number'])
                text=expansion.segments(docs[pack['sourceFile']],starts,index)
                labels=sorted({int(m[1]) for line in text if (m:=re.match(r'^([1-5])\s*[.．]',line))})
                assert q['options']==list(map(str,labels)) and len(labels)==evidence['optionCount']
                assert [r['page'] for r in evidence['images']]==expansion.question_pages(docs[pack['sourceFile']],starts,index)
            if provider=='ESTATE':
                assert q['options']==list('1234')
                first=starts[int(evidence['number'])-1][1]
                assert first in {r['page'] for r in evidence['images']}
                if pack['answerFile']==pack['sourceFile']:
                    assert len(docs[pack['sourceFile']])-1 not in {r['page'] for r in evidence['images']},'Answer page leaked into questions'
            if provider=='TOURISM':
                if pack['kind'] in ('kouron','jnto'):
                    assert all(r['page']<=tourism.question_end(docs[pack['sourceFile']],pack) for r in evidence['images'] if not r.get('sourceFile')),'Answer pages leaked into questions'
                if pack['kind']=='jata' and pack['subject'] in ('国内実務','海外実務'):
                    assert [r['page'] for r in evidence['images'] if not r.get('sourceFile')]==list(range(1,len(docs[pack['sourceFile']])))
                    assert tourism.question_starts(docs[pack['sourceFile']],pack)[0][1]>0
                    assert {r.get('sourceFile') for r in evidence['images'] if r.get('sourceFile')}=={s['file'] for s in pack['sources'][2:]}
            if provider=='JLPT':
                assert q['audio']==evidence['audio']
                for audio in q['audio']:
                    file=audio['src'].removeprefix('assets/github-material/')
                    assert file in {s['file'] for s in pack['sources']}
                    assert (OUT/'assets'/file).read_bytes()==(SRC/file).read_bytes()
            assert len(q['images'])==len(evidence['images'])
            if provider=='JINJI':
                assert evidence['number'] in {n for n,p,y in starts}
                assert next(p for n,p,y in starts if n==evidence['number']) in {r['page'] for r in evidence['images']}
                assert len(answer)-1 not in {r['page'] for r in evidence['images']},'Answer page leaked into question'
            if provider=='JMBSC':
                assert pack['localOnly'] and q['options']==list('12345')
                i=evidence['number']-1; first=starts[i][1]
                last=starts[i+1][1] if i+1<len(starts) else len(docs[pack['sourceFile']])-1
                if i+1<len(starts) and starts[i+1][2]<65:last-=1
                assert [r['page'] for r in evidence['images']]==list(range(first,last+1))
            if provider=='MHLW':
                assert q['options']==evidence['choices'] and q['prompt'].endswith('\n'+evidence['originalText'])
                assert all(nonit.tidy(value) in text for value in [evidence['originalText'],*evidence['choices']])
                assert [r['page'] for r in evidence['images']]==nonit.medical_pages(page_texts,{'problem_text':evidence['originalText'],'choices':evidence['choices']})
            if provider in ('ECEE','MHLW-PHARM'):
                number=int(re.match(r'\d+',evidence['number'])[0]);index=next(i for i,s in enumerate(starts) if s[0]==number)
                assert starts[index][1] in {r['page'] for r in evidence['images']},'Question page missing'
            if provider=='MHLW-PHARM':
                assert number not in (92,199,220,221,287,316)
                nums=nonit.pharm_options(source_doc,starts,index,page_lines)
                if not nums:
                    reviewed=option_review[number]
                    assert reviewed['sourceFile']==pack['sourceFile'] and reviewed['sha256']==sha((SRC/pack['sourceFile']).read_bytes())
                    nums=list(range(1,reviewed['count']+1))
                assert q['options']==list(map(str,nums))
            if provider in ('MHLW-NUMERIC','MHLW-MEDICAL'):
                number=int(evidence['number']);source_doc=docs[pack['sourceFile']]
                text=expansion.segments(source_doc,starts,number-1)
                labels=sorted({int(m[1]) for line in text if (m:=re.match(r'^([1-5])\s*[.．]',line))})
                assert q['options']==list(map(str,labels)) and len(labels)==evidence['optionCount']
                pages=expansion.question_pages(source_doc,starts,number-1)
                assert [r['page'] for r in evidence['images']]==pages
                assert not any('別冊' in source_doc[p].get_text() for p in pages)
            if provider=='RBC':
                assert q['options']==['1','2','3','4']
                assert len(q['solutionImages'])==len(evidence['solutionImages'])==len(q['images'])
            for image,record in zip(q['images']+q.get('solutionImages',[]),evidence['images']+evidence.get('solutionImages',[])):
                assert image['src']=='assets/github-material/'+record['file']
                identity=(pack['sourceFile'],record.get('sourceFile'),record['file'],record['sha256'],record['page'],tuple(record['rect']))
                if identity in checked_images:continue
                path=OUT/'assets'/record['file'];assert sha(path.read_bytes())==record['sha256']
                page=docs[record.get('sourceFile',pack['sourceFile'])][record['page']];rect=fitz.Rect(record['rect']);assert page.rect.contains(rect)
                pix=page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),clip=rect,alpha=False)
                expected=design.cleaned(page)[0].tobytes() if provider=='RBC' and '-question' in record['file'] else pix.samples
                with Image.open(path) as stored:assert stored.size==(pix.width,pix.height) and stored.convert('RGB').tobytes()==expected,record['file']
                checked_images.add(identity)
            count+=1
        prepared_count+=1
        cache[pack['file']]=fingerprint
        cache_file.write_text(json.dumps(cache),encoding='utf-8')
        if prepared_count%25==0:print('Verified packs:',prepared_count,'questions:',count,flush=True)
    verification={'reportSha256':sha(raw),'questions':count,'officialAnswers':'pass','originalPixels':'pass',
                  'method':'IPA keys independently checked by word geometry; GSI No./answer pairs; ECEE/MHLW answer cells and complete subquestion pairs. Medical text/choices matched against the official PDF. Nursing/laboratory numbering, option labels and shared case pages rechecked. JLPT native answer tables matched by cell geometry; 2009 scanned keys pinned to reviewed PDF hashes; official audio bytes matched. RBC answer marks matched to four OCR option labels; question images regenerated with red margin marks removed and faded light margin pixels whitened, solution images regenerated unchanged. Every source/pack/image hash checked.',
                  'visualReview':'Representative pages only; OCR numeral guesses are not official evidence; pending papers are excluded.'}
    verification['method']+=' JINJI native answer cells and headings checked; scanned answer tables and exceptional headings pinned to visually reviewed source hashes; answer pages excluded.'
    verification['method']+=' TOURISM native JATA/ANTA/UNKAN answer cells and numbering checked; JNTO scanned answer sheets pinned to fully reviewed source hashes. Kouron answers are publisher-provided, not independently certified official answers. Shared JATA reference pages preserved and answer pages excluded.'
    verification['method']+=' ESTATE answer cells and complete 1-50 numbering checked; exceptional answer tables pinned to visually reviewed source hashes. Question page rotations handled by rendered OCR, and combined-paper answer pages excluded.'
    verification['method']+=' JINJI native answer cells and headings checked; scanned answer tables and exceptional headings pinned to visually reviewed source hashes; answer pages excluded.'
    (OUT/verification_name).write_text(json.dumps(verification,ensure_ascii=False,indent=2),encoding='utf-8')
    print('PASS: archived official questions',count,'all original/processed crop pixels and official keys checked',flush=True)

if __name__=='__main__':main()
