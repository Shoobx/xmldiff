"""
xmldiff non regression test
"""
from os.path import join, basename, dirname
import sys
import six
import pytest
import glob

from xmldiff import main

HERE = dirname(__file__)


def get_output(options, expected):
    backup = sys.stdout

    # capture stdout
    sys.stdout = six.StringIO()
    try:
        main.run(options)
    except SystemExit:
        pass
    finally:
        output = sys.stdout.getvalue().strip()
        sys.stdout.close()
        sys.stdout = backup

    return output


def test_recursive():
    options = ['-r', join(HERE, 'data', 'dir1'), join(HERE, 'data', 'dir2')]
    expected = """--------------------------------------------------------------------------------
FILE: onlyindir1.xml deleted
--------------------------------------------------------------------------------
FILE: onlyindir2.xml added
--------------------------------------------------------------------------------
FILE: inbothdir.xml"""
    data = get_output(options, expected)
    assert data == expected, '%s:\n%r != %r' % (options, data, expected)


def test_broken():
    options = ['-r', join(HERE, 'data', 'broken', 'broken.xml'),
               join(HERE, 'data', 'broken', 'broken.xml')]
    expected = "xmldiff/tests/data/broken/broken.xml:11:4: mismatched tag"
    data = get_output(options, expected)
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

    result = []
    for t_name, t_dict in tests.items():
        # quick check whether input, output, result is there
        old = t_dict['old']
        new = t_dict['new']
        res_data = t_dict['result']

    return sorted(tests.values())


@pytest.fixture(params=make_tests())
def fnames(request):
    return request.param


def test_known(fnames, lcs2_type):
    old = fnames['old']
    new = fnames['new']
    res_file = fnames['result']
    f = open(res_file)
    expected = f.read().strip()
    f.close()
    options = [old, new]
    data = get_output(options, expected)
    assert data == expected, '%s:\n%r != %r' % (options, data, expected)
