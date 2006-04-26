"""
xmldiff non regression test
"""
__revision__ = "$Id: regrtest.py,v 1.19 2005-04-27 12:36:01 syt Exp $"

from __future__ import nested_scopes
from os.path import join, basename
from cStringIO import StringIO
import sys
import os
import unittest
import glob

from xmldiff import main 

DATA_DIR = 'data'

class BaseTest(unittest.TestCase):
    def check_output(self, options, expected):
        try:
            output = os.popen('%s %s %s' % (sys.executable,
                                            main.__file__,
                                            ' '.join(options)))
        except SystemExit:
            pass
        data = output.read().strip()
        output.close()
        self.assertEqual(data, expected, '%s:\n%r != %r' %
                         (self.name, data, expected) )
        

class DiffTest(BaseTest):
    
    def test_known(self):
        old = self.data['old']
        new = self.data['new']
        for options, res_file in self.data['result']:
            options = options + [old, new]
            f = open(res_file)
            expected = f.read().strip()
            f.close()
            self.check_output(options, expected)


class RecursiveDiffTest(BaseTest):
    name = 'RecursiveDiffTest'
    def test(self):
        options = ['-r', join(DATA_DIR, 'dir1'), join(DATA_DIR, 'dir2')]
        expected = """--------------------------------------------------------------------------------
FILE: onlyindir1.xml deleted
--------------------------------------------------------------------------------
FILE: onlyindir2.xml added
--------------------------------------------------------------------------------
FILE: inbothdir.xml"""
        self.check_output(options, expected)

def make_tests():
    """generate tests classes from test info
    
    return the list of generated test classes
    """
    tests_files = glob.glob(join(DATA_DIR, '*.xml')) + glob.glob(join(DATA_DIR, '*_result')) + glob.glob(join(DATA_DIR, '*_result_xupdate'))
    tests = {}
    # regroup test files
    for filename in tests_files:
        base = basename(filename)
        name = base[:6]
        filetype = base[7:]
        if filetype == '1.xml':
            tests.setdefault(name, {})['old'] = filename
        elif filetype == '2.xml':
            tests.setdefault(name, {})['new'] = filename
        else:
            options = filetype.split('_')[:-1]
            tests.setdefault(name, {}).setdefault('result', []).append(
                [options, filename])
                    
    result = []
    for t_name, t_dict in tests.items():
        try:
            old = t_dict['old']
            new = t_dict['new']
            res_data = t_dict['result']
        except KeyError, e:
            msg = '** missing files in %s (%s)' % (t_name, e)
            print >>sys.stderr, msg
            continue
            
        class DiffTestSubclass(DiffTest):
            name = t_name
            data = t_dict
                
        result.append(DiffTestSubclass)
    return result


    
def suite():
    return unittest.TestSuite([unittest.makeSuite(test)
                               for test in make_tests() + [RecursiveDiffTest]])

def Run(runner=None):
    testsuite = suite()
    if runner is None:
        runner = unittest.TextTestRunner()
    return runner.run(testsuite)

   
if __name__ == '__main__':
    Run()
