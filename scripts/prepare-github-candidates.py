"""Convert archived candidate data for personal use, keeping incomplete rows out."""
import ast, csv, hashlib, html, importlib.util, json, re, sqlite3, sys, unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / 'private-data/github-candidates'
OUT = SRC / 'prepared'
spec = importlib.util.spec_from_file_location('literals', ROOT / 'scripts/github-literals.py')
literal = importlib.util.module_from_spec(spec); spec.loader.exec_module(literal)
sha = lambda data: hashlib.sha256(data).hexdigest()
encode = lambda data: (json.dumps(data, ensure_ascii=False, indent=2) + '\n').encode('utf-8')
NOTICE = 'GitHub提供元の教材。公式原本との一致・正答・解説は未検証。取得時点の内容で、法改正等への対応は未確認。'

def fingerprint(q):
    value = '\n'.join([q['prompt'], q.get('passage', ''), *q.get('options', [])])
    return sha(re.sub(r'\s+', '', unicodedata.normalize('NFKC', value)).encode())

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inventory = json.loads((SRC / 'inventory.json').read_bytes())
    selected = sys.argv[sys.argv.index('--repos') + 1:] if '--repos' in sys.argv else []
    if selected: inventory = [r for r in inventory if r['repo'] in selected]
    acquired = json.loads((SRC / 'acquisition.json').read_bytes())
    source_map = {(r['repo'], r['path']): r for r in acquired if r['status'] == 'downloaded'}
    existing = []
    manifest = ROOT / 'build/private/manifest.json'
    if manifest.exists():
        for p in json.loads(manifest.read_bytes())['packs']:
            if not p['id'].startswith('candidate-'):
                existing.extend(json.loads((ROOT / 'build/private/web' / p['url']).read_bytes()))
    seen = {q['examId'] + '|' + fingerprint(q): {'examId': q['examId'], 'id': q['id']} for q in existing}
    packs, results, excluded = [], [], []
    custom_exams = [{'id': 'github-fire-common', 'name': '消防設備士向け共通対策教材（GitHub）', 'field': '安全・消防・設備', 'subjects': [], 'categories': []},
                    {'id': 'sme-consultant', 'name': '中小企業診断士試験', 'field': '経営・事務・販売', 'subjects': [], 'categories': []}]

    for repo_row in inventory:
        repo = repo_row['repo']; folder = SRC / repo
        rows, reasons, sources, row_ids = [], Counter(), {}, set()

        def path_file(path):
            relative = str(path).replace('\\', '/')
            record = source_map[(repo, relative)]
            file = folder / record.get('localPath', relative)
            assert file.resolve().is_relative_to(folder.resolve())
            if relative in sources: return file
            assert sha(file.read_bytes()) == record['sha256'], 'Source changed: ' + relative
            sources[relative] = {k: record[k] for k in ('path', 'localPath', 'url', 'sha256', 'bytes') if k in record}
            return file

        def read(path): return path_file(path).read_text(encoding='utf-8-sig')
        def data(path): return json.loads(read(path))
        def js(path, name): return literal.assignment(read(path), name)
        def table(path): return list(csv.DictReader(read(path).splitlines(keepends=True)))

        def reject(identity, reason):
            reasons[reason] += 1; excluded.append({'repo': repo, 'identity': str(identity), 'reason': reason})

        def emit(exam, identity, file, prompt, options=None, answer=None, model=None, **meta):
            identity = str(identity)
            if not isinstance(prompt, str) or not prompt.strip(): reject(identity, '問題文なし'); return
            if model is None:
                if not isinstance(options, list) or not 2 <= len(options) <= 26 or not all(isinstance(o, str) and o.strip() for o in options): reject(identity, '選択肢不備'); return
                options = [o.strip() for o in options]
                if len(set(options)) != len(options): reject(identity, '重複選択肢'); return
                answers = answer if isinstance(answer, list) else [answer]
                if not answers or any(type(a) != int or not 0 <= a < len(options) for a in answers) or len(set(answers)) != len(answers): reject(identity, '正答番号不備'); return
                answer = sorted(answers) if len(answers) > 1 else answers[0]
            elif not isinstance(model, str) or not model.strip(): reject(identity, '模範解答なし'); return
            relative = str(file).replace('\\', '/')
            path_file(relative)
            q = {'id': 'github-' + sha((repo + '|' + identity).encode())[:24], 'examId': exam,
                 'type': 'written' if model is not None else 'multiple' if isinstance(answer, list) else 'single',
                 'prompt': prompt.strip(), 'options': options or [], 'answer': answer, 'modelAnswer': model or '',
                 'source': f'{repo} / {identity} — {NOTICE}', 'sourceUrl': sources[relative]['url'],
                 'explanationSource': repo + '（提供元の解説・未検証）',
                 'year': str(meta.pop('year', '')), 'subject': str(meta.pop('subject', '')),
                 'category': str(meta.pop('category', '')), **meta}
            fp = exam + '|' + fingerprint(q)
            # Compare only within the same exam; identical true/false text can belong to different exams.
            previous = seen.get(fp)
            if previous and previous['examId'] == exam:
                reject(identity, '同一試験の本文・共通本文・選択肢が既存問題と一致'); return
            seen[fp] = {'examId': exam, 'id': q['id']}
            if q['id'] in row_ids: reject(identity, '同じ提供元IDの重複'); return
            row_ids.add(q['id']); rows.append(q)

        def generic(exam, file, items, base=0, **meta):
            for n, q in enumerate(items):
                identity = str(file) + '#' + str(q.get('id', n + 1))
                prompt = q.get('prompt', q.get('question', q.get('q', q.get('text', q.get('body', '')))))
                opts = q.get('options', q.get('choices', q.get('c')))
                ans = q.get('correctIndex', q.get('answer', q.get('answers', q.get('correct', q.get('a')))))
                model = None
                if isinstance(opts, dict):
                    keys = list(opts); ans = keys.index(ans) if ans in keys else None; opts = list(opts.values())
                elif isinstance(opts, list) and opts and isinstance(opts[0], dict):
                    keys = [o['id'] for o in opts]; ans = keys.index(q.get('correctChoiceId')) if q.get('correctChoiceId') in keys else None; opts = [o['text'] for o in opts]
                elif isinstance(ans, str) and opts:
                    ans = opts.index(ans) if ans in opts else None
                elif type(ans) == bool:
                    opts, ans = ['正しい', '誤り'], 0 if ans else 1
                elif not opts and isinstance(ans, str): model = ans
                elif type(ans) == int: ans -= base
                elif isinstance(ans, list): ans = [a - base for a in ans]
                extra = {**meta, 'explanation': q.get('explanation', q.get('exp', q.get('expl', q.get('e', q.get('why', ''))))),
                         'subject': q.get('subject', q.get('law', meta.get('subject', ''))),
                         'category': q.get('category', q.get('topic', q.get('section', meta.get('category', '')))),
                         'term': q.get('term', meta.get('term', '')),
                         'year': q.get('year', q.get('fiscalYear', meta.get('year', ''))),
                         'passage': q.get('passage', q.get('context', ''))}
                emit(exam, identity, file, prompt, opts, ans, model, **extra)

        try:
            if repo == 'iamirtasam/AWS-AI-Practitioner-Exam-Mock':
                license_text = read('LICENSE')
                assert 'MIT License' in license_text
                assert 'covering both the code and the question content' in read('README.md')
                for file in sorted(folder.glob('data/qb-*.js')):
                    relative = file.relative_to(folder)
                    text = read(relative)
                    start = text.index('window.QBANK.push(') + len('window.QBANK.push(')
                    parser = literal.Literal(text, start)
                    while True:
                        q = parser.value()
                        if q['type'] not in ('single', 'multi'):
                            reject(q['id'], '並べ替え形式は未対応');
                        else:
                            explanation = q['explanation']
                            for i, rationale in enumerate(q.get('rationales', [])):
                                if rationale: explanation += '\n\n' + str(i + 1) + ': ' + rationale
                            emit('aws-aif', q['id'], relative, q['stem'], q['options'], q['answer'],
                                 subject='AIF-C01', category='Domain ' + str(q['domain']), topic=q['task'],
                                 explanation=explanation + '\n\n' + license_text)
                        if not parser.take(','): break
                        parser.skip()
                        if parser.text[parser.i] == ')': break
            elif repo in ('ikuma-hiroyuki/python_engineer_basic_demo', 'ThREE100/chosashi-app'):
                reasons['本文データあり。教材の収録許諾を確認できず保留'] += 1
            elif repo == 'tossh23/architect-study-app':
                for file in sorted(folder.glob('csv/utf8_*.csv')):
                    relative = file.relative_to(folder)
                    for q in table(relative):
                        identity = q['年度'] + q['科目'] + q['No.']
                        if q.get('図') or re.search('図に示す|下図|図中', q['問題文']): reject(identity, '必要図版がリポジトリにない'); continue
                        if not re.fullmatch('[1-4]', q['正答']): reject(identity, '削除・複数許容または正答不明'); continue
                        emit('architect1', identity, relative, q['問題文'], [q['選択肢' + str(i)] for i in range(1, 5)], int(q['正答']) - 1, year=q['年度'], subject=q['科目'])
            elif repo == 'pousan/mansion-exam-prediction':
                structure = next(folder.rglob('問題構造.jsonl')).relative_to(folder)
                answerfile = next(folder.rglob('正解表.csv')).relative_to(folder)
                keys = {q['問題ID']: q for q in table(answerfile)}
                for line in read(structure).splitlines():
                    q = json.loads(line); key = keys.get(q['問題ID'])
                    if not key or not re.fullmatch('[1-4]', key['正解']): reject(q['問題ID'], '削除・複数許容または正答不明'); continue
                    opts = q['選択肢'] or q['肢']
                    prompt = q['設問文'] + ('\n\n' + '\n'.join(q['肢']) if q.get('肢') and q['選択肢'] else '')
                    if re.search('下図|図に示|図の|図中|別図', prompt): reject(q['問題ID'], '図版の対応未確認'); continue
                    emit('mankan', q['問題ID'], structure, prompt, opts, int(key['正解']) - 1, year=q['年度'])
            elif repo == 'medicalillustotter/PTOT-kokushi-study':
                file = 'data/questions.json'
                for q in data(file):
                    if q['needsImage'] or q['excluded'] or q['alsoAccepted']: reject(q['id'], '必要図版なし・削除または別正答あり'); continue
                    generic('physical-therapist', file, [q], base=1, subject=q['session'])
            elif repo == 'yma3mama-tech/hoikushi-shiken-app':
                file = 'index.html'
                for subject in js(file, 'SUBJECTS'):
                    for q in subject['問題']:
                        opts = q['選択肢']; combinations = q.get('組み合わせ表', [])
                        if combinations:
                            opts = [', '.join(f'{k}: {v}' for k, v in row.items() if k != '番号') for row in combinations]
                        else: opts = list(opts.values()) if isinstance(opts, dict) else opts
                        answer = [int(a) - 1 for a in q['正解']] if isinstance(q['正解'], list) else int(q['正解']) - 1
                        emit('childcare', q['id'], file, q['問題文'], opts, answer, subject=q['科目'], term=q['出題期'], explanation=q.get('正解の根拠', ''))
            elif repo == 'kikkawamotoharu/sharoushi-app':
                file = 'index.html'
                generic('sharosi', file, js(file, 'SAMPLE_QUESTIONS'))
                for q in js(file, 'SAMPLE_SELECT_QUESTIONS'):
                    emit('sharosi', q['id'], file, q['problemIntro'] + '\n\n' + q['problemText'] + '\n\n空欄【' + q['blankKey'] + '】に入る語句を選んでください。', q['choices'], q['correctIndex'], subject=q['law'], year=q['year'], explanation=q.get('explanation', ''))
                reject('SAMPLE_CASES', '第三者の市販模試由来で出典・利用条件未確定')
            elif repo == 'mjrt0817/gyoseishoshi':
                for q in table('questions.csv'):
                    opts = [q['choice_' + str(i)] for i in range(1, 9) if q['choice_' + str(i)]]
                    correct = q['correct_text']
                    passage = q['passage']
                    if correct not in opts and opts: passage += '\n\n選択肢:\n' + '\n'.join(str(i + 1) + '. ' + value for i, value in enumerate(opts))
                    emit('gyosei', q['id'], 'questions.csv', q['question'], opts if correct in opts else None, opts.index(correct) if correct in opts else None, None if correct in opts else correct, subject=q['subject'], category=q['area'], passage=passage, explanation=q['explanation'])
                for q in table('written_prompts.csv'):
                    emit('gyosei', q['id'], 'written_prompts.csv', q['prompt'], model=q['model'], subject=q['subject'], category=q['area'])
            elif repo == 'masatopapa/unkan-quiz':
                categories = js('index.html', 'CATS')
                items = [{**q, 'category': categories[str(q['cat'])], 'year': re.search(r'令和\d+年度', q['src'])[0], 'term': q['src']} for q in js('index.html', 'BANK')]
                generic('transport-cargo', 'index.html', items)
            elif repo == 'masaosan425-alt/takken-app': generic('takken', 'src/data/questions.ts', js('src/data/questions.ts', 'questions'))
            elif repo == 'nappe0209/hoikushi-quiz':
                names = {s['id']: s['name'] for s in js('src/App.js', 'SUBJECTS')}
                generic('childcare', 'src/App.js', [{**q, 'subject': names[q['subject']]} for q in js('src/App.js', 'ALL_QUESTIONS')])
            elif repo == 'inamuu/KikenbutsuExams':
                file = 'data/practiceExams.mjs'
                for exam in js(file, 'examCatalog')['exams']: generic('hazmat-c', file, exam['questions'], year=exam['year'])
            elif repo == 'shajime0909-bit/eisei2':
                names = js('index.html', 'SUBJECTS')
                generic('health2', 'index.html', [{**q, 'subject': names[q['s']]} for q in js('index.html', 'Q')])
            elif repo == 'no2shi4ni0-dot/syoubou-quiz':
                file = 'quiz_data.py'; tree = ast.parse(read(file))
                for node in tree.body:
                    if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'quiz_list' for t in node.targets): generic('github-fire-common', file, ast.literal_eval(node.value))
            elif repo == '5150kouhei-rgb/fp2-drill':
                file = 'index.html'
                categories = js(file, 'CATEGORIES')
                for exam in js(file, 'EXAMS'):
                    for q in exam['questions']:
                        meta = {'category': categories[q['category']]['name'], 'year': re.search(r'20\d\d', exam['examLabel'])[0], 'term': exam['examLabel'], 'subject': '実技' if 'jitsugi' in exam['examId'] else '学科', 'explanation': q.get('explanation', '')}
                        if q['type'] == 'mc4': emit('fp2', q['id'], file, q['question'], q['choices'], q['correctIndex'], **meta)
                        elif q['type'] == 'ox':
                            passage = '\n'.join(i['label'] + ': ' + i['text'] for i in q['items'])
                            model = '\n'.join(i['label'] + ': ' + ('○' if i['correct'] else '×') for i in q['items'])
                            emit('fp2', q['id'], file, q['question'], model=model, passage=passage, **meta)
                        else:
                            passage = '\n'.join(i['num'] + ': ' + i['text'] for i in q.get('bank', []))
                            model = '\n'.join(str(i.get('label') or '解答') + ': ' + str(i['answer']) for i in q.get('blanks', []))
                            emit('fp2', q['id'], file, q['question'], model=model, passage=passage, **meta)
            elif repo == 'fp-hitorigoto/fp3-quiz': generic('fp3', 'index.html', js('index.html', 'allQuestions'))
            elif repo == 'edwin6780-tech/Boki-3':
                file = 'CBT.txt'
                for i, q in enumerate(js(file, 'PROBLEMS')):
                    model = '\n'.join(side + ': ' + ', '.join(a['a'] + ' ' + str(a['amt']) + '円' for a in q[key]) for side, key in [('借方', 'debit'), ('貸方', 'credit')])
                    emit('boki3', i + 1, file, q['text'], model=model, category=q['cat'], explanation=q.get('note', ''))
            elif repo == 'yuaoki08/kokunai-travel-exam':
                names = {key: value['name'] for key, value in js('questions.js', 'SUBJECTS').items()}
                generic('travel-domestic', 'questions.js', [{**q, 'subject': names[q['subject']]} for q in js('questions.js', 'QUESTIONS')])
                for file in sorted(folder.glob('bank/*.js')):
                    relative = file.relative_to(folder); text = read(relative); m = re.search(r'QUESTIONS\.push\s*\(', text)
                    parser = literal.Literal(text, m.end()); items = []
                    while not parser.take(')'):
                        items.append(parser.value())
                        if not parser.take(','): assert parser.take(')'); break
                    generic('travel-domestic', relative, [{**q, 'subject': names[q['subject']]} for q in items])
            elif repo == 'pose-shell/weather-quiz-app':
                read('LICENSE-CONTENT.md')
                reasons['教材はコードのMIT対象外。複製条件を確定するまで原本保存のみ'] += 1
            elif repo == 'nomu770501-Git/chouri-quiz': generic('cook', 'index.html', js('index.html', 'QUESTIONS'))
            elif repo == 'bang-prog/nutritionist': generic('nutritionist', 'data/questions.json', data('data/questions.json'))
            elif repo == 'toru830/shindanshi':
                file = 'questions.json'
                for q in data(file)['questions']:
                    images = []
                    if q.get('image'):
                        files = list(folder.rglob(q['image']))
                        if not files: reject(q['id'], '必要画像なし'); continue
                        image_path = files[0].relative_to(folder); record = source_map[(repo, str(image_path).replace('\\', '/'))]; path_file(image_path)
                        asset = record['sha256'] + files[0].suffix.lower(); assets = OUT / 'assets'; assets.mkdir(exist_ok=True)
                        (assets / asset).write_bytes(files[0].read_bytes()); images = [{'src': 'assets/github-candidates/' + asset, 'alt': '提供元の問題図版'}]
                    # script.js compares index + 1 with question.correct.
                    generic('sme-consultant', file, [q], base=1, images=images)
            elif repo == 'wangchang2049/eikenQuest':
                for file in sorted(folder.glob('data/*/test_*.json')):
                    items = data(file.relative_to(folder))
                    for i, q in enumerate(items): reject(str(file.relative_to(folder)) + '#' + str(i + 1), '生成データの設問と本文・選択肢の対応が不整合。提供元修正待ち')
            elif repo == 'hangonkou-ux/takken-app':
                file = next(folder.glob('*.csv')).relative_to(folder)
                for q in table(file):
                    if not re.fullmatch('[1-4]', q['正解']): reject(q['年度'] + '-' + q['問題番号'], '正答不明または複数許容'); continue
                    emit('takken', q['年度'] + '-' + q['問題番号'], file, q['問題文'], [q['選択肢' + str(i)] for i in range(1, 5)], int(q['正解']) - 1, year=q['年度'])
            elif repo == 'makio1988/takkenkakomon':
                file = 'takken-exam-system/takken_exam.db'; db = sqlite3.connect(path_file(file).resolve().as_uri() + '?mode=ro', uri=True); db.row_factory = sqlite3.Row
                tree = ast.parse(read('takken-exam-system/app.py'))
                genres = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'GENRES' for t in n.targets))
                for raw in db.execute('select * from questions order by id'):
                    q = dict(raw); opts = json.loads(q['options']) if q['options'] else []
                    answer = int(q['correct_answer']) - 1 if str(q['correct_answer']).isdigit() else None
                    emit('takken', q['id'], file, q['question_text'], opts, answer, year=q['year'] or '', category=genres.get(q['genre'], q['genre'] or ''), explanation=q['explanation'] or '')
                db.close()
            elif repo == 'Fkzyk/takken-dojo':
                file = 'index.html'; match = re.search(r'<script id="data-orig"[^>]*>([\s\S]*?)</script>', read(file))
                categories = {c['key']: c['label'] for c in js(file, 'CATS')}
                for q in json.loads(match[1])['questions']:
                    opts = q.get('choices', ['正しい', '誤り'])
                    emit('takken', q['id'], file, q['body'], opts, q['answer'] - 1, category=categories[q['cat']], topic=q['theme'], explanation=q['expl'])
            elif repo == 'kita0709/pt-exam-study-app':
                import openpyxl
                file = 'questions.xlsx'; book = openpyxl.load_workbook(path_file(file), data_only=True)
                for sheet in book:
                    values = list(sheet.values); headers = values[0]
                    for i, cells in enumerate(values[1:], 2):
                        q = dict(zip(headers, cells)); opts = [q.get('choice' + str(n)) for n in range(1, 6) if q.get('choice' + str(n))]
                        if q.get('answers'):
                            emit('physical-therapist', sheet.title + str(i), file, q['question'], model=str(q['answers']).replace('|', '\n'), explanation=q.get('explanation') or '')
                        else: emit('physical-therapist', sheet.title + str(i), file, q['question'], opts, opts.index(q['answer']) if q['answer'] in opts else None, explanation=q.get('explanation') or '')
            elif repo == 'nekomarugt/j-kokushi-portal':
                names = {'anatomy': '解剖学', 'clinical': '一般臨床医学', 'physiology': '生理学', 'anatomy-qa': '解剖学（記述）', 'basics-qa': '基礎医学（記述）', 'clinical-qa': '一般臨床医学（記述）'}
                for file in sorted(folder.rglob('questions.json')):
                    relative = file.relative_to(folder)
                    for i, q in enumerate(data(relative)):
                        if re.search('図に示|図のよう|図中|下図|別冊', q['question']): reject(str(relative) + str(q.get('number')), '必要図版がリポジトリにない')
                        else: generic('judo-therapist', relative, [{**q, 'id': str(q.get('exam', '')) + '-' + str(q.get('number', i + 1))}], subject=names[file.parent.name])
                for file in sorted(folder.rglob('questions.js')):
                    relative = file.relative_to(folder); text = read(relative); m = re.search(r'window\.(\w+)\s*=\s*\[', text)
                    if m: generic('judo-therapist', relative, js(relative, m[1]), subject=names[file.parent.name])
            elif repo.startswith('Ditectrev/'):
                file = 'README.md'
                for i, block in enumerate(re.split(r'^### ', read(file), flags=re.M)[1:], 1):
                    prompt = block.splitlines()[0]; choices = re.findall(r'^- \[([xX ])\] (.+)$', block, re.M)
                    if choices: emit('aws-clf', i, file, prompt, [c[1] for c in choices], [n for n, c in enumerate(choices) if c[0].lower() == 'x'])
            elif repo == 'keisks/j_bar_exam':
                subjects = {'civil': '民法', 'constitution': '憲法', 'penal': '刑法'}
                for file in sorted(folder.glob('questions/**/*.jsonl')):
                    relative = file.relative_to(folder)
                    for line in read(relative).splitlines():
                        if not line.strip(): continue
                        q = json.loads(line)
                        # Keep the original statements and numbered choices together for self-assessment.
                        emit('shiho', q['qid'], relative, q['question_sentence'],
                             model='正答番号：' + '・'.join(str(a) for a in q['answer']),
                             year=file.parent.name, subject=subjects[file.stem.split('_')[-1]])
            elif repo == 'MCCMDave/linux-essentials-quiz':
                file = 'fragen.json'
                for i, q in enumerate(data(file)['fragen'], 1):
                    emit('linux-essentials', i, file, q['frage'], q['optionen'], q['richtige_antwort'], category=q['kategorie'])
            elif repo == 'CarbonRaven/AWS-Quiz-SAA-C03':
                for file in sorted(folder.glob('questions/*.json')):
                    relative = file.relative_to(folder); q = data(relative); keys = list(q['options'])
                    correct = q['correct_answer']
                    answers = [keys.index(a) for a in correct] if isinstance(correct, str) and correct and all(a in keys for a in correct) else None
                    emit('aws-saa', q['question_number'], relative, q['question_text'], list(q['options'].values()), answers, subject='SAA-C03', category='Topic ' + str(q['topic']))
            elif repo == 'stueja/lpic-1-102-500-anki-flashcards':
                file = 'deck.json'
                for q in data(file)['notes']:
                    fields = q['fields']; images = []
                    for name in re.findall(r'<img\b[^>]*src=["\']([^"\']+)', fields[1], re.I):
                        image_path = 'media/' + name; image_file = path_file(image_path)
                        asset = sources[image_path]['sha256'] + image_file.suffix.lower()
                        assets = OUT / 'assets'; assets.mkdir(exist_ok=True); (assets / asset).write_bytes(image_file.read_bytes())
                        images.append({'src': 'assets/github-candidates/' + asset, 'alt': '提供元の解答図版'})
                    plain = lambda text: html.unescape(re.sub(r'<[^>]+>', '', re.sub(r'<br\s*/?>|</(?:div|p|li)>', '\n', text, flags=re.I))).strip()
                    emit('lpic1', q['guid'], file, plain(fields[0]), model=plain(fields[1]), subject='102-500', category=' / '.join(q['tags']), solutionImages=images)
            elif repo == 'eulerex/jlpt-test':
                for file in sorted(folder.glob('normalized/**/*.json')):
                    relative = file.relative_to(folder); data(relative)
                    reject(relative, '冊子単位OCRで問題・選択肢・正答の対応を確定できない。全原本を保存し登録保留')
            elif repo == 'Valsuh45/LPIC-Past-Questions':
                from pypdf import PdfReader
                for file in sorted(folder.rglob('*.pdf')):
                    path_file(file.relative_to(folder)); extracted = OUT / (sha(str(file.relative_to(folder)).encode()) + '.txt')
                    if not extracted.exists(): extracted.write_text('\n'.join(p.extract_text() or '' for p in PdfReader(file).pages), encoding='utf-8')
                reasons['市販dumps由来・正答範囲外やカード状態を正答にした設問あり。教材化を保留'] += 1
            elif repo == 'Sunmax0731/color-certification-exam-trainer': reasons['検証用の仮問題のみ。学習問題なし'] += 1
            else: reasons['配布された学習問題・正答の実体なし'] += 1
        except Exception as error:
            raise RuntimeError(repo + ': ' + str(error)) from error

        pack_sources = [{'repo': repo, **s} for s in sources.values()]
        for start in range(0, len(rows), 500):
            chunk = rows[start:start+500]; name = 'candidate-' + sha(repo.encode())[:12] + '-' + str(start // 500 + 1)
            raw = encode(chunk); (OUT / (name + '.json')).write_bytes(raw)
            packs.append({'id': name, 'repo': repo, 'examId': chunk[0]['examId'], 'file': name + '.json', 'sha256': sha(raw), 'count': len(chunk), 'sources': pack_sources})
        results.append({'repo': repo, 'commit': repo_row['commit'], 'imported': len(rows), 'excluded': dict(reasons), 'consumedFiles': len(sources)})
        print(repo, 'prepared', len(rows), 'excluded', dict(reasons), flush=True)

    report = {'version': 1, 'notice': NOTICE, 'repositoryCount': len(results), 'addedBeforeBuildDedup': sum(p['count'] for p in packs), 'exams': custom_exams, 'packs': packs, 'repositories': results, 'excluded': excluded}
    if selected:
        old = json.loads((OUT / 'report.json').read_bytes())
        for key in ('packs', 'repositories', 'excluded'):
            report[key] = [r for r in old[key] if r['repo'] not in selected] + report[key]
        report['repositoryCount'] = len(report['repositories'])
        report['addedBeforeBuildDedup'] = sum(p['count'] for p in report['packs'])
        report['exams'] = old['exams']
    (OUT / 'report.json').write_bytes(encode(report))

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8'); main()
