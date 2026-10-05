"""Extract private IPA packs. Requires PyMuPDF in build/python-deps or Python."""
import hashlib, json, re, sys, unicodedata
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'build/python-deps'))
import pymupdf as fitz
sys.stdout.reconfigure(encoding='utf-8')
SRC=ROOT/'private-data/ipa'
OUT=ROOT/'private-data/material'
NAMES=dict(ap='応用情報技術者',st='ITストラテジスト',sa='システムアーキテクト',pm='プロジェクトマネージャ',nw='ネットワークスペシャリスト',db='データベーススペシャリスト',es='エンベデッドシステムスペシャリスト',sm='ITサービスマネージャ',au='システム監査技術者',sc='情報処理安全確保支援士')
SUBJECTS=dict(am='午前',am1='午前Ⅰ',am2='午前Ⅱ',pm='午後',pm1='午後Ⅰ',pm2='午後Ⅱ')
norm=lambda s:unicodedata.normalize('NFKC',s)

def sections(doc, answer=False):
    starts=[]
    layouts=[]
    for pi,page in enumerate(doc):
        cache=SRC/'ocr'/f'{Path(doc.name).name}-{pi}.json'
        layout=json.loads(cache.read_text(encoding='utf-8')) if cache.exists() else page.get_text('dict')
        layouts.append(layout)
        if not answer and pi==0: continue
        for block in layout['blocks']:
            for line in block.get('lines',[]):
                value=norm(''.join(s['text'] for s in line['spans'])).strip()
                m=re.fullmatch(r'問\s*(\d+)',value) if answer else re.match(r'^[問間]\s*(\d+)',value)
                if m and line['bbox'][0]<115:
                    starts.append((int(m[1]),pi,line['bbox'][1]))
    verified=SRC/'verified-starts.json'
    if not answer and verified.exists():
        starts=json.loads(verified.read_text(encoding='utf-8')).get(Path(doc.name).name,starts)
    # Reject ambiguous extraction, never silently pair an answer with another question.
    assert starts and [s[0] for s in starts]==list(range(1,len(starts)+1)), starts
    result={}
    for i,(number,pi,y) in enumerate(starts):
        ep,ey=(starts[i+1][1],starts[i+1][2]-3) if i+1<len(starts) else (len(doc)-1,doc[-1].rect.height-30)
        clips=[]; texts=[]
        for pn in range(pi,ep+1):
            page=doc[pn]; top=max(28,y-3) if pn==pi else 30; bottom=ey if pn==ep else page.rect.height-30
            if bottom<=top: continue
            rect=fitz.Rect(0,top,page.rect.width,bottom)
            content='\n'.join(''.join(s['text'] for s in line['spans']) for b in layouts[pn]['blocks'] for line in b.get('lines',[]) if line['bbox'][1]>=top-1 and line['bbox'][3]<=bottom+1).strip()
            if not content or 'この用紙は空白' in content: continue
            if pn==len(doc)-1 and '監督員' in content and '退室' in content: continue
            texts.append(norm(content)); clips.append((pn,rect))
        result[number]=( '\n\n'.join(texts),clips)
    return result

def pictures(doc,clips,stem):
    images=[]
    for i,(pn,rect) in enumerate(clips):
        name=f'{stem}-{i+1}.png'; path=OUT/'assets'/name
        geometry=json.dumps([pn,list(rect)])
        stamp=path.with_suffix('.geometry.json')
        if not path.exists() or not stamp.exists() or stamp.read_text()!=geometry:
            doc[pn].get_pixmap(matrix=fitz.Matrix(1.5,1.5),clip=rect,alpha=False).save(path)
            stamp.write_text(geometry)
        images.append(dict(src='assets/material/'+name,alt=f'公式資料 {stem} ({i+1}/{len(clips)})'))
    return images

def main():
    (OUT/'assets').mkdir(parents=True,exist_ok=True)
    sources=json.loads((SRC/'sources.json').read_text(encoding='utf-8'))
    by_file={r['file']:r for r in sources}
    packs=[]; audit=[]; errors=[]
    for src in sources:
        if src['kind']!='qs': continue
        try:
            stem=src['file'][:-7]; exam=src['examId']; subject=src['subject']
            answer_src=by_file[stem+'_ans.pdf']; doc=fitz.open(SRC/src['file']); answers_doc=fitz.open(SRC/answer_src['file'])
            qs=sections(doc)
            choice=subject.startswith('am')
            if choice:
                answer_text=norm('\n'.join(p.get_text() for p in answers_doc))
                answers={int(n):a for n,a in re.findall(r'問\s*(\d+)\s*([アイウエ])',answer_text)}
                assert set(answers)==set(qs),(stem,'answer mismatch',len(answers),len(qs))
            else:
                answers=sections(answers_doc,True)
                assert set(answers)==set(qs),(stem,'written answer mismatch')
            cmnt=by_file.get(stem+'_cmnt.pdf'); commentary={}
            if cmnt:
                cd=fitz.open(SRC/cmnt['file']); commentary=sections(cd,True)
                assert set(commentary)==set(qs),(stem,'commentary mismatch')
            rows=[]
            for number,(body,clips) in qs.items():
                images=pictures(doc,clips,f'{stem}-q{number:02}')
                common=dict(id=f'{stem}-q{number:02}',examId=exam,subject=SUBJECTS[subject],category='',topic=f'{src["year"]} {src["term"]} {SUBJECTS[subject]} 問{number}',year=str(src['year']),term=src['term'],passage=body,images=images,source=f'出典：{src["year"]}年度 {src["term"]} {NAMES.get(exam,"高度試験共通")} {SUBJECTS[subject]} 問{number} ©{src["year"]} IPA',sourceUrl=src['url'],explanationSource='IPA公式資料（独自解説なし）')
                if choice:
                    rows.append(dict(**common,type='single',prompt='問題文・図表・選択肢を確認して回答してください。',options=list('アイウエ'),answer='アイウエ'.index(answers[number]),explanation=f'公式解答：{answers[number]}。公式資料には解説がありません。'))
                else:
                    answer,answer_clips=answers[number]
                    solution_images=pictures(answers_doc,answer_clips,f'{stem}-answer{number:02}')
                    essay=exam in {'st','sa','pm','sm','au','es'} and subject=='pm2'
                    if essay:
                        guide=answer+'\n\n採点講評\n'+commentary.get(number,('',[]))[0]
                        rows.append(dict(**common,type='essay',prompt='設問ア・イ・ウを含む論述を入力してください。',evaluationGuide=guide,modelAnswer='',solutionImages=solution_images,options=[],answer=None))
                    else:
                        matches=list(re.finditer(r'設問\s*(\d+)',answer))
                        if not matches and exam=='db' and subject=='pm2':
                            matches=list(re.finditer(r'^\s*\((\d+)\)',answer,re.M))
                        assert matches,(stem,number,'no subquestions')
                        assert len({m[1] for m in matches})==len(matches),(stem,number,'duplicate subquestions')
                        for i,m in enumerate(matches):
                            sub=m[1]; text=answer[m.start():matches[i+1].start() if i+1<len(matches) else len(answer)].strip()
                            row={**common,'id':common['id']+f'-s{sub}','topic':common['topic']+f' 設問{sub}'}
                            rows.append(dict(**row,type='written',prompt=f'問題資料の設問{sub}に回答してください。小問・空欄の番号を付けて入力してください。',modelAnswer=text,solutionImages=solution_images,explanation=commentary.get(number,('',[]))[0],options=[],answer=None))
                audit.append(dict(file=src['file'],question=number,pages=[pn+1 for pn,_ in clips],answerFile=answer_src['file'],method='official-answer-map' if choice else 'question-and-subquestion-labels'))
            # Shared morning I material belongs to each exam held in this term.
            targets=[exam] if exam!='koudo' else sorted({s['examId'] for s in sources if s['year']==src['year'] and s['term']==src['term'] and s['subject']=='am2'})
            for target in targets:
                copied=[{**q,'examId':target} for q in rows]
                pack_id=f'{stem}-{target}'
                (OUT/f'{pack_id}.json').write_text(json.dumps(copied,ensure_ascii=False),encoding='utf-8')
                packs.append(dict(id=pack_id,examId=target,year=str(src['year']),term=src['term'],subject=SUBJECTS[subject],count=len(copied),file=pack_id+'.json'))
            print(stem,len(rows),flush=True)
        except (AssertionError,KeyError) as error:
            errors.append(dict(file=src['file'],error=str(error)))
    (OUT/'packs.json').write_text(json.dumps(packs,ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'audit.json').write_text(json.dumps(dict(sources=sources,questions=audit),ensure_ascii=False,indent=2),encoding='utf-8')
    (OUT/'errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2),encoding='utf-8')
    if errors: print('NEEDS REVIEW',len(errors),flush=True)
    print('TOTAL',sum(p['count'] for p in packs), 'packs',len(packs),flush=True)

if __name__=='__main__': main()
