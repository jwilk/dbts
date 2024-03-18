# Copyright © 2017-2023 Jakub Wilk <jwilk@jwilk.net>
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
    ap.add_argument('-s', '--severity', metavar='SEVERITY', choices=deblogic.severities)
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

class Table:

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
            line = (
                s.ljust(widths[i])
                for i, s in enumerate(item)
            )
            line = str.join('  ', line)
            line = line.rstrip()
            lines += [line]
        return str.join('\n', lines)

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

def dpkg_search(path):
    path = os.path.realpath(path)
    info = utils.xcmd('dpkg-query', '-S', path)
    info = info.decode('UTF-8')
    info = info.splitlines()
    if len(info) > 1:
        raise RuntimeError('could not parse dpkg -S output: multiple lines')
    [line] = info
    pkg, dpath = line.split(':', 1)
    if ',' in pkg:
        raise RuntimeError('could not parse dpkg -S output: multiple packages')
    return pkg

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
            options.error(f'{path!r} is not a package')
        if os.path.isdir(path + '/debian'):
            (source, version) = pkginfo_for_unpacked(path)
        elif path.endswith('.dsc'):
            (source, version) = pkginfo_for_dsc(path)
        elif path.endswith('.deb'):
            (package, version, architecture) = pkginfo_for_deb(path)
        else:
            options.error(f'{path!r} is not a package')
    elif package.startswith(('src:', 'source:')):
        (prefix, source) = package.split(':', 1)
        package = None
    elif package.endswith(':source'):
        (source, suffix) = package.rsplit(':', 1)
        package = None
    else:
        look_for_source = False
        if package.startswith(('srcfor:', 'sourcefor:')):
            look_for_source = True
            tmp, package = package.split(':', 1)
            del tmp
        if package.startswith('file:'):
            tmp, path = package.split(':', 1)
            del tmp
            package = dpkg_search(path)
        try:
            info = utils.xcmd('dpkg-query', '-Wf', '${Package}\x1F${Source}\x1F${Architecture}\x1F${Version}\x1F${Pre-Depends}\x1F${Depends}\x1F${Recommends}\x1F${Suggests}\n', package)
        except subprocess.CalledProcessError:
            pass
        else:
            info = info.decode('ASCII')
            info = info.splitlines()
            if len(info) != 1:
                options.error(f'ambiguous package name: {package!r}')
            [package, source, architecture, version, *dep_lists] = info[0].split('\x1F')
            if not look_for_source:
                source = None
            if look_for_source:
                source = source or package
                if ' ' in source:
                    source, version = source.split(' ', 1)
                    version = version.strip('()')
                package = None
                architecture = None
                del dep_lists
            elif version:
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
        a(f'Package: {package}')
    if source:
        a(f'Source: {source}')
    if version:
        a(f'Version: {version}')
    if options.severity is not None:
        a(f'Severity: {options.severity}')
    a()
    a()
    if installed or architecture:
        a('-- System Information:')
        if installed and architecture == 'all':
            architecture = dpkg_get_architecture()
        a(f'Architecture: {architecture}')
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
                a(f'Versions of packages {package} {dverb}:')
                a(str(deptable))
                a()
    body = str.join('\n', body)
    subject = f'{(package or source)}:'
    url = 'mailto:submit@bugs.debian.org?' + urlencode(subject=subject, body=body)
    cmdline = ['neomutt',
        '-e', 'my_hdr X-Debbugs-No-Ack: please',
        '-e', 'my_hdr X-Debbugs-Cc: $from',
    ]
    if options.attach:
        cmdline += ['-a']
        cmdline += options.attach
    cmdline += ['--', url]
    try:
        os.execvp(cmdline[0], cmdline)
    except FileNotFoundError as exc:
        if exc.filename is None:
            exc.filename = cmdline[0]
        raise

__all__ = [
    'add_argument_parser',
    'run'
]

# vim:ts=4 sts=4 sw=4 et
