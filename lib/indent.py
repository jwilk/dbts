# Copyright © 2015 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

'''
indenting multi-line strings
'''

import re

def indent(s, n, bullet=''):
    blen = len(bullet)
    return re.sub(
        '^',
        ' ' * (n + blen),
        bullet + s,
        flags=re.MULTILINE
    )[blen:]

__all__ = [
    'indent',
]

# vim:ts=4 sts=4 sw=4 et
