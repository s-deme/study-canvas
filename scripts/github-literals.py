"""Read data-only JavaScript literals; never evaluate downloaded code."""
import json, re
SPACE = re.compile(r'(?:\s+|//[^\n]*|/\*[\s\S]*?\*/)')
KEY = re.compile(r'[\w$]+')
VALUE = re.compile(r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?|true\b|false\b|null\b')

class Literal:
    def __init__(self, text, offset=0): self.text, self.i = text, offset
    def skip(self):
        while True:
            m = SPACE.match(self.text, self.i)
            if not m: return
            self.i += len(m[0])
    def take(self, token):
        self.skip()
        if self.text.startswith(token, self.i): self.i += len(token); return True
        return False
    def value(self):
        self.skip(); c = self.text[self.i]
        if c in "\"'`":
            quote = c; self.i += 1; result = ''
            while self.i < len(self.text):
                c = self.text[self.i]; self.i += 1
                if c == quote:
                    if self.take('+'):
                        self.skip()
                        if self.text[self.i:self.i+1] not in ('"', "'", '`'): raise ValueError('Only string literal concatenation is allowed')
                        result += self.value()
                    return result
                if quote == '`' and c == '$' and self.text[self.i:self.i+1] == '{': raise ValueError('Template expression')
                if c == '\\':
                    c = self.text[self.i]; self.i += 1
                    if c in ('u', 'x'):
                        n = 4 if c == 'u' else 2; c = chr(int(self.text[self.i:self.i+n], 16)); self.i += n
                    else: c = {'n':'\n','r':'\r','t':'\t','b':'\b','f':'\f','v':'\v','0':'\0','\n':''}.get(c, c)
                result += c
            raise ValueError('Unclosed string')
        if self.take('['):
            result = []
            while not self.take(']'):
                result.append(self.value())
                if not self.take(','):
                    if not self.take(']'): raise ValueError('Expected array end')
                    break
            return result
        if self.take('{'):
            result = {}
            while not self.take('}'):
                self.skip()
                if self.text[self.i] in "\"'": key = self.value()
                else:
                    m = KEY.match(self.text, self.i); assert m, 'Nonliteral object key'
                    key = m[0]; self.i += len(key)
                if not self.take(':'): raise ValueError('Nonliteral object property')
                if key in result: raise ValueError('Repeated object key')
                result[key] = self.value()
                if not self.take(','):
                    if not self.take('}'): raise ValueError('Expected object end')
                    break
            return result
        m = VALUE.match(self.text, self.i)
        if not m: raise ValueError('Executable expression refused at ' + self.text[self.i:self.i+50])
        self.i += len(m[0]); return json.loads(m[0])

def assignment(text, name):
    m = re.search(r'\b' + re.escape(name) + r'(?:\s*:\s*[^=\n]+)?\s*=\s*', text)
    if not m: raise ValueError('Missing literal: ' + name)
    return Literal(text, m.end()).value()
