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
import random
import xmldiff.difflib


def _cmp(a, b):
    return a == b


def lcsl(X, Y, equal):
    """return the length of the result sent by lcs2"""
    return len(xmldiff.difflib.lcs2(X, Y, equal))


def help_test(seq1, seq2, res):
    seq = xmldiff.difflib.lcs2(seq1, seq2, _cmp)
    assert seq == list(zip(res, res))


def test_lcs_1():
    help_test("abcdefghijkl", "bcdeghijk", "bcdeghijk")


def test_lcs_2():
    help_test("abdefghijkl", "bcdeghijk", "bdeghijk")


def test_lcs_3():
    help_test("abdefghijkl", "bxcydzewgzhijk", "bdeghijk")


def test_lcs_4():
    help_test("abdefghijkl", "zzzbcdeghijk", "bdeghijk")


def test_lcs_5():
    help_test("", "", [])


def test_lcs_6():
    seq = xmldiff.difflib.lcs4("", "", _cmp)
    assert seq == []


def test_quick_ratio():
    seq = xmldiff.difflib.quick_ratio("", "")
    assert seq == 1


# def test_time_lcs2(lcs2=lcs2):
#     import time
#     t = time.clock()
#     quick_ratio('abcdefghijklmnopqrst'*100, 'abcdefghijklmnopqrst'*100)
#     print 'quick ratio :', time.clock()-t
#     lcs2('abcdefghijklmnopqrst'*100, 'abcdefghijklmnopqrst'*100,
#          lambda x, y: x == y)
#     print 'lcs2 :       ', time.clock()-t
#     quick_ratio('abcdefghijklmno'*100, 'zyxwvutsrqp'*100)
#     print 'quick ratio :', time.clock()-t
#     lcs2('abcdefghijklmno'*100, 'zyxwvutsrqp'*100, lambda x, y: x == y)
#     print 'lcs2 :       ', time.clock()-t
#     quick_ratio('abcdefghijklmnopqrst'*100, 'abcdefghijklmnopqrst'*100)
#     print 'quick ratio :', time.clock()-t
#     lcs2('abcdefghijklmnopqrst'*100, 'abcdefghijklmnopqrst'*100,
#          lambda x, y: x == y)
#     print 'lcs2 :       ', time.clock()-t
#     quick_ratio('abcdefghijklmno'*100, 'zyxwvutsrqp'*100)
#     print 'quick ratio :', time.clock()-t
#     lcs2('abcdefghijklmno'*100, 'zyxwvutsrqp'*100, lambda x, y: x == y)
#     print 'lcs2 :       ', time.clock()-t


# def test_main_lcs2(lcs2=lcs2):
#     print "abcde - bydc"
#     print lcsl('abcde', 'bydc', lambda x, y: x == y)
#     for a in lcs2('abcde', 'bydc', lambda x, y: x == y):
#         print a
#     print "abacdge - bcdg"
#     print lcsl('abacdge', 'bcdg', lambda x, y: x == y)
#     for a in lcs2('abacdge', 'bcdg', lambda x, y: x == y):
#         print a


def randstr(lmin, lmax, alphabet):
    L = random.randint(lmin, lmax)
    S = []
    N = len(alphabet) - 1
    for i in range(L):
        S.append(alphabet[random.randint(0, N)])
    return "".join(S)


def test_random_string():
    """Generate random test sequences and compare lcs2, lcs4"""

    _alpha = "abcdefghijklmnopqrstuvwxyz"
    for i in range(100):
        S1 = randstr(2, 5, _alpha)
        S2 = randstr(2, 5, _alpha)
        # print S1, S2
        R1 = xmldiff.difflib.lcs2(S1, S2, _cmp)
        # print "lcs2:", "".join([x[0] for x in R1])
        R2 = xmldiff.difflib.lcs4(S1, S2, _cmp)
        # print "lcs4", "".join([x[0] for x in R2])
        assert R1 == R2, (S1, S2)
