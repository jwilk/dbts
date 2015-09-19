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
import datetime

import lxml.html

from lib import colors
from lib import dotparser
from lib import indent
from lib import soapbar

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
    soapclient = soapbar.Client(session=session, url='https://bugs.debian.org/cgi-bin/soap.cgi', ns='Debbugs/SOAP')
    bug_status = soapclient.get_status(bugno)
    def sget(name):
        return bug_status.find('.//{Debbugs/SOAP}' + name).text
    def sget_list(name):
        xp = './/d:' + name + '/d:item/text()'
        return bug_status.xpath(xp, namespaces=dict(d='Debbugs/SOAP'))
    def sget_int_list(name):
        s = bug_status.find('.//{Debbugs/SOAP}' + name).text or ''
        return [int(x) for x in s.split()]
    print('Subject: {colors.bold}{subject}{colors.off}'.format(subject=sget('subject'), colors=colors))
    package = sget('package')
    if package.startswith('src:'):
        source = package[4:]
        print('Source: {colors.bold}{pkg}{colors.off}'.format(pkg=source, colors=colors))
    else:
        print('Package: {colors.bold}{pkg}{colors.off}'.format(pkg=package, colors=colors))
        source = sget('source')
        if source is not None:
            print('Source: {pkg}'.format(pkg=source, colors=colors))
    affects = (sget('affects') or '').split()
    if affects:
        print('Affects:')
        for apkg in affects:
            print('  {pkg}'.format(pkg=apkg))
    # TODO: Maintainer
    owner = sget('owner')
    if owner:
        print('Owner: {user}'.format(user=owner))
    submitter = sget('originator')
    if package == 'wnpp' and owner == submitter:
        pass
    else:
        print('Submitter: {user}'.format(user=submitter))
    date = int(sget('date'))
    date = datetime.datetime.utcfromtimestamp(date)
    print('Date: {date} UTC'.format(date=date))
    severity = sget('severity')
    severity_color = (
        (colors.bold + colors.red) if severity in rc_severities
        else colors.off
    )
    print('Severity: {color}{severity}{colors.off}'.format(severity=severity, color=severity_color, colors=colors))
    version_graph = extract_bug_version_graph(html, options=options)
    tags = sget('tags')
    if tags:
        print('Tags: {tags}'.format(tags=tags))
    merged_with = sget_int_list('mergedwith')
    if merged_with:
        print('Merged-with:')
        for mbug in merged_with:
            print('  https://bugs.debian.org/{N}'.format(N=mbug))
    found_versions = sget_list('found_versions')
    if found_versions:
        print('Found:')
        for version in found_versions:
            print('  {ver}'.format(ver=version))
    fixed_versions = sget_list('fixed_versions')
    if fixed_versions:
        print('Fixed:')
        for version in fixed_versions:
            print('  {ver}'.format(ver=version))
    if version_graph:
        print('Version-Graph:')
        print_version_graph(version_graph, ilevel=2)
    done = sget('done')
    blocked_by = sget_int_list('blockedby')
    if blocked_by:
        print('Blocked-by:')
        for bbug in blocked_by:
            print('  https://bugs.debian.org/{N}'.format(N=bbug))
    blocks = sget_int_list('blocks')
    if blocks:
        print('Blocks:')
        for bbug in blocks:
            print('  https://bugs.debian.org/{N}'.format(N=bbug))
    if done:
        print('Done: {user}'.format(user=done))
    if int(sget('archived')):
        print('Archived: yes')
    forwarded = sget('forwarded')
    if forwarded:
        print('Forwarded: {url}'.format(url=forwarded))

__all__ = ['run']

# vim:ts=4 sts=4 sw=4 et
