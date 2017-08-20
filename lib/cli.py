# Copyright © 2015-2017 Jakub Wilk <jwilk@jwilk.net>
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

'''
command-line interface
'''

import argparse
import importlib

from lib import pager
from lib import web

def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers()
    sp.dest = 'cmd'  # https://bugs.python.org/issue9253
    sp.required = True
    for cmd in ['ls', 'show', 'new']:
        mod = importlib.import_module('lib.cmd.{cmd}'.format(cmd=cmd))
        mod.add_argument_parser(sp)
    options = ap.parse_args()
    options.session = web.UserAgent()
    mod = importlib.import_module('lib.cmd.{cmd}'.format(cmd=options.cmd))
    options.error = ap.error
    with pager.autopager():
        mod.run(options)

__all__ = [
    'main',
]

# vim:ts=4 sts=4 sw=4 et
