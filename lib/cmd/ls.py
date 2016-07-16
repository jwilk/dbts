# Copyright © 2015-2016 Jakub Wilk <jwilk@jwilk.net>
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

'the “ls” command'

import functools
import os
import re
import subprocess

from lib import colorterm
from lib import deblogic
from lib import debsoap

def add_argument_parser(subparsers):
    ap = subparsers.add_parser('ls')
    ap.add_argument('selections', metavar='SELECTION', type=str, nargs='+')
    return ap

def select_sources_for(pkgname):
    @functools.lru_cache(maxsize=None)
    def get_cache():
        import apt
        return apt.Cache()
    cache = get_cache()
    return [
        {'src': pkg.source_name}
        for pkg in cache[pkgname].versions
    ]

def select_for_dsc(path):
    import debian.deb822 as deb822
    with open(path, 'r', encoding='UTF-8') as file:
        for dctrl in deb822.Deb822.iter_paragraphs(file):
            srcpkg = dctrl['Source']
            return [{'src': srcpkg}]
    raise RuntimeError

def select_for_unpacked(path):
    return select_for_dsc(path + '/debian/control')

def xcmd(*cmdline):
    child = subprocess.Popen(
        cmdline,
        stdout=subprocess.PIPE,
    )
    (stdout, stderr) = child.communicate()
    if child.returncode != 0:
        raise RuntimeError
    return stdout

def select_for_deb(path):
    pkg = xcmd('dpkg-deb', '-f', path, 'Package')
    pkg = pkg.decode('ASCII').strip()
    return [{'package': pkg}]

selectors = {  # sort -t: -k2
    'commented': 'correspondent',
    'correspondent': 'correspondent',
    'maint': 'maintainer',
    'maintainer': 'maintainer',
    'last': 'newest',
    'newest': 'newest',
    'owner': 'owner',
    'package': 'package',
    'pkg': 'package',
    'source': 'src',
    'src': 'src',
    'from': 'submitter',
    'submitter': 'submitter',
    'sourcefor': select_sources_for,
    'srcfor': select_sources_for,
}

def strip_package_prefix(subject, package):
    regex = r'\A{pkg}(?:[:]\s*|\s+)'.format(pkg=re.escape(package))
    return re.sub(regex, '', subject)

def run(options):
    debsoap_client = debsoap.Client(session=options.session)
    queries = []
    for selection in options.selections:
        bugno = None
        try:
            bugno = deblogic.parse_bugspec(selection)
        except ValueError:
            pass
        if bugno is not None:
            queries += [bugno]
        elif ':' in selection:
            selector, value = selection.split(':', 1)
            selector = selectors[selector]
            if callable(selector):
                queries += selector(value)
            else:
                queries += [{selector: value}]
        elif deblogic.is_package_name(selection):
            queries += [dict(package=selection)]
        else:
            path = selection
            try:
                os.stat(path)
            except OSError:
                options.error('{0!r} is not a valid package name'.format(selection))
            if os.path.isdir(path):
                queries += select_for_unpacked(path)
            elif path.endswith('.deb'):
                queries += select_for_deb(path)
            elif path.endswith('.dsc'):
                queries += select_for_dsc(path)
            else:
                options.error('{0!r} is not a valid package name'.format(selection))
    bugs = debsoap_client.get_bugs(*queries)
    bugs = sorted(bugs, key=(lambda bug: -bug.id))
    for bug in bugs:
        package = bug.package
        subject = bug.subject or ''
        default_severity = 'normal'
        if package == 'wnpp':
            for wnpp_tag in deblogic.wnpp_tags:
                if subject.startswith(wnpp_tag + ': '):
                    if wnpp_tag[-1] == 'P':
                        default_severity = 'wishlist'
                    package = None
                    break
        elif package == 'sponsorship-requests':
            if subject.startswith('RFS:'):
                package = None
        template = ''
        source = None
        subject_color = '{t.green}' if bug.done else '{t.bold}'
        if package is not None:
            if package.startswith('src:'):
                source = package[4:]
                new_subject = strip_package_prefix(subject, source)
                if subject != new_subject:
                    subject = new_subject
                    template += '[src:' +  subject_color + '{src}{t.off}] '
                else:
                    template += '[src:{src}] '
            else:
                new_subject = strip_package_prefix(subject, package)
                if subject != new_subject:
                    subject = new_subject
                    template += '[' +  subject_color + '{pkg}{t.off}] '
                else:
                    template += '[{pkg}] '
        if subject:
            template += subject_color + '{subject}{t.off}'
        else:
            template += '{t.red}(no subject){t.off}'
        colorterm.print(template,
            pkg=package,
            src=source,
            subject=subject,
        )
        indent = '  '
        template = indent + '{t.cyan}https://bugs.debian.org/{n}{t.off}'
        if bug.forwarded:
            template += ' -> {t.cyan}{forwarded}{t.off}'
        colorterm.print(template, n=bug.id, forwarded=bug.forwarded)
        template = indent + '{user}; {date}-00:00'
        user = bug.submitter
        if package == 'wnpp' and bug.owner is not None:
            user = bug.owner
        colorterm.print(template,
            user=user,
            date=bug.date,
        )
        template = ''
        if bug.severity != default_severity:
            severity_color = (
                '{t.bold}{t.red}' if bug.severity in deblogic.rc_severities
                else ''
            )
            template = severity_color + '{severity}{t.off}'
        if bug.tags:
            if template:
                template += ' '
            template += '{tags}'
        if template:
            template = indent + template
            colorterm.print(template,
                tags=' '.join('+' + t for t in bug.tags),
                severity=bug.severity,
            )
        template = ''
        if bug.found_versions:
            template = 'found in {found}'
        if bug.fixed_versions:
            if template:
                template += '; '
            template += 'fixed in {fixed}'
        if template:
            template = indent + template
            colorterm.print(template,
                found=', '.join(bug.found_versions),
                fixed=', '.join(bug.fixed_versions),
            )
        print()

__all__ = [
    'add_argument_parser',
    'run'
]

# vim:ts=4 sts=4 sw=4 et