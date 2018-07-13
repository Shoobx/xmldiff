import glob
import lxml.etree
import os
import unittest

from xmldiff.input import tree_from_lxml
from xmldiff.fmes import FmesCorrector
from xmldiff.format import InternalPrinter
from six import StringIO


class PerformanceTest(unittest.TestCase):
    # This tests don't fail, they just run the diff loads of times
    # so you can get a rough measurement of how long it takes.
    # It's disabled by default (prefixed with "no_").

    def no_test_performance(self):
        HERE = os.path.dirname(__file__)
        left_files = glob.glob(os.path.join(HERE, 'data', '*_1.xml'))
        right_files = glob.glob(os.path.join(HERE, 'data', '*_2.xml'))

        for left, right in zip(sorted(left_files), sorted(right_files)):
            with open(left, 'rb') as leftfile, open(right, 'rb') as rightfile:
                lefttree = tree_from_lxml(lxml.etree.parse(leftfile))
                righttree = tree_from_lxml(lxml.etree.parse(rightfile))

            stream = StringIO()
            formatter = InternalPrinter(stream=stream)
            # Prioritized xmlid, and increase f to 0.7, to get better matches.
            strategy = FmesCorrector(formatter, f=0.7)

            for i in range(1000):
                strategy.process_trees(lefttree, righttree)
