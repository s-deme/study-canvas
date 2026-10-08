"""Check official keys by text order independently of coordinate extraction."""
import importlib.util,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
s=importlib.util.spec_from_file_location('estate',ROOT/'scripts/prepare-estate-material.py')
e=importlib.util.module_from_spec(s);s.loader.exec_module(e)

def textual_keys(doc,task):
    text=e.ipa.norm(doc[-1].get_text());keys={}
    reviewed_file=e.SRC/'estate-reviewed-keys.json'
    reviewed=(json.loads(reviewed_file.read_bytes()) if reviewed_file.exists() else {}).get(task['answerFile'])
    if reviewed:
        assert e.ipa.sha((e.SRC/task['answerFile']).read_bytes())==reviewed['sha256']
        return {str(i+1):a for i,a in enumerate(reviewed['answers'])}
    if task['examId']=='takken':
        for labels,answers in re.findall(r'((?:問\s*\d+\s*){10})((?:(?:(?:正解|正答)?\s*なし|[1-4]\s*(?:又は|及び|、|,|・)\s*[1-4]|[1-4])\s*){10})',text):
            cells=re.findall(r'(?:正解|正答)?\s*なし|[1-4]\s*(?:又は|及び|、|,|・)\s*[1-4]|[1-4]',answers)
            keys.update({str(int(n)):int(a)-1 if a in '1234' else None for n,a in zip(re.findall(r'問\s*(\d+)',labels),cells)})
    else:
        for n,a in re.findall(r'(?:問\s*)?(\d+)\s*\n\s*([1-4])\s*(?:\n|$)',text):
            if 1<=int(n)<=50:keys[str(int(n))]=int(a)-1
    return keys

def main():
    report=json.loads((e.OUT/'estate-report.json').read_bytes());count=0
    for pack in report['packs']:
        if pack['status']!='prepared':continue
        doc=e.fitz.open(e.SRC/pack['sourceFile']);answer=e.fitz.open(e.SRC/pack['answerFile'])
        keys=e.official_keys(answer,pack);textual=textual_keys(answer,pack)
        assert all(textual.get(n)==a for n,a in keys.items() if a is not None),('Text/coordinate key mismatch',pack['file'])
        starts=e.question_starts(doc,pack);rows=json.loads((e.OUT/pack['file']).read_bytes())
        assert len(rows)==pack['count']
        assert {x['number'] for x in pack['questions']}|{x['number'] for x in pack['excludedQuestions']}==set(map(str,range(1,51)))
        for q,record in zip(rows,pack['questions']):
            assert q['answer']==keys[record['number']] and q['options']==list('1234')
            assert starts[int(record['number'])-1][1] in {r['page'] for r in record['images']}
            if pack['sourceFile']==pack['answerFile']:assert all(r['page']<len(doc)-1 for r in record['images'])
            count+=1
    print('PASS: estate questions',count,'text/geometry keys, complete numbering, answer-page isolation')
if __name__=='__main__':main()
