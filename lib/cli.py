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

import argparse
import datetime
import os
import re

import appdirs
import lxml.html
import requests

from lib import colors
from lib import dotparser
from lib import indent
from lib import soapbar

if int(requests.__version__.split('.')[0]) < 1:
    raise RuntimeError('requests >= 1.0 is required')

def setup_cache():
    try:
        import requests_cache
    except ImportError:
        return
    cache_dir = appdirs.user_cache_dir('dbts')
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, 0o700)
    cache_name = '{dir}/cache'.format(dir=cache_dir)
    requests_cache.install_cache(
        cache_name=cache_name,
        backend='sqlite',
        allowable_methods=('GET', 'POST'),
    )

def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers()
    sp.dest = 'cmd'  # https://bugs.python.org/issue9253
    sp.required = True
    cmd_show = sp.add_parser('show')
    cmd_show.add_argument('bug', metavar='BUGNO')
    options = ap.parse_args()
    setup_cache()
    session = requests.Session()
    session.verify = True
    session.trust_env = False
    session.headers['User-Agent'] = 'dbts (https://github.com/jwilk/dbts)'
    options.session = session
    globals()['do_' + options.cmd](options)

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

def extract_bug_version_graph(session, html):
    version_urls = html.xpath('//div[@class="versiongraph"]/a/@href')
    if not version_urls:
        return
    [version_url] = version_urls
    version_url += ';dot=1'
    response = session.get(version_url)
    response.raise_for_status()
    return dotparser.parse(response.text)

def do_show(options):
    bugno = int(options.bug)
    print('Bug: {colors.blue}{colors.bold}http://bugs.debian.org/{N}{colors.off}'.format(N=bugno, colors=colors))
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
    # TODO: Maintainer
    owner = sget('owner')
    if owner:
        print('Owner: {user}'.format(user=owner))
    print('Submitter: {user}'.format(user=sget('originator')))
    date = int(sget('date'))
    date = datetime.datetime.utcfromtimestamp(date)
    print('Date: {date} UTC'.format(date=date))
    severity = sget('severity')
    severity_color = (colors.bold + colors.red) if severity in {'serious', 'grave', 'critical'} else colors.off
    print('Severity: {color}{severity}{colors.off}'.format(severity=severity, color=severity_color, colors=colors))
    version_graph = extract_bug_version_graph(session, html)
    tags = sget('tags')
    if tags:
        print('Tags: {tags}'.format(tags=tags))
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

# vim:ts=4 sts=4 sw=4 et
