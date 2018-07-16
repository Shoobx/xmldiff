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
"""
xmldiff non regression test
"""
from os.path import join, basename, dirname
import re
import sys
import six
import pytest
import glob

from xmldiff import main

HERE = dirname(__file__)


def get_output(options):
    backup = sys.stdout

    # capture stdout
    sys.stdout = out = six.StringIO()
    try:
        main.run(options)
    except SystemExit:
        pass
    finally:
        sys.stdout = backup
        output = out.getvalue().strip()
        out.close()

    return output


def test_recursive():
    options = ['-r', join(HERE, 'data', 'dir1'), join(HERE, 'data', 'dir2')]
    expected = """--------------------------------------------------------------------------------
FILE: onlyindir1.xml deleted
--------------------------------------------------------------------------------
FILE: dir_inboth/onlyindir1.xml deleted
--------------------------------------------------------------------------------
DIRECTORY: dir_only1 deleted
--------------------------------------------------------------------------------
FILE: onlyindir2.xml added
--------------------------------------------------------------------------------
FILE: dir_inboth/onlyindir2.xml added
--------------------------------------------------------------------------------
DIRECTORY: dir_only2 added
--------------------------------------------------------------------------------
FILE: changing.xml
[append-first, /,
<gap/>
]
[remove, /oopoyy[1]]
--------------------------------------------------------------------------------
FILE: inbothdir.xml
--------------------------------------------------------------------------------
FILE: dir_inboth/changing.xml
[append-first, /,
<gap/>
]
[remove, /oopoyy[1]]
--------------------------------------------------------------------------------
FILE: dir_inboth/inbothdir.xml"""
    data = get_output(options)
    assert data == expected, '%s:\n%r != %r' % (options, data, expected)


def test_broken():
    options = ['-r', join(HERE, 'data', 'broken', 'broken.xml'),
               join(HERE, 'data', 'broken', 'broken.xml')]
    expected = "xmldiff/tests/data/broken/broken.xml:11:4: mismatched tag"
    data = get_output(options)
    assert expected in data


def test_verbose():
    options = ['--verbose', join(HERE, 'data', 'test01_1.xml'),
               join(HERE, 'data', 'test01_2.xml')]
    expected = """Source tree:
R: (/) node-id 2
  \-NN:oopoyy (/oopoyy[1]) node-id 1
    \-NN:function (/oopoyy[1]/function[1]) node-id 0

Destination tree:
R: (/) node-id 1
  \-NN:gap (/gap[1]) node-id 0

Source tree has 2 nodes
Destination tree has 1 nodes
[append-first, /,
<gap/>
]
[remove, /oopoyy[1]]"""
    data = get_output(options)
    data = re.sub(r"\d{10,20}", "node-id", data)
    assert expected in data


def test_wrong_combo():
    options = ['-r', join(HERE, 'data', 'dir1'), join(HERE, 'data', 'test00_1.xml')]
    expected = "are not comparable, or not directory nor regular files"
    data = get_output(options)
    assert expected in data


def make_tests():
    """generate tests classes from test info

    return the list of generated test classes
    """
    tests_files = glob.glob(join(HERE, 'data', '*.xml')) + \
        glob.glob(join(HERE, 'data', '*_result'))
    tests = {}
    # regroup test files
    for filename in tests_files:
        base = basename(filename)
        name = base[:6]
        filetype = base[-5:]
        if filetype == '1.xml':
            tests.setdefault(name, {})['old'] = filename
        elif filetype == '2.xml':
            tests.setdefault(name, {})['new'] = filename
        else:
            tests.setdefault(name, {})['result'] = filename

    for t_dict in tests.values():
        # quick check whether input, output, result is there
        t_dict['old']
        t_dict['new']
        t_dict['result']

    return sorted(tests.values(), key=lambda td: td['old'])


@pytest.fixture(params=make_tests())
def fnames(request):
    return request.param


def test_known(fnames):
    old = fnames['old']
    new = fnames['new']
    res_file = fnames['result']
    with open(res_file) as f:
        expected = f.read().strip()
    options = [old, new]
    data = get_output(options)
    assert data == expected, '%s:\n%r != %r' % (options, data, expected)
