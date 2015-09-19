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

import re

import lxml.html

from lib import colors
from lib import dotparser
from lib import indent
from lib import debsoap

def print_version_graph(graph, *, ilevel=0):
    vcolors = dict(
        salmon=(colors.red, colors.off),
        chartreuse=(colors.green, colors.off),
    )
    def render(node):
        color = vcolors.get(node.get('fillcolor'), ('', ''))
        label = str(node)
        if label == 'some versions':
            label = '...'
        def repl(match):
            return color[0] + match.group(1) + color[1]
        return re.sub(r'\A(.*)$', repl, label, flags=re.MULTILINE)
    s = graph.pformat(render=render)
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

def run(options):
    bugno = int(options.bug)
    print('Location: {colors.blue}{colors.bold}https://bugs.debian.org/{N}{colors.off}'.format(N=bugno, colors=colors))
    session = options.session
    url = 'https://bugs.debian.org/cgi-bin/bugreport.cgi?bug={0}'.format(bugno)
    response = session.get(url)
    response.raise_for_status()
    html = lxml.html.fromstring(response.text)
    html.make_links_absolute(base_url=url)
    debsoap_client = debsoap.Client(session=session)
    status = debsoap_client.get_status(bugno)
    print('Subject: {colors.bold}{subject}{colors.off}'.format(subject=status.subject, colors=colors))
    if status.package.startswith('src:'):
        print('Source: {colors.bold}{pkg}{colors.off}'.format(pkg=status.package[4:], colors=colors))
    else:
        print('Package: {colors.bold}{pkg}{colors.off}'.format(pkg=status.package, colors=colors))
        if status.source is not None:
            print('Source: {pkg}'.format(pkg=status.source, colors=colors))
    if status.affects:
        print('Affects:')
        for apkg in status.affects:
            print('  {pkg}'.format(pkg=apkg))
    # TODO: Maintainer
    if status.owner:
        print('Owner: {user}'.format(user=status.owner))
    if status.package == 'wnpp' and status.owner == status.submitter:
        pass
    else:
        print('Submitter: {user}'.format(user=status.submitter))
    print('Date: {date} UTC'.format(date=status.date))
    severity_color = (
        (colors.bold + colors.red) if status.severity in rc_severities
        else colors.off
    )
    print('Severity: {color}{severity}{colors.off}'.format(
        severity=status.severity,
        color=severity_color, colors=colors)
    )
    version_graph = extract_bug_version_graph(html, options=options)
    if status.tags:
        print('Tags: {tags}'.format(tags=' '.join(status.tags)))
    if status.merged_with:
        print('Merged-with:')
        for mbug in status.merged_with:
            print('  https://bugs.debian.org/{N}'.format(N=mbug))
    if status.found_versions:
        print('Found:')
        for version in status.found_versions:
            print('  {ver}'.format(ver=version))
    if status.fixed_versions:
        print('Fixed:')
        for version in status.fixed_versions:
            print('  {ver}'.format(ver=version))
    if version_graph:
        print('Version-Graph:')
        print_version_graph(version_graph, ilevel=2)
    if status.blocked_by:
        print('Blocked-by:')
        for bbug in status.blocked_by:
            print('  https://bugs.debian.org/{N}'.format(N=bbug))
    if status.blocks:
        print('Blocks:')
        for bbug in status.blocks:
            print('  https://bugs.debian.org/{N}'.format(N=bbug))
    if status.done:
        print('Done: {user}'.format(user=status.done))
    if status.archived:
        print('Archived: yes')
    if status.forwarded:
        print('Forwarded: {url}'.format(url=status.forwarded))

__all__ = ['run']

# vim:ts=4 sts=4 sw=4 et
