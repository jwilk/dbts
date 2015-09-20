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
            colorterm.tformat(fmt1 if i == 0 else fmt2, line=line)
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


def run_one(bugno, *, options):
    tprint = colorterm.tprint
    tprint('Location: {t.blue}{t.bold}https://bugs.debian.org/{N}{t.off}', N=bugno)
    session = options.session
    url = 'https://bugs.debian.org/cgi-bin/bugreport.cgi?bug={0}'.format(bugno)
    response = session.get(url)
    response.raise_for_status()
    html = lxml.html.fromstring(response.text)
    html.make_links_absolute(base_url=url)
    debsoap_client = debsoap.Client(session=session)
    status = debsoap_client.get_status(bugno)
    tprint('Subject: {t.bold}{subject}{t.off}', subject=status.subject)
    if status.package.startswith('src:'):
        tprint('Source: {t.bold}{pkg}{t.off}', pkg=status.package[4:])
    else:
        tprint('Package: {t.bold}{pkg}{t.off}', pkg=status.package)
        if status.source is not None:
            tprint('Source: {pkg}', pkg=status.source)
    if status.affects:
        tprint('Affects:')
        for apkg in status.affects:
            tprint('  {pkg}', pkg=apkg)
    # TODO: Maintainer
    if status.owner:
        tprint('Owner: {user}', user=status.owner)
    if status.package == 'wnpp' and status.owner == status.submitter:
        pass
    else:
        tprint('Submitter: {user}', user=status.submitter)
    tprint('Date: {date} UTC', date=status.date)
    severity_color = (
        '{t.bold}{t.red}' if status.severity in rc_severities
        else ''
    )
    tprint('Severity: ' + severity_color + '{severity}{t.off}',
        severity=status.severity,
    )
    version_graph = extract_bug_version_graph(html, options=options)
    if status.tags:
        tprint('Tags: {tags}', tags=' '.join(status.tags))
    if status.merged_with:
        tprint('Merged-with:')
        for mbug in status.merged_with:
            tprint('  https://bugs.debian.org/{N}', N=mbug)
    if status.found_versions:
        tprint('Found:')
        for version in status.found_versions:
            tprint('  {ver}', ver=version)
    if status.fixed_versions:
        tprint('Fixed:')
        for version in status.fixed_versions:
            tprint('  {ver}', ver=version)
    if version_graph:
        tprint('Version-Graph:')
        print_version_graph(version_graph, ilevel=2)
    if status.blocked_by:
        tprint('Blocked-by:')
        for bbug in status.blocked_by:
            tprint('  https://bugs.debian.org/{N}', N=bbug)
    if status.blocks:
        tprint('Blocks:')
        for bbug in status.blocks:
            tprint('  https://bugs.debian.org/{N}', N=bbug)
    if status.done:
        tprint('Done: {user}', user=status.done)
    if status.archived:
        tprint('Archived: yes')
    if status.forwarded:
        tprint('Forwarded: {url}', url=status.forwarded)
    tprint()

__all__ = [
    'add_argument_parser',
    'run'
]

# vim:ts=4 sts=4 sw=4 et
