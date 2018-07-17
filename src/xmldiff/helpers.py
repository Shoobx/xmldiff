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
longest common subsequence algorithm

the algorithm is describe in "An O(ND) Difference Algorithm and its Variation"
by Eugene W. MYERS

As opposed to the algorithm in difflib.py, this one doesn't require hashable
elements
"""

from six.moves import range


def lcs2(X, Y, equal):
    """
    apply the greedy lcs/ses algorithm between X and Y sequence
    (should be any Python's sequence)
    equal is a function to compare X and Y which must return 0 if
    X and Y are different, 1 if they are identical
    return a list of matched pairs in tuplesthe greedy lcs/ses algorithm
    """
    N, M = len(X), len(Y)
    if not X or not Y:
        return []
    max = N + M
    v = [0 for i in range(2 * max + 1)]
    common = [[] for i in range(2 * max + 1)]

    for D in range(max + 1):
        for k in range(-D, D + 1, 2):
            if k == -D or k != D and v[k - 1] < v[k + 1]:
                x = v[k + 1]
                common[k] = common[k + 1][:]
            else:
                x = v[k - 1] + 1
                common[k] = common[k - 1][:]

            y = x - k
            while x < N and y < M and equal(X[x], Y[y]):
                common[k].append((x, y))
                x += 1
                y += 1

            v[k] = x
            if x >= N and y >= M:
                return [(X[xl], Y[yl]) for xl, yl in common[k]]


def lcs4(X, Y, equal):
    """
    apply the greedy lcs/ses algorithm between X and Y sequence
    (should be any Python's sequence)
    equal is a function to compare X and Y which must return 0 if
    X and Y are different, 1 if they are identical
    return a list of matched pairs in tuplesthe greedy lcs/ses algorithm
    """
    N, M = len(X), len(Y)
    if not X or not Y:
        return []
    max = N + M
    v = [0 for i in range(2 * max + 1)]
    vl = [v]
    for D in range(max + 1):
        for k in range(-D, D + 1, 2):
            if k == -D or k != D and v[k - 1] < v[k + 1]:
                x = v[k + 1]
            else:
                x = v[k - 1] + 1

            y = x - k
            while x < N and y < M and equal(X[x], Y[y]):
                x += 1
                y += 1

            v[k] = x
            if x >= N and y >= M:
                # reconstruction du chemin
                vl.append(v)
                path = []
                k = N - M

                while vl:
                    oldv = vl.pop(-1)
                    if k == -D or k != D and oldv[k - 1] < oldv[k + 1]:
                        xs = oldv[k + 1]
                        k = k + 1
                    else:
                        xs = oldv[k - 1] + 1
                        k = k - 1
                    # print "-> x=%d y=%d v=%r ok=%d k=%d xs=%d D=%d" % (
                    #   x,y,oldv,oldk,k,xs,D)
                    while x > xs:
                        x -= 1
                        y -= 1
                        # print "(%d,%d)" % (x,y)
                        path.append((X[x], Y[y]))
                    D -= 1
                    x = oldv[k]
                    y = x - k
                    # print "<- x=%d y=%d v=%r ok=%d k=%d xs=%d D=%d" % (
                    #   x,y,oldv,oldk,k,xs,D)
                # print x,y,deltax,deltay,oldv, oldk, k
                path.reverse()
                return path
        vl.append(v[:])


# BBB remove in 2.1
# save the reference for tests
lcs2_python = lcs2
have_c_extension = False


def quick_ratio(a, b):
    """
    optimized version of the standard difflib.py quick_ration
    (without junk and class)
    Return an upper bound on ratio() relatively quickly.
    """
    # viewing a and b as multisets, set matches to the cardinality
    # of their intersection; this counts the number of matches
    # without regard to order, so is clearly an upper bound
    if not a and not b:
        return 1
    fullbcount = {}
    for elt in b:
        fullbcount[elt] = fullbcount.get(elt, 0) + 1
    # avail[x] is the number of times x appears in 'b' less the
    # number of times we've seen it in 'a' so far ... kinda
    avail = {}
    matches = 0
    for elt in a:
        if elt in avail:
            numb = avail[elt]
        else:
            numb = fullbcount.get(elt, 0)
        avail[elt] = numb - 1
        if numb > 0:
            matches = matches + 1
    return 2.0 * matches / (len(a) + len(b))
