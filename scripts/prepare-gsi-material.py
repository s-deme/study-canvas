"""Follow a GitHub surveying question archive to its official GSI originals."""
import concurrent.futures, importlib.util, json, os, re, sys
from pathlib import Path
from urllib.parse import urljoin

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('ipa_archive',ROOT/'scripts/prepare-github-material.py')
ipa=importlib.util.module_from_spec(spec);spec.loader.exec_module(ipa)
spec=importlib.util.spec_from_file_location('archive_fetch',ROOT/'scripts/fetch-github-material.py')
fetcher=importlib.util.module_from_spec(spec);spec.loader.exec_module(fetcher)
fitz=ipa.fitz;SRC=ipa.SRC;OUT=ipa.OUT

def prepare(task):
    year,exam,question_urls,answer_url=task
    stem=f'gsi-{year}-{exam}'
    result={'examId':exam,'year':str(year),'term':'公開問題','subject':'午前' if exam=='surveyor' else '筆記','file':stem+'.json'}
    try:
        sources=[fetcher.fetch(url,stem+f'-part{i+1}-qs.pdf') for i,url in enumerate(question_urls)]
        answer=fetcher.fetch(answer_url,stem+'-ans.pdf');sources.append(answer)
        ans=fitz.open(SRC/answer['file']);text=ipa.norm('\n'.join(p.get_text() for p in ans))
        keys={int(n):int(a)-1 for n,a in re.findall(r'No\.?\s*(\d+)\s*([1-5])',text)}
        assert sorted(keys)==list(range(1,29)), 'GSI official answer count'
        docs={s['file']:fitz.open(SRC/s['file']) for s in sources[:-1]};pages=[];starts=[];tables=[]
        reviewed=json.loads((SRC/'gsi-function-tables-verified.json').read_text(encoding='utf-8'))
        for source in sources[:-1]:
            for pn,page in enumerate(docs[source['file']]):
                cache=SRC/'ocr'/f'{source["file"]}-{pn}-full.json'
                if cache.exists():data=json.loads(cache.read_text(encoding='utf-8'))
                else:
                    tp=page.get_textpage_ocr(language='jpn+eng',dpi=150,full=True,tessdata=str(ROOT/'build/tessdata'))
                    data=page.get_text('dict',textpage=tp);data['blocks']=[b for b in data['blocks'] if b.get('type')==0]
                    cache.write_bytes(ipa.encode(data))
                index=len(pages);pages.append((source,pn,page,data))
                review=reviewed.get(source['file'])
                if review and review['sha256']==source['sha256'] and review['page']==pn:tables.append(index)
                page_lines=ipa.lines(data)
                cover=pn==0 and source==sources[0] and re.search(r'注意|試験問題|電子計算機',ipa.norm(' '.join(''.join(s['text'] for s in line['spans']) for line in page_lines)))
                for heading in page_lines:
                    if heading['bbox'][1]>100:continue
                    same_row=sorted((line for line in page_lines if abs(line['bbox'][1]-heading['bbox'][1])<4),key=lambda line:line['bbox'][0])
                    row_text=' '.join(ipa.norm(''.join(s['text'] for s in line['spans'])).strip() for line in same_row)
                    if re.fullmatch(r'関\s*数\s*表',row_text):tables.append(index)
                for line in page_lines:
                    value=ipa.norm(''.join(s['text'] for s in line['spans'])).strip()
                    if re.search(r'N[oO0]\s*[.,]?\s*$',value):
                        adjacent=sorted((other for other in page_lines if abs(other['bbox'][1]-line['bbox'][1])<3 and 0<other['bbox'][0]-line['bbox'][2]<25),key=lambda other:other['bbox'][0])
                        value+=' '+ ' '.join(ipa.norm(''.join(s['text'] for s in other['spans'])).strip() for other in adjacent)
                    match=re.search(r'N[oO0]\s*[.,]?\s*(\d+)',value)
                    if match and not cover and line['bbox'][0]<100 and line['bbox'][1]>45:starts.append((int(match[1]),index,line['bbox'][1]))
                    if re.fullmatch(r'関\s*数\s*表',value):tables.append(index)
        assert [n for n,_,_ in starts]==list(range(1,29)), ('GSI question sequence', [n for n,_,_ in starts])
        assert tables,'GSI supplementary function table missing'
        rows=[];evidence=[]
        def picture(index,rect,label):
            source,pn,page,_=pages[index];file=stem+'-'+label+f'-p{index+1}.png';path=OUT/'assets'/file
            page.get_pixmap(matrix=fitz.Matrix(1.5,1.5),clip=rect,alpha=False).save(path)
            return {'src':'assets/github-material/'+file,'alt':label+' 原本画像'}, {'file':file,'sourceFile':source['file'],'page':pn,'rect':list(rect),'sha256':ipa.sha(path.read_bytes())}
        shared=[picture(index,fitz.Rect(0,35,pages[index][2].rect.width,pages[index][2].rect.height-35),'function-table') for index in sorted(set(tables))]
        for i,(number,index,y) in enumerate(starts):
            end,bottom=(starts[i+1][1],starts[i+1][2]-3) if i+1<len(starts) else (min(tables)-1,pages[min(tables)-1][2].rect.height-35)
            images=[];records=[]
            for pi in range(index,end+1):
                if pi in tables:continue
                page=pages[pi][2];top=y-4 if pi==index else 35;stop=bottom if pi==end else page.rect.height-35
                if stop<=top:continue
                image,record=picture(pi,fitz.Rect(0,top,page.rect.width,stop),f'q{number:03}');images.append(image);records.append(record)
            for image,record in shared:images.append(image);records.append(record)
            title=f'{year}年度 '+('測量士' if exam=='surveyor' else '測量士補')+' '+result['subject']+f' No.{number}'
            source=pages[index][0];q={'id':stem+f'-q{number:03}','examId':exam,'type':'single','year':str(year),'term':result['term'],'subject':result['subject'],'category':'過去問','topic':title,
               'prompt':title+'\n原本画像の該当問題を解答してください。共通の関数表も表示しています。','options':['1','2','3','4','5'],'answer':keys[number],'images':images,
               'explanation':'公式解答：'+str(keys[number]+1)+'。理由解説は未収録です。\n実施当時の法令・規格を前提とします。',
               'source':'出典：国土地理院 '+title+'。原本PDFを設問単位の画像に加工（PDL1.0）。国土地理院が作成したアプリではありません。','sourceUrl':source['url'],'explanationSource':'国土地理院公式解答（理由解説なし）'}
            rows.append(q);evidence.append({'id':q['id'],'number':number,'answer':q['answer'],'sourceUrl':source['url'],'images':records})
        raw=ipa.encode(rows);(OUT/result['file']).write_bytes(raw)
        return {**result,'status':'prepared','count':len(rows),'sha256':ipa.sha(raw),'sourceFile':sources[0]['file'],'answerFile':answer['file'],
                'url':sources[0]['url'],'sources':sources,'questions':evidence,'provider':'GSI'}
    except Exception as error:return {**result,'status':'pending-review','reason':str(error)}

def main():
    sys.stdout.reconfigure(encoding='utf-8');os.environ['OMP_THREAD_LIMIT']='1'
    tasks=[];html=(SRC/'gsi-past.html').read_text(encoding='utf-8')
    for row in re.findall(r'<tr\b[^>]*>(.*?)</tr>',html,re.S):
        match=re.search(r'令和(\d+)年',row)
        if not match:continue
        year=int(match[1])+2018;cells=re.findall(r'<td\b[^>]*>(.*?)</td>',row,re.S)
        for exam,index in [('surveyor',0),('surveyor-assistant',5)]:
            urls=[urljoin('https://www.gsi.go.jp',href) for href in re.findall(r'href="([^"]+\.pdf)"',cells[index])]
            tasks.append((year,exam,urls[:-1],urls[-1]))
    with concurrent.futures.ProcessPoolExecutor(max_workers=2) as pool:
        results=[]
        for result in pool.map(prepare,tasks):
            results.append(result);print(result['year'],result['examId'],result['status'],result.get('reason',''),flush=True)
    (OUT/'gsi-report.json').write_bytes(ipa.encode({'packs':results}))

if __name__=='__main__':main()
