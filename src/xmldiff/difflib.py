"""
longest common subsequence algorithm

the algorithm is describe in "An O(ND) Difference Algorithm and its Variation"
by Eugene W. MYERS

As opposed to the algorithm in difflib.py, this one doesn't require hashable
elements 
"""


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
    v = [0 for i in xrange(2*max+1)]
    common = [[] for i in xrange(2*max+1)]
    for D in xrange(max+1):
        for k in xrange(-D, D+1, 2):
            if k == -D or k != D and v[k-1] < v[k+1]:
                x = v[k+1]
                common[k] = common[k+1][:]
            else:
                x = v[k-1] + 1
                common[k] = common[k-1][:]

            y = x - k
            while x < N and y < M and equal(X[x], Y[y]):
                common[k].append((x, y))
                x += 1
                y += 1

            v[k] = x
            if x >= N and y >= M:
                return [(X[x], Y[y]) for x, y in common[k]]


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
    v = [0 for i in xrange(2*max+1)]
    vl = [v]
    for D in xrange(max+1):
        for k in xrange(-D, D+1, 2):
            if k == -D or k != D and v[k-1] < v[k+1]:
                x = v[k+1]
            else:
                x = v[k-1] + 1

            y = x - k
            while x < N and y < M and equal(X[x], Y[y]):
                x += 1
                y += 1

            v[k] = x
            if x >= N and y >= M:
                # reconstruction du chemin
                vl.append(v)
                vl_saved = vl[:]
                path = []
                k = N-M

                while vl:
                    oldv = vl.pop(-1)
                    oldk = k
                    if k == -D or k != D and oldv[k-1] < oldv[k+1]:
                        xs = oldv[k+1]
                        k = k + 1
                    else:
                        xs = oldv[k-1]+1
                        k = k - 1
                    # print "-> x=%d y=%d v=%r ok=%d k=%d xs=%d D=%d" % (x,y,oldv,oldk,k,xs,D)
                    while x > xs:
                        x -= 1
                        y -= 1
                        # print "(%d,%d)" % (x,y)
                        path.append((X[x], Y[y]))
                    D -= 1
                    x = oldv[k]
                    y = x - k
                    # print "<- x=%d y=%d v=%r ok=%d k=%d xs=%d D=%d" % (x,y,oldv,oldk,k,xs,D)
                # print x,y,deltax,deltay,oldv, oldk, k
                path.reverse()
                return path  # , vl_saved
        vl.append(v[:])


def pprint_V(V, N, M):
    for v in V:
        for k in xrange(-N-M, N+M+1):
            print "% 3d" % v[k],
        print


def lcs3(X, Y, equal):
    N = len(X)+1
    M = len(Y)+1
    if not X or not Y:
        return []
    # D(i,j) is the length of longest subsequence for X[:i], Y[:j]
    pre = [0]*M
    row = [0]*M
    B = [[0]*M for i in xrange(N)]
    for i in xrange(1, N):
        for j in xrange(1, M):
            if equal(X[i-1], Y[j-1]):
                row[j] = pre[j-1] + 1
                B[i][j] = 2  # move back (-1,-1)
            elif pre[j] >= row[j-1]:
                row[j] = pre[j]
                B[i][j] = 1  # move back (0,-1)
            else:
                row[j] = row[j-1]
                B[i][j] = 0  # move back (-1,0)
        pre, row = row, pre
    i = N - 1
    j = M - 1
    L = []
    while i >= 0 and j >= 0:
        d = B[i][j]
        # print i,j,d
        if d == 0:
            j -= 1
        elif d == 1:
            i -= 1
        else:
            i -= 1
            j -= 1
            L.append((X[i], Y[j]))
    L.reverse()
    #from pprint import pprint
    # pprint(D)
    # pprint(B)
    return L


try:
    import maplookup
    lcs2 = maplookup.lcs2
    #lcs2 = lcs4
except:
    pass


def lcsl(X, Y, equal):
    """return the length of the result sent by lcs2"""
    return len(lcs2(X, Y, equal))


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
    availhas, matches = avail.has_key, 0
    for elt in a:
        if availhas(elt):
            numb = avail[elt]
        else:
            numb = fullbcount.get(elt, 0)
        avail[elt] = numb - 1
        if numb > 0:
            matches = matches + 1
    return 2.0 * matches / (len(a) + len(b))


def test(lcs2=lcs2):
    """
    FIXME this should go into the test suite.
    """
    import time
    t = time.clock()
    quick_ratio('abcdefghijklmnopqrst'*100, 'abcdefghijklmnopqrst'*100)
    print 'quick ratio :', time.clock()-t
    lcs2('abcdefghijklmnopqrst'*100, 'abcdefghijklmnopqrst'*100,
         lambda x, y: x == y)
    print 'lcs2 :       ', time.clock()-t
    quick_ratio('abcdefghijklmno'*100, 'zyxwvutsrqp'*100)
    print 'quick ratio :', time.clock()-t
    lcs2('abcdefghijklmno'*100, 'zyxwvutsrqp'*100, lambda x, y: x == y)
    print 'lcs2 :       ', time.clock()-t
    quick_ratio('abcdefghijklmnopqrst'*100, 'abcdefghijklmnopqrst'*100)
    print 'quick ratio :', time.clock()-t
    lcs2('abcdefghijklmnopqrst'*100, 'abcdefghijklmnopqrst'*100,
         lambda x, y: x == y)
    print 'lcs2 :       ', time.clock()-t
    quick_ratio('abcdefghijklmno'*100, 'zyxwvutsrqp'*100)
    print 'quick ratio :', time.clock()-t
    lcs2('abcdefghijklmno'*100, 'zyxwvutsrqp'*100, lambda x, y: x == y)
    print 'lcs2 :       ', time.clock()-t


def main(lcs2=lcs2):
    print "abcde - bydc"
    print lcsl('abcde', 'bydc', lambda x, y: x == y)
    for a in lcs2('abcde', 'bydc', lambda x, y: x == y):
        print a
    print "abacdge - bcdg"
    print lcsl('abacdge', 'bcdg', lambda x, y: x == y)
    for a in lcs2('abacdge', 'bcdg', lambda x, y: x == y):
        print a


import random


def randstr(lmin, lmax, alphabet):
    L = random.randint(lmin, lmax)
    S = []
    N = len(alphabet)-1
    for i in range(L):
        S.append(alphabet[random.randint(0, N)])
    return "".join(S)


def randtest():
    """Generate random test sequences and compare lcs2, lcs3, lcs4"""
    def _cmp(x, y): return x == y
    import maplookup
    lcsm = maplookup.lcs2

    _alpha = "abcdefghijklmnopqrstuvwxyz"
    while 1:
        S1 = randstr(2, 5, _alpha)
        S2 = randstr(2, 5, _alpha)
        print S1, S2
        R1 = lcs2(S1, S2, _cmp)
        print "lcs2:", "".join([x[0] for x in R1])
        R2 = lcs4(S1, S2, _cmp)
        print "lcs4", "".join([x[0] for x in R2])
        R3 = lcsm(S1, S2, _cmp)
        print "lcsm", "".join([x[0] for x in R3])
        print
        assert R1 == R2
        assert R1 == R3


if __name__ == '__main__':
    main()
