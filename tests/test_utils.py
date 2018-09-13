import unittest

from lxml import etree
from xmldiff import utils


class TraverseTests(unittest.TestCase):

    def test_post_order(self):
        xml = u'''<document>
    <story firstPageTemplate='FirstPage'>
        <section xml:id='oldfirst' ref='3' single-ref='3'>
            <para>First paragraph</para>
        </section>
        <section xml:id='oldlast' ref='4' single-ref='4'>
            <para>Last paragraph</para>
        </section>
    </story>
</document>
'''
        root = etree.fromstring(xml)
        tree = root.getroottree()
        res = [tree.getpath(x) for x in utils.post_order_traverse(root)]
        self.assertEqual(res, ['/document/story/section[1]/para',
                               '/document/story/section[1]',
                               '/document/story/section[2]/para',
                               '/document/story/section[2]',
                               '/document/story',
                               '/document'])

    def test_reverse_post_order(self):
        xml = u'''<document>
    <story firstPageTemplate='FirstPage'>
        <section xml:id='oldfirst' ref='3' single-ref='3'>
            <para>First paragraph</para>
        </section>
        <section xml:id='oldlast' ref='4' single-ref='4'>
            <para>Last paragraph</para>
        </section>
    </story>
</document>
'''
        root = etree.fromstring(xml)
        tree = root.getroottree()
        res = [tree.getpath(x) for x in
               utils.reverse_post_order_traverse(root)]
        self.assertEqual(res, ['/document/story/section[2]/para',
                               '/document/story/section[2]',
                               '/document/story/section[1]/para',
                               '/document/story/section[1]',
                               '/document/story',
                               '/document'])

    def test_breadth_first(self):
        xml = u'''<document>
    <story>
        <section>
            <para>First <i>paragraph</i></para>
            <para>Second paragraph</para>
        </section>
        <section>
            <para>Third paragraph</para>
            <para>Fourth <b>paragraph</b></para>
        </section>
    </story>
    <story>
        <section>
            <para>Fifth paragraph</para>
        </section>
    </story>
</document>
'''
        root = etree.fromstring(xml)
        tree = root.getroottree()
        res = [tree.getpath(x) for x in utils.breadth_first_traverse(root)]
        self.assertEqual(res, ['/document',
                               '/document/story[1]',
                               '/document/story[2]',
                               '/document/story[1]/section[1]',
                               '/document/story[1]/section[2]',
                               '/document/story[2]/section',
                               '/document/story[1]/section[1]/para[1]',
                               '/document/story[1]/section[1]/para[2]',
                               '/document/story[1]/section[2]/para[1]',
                               '/document/story[1]/section[2]/para[2]',
                               '/document/story[2]/section/para',
                               '/document/story[1]/section[1]/para[1]/i',
                               '/document/story[1]/section[2]/para[2]/b',
                               ])


class LongestCommonSubsequenceTests(unittest.TestCase):

    def _diff(self, left, right, result):
        res = []
        for x, y in utils.longest_common_subsequence(left, right):
            self.assertEqual(left[x], right[y])
            res.append(left[x])

        self.assertEqual(''.join(res), result)

    def test_lcs(self):

        self._diff('ABCDEF', 'ABCDEF', 'ABCDEF')

        self._diff('ABCDEF', 'GHIJKL', '')

        self._diff('ABCDEF', 'ACDQRB', 'ACD')

        self._diff('CXCDEFX', 'CDEFX', 'CDEFX')

        self._diff('HUMAN', 'CHIMPANZEE', 'HMAN')

        self._diff('ABCDEF', 'A', 'A')

        self._diff('123AAAAAAAAA', '123BBBBBBBBB', '123')

        self._diff('AAAAAAAAA123', 'BBBBBBBBB123', '123')

        self._diff('ABCDE1', '1FGHIJK', '1')

        # There are several correct options here, make sure that doesn't
        # confuse it, we want just one, and don't care which.
        self._diff('HORSEBACK', 'SNOWFLAKE', 'SAK')

        # Empty sequences:
        self._diff('', '', '')


class MakeAsciiTreeTests(unittest.TestCase):

    def test_make_ascii_tree(self):
        xml = u'''<document xmlns:diff="http://namespaces.shoobx.com/diff">
    <story firstPageTemplate='FirstPage'>
        <section xml:id='oldfirst' ref='3' single-ref='3'>
            <para diff:delete="">First paragraph</para>
        </section>
        <section xml:id='oldlast' ref='4' single-ref='4'>
            <para><diff:insert>Last paragraph</diff:insert></para>
        </section>
    </story>
</document>
'''
        root = etree.fromstring(xml)
        tree = utils.make_ascii_tree(root)
        self.assertEqual(
            tree,
            ' document \n   story \n     section \n       para (delete)\n'
            '     section \n       para \n         diff:insert '
        )
