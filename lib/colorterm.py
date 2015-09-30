# Copyright © 2015 Jakub Wilk <jwilk@jwilk.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

'''
color terminal support
'''

import builtins
import codecs
import os
import re
import sys

try:
    _terminal_width = os.get_terminal_size()[0]
except (AttributeError, OSError):
    _terminal_width = 80

class _seq:
    black = '\x1b[30m'
    red = '\x1b[31m'
    green = '\x1b[32m'
    yellow = '\x1b[33m'
    blue = '\x1b[34m'
    bold = '\x1b[1m'
    off = '\x1b[0m'
    reverse = '\x1b[7m'
    unreverse = '\x1b[27m'

def print(_s='', **kwargs):
    builtins.print(format(_s, **kwargs))

def _quote_unsafe_char(ch):
    if ch == '\t':
        return '{t.reverse}\t{t.unreverse}'.format(t=_seq)
    else:
        return '{t.reverse}<U+{u:04X}>{t.unreverse}'.format(t=_seq, u=ord(ch))

def _quote_unsafe(s):
    return ''.join(map(_quote_unsafe_char, s))

def _encoding_error_handler(exc):
    if isinstance(exc, UnicodeEncodeError):
        return _quote_unsafe(exc.object[exc.start:exc.end]), exc.end
    else:
        raise TypeError

codecs.register_error('_dbts_colorterm', _encoding_error_handler)

def _quote(s):
    if not isinstance(s, str):
        return s
    encoding = sys.stdout.encoding
    chunks = re.split(r'([\x00-\x1F\x7F-\x9F]+)', s)
    def esc():
        for i, s in enumerate(chunks):
            if i & 1:
                yield _quote_unsafe(s)
            else:
                yield s.encode(encoding, '_dbts_colorterm').decode(encoding)
    return ''.join(esc())

def format(_s, **kwargs):
    kwargs.update(t=_seq)
    return _s.format(**{
        key: _quote(value)
        for key, value in kwargs.items()
    })

def print_hr():
    ch = '─'
    try:
        ch.encode(sys.stdout.encoding)
    except UnicodeError:
        ch = '-'
    s = ch * _terminal_width
    print('{t.black}{t.bold}{s}{t.off}', s=s)

__all__ = [
    'format',
    'print',
    'print_hr',
]

# vim:ts=4 sts=4 sw=4 et
