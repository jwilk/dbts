# Copyright © 2015-2024 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

'''
various utilities
'''

import os
import signal
import subprocess

def looks_like_path(s):
    return (
        s == '.' or
        s.startswith(('./', '../', '/'))
    )

def raise_SIGPIPE():
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    os.kill(os.getpid(), signal.SIGPIPE)

def xcmd(*cmdline):
    def reset_locale():
        os.environ['LC_ALL'] = 'C'
    proc = subprocess.run(
        cmdline,
        stdout=subprocess.PIPE,
        preexec_fn=reset_locale,
        check=True,
    )
    return proc.stdout

__all__ = [
    'looks_like_path',
    'raise_SIGPIPE',
    'xcmd',
]

# vim:ts=4 sts=4 sw=4 et
