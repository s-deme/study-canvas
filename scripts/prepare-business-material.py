"""Import official business papers using existing PDF image helpers."""
import importlib.util,json,re,sys
from pathlib import Path
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('business_base',ROOT/'scripts/prepare-tourism-material.py')
b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
SRC,OUT,fitz,norm=b.SRC,b.OUT,b.fitz,b.norm
from bs4 import BeautifulSoup
INDEX='https://www.jf-cmca.jp/contents/010_c_/shikenmondai.html'
SUBJECTS=['経済学・経済政策','財務・会計','企業経営理論','運営管理','経営法務','経営情報システム','中小企業経営・政策']

def acquire():
    html=BeautifulSoup((SRC/'business-sme-index.html').read_bytes().decode('cp932'),'html.parser')
    tasks=[]
    for year in range(2011,2027):
        page=SRC/f'business-answers-{year}.html'
        if not page.exists():continue
        tag=f'{"r" if year>=2019 else "h"}{year-(2018 if year>=2019 else 1988):02}'
        base=f'https://www.jf-cmca.jp/contents/010_c_/010_c_{tag}_shiken/{tag.upper()}_1ji_shiken_kaitou.html'
        answers=BeautifulSoup(page.read_bytes(),'html.parser')
        urls=[urljoin(base,a['href']) for a in answers.find_all('a',href=True) if re.search(r'/1j(?:i)?_seikai/|/h\d+_1ji_seikai/',a['href']) and ('teisei' not in a['href'] or '2021g_teisei' in a['href'])]
        if len(urls)!=7:continue
        for i,letter in enumerate('ABCDEFG'):
            q=[urljoin(INDEX,a['href']) for a in html.find_all('a',href=True) if re.search(r'/1ji'+str(year)+r'/'+letter+r'1ji'+str(year)+r'\.pdf$',a['href'],re.I) or re.search(r'/1ji'+str(year)+r'/'+letter+r'1JC'+str(year)+r'\.pdf$',a['href'],re.I)]
            if len(q)!=1:continue
            stem=f'business-sme-{year}-{letter}'
            tasks.append(dict(file=stem+'.json',sourceFile=stem+'.pdf',answerFile=stem+'-answer.pdf',url=q[0],answerUrl=urls[i],examId='sme-consultant',year=str(year),subject=SUBJECTS[i],term='第1次試験',localOnly=True))
    def download(t):
        try:t['sources']=[b.fetch.fetch(t['url'],t['sourceFile']),b.fetch.fetch(t['answerUrl'],t['answerFile'])]
        except Exception as e:t['downloadError']=str(e)
        return t
    with ThreadPoolExecutor(max_workers=6) as pool:tasks=list(pool.map(download,tasks))
    (SRC/'business-discovery.json').write_bytes(b.ipa.encode(tasks));return tasks

def acquire_cases():
    base='https://www.jf-cmca.jp/contents/010_c_/001_shiken_kakokekka_syusi.html'
    index=BeautifulSoup((SRC/'business-sme-intent-index.html').read_bytes(),'html.parser')
    papers=BeautifulSoup((SRC/'business-sme-index.html').read_bytes().decode('cp932'),'html.parser');tasks=[]
    for year in range(2007,2026):
        tag=f'h{year-1988:02}' if year<=2019 else f'r{year-2018:02}'
        links=[urljoin(base,a['href']) for a in index.find_all('a',href=True) if f'010_c_{tag}_shiken' in a['href']]
        assert len(links)==1
        name=f'business-intent-{year}.html';b.fetch.fetch(links[0],name)
        html=BeautifulSoup((SRC/name).read_bytes(),'html.parser')
        intents=[urljoin(links[0],a['href']) for a in html.find_all('a',href=True) if '.pdf' in a['href']]
        if len(intents)==1:intents*=4
        if len(intents)!=4:continue
        for i,letter in enumerate('ABCD'):
            urls=[urljoin(INDEX,a['href']) for a in papers.find_all('a',href=True) if re.search(r'/2ji'+str(year)+r'/'+letter+r'2ji?'+str(year)+r'\.pdf$',a['href'],re.I)]
            assert len(urls)==1
            stem=f'business-sme-case-{year}-{i+1}'
            t=dict(file=stem+'.json',sourceFile=stem+'.pdf',answerFile=stem+'-intent.pdf',url=urls[0],answerUrl=intents[i],examId='sme-consultant',year=str(year),subject=f'事例{i+1}',term='第2次試験',localOnly=True,kind='case')
            tasks.append(t)
    def download(t):
        try:t['sources']=[b.fetch.fetch(t['url'],t['sourceFile']),b.fetch.fetch(t['answerUrl'],t['answerFile'])]
        except Exception as e:t['downloadError']=str(e)
        return t
    with ThreadPoolExecutor(max_workers=6) as pool:tasks=list(pool.map(download,tasks))
    (SRC/'business-case-discovery.json').write_bytes(b.ipa.encode(tasks));return tasks

def keys(doc):
    result={};number=None
    for page in doc:
        lines=b.native_lines(page)
        headers=sorted([box[0] for text,box in lines if text=='問題'])
        assert headers
        for i,x in enumerate(headers):
            column=[(text,box) for text,box in lines if x-35<=box[0]<(headers[i+1]-35 if i+1<len(headers) else page.rect.width)]
            for text,box in column:
                m=re.fullmatch(r'第\s*(\d+)\s*問',text)
                if m:number=int(m[1])
                if text not in list('アイウエオカキ') or number is None:continue
                sub=[t for t,r in column if abs(r[1]-box[1])<2 and re.fullmatch(r'設問\s*\d+',t)]
                key=str(number)+(('-'+re.search(r'\d+',sub[0])[0]) if sub else '')
                assert key not in result,key
                result[key]='アイウエオカキ'.index(text)
    assert result
    return result

def prepare(t):
    if t.get('downloadError'):return {**t,'status':'pending-review','reason':t['downloadError']}
    try:
        with fitz.open(SRC/t['sourceFile']) as doc,fitz.open(SRC/t['answerFile']) as answer:
            if t.get('kind')=='case':return case(t,doc,answer)
            if int(t['year'])<=2017 or t['sourceFile']=='business-sme-2023-D.pdf':return historical(t,doc,answer)
            answers=keys(answer);starts=[]
            for pn,page in enumerate(doc):
                for text,box in b.native_lines(page):
                    m=re.fullmatch(r'第\s*(\d+)\s*問',text)
                    if m:starts.append((int(m[1]),pn,box[1]))
            assert starts and len({n for n,p,y in starts})==len(starts)
            assert [n for n,p,y in starts]==list(range(1,len(starts)+1))
            rows=[];evidence=[];excluded=[];cache={};stem=Path(t['file']).stem
            for i,(number,pn,y) in enumerate(starts):
                nextp=starts[i+1][1] if i+1<len(starts) else len(doc)
                end=nextp if i+1<len(starts) and nextp==pn else nextp-1
                pages=list(range(pn,end+1));assert pages
                text='\n'.join(doc[p].get_text(clip=fitz.Rect(0,y-1 if p==pn else 0,doc[p].rect.width,
                     starts[i+1][2]-1 if i+1<len(starts) and p==starts[i+1][1] else doc[p].rect.height)) for p in pages)
                matching=[k for k in answers if k.split('-')[0]==str(number)]
                if not matching:excluded.append(dict(number=str(number),reason='単一の公式正解が取得できない（採点変更等）'))
                for key in matching:
                    value=answers[key]
                    section=norm(text)
                    if '-' in key:
                        parts=re.split(r'\(?設問\s*(\d+)\)?',section)
                        found=[parts[j+1] for j in range(1,len(parts)-1,2) if parts[j]==key.split('-')[1]]
                        if len(found)!=1:
                            excluded.append(dict(number=key,reason='枝問区切り未確認'));continue
                        section=found[0]
                    labels=[x for x in 'アイウエオカキ' if re.search(r'(?:^|\n)\s*'+x+r'\s',section)]
                    if labels!=list('アイウエオカキ')[:len(labels)] or len(labels)<2 or value>=len(labels):
                        excluded.append(dict(number=key,reason='選択肢記号の連続性未確認'));continue
                    images,records=zip(*(b.nonit.picture(doc,p,stem,cache) for p in pages))
                    title=f'{t["year"]}年度 中小企業診断士 {t["subject"]} 第{number}問'+(' 設問'+key.split('-')[1] if '-' in key else '')
                    q=dict(id=stem+'-q'+key,examId=t['examId'],year=t['year'],term=t['term'],subject=t['subject'],type='single',category='過去問',topic=title,prompt=title+'\n原本画像の指定問題・設問に解答してください。共通本文・図表も画像で確認できます。',options=labels,answer=value,images=list(images),sourceUrl=t['url'],source='出典：日本中小企業診断士協会連合会。公式PDFの原本ページ画像。個人学習用。',explanation='公式正解：'+labels[value]+'。理由解説は未収録。実施当時の制度を前提とします。',explanationSource='公式正解・配点')
                    rows.append(q);evidence.append(dict(id=q['id'],number=key,answer=value,images=list(records)))
            assert rows
            return b.nonit.finish(t,rows,evidence,excluded)
    except Exception as e:return {**t,'status':'pending-review','reason':str(e) or type(e).__name__}

def case(t,doc,answer):
    expected=sorted({int(n) for page in answer for n in re.findall(r'第\s*(\d+)\s*問',norm(page.get_text()))})
    assert expected==list(range(1,len(expected)+1)) and 3<=len(expected)<=6
    numbers=[];glyphs={}
    for page in doc:
        for text,box in b.native_lines(page):
            m=re.match(r'^第([^次]{1,4}?)問',text,re.S)
            if m:
                glyph=m[1].replace(' ','')
                if glyph.isdigit():value=int(glyph)
                else:
                    assert len(glyph)==1 and ord(glyph)<32,repr(glyph)
                    value=glyphs.get(glyph,len(numbers)+1)
                if numbers and numbers[-1]==value and ('設問' in text or '続' in text):continue
                assert value==len(numbers)+1 and glyphs.get(glyph,value)==value
                glyphs[glyph]=value;numbers.append(value)
    assert numbers==expected
    stem=Path(t['file']).stem
    images,records=zip(*(b.nonit.picture(doc,p,stem,{}) for p in range(len(doc))))
    solutions,srecords=zip(*(b.nonit.picture(answer,p,stem+'-intent',{}) for p in range(len(answer))))
    rows=[];evidence=[]
    for number in numbers:
        title=f'{t["year"]}年度 中小企業診断士 第2次試験 {t["subject"]} 第{number}問（枝問を含む）'
        q=dict(id=stem+'-q'+str(number),examId=t['examId'],year=t['year'],term=t['term'],subject=t['subject'],type='written',category='過去問',topic=title,prompt=title+'\n原本画像の事例本文を読み、指定問題と枝問に解答してください。解答後は出題趣旨を確認してください。',options=[],answer=None,images=list(images),solutionImages=list(solutions),modelAnswer='公式出題趣旨画像の該当問題を参照してください。模範解答・配点基準は未公表のため、自動採点できません。',sourceUrl=t['url'],source='出典：日本中小企業診断士協会連合会。公式問題・出題趣旨の原本ページ画像。個人学習用。',explanation='解答後に公式出題趣旨を確認してください。模範解答・詳細採点基準・理由解説は未収録。',explanationSource='公式出題趣旨（模範解答ではありません）')
        rows.append(q);evidence.append(dict(id=q['id'],number=str(number),answer=None,images=list(records),solutionImages=list(srecords)))
    return b.nonit.finish({**t,'verificationLabel':'公式問題番号の連続性・事例全文と出題趣旨画像の画素一致（記述・自己確認）'},rows,evidence,[])

def historical(t,doc,answer):
    """Keep legacy broken character maps as pixels; infer only consecutive headings."""
    numbers={int(m[1]) for page in answer for text,box in b.native_lines(page) if (m:=re.fullmatch(r'第\s*(\d+)\s*問',text))}
    if t['sourceFile']=='business-sme-2023-D.pdf':
        # Visually reviewed 2023 corrected scan: questions 1–40; 14/31 all correct.
        assert b.ipa.sha((SRC/t['answerFile']).read_bytes())=='a9a7f1044251c503cbfea6e6acb8e008f6733a96c8190a80352f2ab8ebcf749e'
        numbers=set(range(1,41))
    assert numbers==set(range(1,max(numbers)+1))
    starts=[];mapping={}
    for pn,page in enumerate(doc):
        for text,box in b.native_lines(page):
            m=re.fullmatch(r'第(.+?)問',text,re.S)
            if not m:continue
            number=len(starts)+1;glyph=m[1].replace(' ','');digits=str(number)
            assert len(glyph)==len(digits),(number,repr(glyph))
            for char,digit in zip(glyph,digits):
                assert mapping.get(char,digit)==digit
                mapping[char]=digit
            starts.append((number,pn,box[1]))
    assert len(starts)==len(numbers) and set(mapping.values())==set('0123456789')
    stem=Path(t['file']).stem;cache={};acache={};rows=[];evidence=[]
    solutions,srecords=zip(*(b.nonit.picture(answer,p,stem+'-answer',acache) for p in range(len(answer))))
    for i,(number,pn,y) in enumerate(starts):
        if t['sourceFile']=='business-sme-2023-D.pdf' and number in [14,31]:continue
        nextp=starts[i+1][1] if i+1<len(starts) else len(doc);end=nextp if nextp==pn else nextp-1
        images,records=zip(*(b.nonit.picture(doc,p,stem,cache) for p in range(pn,end+1)))
        title=f'{t["year"]}年度 中小企業診断士 {t["subject"]} 第{number}問（枝問を含む）'
        q=dict(id=stem+'-q'+str(number),examId=t['examId'],year=t['year'],term=t['term'],subject=t['subject'],type='written',category='過去問',topic=title,prompt=title+'\n原本画像のこの問題番号と枝問すべてに解答し、公式正解表で自己採点してください。',options=[],answer=None,images=list(images),solutionImages=list(solutions),modelAnswer=f'公式正解表の第{number}問と各枝問を参照してください。',sourceUrl=t['url'],source='出典：日本中小企業診断士協会連合会。公式PDF原本ページ画像。個人学習用。',explanation='原本の公式正解表を参照してください。理由解説は未収録。実施当時の制度を前提とします。',explanationSource='公式正解・配点（画像・自己採点）')
        rows.append(q);evidence.append(dict(id=q['id'],number=str(number),answer=None,images=list(records),solutionImages=list(srecords)))
    excluded=[dict(number=str(n),reason='公式訂正：全員正解') for n in [14,31]] if t['sourceFile']=='business-sme-2023-D.pdf' else []
    return b.nonit.finish({**t,'verificationLabel':'公式正解表の連続番号・問題見出しの一貫した文字対応・原本画像の画素一致（枝問は一括自己採点）'},rows,evidence,excluded)

def examples():
    packs=[]
    for code,prefix in [('HS','secretary'),('BB','business-doc'),('BZ','business-manner'),('SV','service')]:
        file=f'business-{code}-example.html';raw=(SRC/file).read_bytes();url=f'https://jitsumu-ginou-kentei.jp/{code}/example'
        html=BeautifulSoup(raw,'html.parser')
        for group in html.select('div.anchor'):
            grade={'3rd-grade':'3','2nd-grade':'2','pre-1st-grade':'-pre1','1st-grade':'1'}.get(group.get('id'))
            if not grade:continue
            stem=f'business-{prefix}{grade}-examples';rows=[];evidence=[];excluded=[]
            for i,dl in enumerate(group.select('dl.q-a'),1):
                if dl.find('img'):
                    excluded.append(dict(number=str(i),reason='図表画像の個別確認が必要'));continue
                dt,dd=dl.select_one('dt'),dl.select_one('dd')
                for button in dt.select('.button'):button.decompose()
                for u in dt.select('u'):u.string='【下線：'+u.get_text()+'】'
                prompt=norm(dt.get_text('\n',strip=True));solution=norm(dd.get_text('\n',strip=True))
                parts=re.split(r'(?:^|\n)\s*(?:\((\d+)\)|(\d+)\))\s*',prompt)
                labels=[];options=[]
                for j in range(1,len(parts)-2,3):labels.append(int(parts[j] or parts[j+1]));options.append(parts[j+2].strip())
                key=re.match(r'^\s*(?:\((\d+)\)|(\d+)\))',solution)
                single=labels==list(range(1,len(labels)+1)) and len(labels)>=2 and key is not None
                answer=int(key[1] or key[2])-1 if single else None
                assert not single or 0<=answer<len(options)
                q=dict(id=stem+'-q'+str(i),examId=prefix+grade,year='',term='公式問題例',subject='公式問題例',type='single' if single else 'written',category='公式問題例',topic=dl.find_previous('h3').get_text(strip=True),prompt=parts[0].strip() if single else prompt,options=options if single else [],answer=answer,images=[],sourceUrl=url,source='出典：実務技能検定協会 公式問題例。実施過去問の年度は未公表。個人学習用。',explanation=solution,explanationSource='公式解答・解説')
                if not single:q['modelAnswer']=solution
                rows.append(q);evidence.append(dict(id=q['id'],number=str(i),answer=answer,images=[]))
            if rows:packs.append(b.nonit.finish(dict(file=stem+'.json',examId=prefix+grade,year='',term='公式問題例',subject='公式問題例',url=url,localOnly=True,sources=[dict(file=file,url=url,sha256=b.ipa.sha(raw),bytes=len(raw))],verificationLabel='公式HTMLの問題・選択肢・解答照合（記述は自己採点）'),rows,evidence,excluded))
    return packs

def commercial_examples():
    packs=[];file='business-manager-example.html';url='https://kentei.tokyo-cci.or.jp/bijimane/support/challenge/example.html'
    raw=(SRC/file).read_bytes();html=BeautifulSoup(raw,'html.parser');rows=[];evidence=[]
    for i,block in enumerate(html.select('.example-block'),1):
        answer=block.find_next(class_='answer__text').get_text(strip=True);value='①②③④⑤⑥⑦'.index(answer)
        options=[li.get_text(strip=True)[1:] for li in block.select('li')];assert 0<=value<len(options)
        q=dict(id=f'business-manager-examples-q{i}',examId='business-manager',year='',term='公式問題例',subject='公式問題例',type='single',category='公式問題例',topic=f'ビジネスマネジャー 公式問題例{i}',prompt=block.select_one('.example__title').get_text(strip=True),options=options,answer=value,images=[],sourceUrl=url,source='出典：東京商工会議所 公式試験問題例。個人学習用。',explanation='公式解答：'+answer+'。理由解説は未収録。',explanationSource='公式解答')
        rows.append(q);evidence.append(dict(id=q['id'],number=str(i),answer=value,images=[]))
    packs.append(b.nonit.finish(dict(file='business-manager-examples.json',examId='business-manager',year='',term='公式問題例',subject='公式問題例',url=url,localOnly=True,sources=[dict(file=file,url=url,sha256=b.ipa.sha(raw),bytes=len(raw))],verificationLabel='公式HTMLの問題・選択肢・解答照合'),rows,evidence,[]))
    file='business-retail-leaflet.pdf';url='https://www.kentei.ne.jp/wp/wp-content/uploads/2026/02/2026RML.pdf';answerfile='business-retail-answers.html';answerurl='https://www.kentei.ne.jp/retailsales/answers'
    html=BeautifulSoup((SRC/answerfile).read_bytes(),'html.parser')
    with fitz.open(SRC/file) as doc:
        images,records=b.nonit.picture(doc,1,'business-retail-leaflet',{})
        for grade in [1,2,3]:
            heading=next(h for h in html.select('h2') if norm(h.get_text(strip=True))==str(grade)+'級')
            values=[]
            for n in heading.next_siblings:
                if getattr(n,'name',None)=='h2':break
                if getattr(n,'name',None)=='p' and n.find('strong'):values.append(norm(n.find('strong').get_text(strip=True)))
            assert len(values)==2
            stem=f'business-retail{grade}-examples';rows=[];evidence=[]
            for i,value in enumerate(values,1):
                title=f'販売士{grade}級 リーフレット公式問題例 第{i}問'
                q=dict(id=stem+'-q'+str(i),examId='retail'+str(grade),year='2026',term='公式問題例（リーフレット公開年）',subject='公式問題例',type='written',category='公式問題例',topic=title,prompt=title+'\n画像の指定した級・問題番号だけに解答し、公式解答で自己採点してください。',options=[],answer=None,modelAnswer=value,images=[images],sourceUrl=url,source='出典：日本商工会議所 2026年リーフレット。個人学習用。年度はリーフレットの公開年。',explanation='公式解答：'+value,explanationSource='公式リーフレット掲載サンプル問題の解答')
                rows.append(q);evidence.append(dict(id=q['id'],number=str(i),answer=None,images=[records]))
            sources=[dict(file=f,url=u,sha256=b.ipa.sha((SRC/f).read_bytes()),bytes=(SRC/f).stat().st_size) for f,u in [(file,url),(answerfile,answerurl)]]
            packs.append(b.nonit.finish(dict(file=stem+'.json',examId='retail'+str(grade),year='2026',term='公式問題例（リーフレット公開年）',subject='公式問題例',url=url,sourceFile=file,localOnly=True,sources=sources,verificationLabel='公式リーフレット問題と公式HTML解答の対応・原本画像画素一致（自己採点）'),rows,evidence,[]))
    return packs

def main():
    sys.stdout.reconfigure(encoding='utf-8');(OUT/'assets').mkdir(parents=True,exist_ok=True)
    tasks=acquire() if '--fetch' in sys.argv else json.loads((SRC/'business-discovery.json').read_bytes())
    if '--fetch-cases' in sys.argv:tasks+=acquire_cases()
    elif (SRC/'business-case-discovery.json').exists():tasks+=json.loads((SRC/'business-case-discovery.json').read_bytes())
    report={'packs':[],'discovery':[INDEX,'https://shigyo-get.com/shindanshi-kakomon-muryou-download/','https://github.com/toru830/shindanshi']}
    for i,t in enumerate(tasks):
        p=prepare(t);report['packs'].append(p);print(i+1,len(tasks),p['file'],p['status'],p.get('count',p.get('reason')),flush=True)
        (OUT/'business-report.json').write_bytes(b.ipa.encode(report))
    report['packs'].extend(examples()+commercial_examples());(OUT/'business-report.json').write_bytes(b.ipa.encode(report))
if __name__=='__main__':main()
