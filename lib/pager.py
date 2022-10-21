# Copyright © 2015 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

'''
automatic pager
'''

import contextlib
import io
import os
import subprocess as ipc
import sys

@contextlib.contextmanager
def autopager():
    if not sys.stdout.isatty():
        yield
        return
    cmdline = os.environ.get('PAGER', 'pager')
    if cmdline == 'cat':
        yield
        return
    env = None
    if 'LESS' not in os.environ:
        env = dict(env or os.environ, LESS='-FRXi')
    if 'LV' not in os.environ:
        env = dict(env or os.environ, LV='-c')
    orig_stdout = sys.stdout
    try:
        pager = ipc.Popen(cmdline, shell=True, stdin=ipc.PIPE, env=env)
        try:
            sys.stdout = io.TextIOWrapper(pager.stdin,
                encoding=orig_stdout.encoding,
            )
            try:
                yield
            finally:
                sys.stdout.close()
        finally:
            pager.wait()
    finally:
        sys.stdout = orig_stdout

__all__ = [
    'autopager',
]

# vim:ts=4 sts=4 sw=4 et
