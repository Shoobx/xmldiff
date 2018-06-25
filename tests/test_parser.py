# Copyright (c) 2000-2010 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
# Copyright (c) 2018 Shoobx.com.
# https://www.shoobx.com/ -- mailto:dev@shoobx.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
""" unit tests for xmldiff.
"""

import os
import lxml.etree
import mock
import six

from xmldiff.input import tree_from_stream
from xmldiff.input import tree_from_lxml

from xmldiff.objects import N_VALUE, N_CHILDS, N_PARENT, N_NSPREFIX


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
          [[1, u'b', u'b', [], mock.ANY, 0, 1, None],
           [1, u'c', u'c', [], mock.ANY, 0, 1, None],
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
                1,
                None]],
              mock.ANY,
              1,
              1,
              None],
             [1,
              u'f',
              u'f',
              [],
              mock.ANY,
              0,
              1,
              None]],
            mock.ANY,
            3,
            1,
            None]],
          mock.ANY,
          6,
          1,
          None]],
        None,
        7,
        0,
        None]
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
              [[4, 'text()', u'S001', [], None, 0, 1, None]],
              None,
              1,
              1,
              'sec'],
             [1,
              u'{urn:corp:sec}name',
              u'{urn:corp:sec}name',
              [[4, 'text()', u'Sales', [], None, 0, 1, None]],
              None,
              1,
              1,
              'sec']],
            None,
            4,
            1,
            'sec'],
           [1,
            u'{urn:corp:sec}sectionInfo',
            u'{urn:corp:sec}sectionInfo',
            [[2,
              u'@nameName',
              u'name',
              [[3, u'@name', u'Development', [], None, 0, 0, None]],
              None,
              1,
              0,
              None],
             [2,
              u'@secIDName',
              u'secID',
              [[3, u'@secID', u'S002', [], None, 0, 0, None]],
              None,
              1,
              0,
              None]],
            None,
            4,
            2,
            'sec'],
           [1,
            u'{urn:corp:sec}sectionInfo',
            u'{urn:corp:sec}sectionInfo',
            [[2,
              u'@{urn:corp:sec}nameName',
              u'{urn:corp:sec}name',
              [[3, u'@{urn:corp:sec}name', u'Gardening', [], None, 0, 0, 'sec']],
              None,
              1,
              0,
              'sec'],
             [2,
              u'@{urn:corp:sec}secIDName',
              u'{urn:corp:sec}secID',
              [[3, u'@{urn:corp:sec}secID', u'S003', [], None, 0, 0, 'sec']],
              None,
              1,
              0,
              'sec']],
            None,
            4,
            3,
            'sec']],
          None,
          15,
          1,
          'sec']],
        None,
        16,
        0,
        None]

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


# In lxml, up to and including version 4.2.1, the namespace prefixes
# will be replaced by auto-generated namespace prefixes, ns00, ns01, etc
# If we encounter an "ns00:"" prefix, replace it.
# This code can be removed once we no longer need to run the tests with
# lxml 4.2.1 or earlier.
# This is only to fix this test, using xmldiff with these versions of
# lxml will still work, but the prefixes will be wrong.
def fix_lxml_421_tree(t, prefix):
    if t[N_NSPREFIX] == 'ns00':
        t[N_NSPREFIX] = prefix
    for subtree in t[3]:
        fix_lxml_421_tree(subtree, prefix)


def test_tree_from_lxml_with_namespace():
    fname = os.path.join(HERE, 'data', 'parse', 'simple_ns.xml')
    xml = lxml.etree.parse(fname)
    tree = tree_from_lxml(xml)

    with open(fname, 'r') as fhandle:
        tree_stream = tree_from_stream(fhandle)

    _nuke_parent(tree)
    _nuke_parent(tree_stream)

    # lxml <= 4.2.1
    fix_lxml_421_tree(tree, 'sec')

    assert tree == tree_stream

    fname = os.path.join(HERE, 'data', 'parse', 'tal_ns.xml')
    xml = lxml.etree.parse(fname)
    tree = tree_from_lxml(xml)

    with open(fname, 'r') as fhandle:
        tree_stream = tree_from_stream(fhandle)

    _nuke_parent(tree)
    _nuke_parent(tree_stream)

    # lxml <= 4.2.1
    fix_lxml_421_tree(tree, 'z')

    assert tree == tree_stream


def test_tree_from_lxml_with_default_namespace():
    fname = os.path.join(HERE, 'data', 'parse', 'default_ns.xml')
    xml = lxml.etree.parse(fname)
    tree = tree_from_lxml(xml)

    with open(fname, 'r') as fhandle:
        tree_stream = tree_from_stream(fhandle)

    _nuke_parent(tree)
    _nuke_parent(tree_stream)

    fix_lxml_421_tree(tree, None)

    assert tree == tree_stream


def test_parse_html():
    fname = os.path.join(HERE, 'data', 'parse', 'html.html')
    with open(fname, 'r') as fhandle:
        tree = tree_from_stream(fhandle, html=True)
        # lets not dump the whole tree
        assert len(tree[N_CHILDS]) == 1
