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

'the “show” command'

import datetime
import email.header
import email.utils
import re
import sys

import lxml.html

from lib import colorterm
from lib import dotparser
from lib import indent
from lib import debsoap

def print_version_graph(graph, *, ilevel=0):
    vcolors = dict(
        salmon='{t.red}',
        chartreuse='{t.green}',
    )
    def render(node):
        label = str(node)
        if label == 'some versions':
            label = '...'
        color = vcolors.get(node.get('fillcolor'))
        fmt1 = fmt2 = '{line}'
        if color is not None:
            fmt1 = color + fmt1 + '{t.off}'
        label = '\n'.join(
            colorterm.format(fmt1 if i == 0 else fmt2, line=line)
            for i, line in enumerate(label.splitlines())
        )
        return label
    bullet = '∙'
    try:
        bullet.encode(sys.stdout.encoding)
    except UnicodeError:
        bullet = '*'
    s = graph.pformat(render=render, bullet=bullet)
    s = s.rstrip('\n')
    s = indent.indent(s, ilevel)
    print(s)

def extract_bug_version_graph(html, *, options):
    version_urls = html.xpath('//div[@class="versiongraph"]/a/@href')
    if not version_urls:
        return
    [version_url] = version_urls
    version_url += ';dot=1'
    response = options.session.get(version_url)
    response.raise_for_status()
    return dotparser.parse(response.text)

def decode_header(s):
    return str(
        email.header.make_header(
            email.header.decode_header(s)
        )
    )

def decode_date(s):
    timetuple = email.utils.parsedate_tz(s)
    tz_offset = timetuple[-1]
    dt = datetime.datetime(*timetuple[:6])
    dt = str(dt)
    if tz_offset is not None:
        tz_sign = '+-'[tz_offset < 0]
        tz_offset = abs(tz_offset) // 60
        tz_hour = tz_offset // 60
        tz_min = tz_offset % 60
        dt += '{sign}{hh:02}:{mm:02}'.format(sign=tz_sign, hh=tz_hour, mm=tz_min)
    return str(dt)

rc_severities = {
    'serious',
    'grave',
    'critical',
}

def add_argument_parser(subparsers):
    ap = subparsers.add_parser('show')
    ap.add_argument('bugs', metavar='BUGNO', type=int, nargs='+')
    return ap

def run(options):
    for bugno in options.bugs:
        run_one(bugno, options=options)

def print_header(_h, _s=None, **kwargs):
    template = '{t.yellow}' + _h + ':{t.off}'
    if _s is not None:
        template += ' ' + _s
    colorterm.print(template, **kwargs)

def normalize_space(s):
    return ' '.join(s.split())

def print_control_message(html_message):
    message = normalize_space(
        ''.join(html_message.xpath('.//text()'))
    )
    match = re.match(
        '^(.*) '
        'Request was from (.+) to ([\w-]+@bugs[.]debian[.]org). '
        '(?:[(]([A-Z][a-z]{2}, [0-9]{2} [A-Z][a-z]{2} [0-9]{4} [0-9]{2}:[0-9]{2}:[0-9]{2} GMT)[)] )?'
        'Full text and rfc822 format available[.]$',
        message
    )
    if match is not None:
        message, req_from, req_to, date = match.groups()
        print_header('Request-From', '{mail}', mail=req_from)
        print_header('Request-To', '{mail}', mail=req_to)
        if date is not None:
            date = email.utils.parsedate_to_datetime(date)
            print_header('Date', '{date}', date=date)
    colorterm.print()
    colorterm.print('{msg}', msg=message)

def print_message(message):
    headers = message.header
    for hname in ['From', 'To', 'Cc', 'Subject']:
        value = headers[hname]
        if value is None:
            continue
        value = decode_header(value)
        value = normalize_space(value)
        print_header(hname, '{v}', v=value)
    date = headers['Date']
    if date is not None:
        print_header('Date', '{date}', date=decode_date(date))
    colorterm.print()
    for line in message.body.splitlines():
        colorterm.print('{l}', l=line)

def run_one(bugno, *, options):
    print_header('Location', '{t.blue}{t.bold}https://bugs.debian.org/{N}{t.off}', N=bugno)
    session = options.session
    url = 'https://bugs.debian.org/cgi-bin/bugreport.cgi?bug={0}'.format(bugno)
    response = session.get(url)
    response.raise_for_status()
    html = lxml.html.fromstring(response.text)
    html.make_links_absolute(base_url=url)
    debsoap_client = debsoap.Client(session=session)
    status = debsoap_client.get_status(bugno)
    print_header('Subject', '{t.bold}{subject}{t.off}', subject=status.subject)
    if status.package.startswith('src:'):
        print_header('Source', '{t.bold}{pkg}{t.off}', pkg=status.package[4:])
    else:
        print_header('Package', '{t.bold}{pkg}{t.off}', pkg=status.package)
        if status.source is not None:
            print_header('Source', '{pkg}', pkg=status.source)
    if status.affects:
        print_header('Affects')
        for apkg in status.affects:
            colorterm.print('  {pkg}', pkg=apkg)
    # TODO: Maintainer
    # https://bugs.debian.org/553661
    if status.owner:
        print_header('Owner', '{user}', user=status.owner)
    if status.package == 'wnpp' and status.owner == status.submitter:
        pass
    else:
        print_header('Submitter', '{user}', user=status.submitter)
    print_header('Date', '{date}-00:00', date=status.date)
    severity_color = (
        '{t.bold}{t.red}' if status.severity in rc_severities
        else ''
    )
    print_header('Severity', severity_color + '{severity}{t.off}',
        severity=status.severity,
    )
    version_graph = extract_bug_version_graph(html, options=options)
    if status.tags:
        print_header('Tags', '{tags}', tags=' '.join(status.tags))
    if status.merged_with:
        print_header('Merged-with')
        for mbug in status.merged_with:
            colorterm.print('  https://bugs.debian.org/{N}', N=mbug)
    if status.found_versions:
        print_header('Found')
        for version in status.found_versions:
            colorterm.print('  {ver}', ver=version)
    if status.fixed_versions:
        print_header('Fixed')
        for version in status.fixed_versions:
            colorterm.print('  {ver}', ver=version)
    if version_graph:
        print_header('Version-Graph')
        print_version_graph(version_graph, ilevel=2)
    if status.blocked_by:
        print_header('Blocked-by')
        for bbug in status.blocked_by:
            colorterm.print('  https://bugs.debian.org/{N}', N=bbug)
    if status.blocks:
        print_header('Blocks')
        for bbug in status.blocks:
            colorterm.print('  https://bugs.debian.org/{N}', N=bbug)
    if status.done:
        print_header('Done', '{user}', user=status.done)
    if status.archived:
        print_header('Archived', 'yes')
    if status.forwarded:
        print_header('Forwarded', '{url}', url=status.forwarded)
    colorterm.print_hr()
    bug_log = debsoap_client.get_log(bugno)
    html_messages = html.xpath('//*[@class="msgreceived"]')
    for html_message in html_messages:
        anchors = html_message.xpath('./a/@name')
        if not anchors:
            continue
        msgno = int(anchors[0])
        print_header('Location', 'https://bugs.debian.org/{N}#{id}', N=bugno, id=msgno)
        try:
            message = bug_log[msgno]
        except KeyError:
            print_control_message(html_message)
        else:
            print_message(message)
        colorterm.print_hr()
    colorterm.print()

__all__ = [
    'add_argument_parser',
    'run'
]

# vim:ts=4 sts=4 sw=4 et
