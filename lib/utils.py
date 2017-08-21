# Copyright © 2015-2017 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

'''
various utilities
'''

import subprocess

def looks_like_path(s):
    return (
        s == '.' or
        s.startswith(('./', '../', '/'))
    )

def xcmd(*cmdline):
    return subprocess.check_output(cmdline)

__all__ = [
    'looks_like_path',
    'xcmd',
]

# vim:ts=4 sts=4 sw=4 et
