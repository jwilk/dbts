# Copyright © 2015-2022 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

'''
various utilities
'''

import os
import subprocess
import signal

def looks_like_path(s):
    return (
        s == '.' or
        s.startswith(('./', '../', '/'))
    )

def raise_SIGPIPE():
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    os.kill(os.getpid(), signal.SIGPIPE)

def xcmd(*cmdline):
    return subprocess.check_output(cmdline)

__all__ = [
    'looks_like_path',
    'raise_SIGPIPE',
    'xcmd',
]

# vim:ts=4 sts=4 sw=4 et
