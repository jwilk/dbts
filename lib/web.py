# Copyright © 2017 Jakub Wilk <jwilk@jwilk.net>
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

import gzip
import urllib.request

class UserAgent(object):

    default_headers = {
        'User-Agent': 'dbts (https://github.com/jwilk/dbts)',
        'Accept-Encoding': 'gzip',
    }

    def request(self, url, data=None, headers=(), method=None):
        new_headers = dict(self.default_headers)
        new_headers.update(headers)
        request = urllib.request.Request(url, headers=new_headers, data=data)
        with urllib.request.urlopen(request, cadefault=True) as fp:
            content_encoding = fp.getheader('Content-Encoding', 'identity')
            data = fp.read()
        if content_encoding == 'gzip':
            return gzip.decompress(data)
        elif content_encoding == 'identity':
            return data

    def get(self, url, headers=()):
        return self.request(url, headers=headers, method='GET')

    def post(self, url, data=None, headers=()):
        return self.request(url, data=data, headers=headers, method='POST')

__all__ = ['UserAgent']

# vim:ts=4 sts=4 sw=4 et
