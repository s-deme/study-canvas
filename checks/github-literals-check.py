"""Runnable check for data extraction and refusal to execute source expressions."""
import importlib.util
from pathlib import Path

root = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('literals', root / 'scripts/github-literals.py')
literal = importlib.util.module_from_spec(spec); spec.loader.exec_module(literal)
assert literal.assignment("const rows: Row[] = [/* data */{id:'q1', text:'line\\nnext', answer:0, choices:['a','b'], ok:true,},];", 'rows') == [{'id': 'q1', 'text': 'line\nnext', 'answer': 0, 'choices': ['a', 'b'], 'ok': True}]
assert literal.Literal('{"escaped":"\\u65e5\\x41", "negative":-2}').value() == {'escaped': '日A', 'negative': -2}
for text in ['[{q:process.exit()}]', '[...other]', '[{q:`${fetch("url")}`}]', '[{q:1,q:2}]']:
    try: literal.Literal(text).value()
    except (AssertionError, ValueError): pass
    else: raise AssertionError('Executable or ambiguous literal accepted: ' + text)
print('PASS: JavaScript data literals, escapes, comments, TypeScript annotations, expression and duplicate-key refusal')
