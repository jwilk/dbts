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

import mock
import io

from nose.tools import (
    assert_equal,
)

from lib import colorterm as M

def with_stdout(encoding):
    stdout = io.TextIOWrapper(
        io.StringIO(),
        encoding=encoding,
    )
    return mock.patch('sys.stdout', stdout)

@with_stdout('UTF-8')
def test_control_characters():
    def t(s, x):
        r = M.format('{s}', s=s)
        assert_equal(r, '\x1b[7m' + x + '\x1b[27m')
    t('\x00', '<U+0000>')
    t('\x01', '<U+0001>')
    t('\x02', '<U+0002>')
    t('\x03', '<U+0003>')
    t('\x04', '<U+0004>')
    t('\x05', '<U+0005>')
    t('\x06', '<U+0006>')
    t('\x07', '<U+0007>')
    t('\x08', '<U+0008>')
    t('\x09', '\t')
    t('\x0A', '<U+000A>')
    t('\x0B', '<U+000B>')
    t('\x0C', '<U+000C>')
    t('\x0D', '<U+000D>')
    t('\x0E', '<U+000E>')
    t('\x0F', '<U+000F>')
    t('\x10', '<U+0010>')
    t('\x11', '<U+0011>')
    t('\x12', '<U+0012>')
    t('\x13', '<U+0013>')
    t('\x14', '<U+0014>')
    t('\x15', '<U+0015>')
    t('\x16', '<U+0016>')
    t('\x17', '<U+0017>')
    t('\x18', '<U+0018>')
    t('\x19', '<U+0019>')
    t('\x1A', '<U+001A>')
    t('\x1B', '<U+001B>')
    t('\x1C', '<U+001C>')
    t('\x1D', '<U+001D>')
    t('\x1E', '<U+001E>')
    t('\x1F', '<U+001F>')
    t('\x7F', '<U+007F>')
    t('\x80', '<U+0080>')
    t('\x81', '<U+0081>')
    t('\x82', '<U+0082>')
    t('\x83', '<U+0083>')
    t('\x84', '<U+0084>')
    t('\x85', '<U+0085>')
    t('\x86', '<U+0086>')
    t('\x87', '<U+0087>')
    t('\x88', '<U+0088>')
    t('\x89', '<U+0089>')
    t('\x8A', '<U+008A>')
    t('\x8B', '<U+008B>')
    t('\x8C', '<U+008C>')
    t('\x8D', '<U+008D>')
    t('\x8E', '<U+008E>')
    t('\x8F', '<U+008F>')
    t('\x90', '<U+0090>')
    t('\x91', '<U+0091>')
    t('\x92', '<U+0092>')
    t('\x93', '<U+0093>')
    t('\x94', '<U+0094>')
    t('\x95', '<U+0095>')
    t('\x96', '<U+0096>')
    t('\x97', '<U+0097>')
    t('\x98', '<U+0098>')
    t('\x99', '<U+0099>')
    t('\x9A', '<U+009A>')
    t('\x9B', '<U+009B>')
    t('\x9C', '<U+009C>')
    t('\x9D', '<U+009D>')
    t('\x9E', '<U+009E>')
    t('\x9F', '<U+009F>')

@with_stdout('US-ASCII')
def test_escape_encoding_error():
    def t(s, x=None):
        r = M.format('{s}', s=s)
        if x is None:
            assert_equal(r, s)
        else:
            assert_equal(r, '\x1b[7m' + x + '\x1b[27m')
    t('A')
    t('Á', '<U+00C1>')

@with_stdout('UTF-8')
def test_escape_safe():
    def t(s):
        r = M.format('{s}', s=s)
        assert_equal(r, s)
    t('A')
    t('Á')

# vim:ts=4 sts=4 sw=4 et
