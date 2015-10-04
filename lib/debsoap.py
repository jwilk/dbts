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
import email
import xml.sax.saxutils as saxutils

import lxml.etree

def _get_text(elem):
    tp = elem.get('{http://www.w3.org/1999/XMLSchema-instance}type')
    if tp == 'xsd:base64Binary':
        return base64.b64decode(elem.text).decode('UTF-8', 'replace')
    else:
        return elem.text

class BugStatus(object):

    def __init__(self, xml):
        self._xml = xml

    @property
    def id(self):
        return int(self._get('key'))

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
        return _get_text(elem)

    def _get_list(self, name):
        xp = './/d:' + name + '/d:item/text()'
        return self._xml.xpath(xp, namespaces=dict(d='Debbugs/SOAP'))

    def _get_int_list(self, name):
        s = self._xml.find('.//{Debbugs/SOAP}' + name).text or ''
        return [int(x) for x in s.split()]

class BugLog(object):

    def __init__(self, xml):
        self._messages = {}
        for elem in xml:
            message = BugMessage(elem)
            self._messages[message.id] = message

    def __iter__(self):
        for n, message in sorted(self._messages.items()):
            yield message

    def __getitem__(self, n):
        return self._messages[n]

class BugMessage(object):

    def __init__(self, xml):
        self._xml = xml

    def _get(self, name):
        elem = self._xml.find('./{Debbugs/SOAP}' + name)
        return _get_text(elem)

    @property
    def header(self):
        s = self._get('header')
        return email.message_from_string(s)

    @property
    def body(self):
        return self._get('body')

    @property
    def id(self):
        return int(self._get('msg_num'))

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

    _xsd_types = {
        int: 'xsd:int',
        str: 'xsd:string',
    }

    def __init__(self, *, session):
        self._session = session

    def _call(self, funcname, *args):
        data = _query_template.format(
            func=funcname,
            args=''.join(
                '<v xsi:type="{tp}">{v}</v>'.format(
                    v=saxutils.escape(str(value)),
                    tp=self._xsd_types[type(value)],
                )
                for value in args
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

    def get_log(self, n):
        [xml] = self._call('get_bug_log', n)
        return BugLog(xml)

    def get_bugs(self, *queries):
        def flatten_dict(d):
            for k, v in d.items():
                yield k
                yield v
        bug_numbers = set()
        for query in queries:
            if isinstance(query, int):
                bug_numbers.add(query)
                continue
            [xml] = self._call('get_bugs', *flatten_dict(query))
            bug_numbers.update(
                int(elem.text)
                for elem in xml.findall('./{Debbugs/SOAP}item')
            )
        def groupby(iterable, n):
            a = []
            for o in iterable:
                a += [o]
                if len(a) == n:
                    yield a
                    a = []
            if a:
                yield a
        batch_size = 500
        for bug_group in groupby(sorted(bug_numbers), batch_size):
            # sort() is here only to make HTTP requests reproducible;
            # no particular output order is guaranteed
            [xml] = self._call('get_status', *bug_group)
            if len(bug_group) != len(xml):
                raise RuntimeError('expected {n} bugs, got {m}'.format(n=len(bug_numbers), m=len(xml)))
            for elem in xml:
                yield BugStatus(elem)

__all__ = [
    'BugLog',
    'BugMessage',
    'BugStatus',
    'Client',
]

# vim:ts=4 sts=4 sw=4 et
