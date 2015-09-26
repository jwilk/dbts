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
        colorterm.print('{n:>7} {t.bold}{subject}{t.off}',
            n='#{n}'.format(n=bug.id),
            subject=bug.subject,
        )

__all__ = [
    'add_argument_parser',
    'run'
]

# vim:ts=4 sts=4 sw=4 et
