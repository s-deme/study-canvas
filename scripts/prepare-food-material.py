"""Import released agriculture/food papers into the existing private archive."""
import collections, importlib.util, json, re, sys
from pathlib import Path
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / file)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value
ipa = module('food_ipa', 'prepare-github-material.py')
fetch = module('food_fetch', 'fetch-github-material.py')
nonit = module('food_nonit', 'prepare-nonit-material.py')
SRC, OUT, fitz, norm = ipa.SRC, ipa.OUT, ipa.fitz, ipa.norm
NAMES = {'cook':'調理師試験', 'confectionery-hygiene':'製菓衛生師試験', **{f'agri{n}':f'日本農業検定{n}級' for n in (1,2,3)}}

def links(url, file):
    source = fetch.fetch(url, file)
    html = (SRC / file).read_text(encoding='utf-8')
    return [urljoin(url, u) for u in re.findall(r'href=["\']([^"\']+\.pdf)', html)]

def acquire():
    tasks = []
    for tag, url in [('food-tochigi','https://www.pref.tochigi.lg.jp/e07/kakomon.html'), ('food-agri','https://nou-ken.jp/sample-questions/')]:
        urls = links(url, tag+'.html')
        if tag.endswith('agri'): urls=[u for u in urls if re.search(r'/20\d\d/(question|answer)-[123]\.pdf$',u)]
        assert len(urls) == (20 if tag.endswith('tochigi') else 36), 'Source page structure changed'
        for i in range(0, len(urls), 2):
            if tag.endswith('tochigi'):
                exam = 'cook' if i < 10 else 'confectionery-hygiene'; year = str(2026 - (i//2)%5); term = '栃木県'
            else:
                exam = 'agri'+str(3-(i//2)%3); year = str(2025-i//6); term = '日本農業検定'
            stem = f'{tag}-{i:02}'
            sources = [fetch.fetch(urls[j], f'{tag}-{j:02}.pdf') for j in (i,i+1)]
            tasks.append(dict(provider='FOOD', examId=exam, year=year, term=term, subject='学科', file=stem+'.json',
                              sourceFile=sources[0]['file'], answerFile=sources[1]['file'], url=urls[i], sources=sources))
    (SRC/'food-discovery.json').write_bytes(ipa.encode({'tasks':tasks}))
    return tasks

def official_keys(doc, task):
    """Read the nearest answer cell on each numbered row; retain repeated practical sections."""
    keys = {}; occurrences = collections.Counter()
    symbols = {'ア':0,'イ':1,'ウ':2,'エ':3, **{str(n):n-1 for n in range(1,5)},'➀':0,'➁':1,'➂':2,'➃':3}
    for page in doc:
        lines = ipa.lines(page.get_text('dict', flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES))
        for line in lines:
            value = norm(''.join(s['text'] for s in line['spans'])).strip()
            match = re.fullmatch(r'問\s*(\d+)', value)
            if not match and task['examId'].startswith('agri') and task['year']=='2020':
                match = re.fullmatch(r'(\d+)', ''.join(s['text'] for s in line['spans']).strip())
            if not match: continue
            n = int(match[1]); x0,y0,x1,y1 = line['bbox']
            if task['year']=='2020' and task['examId'].startswith('agri') and occurrences[n]: continue
            candidates = [(other['bbox'][0], norm(''.join(s['text'] for s in other['spans'])).strip()) for other in lines
                          if abs((other['bbox'][1]+other['bbox'][3]-y0-y1)/2)<4 and 0<other['bbox'][0]-x1<120
                          and norm(''.join(s['text'] for s in other['spans'])).strip() in (*symbols,'-','−','―','*','採点除外')]
            symbol = min(candidates)[1] if candidates else '位置不明'; index = occurrences[n]; occurrences[n]+=1
            keys[f'{n}:{index}'] = symbols.get(symbol)
    assert keys, 'No native official answer cells'
    return keys

def question_starts(doc, task):
    starts = []; occurrences = collections.Counter()
    for pn,page in enumerate(doc):
        for line in ipa.lines(page.get_text('dict', flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)):
            value = norm(''.join(s['text'] for s in line['spans'])).strip(); x,y = line['bbox'][:2]
            match = re.match(r'^問\s*(\d+)(?:\s|[.．]|$)', value)
            if match and x<110 and 35<y<page.rect.height-30:
                n = int(match[1]); index = occurrences[n]; occurrences[n]+=1
                starts.append((f'{n}:{index}',pn,y))
    return starts

def prepare(task):
    try:
        doc = fitz.open(SRC/task['sourceFile']); keys = official_keys(fitz.open(SRC/task['answerFile']),task)
        starts = question_starts(doc,task)
        assert set(keys)=={n for n,p,y in starts} and len(starts)==len(keys), ('Question/key mismatch',len(starts),len(keys))
        rows=[]; evidence=[]; excluded=[]; cache={}; stem=Path(task['file']).stem
        for i,(number,pn,y) in enumerate(starts):
            answer=keys[number]
            if answer is None:
                excluded.append({'number':number,'reason':'公式の採点除外・全員加点、または解答セル位置を確定できない'}); continue
            ep=starts[i+1][1] if i+1<len(starts) else len(doc)-1
            if i+1<len(starts) and ep>pn:ep-=1
            body='\n'.join(p.get_text() for p in doc[pn:ep+1])
            if task['examId'].startswith('agri'):
                # Circled numbers survive in native PDF text; count only this question's interval.
                end_page,end_y=starts[i+1][1:] if i+1<len(starts) else (len(doc)-1,doc[-1].rect.height)
                parts=[]
                for p in range(pn,end_page+1):
                    for l in ipa.lines(doc[p].get_text('dict', flags=fitz.TEXTFLAGS_DICT & ~fitz.TEXT_PRESERVE_IMAGES)):
                        if (p!=pn or l['bbox'][1]>y) and (p!=end_page or l['bbox'][1]<end_y):
                            parts.append(''.join(s['text'] for s in l['spans']).strip())
                symbols={'①':1,'②':2,'③':3,'④':4,'➀':1,'➁':2,'➂':3,'➃':4}
                labels={symbols[m[1]] for t in parts if (m:=re.match(r'^([①②③④➀➁➂➃])',t))}
                assert labels in ({1,2,3},{1,2,3,4}), ('Option labels',number,labels)
                options=list('①②③④'[:len(labels)])
            else: options=list('アイウエ')
            assert answer<len(options)
            images,records=zip(*(nonit.picture(doc,p,stem,cache) for p in range(pn,ep+1)))
            n,variant=number.split(':'); suffix='' if variant=='0' else '-'+variant
            title=f'{task["year"]}年度 {task["term"]} {NAMES[task["examId"]]} 問{n}'+(f'（実技区分{int(variant)+1}）' if suffix else '')
            q=dict(id=stem+f'-q{int(n):03}'+suffix,examId=task['examId'],type='single',year=task['year'],term=task['term'],subject=task['subject'],category='過去問',topic=title,
                   prompt=title+'\n原本画像の該当問題を解答してください。選択肢・図表は画像で確認できます。',options=options,answer=answer,images=list(images),
                   sourceUrl=task['url'],source='出典：'+title+'。公式公開PDFの原本ページ画像（本人用教材）。',
                   explanation='公式正答：'+options[answer]+'。理由解説は未収録です。試験実施当時の制度を前提とします。',explanationSource='公式公表解答（理由解説なし）')
            rows.append(q); evidence.append(dict(id=q['id'],number=number,answer=answer,images=list(records)))
        assert rows
        return nonit.finish(task,rows,evidence,excluded)
    except Exception as error:
        return {**task,'status':'pending-review','reason':str(error)}

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    tasks=acquire() if '--fetch' in sys.argv else json.loads((SRC/'food-discovery.json').read_bytes())['tasks']
    packs=[]
    for task in tasks:
        pack=prepare(task);packs.append(pack);print(task['file'],pack['status'],pack.get('count',pack.get('reason')),flush=True)
    (OUT/'food-report.json').write_bytes(ipa.encode({'packs':packs}))

if __name__=='__main__': main()
