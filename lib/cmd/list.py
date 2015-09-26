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

'the “list” command'

from lib import colorterm
from lib import debsoap

def add_argument_parser(subparsers):
    ap = subparsers.add_parser('list')
    ap.add_argument('packages', metavar='PKG', type=str, nargs='+')
    return ap

def run(options):
    for package in options.packages:
        run_one(package, options=options)

def run_one(package, *, options):
    debsoap_client = debsoap.Client(session=options.session)
    bugs = debsoap_client.get_bugs(package=package)
    for bug in bugs:
        colorterm.print('{n:>7} [{pkg}] {t.bold}{subject}{t.off}',
            n='#{n}'.format(n=bug.id),
            pkg=bug.package,
            subject=bug.subject,
        )
        template = '        {submitter}; {date}-00:00'
        if bug.tags:
            template += '; {tags}'
        colorterm.print(template,
            submitter=bug.submitter,
            date=bug.date,
            tags=' '.join(bug.tags)
        )
        template = ''
        if bug.found_versions:
            template = 'found in {found}'
        if bug.fixed_versions:
            if template:
                template += '; '
            template += 'fixed in {fixed}'
        if template:
            template = '        ' + template
            colorterm.print(template,
                found=' ,'.join(bug.found_versions),
                fixed=' ,'.join(bug.fixed_versions),
            )

__all__ = [
    'add_argument_parser',
    'run'
]

# vim:ts=4 sts=4 sw=4 et
