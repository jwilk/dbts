# Copyright © 2015-2022 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

'''
command-line interface
'''

import argparse
import importlib

from lib import pager
from lib import utils
from lib import web

def xmain():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers()
    sp.dest = 'cmd'  # https://bugs.python.org/issue9253
    sp.required = True
    for cmd in ['ls', 'show', 'new']:
        mod = importlib.import_module(f'lib.cmd.{cmd}')
        mod.add_argument_parser(sp)
    options = ap.parse_args()
    options.session = web.UserAgent()
    mod = importlib.import_module(f'lib.cmd.{options.cmd}')
    options.error = ap.error
    with pager.autopager():
        mod.run(options)

def main():
    try:
        xmain()
    except BrokenPipeError:
        utils.raise_SIGPIPE()
        raise

__all__ = [
    'main',
]

# vim:ts=4 sts=4 sw=4 et
