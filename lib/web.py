# Copyright © 2017-2020 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

import gzip
import sys
import urllib.request

if sys.version_info < (3, 4, 3):
    raise RuntimeError('Python >= 3.4.3 is required')

class UserAgent(object):

    default_headers = {
        'User-Agent': 'dbts (https://github.com/jwilk/dbts)',
        'Accept-Encoding': 'gzip',
    }

    def request(self, url, data=None, headers=(), method=None):
        new_headers = dict(self.default_headers)
        new_headers.update(headers)
        request = urllib.request.Request(url, headers=new_headers, data=data)
        with urllib.request.urlopen(request) as fp:
            content_encoding = fp.getheader('Content-Encoding', 'identity')
            data = fp.read()
        if content_encoding == 'gzip':
            return gzip.decompress(data)
        elif content_encoding == 'identity':
            return data
        else:
            raise RuntimeError('unexpected Content-Encoding: {0!r}'.format(content_encoding))

    def get(self, url, headers=()):
        return self.request(url, headers=headers, method='GET')

    def post(self, url, data=None, headers=()):
        return self.request(url, data=data, headers=headers, method='POST')

__all__ = ['UserAgent']

# vim:ts=4 sts=4 sw=4 et
