# Copyright © 2015-2021 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

'''
Debian constants, etc.
'''

import re
import urllib.parse

rc_severities = (
    'serious',
    'grave',
    'critical',
)

severities = (
    'wishlist',
    'minor',
    'normal',
    'important',
    *rc_severities
)

wnpp_tags = {
    'O',
    'RFA',
    'ITA',
    'RFH',
    'ITP',
    'RFP',
}

def parse_bugspec(s):
    match = re.match(r'\A[#]?([0-9]+)\Z', s)
    if match is not None:
        n = match.group(1)
        return int(n)
    url = urllib.parse.urlparse(s)
    if url.scheme not in {'http', 'https'}:
        raise ValueError
    if url.netloc != 'bugs.debian.org':
        raise ValueError
    match = re.match(r'\A/([0-9]+)\Z', url.path)
    if match is not None:
        n = match.group(1)
        return int(n)
    if url.path != '/cgi-bin/bugreport.cgi':
        raise ValueError
    query = url.query.replace(';', '&')
    query = urllib.parse.parse_qs(query)
    try:
        [n] = query['bug']
    except KeyError:
        raise ValueError
    return int(n)

def is_architecture(s):
    match = re.match(r'\A[a-z][a-z0-9-]*\Z', s)
    return match is not None

def is_package_name(s):
    # Policy §5.6.1
    match = re.match(r'\A[a-z0-9][a-z0-9.+-]+\Z', s)
    return match is not None

def is_package_version(s):
    # Policy §5.6.12
    match = re.match(r'\A(?:[0-9]+:)?[a-z0-9.~+-]+\Z', s)
    return match is not None

__all__ = [
    'is_architecture',
    'is_package_name',
    'is_package_version',
    'parse_bugspec',
    'rc_severities',
    'severities',
    'wnpp_tags',
]

# vim:ts=4 sts=4 sw=4 et
