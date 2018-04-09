

import unittest
import os

import xmldiff.main

_xmlpath = xmldiff.main.__file__


class TestProfile(unittest.TestCase):
    def test_profiler(self):
        res = os.system(
            "python %s --profile=test.prof data/test00_1.xml data/test00_2.xml" % _xmlpath)
        self.assert_(res == 0)
        self.assert_(os.access("test.prof", os.R_OK))


if __name__ == "__main__":
    unittest.main()
