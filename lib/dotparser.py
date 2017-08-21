# Copyright © 2015 Jakub Wilk <jwilk@jwilk.net>
# SPDX-License-Identifier: MIT

'''
very crude dot parser
'''

import collections
import io
import re
import sys

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

    def pprint(self, *, file=sys.stdout, render=str, bullet='∙'):
        roots = set(self.nodes.keys())
        for dsts in self.edges.values():
            roots -= dsts
        seen = set()
        def p(node_name, ilevel):
            if node_name in seen:
                return
            node = self.nodes[node_name]
            label = render(node)
            label = indent.indent(
                label,
                max(0, (ilevel - 1) * 2),
                bullet=(bullet + ' ' if ilevel > 0 else '')
            )
            print(label, file=file)
            seen.add(node_name)
            for child in sorted(self.edges[node_name]):
                p(child, ilevel + 1)
        for root in sorted(roots):
            p(root, 0)

    def pformat(self, *, render=str, bullet='∙'):
        fp = io.StringIO()
        self.pprint(file=fp, render=render, bullet=bullet)
        return fp.getvalue()

    def __bool__(self):
        return len(self.edges) > 0

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

__all__ = [
    'Graph',
    'Node',
    'parse',
]

# vim:ts=4 sts=4 sw=4 et
