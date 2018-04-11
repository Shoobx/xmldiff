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
import mock
import six
from xmldiff.parser import SaxHandler
from xmldiff.input import tree_from_stream
from xml.sax import make_parser

from xmldiff.objects import NT_ROOT, NT_NODE, NT_ATTN, NT_ATTV, \
    NT_TEXT, NT_COMM, N_TYPE, N_NAME, N_VALUE, N_CHILDS, N_PARENT, N_ISSUE, \
    N_XNUM, NSIZE, A_DESC, A_N1, A_N2, FALSE, TRUE


HERE = os.path.dirname(__file__)


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
    with open(fname, 'r') as fhandle:
        tree = tree_from_stream(fhandle)
        type_node = tree[N_CHILDS][0][N_CHILDS][0][N_CHILDS][0][N_CHILDS][0]
        text_node = tree[N_CHILDS][0][N_CHILDS][0][N_CHILDS][1][N_CHILDS][0]
        assert type_node[N_VALUE] == u'\xf6\xfc'
        assert text_node[N_VALUE] == u'\xe9\xe1\u03a9'


def test_tree_from_stream_utf16():
    fname = os.path.join(HERE, 'data', 'parse', 'utf16.xml')
    with open(fname, 'r') as fhandle:
        tree = tree_from_stream(fhandle)
        type_node = tree[N_CHILDS][0][N_CHILDS][0][N_CHILDS][0][N_CHILDS][0]
        text_node = tree[N_CHILDS][0][N_CHILDS][0][N_CHILDS][1][N_CHILDS][0]
        assert type_node[N_VALUE] == u'\xf6\xfc'
        assert text_node[N_VALUE] == u'\xe9\xe1\u03a9'


def test_tree_from_stream_iso():
    fname = os.path.join(HERE, 'data', 'parse', 'iso.xml')
    with open(fname, 'r') as fhandle:
        tree = tree_from_stream(fhandle)
        type_node = tree[N_CHILDS][0][N_CHILDS][0][N_CHILDS][0][N_CHILDS][0]
        text_node = tree[N_CHILDS][0][N_CHILDS][0][N_CHILDS][1][N_CHILDS][0]
        assert type_node[N_VALUE] == u'\xf6\xfc'
        assert text_node[N_VALUE] == u'\xe9\xe1'
