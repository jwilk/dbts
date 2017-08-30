# Copyright © 2017 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

'the “new” command'

import collections
import itertools
import os
import re
import subprocess
import urllib.parse

from lib import deblogic
from lib import utils

def add_argument_parser(subparsers):
    ap = subparsers.add_parser('new')
    ap.add_argument('--attach', metavar='FILE', nargs='+')
    ap.add_argument('package', metavar='PACKAGE', type=str)
    return ap

def flatten_depends(deps):
    deps = re.sub(r'[(][^)]+[)]', '', deps)
    for d in re.split(r'\s*[,|]\s*', deps):
        d = d.strip()
        if not d:
            continue
        d = re.sub(':any$', '', d)
        yield d

def get_version_info(packages):
    try:
        raw_info = utils.xcmd('dpkg-query', '-Wf', '${db:Status-Abbrev}\t${Package}\t${Version}\n', *set(packages))
    except subprocess.CalledProcessError as exc:
        raw_info = exc.output
    raw_info = raw_info.decode('ASCII')
    info = {}
    for line in raw_info.splitlines():
        status, package, version = line.split('\t')
        info[package] = (status, version)
    return info

class Table(object):

    def __init__(self):
        self._items = []

    def add(self, *item):
        self._items += [tuple(s.rstrip() for s in item)]

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

def pkginfo_for_dsc(path):
    source = None
    version = None
    with open(path, 'r', encoding='UTF-8') as file:
        for line in file:
            match = re.match(r'^(?:(source)|(version)):\s*(\S+)$', line, re.IGNORECASE)
            if not match:
                continue
            if match.group(1) is not None:
                source = match.group(3)
            else:
                version = match.group(3)
            if source and version:
                break
    if source and version:
        if not deblogic.is_package_name(source):
            raise ValueError
        if not deblogic.is_package_version(version):
            raise ValueError
        return (source, version)
    else:
        raise ValueError

def pkginfo_for_unpacked(path):
    with open(path + '/debian/changelog', 'r', encoding='UTF-8') as file:
        for line in file:
            break
    match = re.match(r'^(\S+) [(]([^)]+)[)]', line)
    if match is None:
        raise ValueError
    (source, version) = match.groups()
    if not deblogic.is_package_name(source):
        raise ValueError
    if not deblogic.is_package_version(version):
        raise ValueError
    return (source, version)

def pkginfo_for_deb(path):
    info = utils.xcmd('dpkg-deb', '-f', path, 'Package', 'Version', 'Architecture')
    info = info.decode('UTF-8')
    match = re.match(r'\A'
        r'Package:\s*(\S+)\n'
        r'Version:\s*(\S+)\n'
        r'Architecture:\s*(\S+)\n'
        r'\Z', info
    )
    if match is None:
        raise ValueError
    (package, version, architecture) = match.groups()
    if not deblogic.is_package_name(package):
        raise ValueError
    if not deblogic.is_package_version(version):
        raise ValueError
    if not deblogic.is_architecture(architecture):
        raise ValueError
    return (package, version, architecture)

def dpkg_get_architecture():
    info = utils.xcmd('dpkg', '--print-architecture')
    info = info.decode('ASCII')
    return info.rstrip()

def run(options):
    package = options.package
    source = None
    version = None
    architecture = None
    installed = False
    if utils.looks_like_path(package):
        path = package
        package = None
        try:
            os.stat(path)
        except OSError:
            options.error('{0!r} is not a package'.format(path))
        if os.path.isdir(path + '/debian'):
            (source, version) = pkginfo_for_unpacked(path)
        elif path.endswith('.dsc'):
            (source, version) = pkginfo_for_dsc(path)
        elif path.endswith('.deb'):
            (package, version, architecture) = pkginfo_for_deb(path)
        else:
            options.error('{0!r} is not a package'.format(path))
    elif package.startswith(('src:', 'source:')):
        (prefix, source) = package.split(':', 1)
        package = None
    elif package.endswith(':source'):
        (source, suffix) = package.rsplit(':', 1)
        package = None
    else:
        try:
            info = utils.xcmd('dpkg-query', '-Wf', '${Package}\n${Architecture}\n${Version}\n${Pre-Depends}\n${Depends}\n${Recommends}\n${Suggests}\n', package)
        except subprocess.CalledProcessError:
            pass
        else:
            info = info.decode('ASCII')
            [package, architecture, version, *dep_lists] = info.splitlines()
            if version:
                dep_lists = [list(flatten_depends(d)) for d in dep_lists]
                dep_lists[0][:0] = dep_lists.pop(0)  # merge Depends + Pre-Depends
                dverbs = ['depends on', 'recommends', 'suggests']
                installed = True
            else:
                del dep_lists
    body = []
    def a(s=''):
        body.append(s)
    if package:
        a('Package: {pkg}'.format(pkg=package))
    if source:
        a('Source: {src}'.format(src=source))
    if version:
        a('Version: {ver}'.format(ver=version))
    a()
    a()
    if installed or architecture:
        a('-- System Information:')
        if installed and architecture == 'all':
            architecture = dpkg_get_architecture()
        a('Architecture: {arch}'.format(arch=architecture))
        a()
    if installed:
        seen = set()
        version_info = get_version_info(itertools.chain(*dep_lists))
        for deps, dverb in zip(dep_lists, dverbs):
            deptable = Table()
            for dep in deps:
                if dep not in seen:
                    try:
                        (status, version) = version_info[dep]
                    except KeyError:
                        status = 'un'
                        version = None
                    version = version or '<none>'
                    deptable.add(status, dep, version)
                    seen.add(dep)
            if deptable:
                a('Versions of packages {pkg} {verb}:'.format(pkg=package, verb=dverb))
                a(str(deptable))
                a()
    body = '\n'.join(body)
    subject = '{pkg}:'.format(pkg=(package or source))
    url = 'mailto:submit@bugs.debian.org?' + urlencode(subject=subject, body=body)
    cmdline = ['mutt',
        '-e', 'my_hdr X-Debbugs-No-Ack: please',
        '-e', 'my_hdr X-Debbugs-Cc: $from',
    ]
    if options.attach:
        print(repr(options.attach))
        cmdline += ['-a']
        cmdline += options.attach
    cmdline += ['--', url]
    print(repr(cmdline))
    os.execvp(cmdline[0], cmdline)

__all__ = [
    'add_argument_parser',
    'run'
]

# vim:ts=4 sts=4 sw=4 et
