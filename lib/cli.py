# Copyright © 2015-2017 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

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
