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

'''
very crude dot parser
'''

import collections
import re

from lib import indent

class Node(object):

    def __init__(self, name, **attrs):
        self.name = name
        self._attrs = attrs

    def __repr__(self):
        return '{tp}({name!r}, ...)'.format(
            tp=type(self).__name__,
            name=self.name,
        )

    def __str__(self):
        return self._attrs.get('label', self.name)

    def get(self, attr):
        return self._attrs.get(attr)

class Graph(object):

    def __init__(self, nodes, edges):
        self.nodes = {
            node.name: node
            for node in nodes
        }
        self.edges = collections.defaultdict(set)
        for src, dst in edges:
            self.edges[src].add(dst)

    def pprint(self, render=str):
        roots = set(self.nodes.keys())
        for dsts in self.edges.values():
            roots -= dsts
        seen = set()
        def p(node_name, level):
            if node_name in seen:
                return
            node = self.nodes[node_name]
            label = render(node)
            label = indent.indent(label, level * 2, bullet='∙ ')
            print(label)
            seen.add(node_name)
            for child in sorted(self.edges[node_name]):
                p(child, level + 1)
        for root in sorted(roots):
            p(root, 0)

    def __repr__(self):
        return '{tp}({nodes!r}, {edges!r})'.format(
            tp=type(self).__name__,
            nodes=list(self.nodes.values()),
            edges=self.edges,
        )

def parse(dot_data):
    match = re.match(r'\Adigraph\s*\w+\s*{\s*(.*)}\s*\Z', dot_data, flags=re.DOTALL)
    lines = match.group(1)
    nodes = set()
    edges = set()
    for line in lines.splitlines():
        match = re.match(r'^"([^"]+)"\s+\[(.*)\]$', line)
        if match is not None:
            [name, tattrs] = match.groups()
            attrs = {}
            for attr in re.findall(r'\w+="[^"]*"', tattrs):
                aname, avalue = attr.split('=', 1)
                avalue = avalue.strip('"')
                avalue = avalue.replace(r'\n', '\n')
                attrs[aname] = avalue
            nodes.add(Node(name, **attrs))
            continue
        match = re.match(r'^"([^"]+)"->"([^"]+)"\s+\[dir="back"\]$', line)
        [name1, name2] = match.groups()
        edges.add((name2, name1))
    return Graph(nodes, edges)

# vim:ts=4 sts=4 sw=4 et
