"""Prepare only released originals with unambiguous official answers."""
import collections, concurrent.futures, importlib.util, json, re, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('archive_prepare',ROOT/'scripts/prepare-github-material.py')
ipa=importlib.util.module_from_spec(spec);spec.loader.exec_module(ipa)
fitz=ipa.fitz;SRC=ipa.SRC;OUT=ipa.OUT;norm=ipa.norm
NAMES={'electrician1':'第一種電気工事士','electrician2':'第二種電気工事士','denken3':'第三種電気主任技術者',
       'doctor':'医師国家試験','dentist':'歯科医師国家試験','pharmacist':'薬剤師国家試験'}
def tidy(s):return re.sub(r'\s+','',norm(s))
def at_row(words,label,right):
    return sorted((w for w in words if abs((w[1]+w[3]-label[1]-label[3])/2)<3 and label[2]<w[0]<right),key=lambda w:w[0])

def official_keys(doc,task):
    """Read answer cells by their row and column, including multiple selections."""
    keys={};provider=task['provider']
    for page in doc:
        words=page.get_text('words')
        if provider=='ECEE' and task['examId']=='denken3':
            anchors=sorted(w[0] for w in words if tidy(w[4])=='問1')
            assert len(anchors)==4,'Expected four ECEE subject columns'
            column=['理論','電力','機械','法規'].index(task['subject']);left=anchors[column]-12;right=anchors[column+1]-12 if column<3 else page.rect.width
            labels=sorted((w for w in words if left<=w[0]<right and re.fullmatch(r'(?:問\d+(?:\([ab]\))?|\(b\))',tidy(w[4]))),key=lambda w:w[1])
            previous_a=None
            for w in labels:
                m=re.fullmatch(r'問(\d+)(?:\(([ab])\))?',tidy(w[4]))
                cells=at_row(words,w,right);assert cells and re.fullmatch('[1-5]',tidy(cells[0][4]))
                # The displayed (b) row belongs to the immediately preceding (a).
                # Some old PDFs retain an incorrect hidden number in that row's text layer.
                if m is None or m[2]=='b':
                    assert previous_a and 0<w[1]-previous_a[1]<30,'Unpaired ECEE (b) row'
                    key=previous_a[0]+'b';previous_a=None
                else:
                    key=m[1]+(m[2] or '');previous_a=(m[1],w[1]) if m[2]=='a' else None
                assert key not in keys,'Repeated ECEE answer label'
                keys[key]=int(tidy(cells[0][4]))-1
        elif provider=='ECEE':
            for w in words:
                if not re.fullmatch(r'\d+',tidy(w[4])):continue
                n=int(tidy(w[4]));cells=at_row(words,w,w[2]+65)
                if cells and tidy(cells[0][4]) in ['イ','ロ','ハ','ニ']:
                    assert str(n) not in keys;keys[str(n)]='イロハニ'.index(tidy(cells[0][4]))
            assert set(keys)==set(map(str,range(1,51))),'Expected 50 official ECEE answers'
        elif provider=='MHLW':
            labels=[w for w in words if re.fullmatch('[A-F][0-9]{3}',tidy(w[4]))]
            columns=sorted(set(round(w[0]) for w in labels))
            for w in labels:
                right=next((x-3 for x in columns if x>w[0]+15),page.rect.width)
                cells=[tidy(v[4]) for v in at_row(words,w,right) if tidy(v[4])]
                # Separate answer cells are alternative accepted answers, not multi-select.
                keys[tidy(w[4])]=[ord(c)-ord('A') for c in cells[0]] if len(cells)==1 and re.fullmatch('[A-F]+',cells[0]) else None
        elif provider=='MHLW-PHARM':
            headers=[w for w in words if tidy(w[4])=='問No']
            for header in headers:
                right=next((w[0]-2 for w in headers if w[0]>header[0]+30),page.rect.width)
                labels=[w for w in words if header[0]-2<=w[0]<header[2]+3 and w[1]>header[3] and re.fullmatch(r'\d+',tidy(w[4]))]
                for w in labels:
                    n=int(tidy(w[4]));cells=at_row(words,w,right)
                    answers=[int(tidy(c[4]))-1 for c in cells if c[0]>header[2]+25 and re.fullmatch('[1-9]',tidy(c[4]))]
                    assert str(n) not in keys,'Repeated pharmacist key'
                    keys[str(n)]=answers or None
        else:raise ValueError(provider)
    if provider=='ECEE' and task['examId']=='denken3':
        parents={int(re.match(r'\d+',k)[0]) for k in keys}
        assert parents==set(range(1,max(parents)+1)),'Incomplete ECEE answer numbers'
        for n in parents:
            assert {k for k in keys if re.fullmatch(str(n)+r'[ab]?',k)} in ({str(n)},{str(n)+'a',str(n)+'b'}),'Incomplete ECEE subquestion pair'
    assert keys,'No official answers'
    return keys

def question_starts(doc,task,ocr=False):
    starts=[];anchor=None
    for pn,page in enumerate(doc):
        if pn<3 and task['provider']=='ECEE' and task['examId']=='denken3':continue
        if pn==0 and task['provider']=='MHLW-PHARM':continue
        if ocr and pn<(4 if task['examId']=='electrician2' else 2):continue
        data=ipa.layout(doc,pn,force_ocr=True)[0] if ocr else page.get_text('dict',flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)
        for line in ipa.lines(data):
            value=norm(''.join(s['text'] for s in line['spans'])).strip();x,y=line['bbox'][:2]
            if not 35<y<page.rect.height-40:continue
            if task['examId']=='denken3':m=re.match(r'^問\s*(\d+)(?:\s|$)',value)
            elif task['provider']=='MHLW-PHARM':m=re.match(r'^問\s*(\d+)(?:\s|[（(]|$)',value)
            else:m=re.match(r'^(\d+)(?:[.．]|\s|$)',value) if x<page.rect.width*.14 else None
            if m:
                first=next((s for s in line['spans'] if s['text'].strip()),None)
                if task['examId'] in ('electrician1','electrician2') and not ocr and not (first and norm(first['text']).strip()==m[1] and first['font'].startswith('CenturyOldstyle') and 9<first['size']<11):continue
                if task['examId'] in ('electrician1','electrician2'):
                    if not 1<=int(m[1])<=50:continue
                    if anchor is None:
                        if int(m[1])!=1 or not ocr and not re.fullmatch(r'\d+[.．]?',value):continue
                        anchor=x
                    # Body continuations are indented; photo questions can move 10pt left.
                    if not anchor-15<=x<=anchor+12:continue
                    if not ocr and int(m[1])<=30 and not re.fullmatch(r'\d+[.．]?',value):continue
                starts.append((int(m[1]),pn,y))
    starts.sort(key=lambda v:(v[1],v[2]))
    if not ocr and task['examId'] in ('electrician1','electrician2') and [n for n,p,y in starts]!=list(range(1,51)):
        return question_starts(doc,task,ocr=True)
    return starts

def picture(doc,pn,stem,cache):
    if pn not in cache:
        page=doc[pn];file=f'{stem}-p{pn+1:03}.png';path=OUT/'assets'/file
        if not path.exists():page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),alpha=False).save(path)
        cache[pn]=({'src':'assets/github-material/'+file,'alt':f'公式問題原本 {pn+1}ページ'},
                   {'file':file,'page':pn,'rect':list(page.rect),'sha256':ipa.sha(path.read_bytes())})
    return cache[pn]

def pharm_options(doc,starts,i,data):
    number,pn,y=starts[i];ep,ey=starts[i+1][1:] if i+1<len(starts) else (len(doc)-1,doc[-1].rect.height)
    labels=set()
    for p in range(pn,ep+1):
        for line in data[p]:
            if p==pn and line['bbox'][1]<=y or p==ep and line['bbox'][1]>=ey:continue
            for span in line['spans']:
                value=norm(span['text']).strip()
                if span['font']=='FutoGoB101Pr6N-Bold' and re.fullmatch('[1-9]',value):labels.add(int(value))
    return sorted(labels)

def medical_pages(page_texts,item):
    text=''.join(page_texts);ends=[];total=0
    for part in page_texts:total+=len(part);ends.append(total)
    page_at=lambda position:next(i for i,end in enumerate(ends) if position<end)
    body=tidy(item['problem_text']);assert body and 2<=len(item['choices'])<=26,'Invalid medical question'
    matches=[];begin=0
    while (begin:=text.find(body,begin))>=0:
        cursor=begin+len(body);valid=True
        for choice in item['choices']:
            found=text.find(tidy(choice),cursor)
            if found<0:valid=False;break
            cursor=found+len(tidy(choice))
        if valid and page_at(cursor-1)-page_at(begin)<=2:matches.append((begin,cursor))
        begin+=len(body)
    assert len(matches)==1,'Medical question/choice location is ambiguous'
    begin,end=matches[0];first=page_at(begin);last=page_at(end-1)
    context=text.rfind('次の文を読み',0,begin)
    if context>=0 and first-page_at(context)<=5:first=page_at(context)
    elif re.match(r'この(?:患者|症例|疾患)',item['problem_text']):first=max(1,first-3)
    return list(range(first,last+1))

def prepare(task):
    result={**task,'questions':[]}
    if task['status']!='downloaded':return result
    try:
        doc=fitz.open(SRC/task['sourceFile']);keys=official_keys(fitz.open(SRC/task['answerFile']),task)
        starts=question_starts(doc,task);numbers=[n for n,_,_ in starts]
        if task['provider']=='ECEE':
            expected=max(int(re.match(r'\d+',k)[0]) for k in keys)
            assert numbers==list(range(1,expected+1)),('Question sequence',numbers,expected)
        elif task['provider']=='MHLW-PHARM':
            assert numbers and len(numbers)==len(set(numbers)) and numbers==list(range(min(numbers),max(numbers)+1)),('Question sequence',numbers)
        else:
            # Medical PDFs with broken character maps cannot prove a text-only import.
            data=[json.loads(line) for line in (SRC/task['dataset']).read_text(encoding='utf-8').splitlines() if line.strip()]
            selected=[q for q in data if q['problem_id'].startswith(str(task['examNumber'])+task['section'])]
            assert selected,'Missing GitHub discovery questions'
            page_texts=[tidy(p.get_text()) for p in doc];text=''.join(page_texts);rows=[];evidence=[];excluded=[];cache={}
            for item in selected:
                number=task['section']+f'{int(item["problem_id"].split(task["section"])[1]):03}'
                answer=keys.get(number)
                if not item.get('text_only') or answer is None:
                    excluded.append({'id':item['problem_id'],'reason':'image-dependent or deleted/alternative official answer'});continue
                if answer!=[ord(c.lower())-ord('a') for c in item['answer']]:
                    excluded.append({'id':item['problem_id'],'reason':'GitHub answer differs from official key'});continue
                # The full question and every choice must occur verbatim after whitespace/NFKC normalization.
                if not all(tidy(value) in text for value in [item['problem_text'],*item['choices']]):
                    excluded.append({'id':item['problem_id'],'reason':'native official text does not match GitHub transcription'});continue
                try:pages=medical_pages(page_texts,item)
                except AssertionError as e:
                    excluded.append({'id':item['problem_id'],'reason':str(e)});continue
                images,records=zip(*(picture(doc,p,Path(task['file']).stem,cache) for p in pages))
                title=f'{task["year"]}年度 {NAMES[task["examId"]]} {task["term"]} {number}'
                q=dict(id=Path(task['file']).stem+'-q'+number,examId=task['examId'],type='multiple' if len(answer)>1 else 'single',
                       year=task['year'],term=task['term'],subject=task['subject'],category='過去問',topic=title,prompt=title+'\n'+item['problem_text'],
                       options=item['choices'],answer=answer if len(answer)>1 else answer[0],images=list(images),sourceUrl=task['url'],
                       source='出典：厚生労働省 '+title+'。公式PDF本文と照合した文字起こしと原本ページ画像を加工して作成（PDL1.0）。連問の共通症例は画像で確認してください。厚生労働省作成のアプリではありません。',
                       explanation='公式正答：'+','.join(chr(97+a) for a in answer)+'。理由解説は未収録です。実施当時の医学・制度を前提とします。',explanationSource='厚生労働省公式正答（理由解説なし）')
                rows.append(q);evidence.append(dict(id=q['id'],number=number,answer=q['answer'],images=list(records),originalText=item['problem_text'],choices=item['choices']))
            assert rows,'No verified text-only questions'
            return finish(result,rows,evidence,excluded)
        cache={};rows=[];evidence=[];excluded=[];stem=Path(task['file']).stem;groups=[];page_lines=[];option_review={}
        if task['provider']=='MHLW-PHARM':
            page_lines=[ipa.lines(p.get_text('dict',flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)) for p in doc]
            review=SRC/'pharmacist-option-counts-verified.json'
            if review.exists():option_review={r['number']:r for r in json.loads(review.read_bytes())}
            for pn,page in enumerate(doc):
                if not pn:continue
                for line in ipa.lines(page.get_text('dict',flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)):
                    value=norm(''.join(s['text'] for s in line['spans'])).strip()
                    m=re.match(r'^問\s*(\d+)\s*[-－−]\s*(\d+)',value)
                    if m:groups.append((int(m[1]),int(m[2]),pn))
        # Whole source pages preserve equations and common figures; share each page asset.
        # ponytail: page-level images also show adjacent questions; crop only if that impairs study.
        shared=[]
        if task['examId'] in ('electrician1','electrician2'):
            shared=[pn for pn in range(starts[0][1],len(doc)) if not any(p==pn for _,p,_ in starts)
                    and (doc[pn].get_images() or doc[pn].get_drawings() or len(doc[pn].get_text().strip())>100)]
            shared.extend(pn for pn in range(starts[0][1],len(doc)) if '配線図' in doc[pn].get_text() and '注意' in doc[pn].get_text())
            if len(doc[starts[0][1]].get_text().strip())<100:
                shared.extend(p for n,p,y in starts if n==(41 if task['examId']=='electrician1' else 31))
            shared=sorted(set(shared))
        for i,(number,pn,y) in enumerate(starts):
            ep=starts[i+1][1] if i+1<len(starts) else len(doc)-1
            if i+1<len(starts) and ep>pn:ep-=1
            context=min([pn]+[p for a,b,p in groups if a<=number<=b and p<=pn])
            pages=sorted(set(range(context,ep+1))|set(shared));assert len(pages)<=30
            matching=[k for k in keys if re.fullmatch(str(number)+r'[ab]?',k)]
            for key in matching:
                answer=keys[key]
                if answer is None or task['provider']=='MHLW-PHARM' and number in [92,199,220,221,316]:
                    excluded.append({'number':key,'reason':'deleted question, official erratum, or alternative/unsupported official key'});continue
                images,records=zip(*(picture(doc,p,stem,cache) for p in pages))
                title=f'{task["year"]}年度 {NAMES[task["examId"]]} {task["term"]} {task["subject"]} 問{key}'
                multi=isinstance(answer,list) and len(answer)>1
                labels=list('イロハニ') if task['examId'].startswith('electrician') else ['1','2','3','4','5']
                if task['provider']=='MHLW-PHARM':
                    nums=pharm_options(doc,starts,i,page_lines)
                    if not nums:
                        checked=option_review.get(number)
                        if not checked or checked['sourceFile']!=task['sourceFile'] or checked['sha256']!=ipa.sha((SRC/task['sourceFile']).read_bytes()):
                            excluded.append({'number':key,'reason':'image option count needs visual verification'});continue
                        nums=list(range(1,checked['count']+1))
                    assert nums==list(range(1,max(nums)+1)) and 2<=len(nums)<=9,'Non-contiguous pharmacist options'
                    labels=list(map(str,nums))
                value=answer if multi or not isinstance(answer,list) else answer[0]
                q=dict(id=stem+'-q'+key,examId=task['examId'],type='multiple' if multi else 'single',year=task['year'],term=task['term'],
                       subject=task['subject'],category='過去問',topic=title,prompt=title+'\n原本ページのこの問題番号だけに解答してください。選択肢・図表・共通の注意事項は画像で確認できます。',
                       options=labels,answer=value,images=list(images),sourceUrl=task['url'],
                       source='出典：'+('電気技術者試験センター ' if task['provider']=='ECEE' else '厚生労働省 ')+title+'。原本PDFをページ画像に加工（本文・図表は変更なし）。'+('著作権：一般財団法人電気技術者試験センター。' if task['provider']=='ECEE' else 'PDL1.0。厚生労働省作成のアプリではありません。'),
                       explanation='公式正答：'+','.join(labels[a] for a in (answer if isinstance(answer,list) else [answer]))+'。理由解説は未収録です。実施当時の制度・規格を前提とします。',
                       explanationSource='公式解答（理由解説なし）')
                rows.append(q);evidence.append(dict(id=q['id'],number=key,answer=q['answer'],images=list(records)))
        assert rows,'No verified questions'
        return finish(result,rows,evidence,excluded)
    except Exception as error:return {**result,'status':'pending-review','reason':str(error)}

def finish(result,rows,evidence,excluded):
    raw=ipa.encode(rows);(OUT/result['file']).write_bytes(raw)
    return {**result,'status':'prepared','count':len(rows),'sha256':ipa.sha(raw),'questions':evidence,'excludedQuestions':excluded}

def main():
    sys.stdout.reconfigure(encoding='utf-8');(OUT/'assets').mkdir(parents=True,exist_ok=True)
    baseline=SRC/'nonit-baseline.json'
    if not baseline.exists():
        m=json.loads((ROOT/'build/private/manifest.json').read_bytes())
        baseline.write_bytes(ipa.encode({'manifest':m,'packs':{p['id']:p['sha256'] for p in m['packs']}}))
    discovery=json.loads((SRC/'nonit-discovery.json').read_bytes());report={'discovery':discovery['discovery'],'terms':discovery['terms'],'packs':[]}
    with concurrent.futures.ProcessPoolExecutor(max_workers=4) as pool:
        for i,result in enumerate(pool.map(prepare,discovery['tasks'])):
            report['packs'].append(result)
            print(i+1,'/',len(discovery['tasks']),result['examId'],result['year'],result['subject'],result['status'],result.get('count',result.get('reason','')),flush=True)
            (OUT/'nonit-report.json').write_bytes(ipa.encode(report))
    print('Non-IT added:',sum(p.get('count',0) for p in report['packs']),'statuses:',dict(collections.Counter(p['status'] for p in report['packs'])),flush=True)

if __name__=='__main__':main()
