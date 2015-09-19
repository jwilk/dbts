#!/usr/bin/python3

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
very crude SOAP client
'''

import lxml.etree

_template = '''
<soap:Envelope
  soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
  xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
  xmlns:senc="http://schemas.xmlsoap.org/soap/encoding/"
  xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance"
  xmlns:xsd="http://www.w3.org/1999/XMLSchema"
>
<soap:Body>
<ns:{func} xmlns:ns="{ns}" senc:root="1">
{args}
</ns:get_status>
</soap:Body>
</soap:Envelope>
'''

class Client(object):

    def __init__(self, *, session, url, ns):
        self.session = session
        self.url = url
        self.ns = ns

    def __getattr__(self, funcname):
        def method(*args):
            if not all(isinstance(arg, int) for arg in args):
                raise TypeError
            data = _template.format(
                ns=self.ns,
                func=funcname,
                args=''.join(
                    '<v{i} xsi:type="xsd:int">{v}</v{i}>'.format(i=index, v=value)
                    for index, value in enumerate(args)
                )
            )
            data = data.encode('UTF-8')
            headers = {
                'Content-Type': 'application/soap+xml; charset=UTF-8',
            }
            response = self.session.post(url=self.url,
                 headers=headers,
                 data=data,
            )
            response.raise_for_status()
            tree = lxml.etree.fromstring(response.content)
            [result] = tree.find('{http://schemas.xmlsoap.org/soap/envelope/}Body')
            return result
        method.__name__ = funcname
        return method

# vim:ts=4 sts=4 sw=4 et
