# Copyright (c) 2000 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
""" unit tests for xmldiff.
"""

import os
import lxml.etree
import mock
import six

from xmldiff.input import tree_from_stream
from xmldiff.input import tree_from_lxml

from xmldiff.objects import N_VALUE, N_CHILDS, N_PARENT


HERE = os.path.dirname(__file__)


def _nuke_parent(tree):
    # having the parent node is cool, but causes all sort of problems
    # with asserts and comparison... get rid of it
    tree[N_PARENT] = None
    for child in tree[N_CHILDS]:
        _nuke_parent(child)


def test_tree_from_stream_simple():
    stream = six.StringIO("""
    <a>
      <b/>
      <c>
      </c>
      <d>
        <e>
          <h/>
        </e>
        <f>
        </f>
      </d>
    </a>
    """)
    tree = tree_from_stream(stream)
    expected = [
        6,
        '/',
        '',
        [[1,
          u'a',
          u'a',
          [[1, u'b', u'b', [], mock.ANY, 0, 1],
           [1, u'c', u'c', [], mock.ANY, 0, 1],
           [1,
            u'd',
            u'd',
            [[1,
              u'e',
              u'e',
              [[1,
                u'h',
                u'h',
                [],
                mock.ANY,
                0,
                1]],
              mock.ANY,
              1,
              1],
             [1,
              u'f',
              u'f',
              [],
              mock.ANY,
              0,
              1]],
            mock.ANY,
            3,
            1]],
          mock.ANY,
          6,
          1]],
        None,
        7,
        0]
    assert tree == expected


def test_tree_from_stream():
    fname = os.path.join(HERE, 'data', 'parse', '1.xml')
    with open(fname, 'r') as fhandle:
        tree = tree_from_stream(fhandle)
        # lets not dump the whole tree
        assert len(tree[N_CHILDS]) == 1


def test_tree_from_stream_utf8():
    fname = os.path.join(HERE, 'data', 'parse', 'utf8.xml')
    with open(fname, 'rb') as fhandle:
        tree = tree_from_stream(fhandle)
        type_node = tree[N_CHILDS][0][N_CHILDS][0][N_CHILDS][0][N_CHILDS][0]
        text_node = tree[N_CHILDS][0][N_CHILDS][0][N_CHILDS][1][N_CHILDS][0]
        assert type_node[N_VALUE] == u'\xf6\xfc'
        assert text_node[N_VALUE] == u'\xe9\xe1\u03a9'


def test_tree_from_stream_utf16():
    fname = os.path.join(HERE, 'data', 'parse', 'utf16.xml')
    with open(fname, 'rb') as fhandle:
        tree = tree_from_stream(fhandle)
        type_node = tree[N_CHILDS][0][N_CHILDS][0][N_CHILDS][0][N_CHILDS][0]
        text_node = tree[N_CHILDS][0][N_CHILDS][0][N_CHILDS][1][N_CHILDS][0]
        assert type_node[N_VALUE] == u'\xf6\xfc'
        assert text_node[N_VALUE] == u'\xe9\xe1\u03a9'


def test_tree_from_stream_iso():
    fname = os.path.join(HERE, 'data', 'parse', 'iso.xml')
    with open(fname, 'rb') as fhandle:
        tree = tree_from_stream(fhandle)
        type_node = tree[N_CHILDS][0][N_CHILDS][0][N_CHILDS][0][N_CHILDS][0]
        text_node = tree[N_CHILDS][0][N_CHILDS][0][N_CHILDS][1][N_CHILDS][0]
        assert type_node[N_VALUE] == u'\xf6\xfc'
        assert text_node[N_VALUE] == u'\xe9\xe1'


def test_tree_from_stream_with_namespace():
    fname = os.path.join(HERE, 'data', 'parse', 'simple_ns.xml')
    with open(fname, 'r') as fhandle:
        tree = tree_from_stream(fhandle)

    _nuke_parent(tree)

    expected = [
        6,
        '/',
        '',
        [[1,
          u'{urn:corp:sec}section',
          u'{urn:corp:sec}section',
          [[1,
            u'{urn:corp:sec}sectionInfo',
            u'{urn:corp:sec}sectionInfo',
            [[1,
              u'{urn:corp:sec}secID',
              u'{urn:corp:sec}secID',
              [[4, 'text()', u'S001', [], None, 0, 1]],
              None,
              1,
              1],
             [1,
              u'{urn:corp:sec}name',
              u'{urn:corp:sec}name',
              [[4, 'text()', u'Sales', [], None, 0, 1]],
              None,
              1,
              1]],
            None,
            4,
            1],
           [1,
            u'{urn:corp:sec}sectionInfo',
            u'{urn:corp:sec}sectionInfo',
            [[2,
              u'@nameName',
              u'name',
              [[3, u'@name', u'Development', [], None, 0, 0]],
              None,
              1,
              0],
             [2,
              u'@secIDName',
              u'secID',
              [[3, u'@secID', u'S002', [], None, 0, 0]],
              None,
              1,
              0]],
            None,
            4,
            2],
           [1,
            u'{urn:corp:sec}sectionInfo',
            u'{urn:corp:sec}sectionInfo',
            [[2,
              u'@{urn:corp:sec}nameName',
              u'{urn:corp:sec}name',
              [[3, u'@{urn:corp:sec}name', u'Gardening', [], None, 0, 0]],
              None,
              1,
              0],
             [2,
              u'@{urn:corp:sec}secIDName',
              u'{urn:corp:sec}secID',
              [[3, u'@{urn:corp:sec}secID', u'S003', [], None, 0, 0]],
              None,
              1,
              0]],
            None,
            4,
            3]],
          None,
          15,
          1]],
        None,
        16,
        0]

    assert tree == expected


def test_tree_from_lxml():
    fname = os.path.join(HERE, 'data', 'parse', '1.xml')
    xml = lxml.etree.parse(fname)
    tree = tree_from_lxml(xml)
    assert len(tree[N_CHILDS]) == 1

    fname = os.path.join(HERE, 'data', 'parse', '1.xml')
    with open(fname, 'r') as fhandle:
        tree_stream = tree_from_stream(fhandle)

    _nuke_parent(tree)
    _nuke_parent(tree_stream)

    assert tree == tree_stream


def test_tree_from_lxml_with_namespace():
    fname = os.path.join(HERE, 'data', 'parse', 'simple_ns.xml')
    xml = lxml.etree.parse(fname)
    tree = tree_from_lxml(xml)

    with open(fname, 'r') as fhandle:
        tree_stream = tree_from_stream(fhandle)

    _nuke_parent(tree)
    _nuke_parent(tree_stream)

    assert tree == tree_stream

    fname = os.path.join(HERE, 'data', 'parse', 'tal_ns.xml')
    xml = lxml.etree.parse(fname)
    tree = tree_from_lxml(xml)

    with open(fname, 'r') as fhandle:
        tree_stream = tree_from_stream(fhandle)

    _nuke_parent(tree)
    _nuke_parent(tree_stream)

    assert tree == tree_stream


def test_parse_html():
    fname = os.path.join(HERE, 'data', 'parse', 'html.html')
    with open(fname, 'r') as fhandle:
        tree = tree_from_stream(fhandle, html=True)
        # lets not dump the whole tree
        assert len(tree[N_CHILDS]) == 1
