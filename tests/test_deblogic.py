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

from nose.tools import (
    assert_equal,
    assert_false,
    assert_is_instance,
    assert_raises,
    assert_true,
)

from lib import deblogic as M

class test_parse_bugspec:

    def t(self, s, expected):
        if expected is None:
            with assert_raises(ValueError):
                M.parse_bugspec(s)
        else:
            n = M.parse_bugspec(s)
            assert_is_instance(n, int)
            assert_equal(n, expected)

    def test_empty(self):
        self.t('', None)

    def test_n(self):
        self.t('155144', 155144)
        self.t('#519321', 519321)

    def test_bad_n(self):
        self.t('85E16', None)
        self.t('6.55941', None)

    def test_short_url(self):
        self.t('http://bugs.debian.org/22282', 22282)
        self.t('https://bugs.debian.org/274135', 274135)

    def test_long_url(self):
        self.t('http://bugs.debian.org/cgi-bin/bugreport.cgi?bug=542953', 542953)
        self.t('https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=288454', 288454)

    def test_bad_scheme(self):
        self.t('ftp://bugs.debian.org/113533', None)
        self.t('ftp://bugs.debian.org/cgi-bin/bugreport.cgi?bug=761836', None)
        self.t('mailto:114752@bugs.debian.org', None)

    def test_bad_host(self):
        self.t('https://bugs.debian.net/635572', None)
        self.t('https://bugs.debian.net/cgi-bin/bugreport.cgi?bug=18408', None)

    def test_bad_path(self):
        self.t('https://bugs.debian.org/bugreport.cgi?bug=395923', None)

    def test_bad_query(self):
        self.t('https://bugs.debian.org/cgi-bin/bugreport.cgi', None)
        self.t('https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=1.8943', None)
        self.t('https://bugs.debian.org/cgi-bin/bugreport.cgi?bug=293727;bug=161662', None)

class test_is_package_name:

    def t(self, s):
        ok = M.is_package_name(s)
        assert_true(ok)

    def f(self, s):
        ok = M.is_package_name(s)
        assert_false(ok)

    def test_minimum_length(self):
        self.f('')
        self.f('a')
        self.t('an')

    def test_leading_digit(self):
        self.t('0ad')

    def punctuation(self):
        self.t('g++')
        self.t('m-tx')
        self.t('tk8.4')

    def test_leading_punctuation(self):
        self.f('+x')
        self.f('-y')
        self.f('.z')

# vim:ts=4 sts=4 sw=4 et
