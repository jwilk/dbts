# Copyright © 2017 Jakub Wilk <jwilk@jwilk.net>
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

'the “new” command'

import collections
import itertools
import os
import re
import subprocess
import urllib.parse

def add_argument_parser(subparsers):
    ap = subparsers.add_parser('new')
    ap.add_argument('package', metavar='PACKAGE', type=str)
    return ap

def xcmd(*cmdline):
    return subprocess.check_output(cmdline)

def flatten_depends(deps):
    deps = re.sub(r'[(][^)]+[)]', '', deps)
    for d in re.split(r'\s*[,|]\s*', deps):
        d = d.strip()
        if d:
            yield d

def get_version_info(packages):
    raw_info = xcmd('dpkg-query', '-Wf', '${db:Status-Abbrev} ${Package} ${Version}\n', *set(packages))
    raw_info = raw_info.decode('ASCII')
    info = {}
    for line in raw_info.splitlines():
        status, package, version = line.split()
        info[package] = (status, version)
    return info

class Table(object):

    def __init__(self):
        self._items = []

    def add(self, *item):
        self._items += [item]

    def __len__(self):
        return len(self._items)

    def __str__(self):
        widths = collections.defaultdict(int)
        for item in self._items:
            for i, s in enumerate(item):
                widths[i] = max(widths[i], len(s))
        lines = []
        for item in self._items:
            line = '  '.join(
                s.ljust(widths[i])
                for i, s in enumerate(item)
            )
            line = line.rstrip()
            lines += [line]
        return '\n'.join(lines)

def urlencode(**data):
    return urllib.parse.urlencode(data, quote_via=urllib.parse.quote)

def run(options):
    info = xcmd('dpkg-query', '-Wf', '${Package}\n${Architecture}\n${Version}\n${Pre-Depends}\n${Depends}\n${Recommends}\n${Suggests}\n', options.package)
    info = info.decode('ASCII')
    [package, architecture, version, *dep_lists] = info.splitlines()
    dep_lists = [list(flatten_depends(d)) for d in dep_lists]
    dep_lists[0][:0] = dep_lists.pop(0)  # merge Depends + Pre-Depends
    dverbs = ['depends on', 'recommends', 'suggests']
    body = []
    def a(s=''):
        body.append(s)
    a('Package: {pkg}'.format(pkg=package))
    a('Version: {ver}'.format(ver=version))
    a()
    a()
    a('-- System Information:')
    a('Architecture: {arch}'.format(arch=architecture))
    a()
    seen = set()
    version_info = get_version_info(itertools.chain(*dep_lists))
    for deps, dverb in zip(dep_lists, dverbs):
        deptable = Table()
        for dep in deps:
            if dep not in seen:
                (status, version) = version_info[dep]
                deptable.add(status, dep, version)
                seen.add(dep)
        if deptable:
            a('Versions of packages {pkg} {verb}:'.format(pkg=package, verb=dverb))
            a(str(deptable))
            a()
    body = '\n'.join(body)
    subject = '{pkg}:'.format(pkg=package)
    url = 'mailto:submit@bugs.debian.org?' + urlencode(subject=subject, body=body)
    os.execlp('mutt', 'mutt', url)

__all__ = [
    'add_argument_parser',
    'run'
]

# vim:ts=4 sts=4 sw=4 et
