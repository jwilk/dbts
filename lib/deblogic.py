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
Debian constants, etc.
'''

import re
import urllib.parse

rc_severities = {
    'serious',
    'grave',
    'critical',
}

wnpp_tags = {
    'O',
    'RFA',
    'RFH',
    'ITP',
    'RFP',
}

def parse_bugspec(s):
    match = re.match(r'\A[#]?([0-9]+)\Z', s)
    if match is not None:
        n = match.group(1)
        return int(n)
    url = urllib.parse.urlparse(s)
    if url.scheme not in {'http', 'https'}:
        raise ValueError
    if url.netloc != 'bugs.debian.org':
        raise ValueError
    match = re.match(r'\A/([0-9]+)\Z', url.path)
    if match is not None:
        n = match.group(1)
        return int(n)
    if url.path != '/cgi-bin/bugreport.cgi':
        raise ValueError
    query = urllib.parse.parse_qs(url.query)
    try:
        [n] = query['bug']
    except KeyError:
        raise ValueError
    return int(n)

def is_package_name(s):
    # Policy §5.6.1
    match = re.match(r'\A[a-z][a-z0-9.+-]*\Z', s)
    return match is not None

__all__ = [
    'is_package_name',
    'parse_bugspec',
    'rc_severities',
    'wnpp_tags',
]

# vim:ts=4 sts=4 sw=4 et
