
import unittest
from xmldiff.mydifflib import quick_ratio, lcs2

def _cmp( a, b ):
    return a==b

class TestLcs2(unittest.TestCase):
    def help_test(self, seq1, seq2, res ):
        seq = lcs2( seq1, seq2, _cmp )
        self.assertEqual( seq, zip( res, res ) )

    def test_lcs_1(self):
        self.help_test( "abcdefghijkl", "bcdeghijk", "bcdeghijk" )

    def test_lcs_2(self):
        self.help_test( "abdefghijkl", "bcdeghijk", "bdeghijk" )

    def test_lcs_3(self):
        self.help_test( "abdefghijkl", "bxcydzewgzhijk", "bdeghijk" )

    def test_lcs_4(self):
        self.help_test( "abdefghijkl", "zzzbcdeghijk", "bdeghijk" )

if __name__ == "__main__":
    unittest.main()

