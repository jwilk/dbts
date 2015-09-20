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
Debian BTS SOAP client
'''

import base64
import datetime

import lxml.etree

class BugStatus(object):

    def __init__(self, xml):
        self._xml = xml

    @property
    def subject(self):
        return self._get('subject')

    @property
    def package(self):
        return self._get('package')

    @property
    def source(self):
        return self._get('source')

    @property
    def affects(self):
        return (self._get('affects') or '').split()

    @property
    def owner(self):
        return self._get('owner')

    @property
    def submitter(self):
        return self._get('originator')

    @property
    def date(self):
        ts = int(self._get('date'))
        return datetime.datetime.utcfromtimestamp(ts)

    @property
    def severity(self):
        return self._get('severity')

    @property
    def tags(self):
        return (self._get('tags') or '').split()

    @property
    def merged_with(self):
        return self._get_int_list('mergedwith')

    @property
    def found_versions(self):
        return self._get_list('found_versions')

    @property
    def fixed_versions(self):
        return self._get_list('fixed_versions')

    @property
    def blocked_by(self):
        return self._get_int_list('blockedby')

    @property
    def blocks(self):
        return self._get_int_list('blocks')

    @property
    def done(self):
        return self._get('done')

    @property
    def archived(self):
        return bool(int(self._get('archived')))

    @property
    def forwarded(self):
        return self._get('forwarded')

    def _get(self, name):
        elem = self._xml.find('.//{Debbugs/SOAP}' + name)
        if elem.get('{http://www.w3.org/1999/XMLSchema-instance}type') == 'xsd:base64Binary':
            return base64.b64decode(elem.text).decode('UTF-8', 'replace')
        else:
            return elem.text

    def _get_list(self, name):
        xp = './/d:' + name + '/d:item/text()'
        return self._xml.xpath(xp, namespaces=dict(d='Debbugs/SOAP'))

    def _get_int_list(self, name):
        s = self._xml.find('.//{Debbugs/SOAP}' + name).text or ''
        return [int(x) for x in s.split()]

_query_template = '''\
<soap:Envelope
  soap:encodingStyle="http://schemas.xmlsoap.org/soap/encoding/"
  xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"
  xmlns:senc="http://schemas.xmlsoap.org/soap/encoding/"
  xmlns:xsi="http://www.w3.org/1999/XMLSchema-instance"
  xmlns:xsd="http://www.w3.org/1999/XMLSchema"
>
<soap:Body>
<ns:{func} xmlns:ns="Debbugs/SOAP" senc:root="1">
{args}
</ns:{func}>
</soap:Body>
</soap:Envelope>
'''

class Client(object):

    def __init__(self, *, session):
        self._session = session

    def _call(self, funcname, *args):
        if not all(isinstance(arg, int) for arg in args):
            raise TypeError
        data = _query_template.format(
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
        response = self._session.post(url='https://bugs.debian.org/cgi-bin/soap.cgi',
             headers=headers,
             data=data,
        )
        response.raise_for_status()
        tree = lxml.etree.fromstring(response.content)
        [result] = tree.find('{http://schemas.xmlsoap.org/soap/envelope/}Body')
        return result

    def get_status(self, n):
        xml = self._call('get_status', n)
        return BugStatus(xml)

__all__ = [
    'BugStatus',
    'Client',
]

# vim:ts=4 sts=4 sw=4 et
