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
import os
import re

import appdirs
import lxml.html
import requests

from lib import colors
from lib import dotparser

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
    requests_cache.install_cache(cache_name=cache_name, backend='sqlite')

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

def render_version_graph(dot_data):
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
    graph = dotparser.parse(dot_data)
    graph.pprint(render=render)

def extract_bug_subject(html):
    [title] = html.xpath('//title/text()')
    title = re.sub('^#[0-9]+ - ', '', title)
    title = re.sub(' - Debian Bug report logs$', '', title)
    return title

def do_show(options):
    print('Bug: {colors.blue}{colors.bold}http://bugs.debian.org/{N}{colors.off}'.format(N=options.bug, colors=colors))
    session = options.session
    url = 'https://bugs.debian.org/cgi-bin/bugreport.cgi?bug={0}'.format(options.bug)
    response = session.get(url)
    response.raise_for_status()
    html = lxml.html.fromstring(response.text)
    html.make_links_absolute(base_url=url)
    subject = extract_bug_subject(html)
    print('Subject: {colors.bold}{subject}{colors.off}'.format(subject=subject, colors=colors))
    [version_url] = html.xpath('//div[@class="versiongraph"]/a/@href')
    version_url += ';dot=1'
    response = session.get(version_url)
    response.raise_for_status()
    print('Versions:')
    render_version_graph(response.text)

# vim:ts=4 sts=4 sw=4 et
