# Copyright © 2015-2020 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

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
    black = '\x1B[30m'
    red = '\x1B[31m'
    green = '\x1B[32m'
    yellow = '\x1B[33m'
    blue = '\x1B[34m'
    cyan = '\x1B[36m'
    bold = '\x1B[1m'
    off = '\x1B[0m'
    reverse = '\x1B[7m'
    unreverse = '\x1B[27m'

def print(_s='', **kwargs):
    builtins.print(format(_s, **kwargs))

def _quote_unsafe_char(ch):
    if ch == '\t':
        return '{t.reverse}\t{t.unreverse}'.format(t=_seq)
    elif ch < ' ' or ch == '\x7F':
        return '{t.reverse}^{c}{t.unreverse}'.format(t=_seq, c=chr(ord('@') ^ ord(ch)))
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
    return _s.format_map({
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
