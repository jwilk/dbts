#!/usr/bin/python3

# Copyright © 2015 Jakub Wilk <jwilk@jwilk.net>
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

import argparse
import importlib
import os

import appdirs
import requests

if int(requests.__version__.split('.')[0]) < 1:
    raise RuntimeError('requests >= 1.0 is required')

def setup_cache():
    try:
        import requests_cache
    except ImportError:
        return
    cache_dir = appdirs.user_cache_dir('dbts')
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, 0o700)
    cache_name = '{dir}/cache'.format(dir=cache_dir)
    requests_cache.install_cache(
        cache_name=cache_name,
        backend='sqlite',
        allowable_methods=('GET', 'POST'),
    )

def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers()
    sp.dest = 'cmd'  # https://bugs.python.org/issue9253
    sp.required = True
    cmd_show = sp.add_parser('show')
    cmd_show.add_argument('bug', metavar='BUGNO')
    options = ap.parse_args()
    setup_cache()
    session = requests.Session()
    session.verify = True
    session.trust_env = False
    session.headers['User-Agent'] = 'dbts (https://github.com/jwilk/dbts)'
    options.session = session
    mod = importlib.import_module('lib.cmd.{cmd}'.format(cmd=options.cmd))
    mod.run(options)

# vim:ts=4 sts=4 sw=4 et
