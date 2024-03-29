# Copyright © 2015-2022 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

'''
automatic pager
'''

import contextlib
import io
import os
import subprocess as ipc
import sys

class Error(RuntimeError):
    pass

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
        env = dict(env or os.environ, LESS='-FXRi')
    if 'LV' not in os.environ:
        env = dict(env or os.environ, LV='-c')
    orig_stdout = sys.stdout
    try:
        pager = ipc.Popen(cmdline, shell=True, stdin=ipc.PIPE, env=env)
        try:
            sys.stdout = io.TextIOWrapper(pager.stdin,
                encoding=orig_stdout.encoding,
                errors=orig_stdout.errors,
            )
            try:
                yield
            finally:
                sys.stdout.close()
        finally:
            pager.wait()
    finally:
        sys.stdout = orig_stdout
    if pager.returncode:
        raise Error

__all__ = [
    'Error',
    'autopager',
]

# vim:ts=4 sts=4 sw=4 et
