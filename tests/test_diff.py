import os
import unittest

from lxml import etree
from xmldiff import utils
from xmldiff.diff import Differ
from xmldiff.actions import (
    UpdateTextIn,
    InsertNode,
    MoveNode,
    DeleteNode,
    UpdateAttrib,
    InsertAttrib,
    RenameAttrib,
    DeleteAttrib,
    UpdateTextAfter,
    RenameNode,
    InsertComment,
)

from .testing import compare_elements


def dedent(string):
    """Remove the maximum common indent of the lines making up the string."""
    lines = string.splitlines()
    indent = min(len(line) - len(line.lstrip()) for line in lines if line)
    return "\n".join(line[indent:] if line else line for line in lines)


class APITests(unittest.TestCase):
    left = "<document><p>Text</p><p>More</p></document>"
    right = "<document><p>Tokst</p><p>More</p></document>"
    lefttree = etree.fromstring(left)
    righttree = etree.fromstring(right)
    differ = Differ()

    def test_set_trees(self):
        # Passing in just one parameter causes an error:
        with self.assertRaises(TypeError):
            self.differ.set_trees(self.lefttree, None)

        # Passing in something that isn't iterable also cause errors...
        with self.assertRaises(TypeError):
            self.differ.set_trees(object(), self.righttree)

        # This is the way:
        self.differ.set_trees(self.lefttree, self.righttree)

    def test_match(self):
        # Passing in just one parameter causes an error:
        with self.assertRaises(TypeError):
            self.differ.match(self.lefttree, None)

        # Passing in something that isn't iterable also cause errors...
        with self.assertRaises(TypeError):
            self.differ.match(object(), self.righttree)

        # This is the way:
        res1 = self.differ.match(self.lefttree, self.righttree)
        lpath = self.differ.left.getroottree().getpath
        rpath = self.differ.right.getroottree().getpath
        res1x = [(lpath(x[0]), rpath(x[1]), x[2]) for x in res1]

        # Or, you can use set_trees:
        self.differ.set_trees(self.lefttree, self.righttree)
        res2 = self.differ.match()
        lpath = self.differ.left.getroottree().getpath
        rpath = self.differ.right.getroottree().getpath
        res2x = [(lpath(x[0]), rpath(x[1]), x[2]) for x in res2]

        # The match sequences should be the same, of course:
        self.assertEqual(res1x, res2x)
        # But importantly, they are not the same object, meaning the
        # matching was redone.
        self.assertIsNot(res1, res2)
        # However, if we call match() a second time without setting
        # new sequences, we'll get a cached result:
        self.assertIs(self.differ.match(), res2)

    def test_diff(self):
        # Passing in just one parameter causes an error:
        with self.assertRaises(TypeError):
            list(self.differ.diff(self.lefttree, None))

        # Passing in something that isn't iterable also cause errors...
        with self.assertRaises(TypeError):
            list(self.differ.diff(object(), self.righttree))

        # This is the way:
        res1 = list(self.differ.diff(self.lefttree, self.righttree))

        # Or, you can use set_trees() or match()
        # We need to reparse self.lefttree, since after the diffing they
        # are equal.
        self.lefttree = etree.fromstring(self.left)
        self.differ.set_trees(self.lefttree, self.righttree)
        res2 = list(self.differ.diff())

        # The match sequences should be the same, of course:
        self.assertEqual(res1, res2)
        # But importantly, they are not the same object, meaning the
        # matching was redone.
        self.assertIsNot(res1, res2)
        # There is no caching of diff(), so running it again means another
        # diffing.
        self.assertIsNot(list(self.differ.diff()), res2)


class NodeRatioTests(unittest.TestCase):
    def test_compare_equal(self):
        xml = """<document>
    <story firstPageTemplate="FirstPage">
        <section xml:id="oldfirst" ref="3" single-ref="3">
            <para>First paragraph</para>
        </section>
        <section ref="4" single-ref="4">
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""
        tree = etree.fromstring(xml)
        differ = Differ()
        differ.set_trees(tree, tree)
        differ.match()

        # Every node in these trees should get a 1.0 leaf_ratio,
        # and if it has children, 1.0 child_ration, else None
        for left, right in zip(
            utils.post_order_traverse(differ.left),
            utils.post_order_traverse(differ.right),
        ):
            self.assertEqual(differ.leaf_ratio(left, right), 1.0)
            if left.getchildren():
                self.assertEqual(differ.child_ratio(left, right), 1.0)
            else:
                self.assertIsNone(differ.child_ratio(left, right))

    def test_compare_different_leafs(self):
        left = """<document>
    <story firstPageTemplate="FirstPage">
        <section ref="2" single-ref="2">
            <para>This doesn't match at all</para>
        </section>
        <section xml:id="oldfirst" ref="3" single-ref="3">
            <para>First paragraph</para>
        </section>
        <section ref="4" single-ref="4">
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""

        right = """<document>
    <story firstPageTemplate="FirstPage">
        <section ref="3" single-ref="3">
            <para>Completely different from before</para>
        </section>
        <section xml:id="oldfirst" ref="4" single-ref="4">
            <para>Another paragraph</para>
        </section>
        <section ref="5" single-ref="5">
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""

        lefttree = etree.fromstring(left)
        righttree = etree.fromstring(right)
        differ = Differ()

        # Make some choice comparisons here
        # These node are exactly the same
        left = lefttree.xpath("/document/story/section[3]/para")[0]
        right = righttree.xpath("/document/story/section[3]/para")[0]

        self.assertEqual(differ.leaf_ratio(left, right), 1.0)

        # These nodes have slightly different text, but no children
        left = lefttree.xpath("/document/story/section[2]/para")[0]
        right = righttree.xpath("/document/story/section[2]/para")[0]

        self.assertAlmostEqual(differ.leaf_ratio(left, right), 0.75)

        # These nodes should not be very similar
        left = lefttree.xpath("/document/story/section[1]/para")[0]
        right = righttree.xpath("/document/story/section[1]/para")[0]
        self.assertAlmostEqual(differ.leaf_ratio(left, right), 0.45614035087719)

    def test_compare_different_nodes(self):
        left = """<document>
    <story firstPageTemplate="FirstPage">
        <section ref="2" single-ref="2">
            <para>First paragraph</para>
            <para>Second paragraph</para>
        </section>
        <section ref="3" single-ref="3">
            <para>Third paragraph</para>
        </section>
        <section ref="4" single-ref="4">
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""

        right = """<document>
    <story firstPageTemplate="FirstPage">
        <section ref="2" single-ref="2">
            <para>First paragraph</para>
        </section>
        <section single-ref="3" ref="3">
            <para>Second paragraph</para>
            <para>Third paragraph</para>
        </section>
        <section single-ref="4" ref="4" >
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""

        differ = Differ()
        differ.set_trees(etree.fromstring(left), etree.fromstring(right))
        differ.match()

        # Make some choice comparisons here. leaf_ratio will always be 1.0,
        # as these leafs have the same attributes and no text, even though
        # attributes may be in different order.
        left = differ.left.xpath("/document/story/section[1]")[0]
        right = differ.right.xpath("/document/story/section[1]")[0]

        self.assertEqual(differ.leaf_ratio(left, right), 1.0)
        # Only one of two matches:
        self.assertEqual(differ.child_ratio(left, right), 0.5)

        left = differ.left.xpath("/document/story/section[2]")[0]
        right = differ.right.xpath("/document/story/section[2]")[0]

        self.assertEqual(differ.leaf_ratio(left, right), 1.0)
        # Only one of two matches:
        self.assertEqual(differ.child_ratio(left, right), 0.5)

        # These nodes should not be very similar
        left = differ.left.xpath("/document/story/section[3]")[0]
        right = differ.right.xpath("/document/story/section[3]")[0]
        self.assertEqual(differ.leaf_ratio(left, right), 1.0)
        self.assertEqual(differ.child_ratio(left, right), 1.0)

    def test_compare_with_xmlid(self):
        left = """<document>
    <story firstPageTemplate="FirstPage">
        <section xml:id="oldfirst" ref="1" single-ref="1">
            <para>First paragraph</para>
            <para>This is the second paragraph</para>
        </section>
        <section ref="3" single-ref="3" xml:id="tobedeleted">
            <para>Det tredje stycket</para>
        </section>
        <section xml:id="last" ref="4" single-ref="4">
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""

        right = """<document>
    <story firstPageTemplate="FirstPage">
        <section xml:id="newfirst" ref="1" single-ref="1">
            <para>First paragraph</para>
        </section>
        <section xml:id="oldfirst" single-ref="2" ref="2">
            <para>This is the second</para>
            <para>Det tredje stycket</para>
        </section>
        <section single-ref="4" ref="4" >
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""

        differ = Differ()
        differ.set_trees(etree.fromstring(left), etree.fromstring(right))
        differ.match()

        # Make some choice comparisons here.

        left = differ.left.xpath("/document/story/section[1]")[0]
        right = differ.right.xpath("/document/story/section[1]")[0]

        # These are very similar
        self.assertEqual(differ.leaf_ratio(left, right), 0.9)
        # And one out of two children in common
        self.assertEqual(differ.child_ratio(left, right), 0.5)
        # But different id's, hence 0 as match
        self.assertEqual(differ.node_ratio(left, right), 0)

        # Here's the ones with the same id:
        left = differ.left.xpath("/document/story/section[1]")[0]
        right = differ.right.xpath("/document/story/section[2]")[0]

        # Only one out of two children in common
        self.assertEqual(differ.child_ratio(left, right), 0.5)
        # But same id's, hence 1 as match
        self.assertEqual(differ.node_ratio(left, right), 1.0)

        # The last ones are completely similar, but only one
        # has an xml:id, so they do not match.
        left = differ.left.xpath("/document/story/section[3]")[0]
        right = differ.right.xpath("/document/story/section[3]")[0]
        self.assertAlmostEqual(differ.leaf_ratio(left, right), 0.81818181818)
        self.assertEqual(differ.child_ratio(left, right), 1.0)
        self.assertEqual(differ.node_ratio(left, right), 0)

    def test_compare_with_uniqueattrs(self):
        # `uniqueattrs` can be pairs of (tag, attribute) as well as just string
        # attributes.
        left = dedent(
            """\
        <document>
            <story firstPageTemplate="FirstPage">
                <section name="oldfirst" ref="1" single-ref="1">
                    <para>First paragraph</para>
                    <para>This is the second paragraph</para>
                </section>
                <section ref="3" single-ref="3" name="tobedeleted">
                    <para>Det tredje stycket</para>
                </section>
                <section name="last" ref="4" single-ref="4">
                    <para>Last paragraph</para>
                </section>
            </story>
        </document>
        """
        )

        right = dedent(
            """\
        <document>
            <story firstPageTemplate="FirstPage">
                <section name="newfirst" ref="1" single-ref="1">
                    <para>First paragraph</para>
                </section>
                <section name="oldfirst" single-ref="2" ref="2">
                    <para>This is the second</para>
                    <para>Det tredje stycket</para>
                </section>
                <section single-ref="4" ref="4">
                    <para>Last paragraph</para>
                </section>
                <subsection name="oldfirst" ref="1" single-ref="1">
                    <para>First paragraph</para>
                    <para>This is the second paragraph</para>
                </subsection>
            </story>
        </document>
        """
        )

        differ = Differ(
            uniqueattrs=[
                ("section", "name"),
                "{http://www.w3.org/XML/1998/namespace}id",
            ]
        )
        differ.set_trees(etree.fromstring(left), etree.fromstring(right))
        differ.match()

        # Make some choice comparisons here.

        left = differ.left.xpath("/document/story/section[1]")[0]
        right = differ.right.xpath("/document/story/section[1]")[0]

        # These are very similar
        self.assertEqual(differ.leaf_ratio(left, right), 0.90625)
        # And one out of two children in common
        self.assertEqual(differ.child_ratio(left, right), 0.5)
        # But different names, hence 0 as match
        self.assertEqual(differ.node_ratio(left, right), 0)

        # Here's the ones with the same tag and name attribute:
        left = differ.left.xpath("/document/story/section[1]")[0]
        right = differ.right.xpath("/document/story/section[2]")[0]

        # Only one out of two children in common
        self.assertEqual(differ.child_ratio(left, right), 0)
        # But same id's, hence 1 as match
        self.assertEqual(differ.node_ratio(left, right), 1.0)

        # The last ones are completely similar, but only one
        # has an name, so they do not match.
        left = differ.left.xpath("/document/story/section[3]")[0]
        right = differ.right.xpath("/document/story/section[3]")[0]
        self.assertAlmostEqual(differ.leaf_ratio(left, right), 0.78260869565)
        self.assertEqual(differ.child_ratio(left, right), 1.0)
        self.assertEqual(differ.node_ratio(left, right), 0)

        # Now these are structurally similar, have the same name, but
        # one of them is not a section, so the uniqueattr does not match
        left = differ.left.xpath("/document/story/section[1]")[0]
        right = differ.right.xpath("/document/story/subsection[1]")[0]
        self.assertAlmostEqual(differ.leaf_ratio(left, right), 1.0)
        self.assertEqual(differ.child_ratio(left, right), 0.5)
        self.assertAlmostEqual(differ.node_ratio(left, right), 0.7905694150420949)

    def test_compare_node_rename(self):
        left = """<document>
  <para>First paragraph</para>
  <para attr="value">Second paragraph</para>
  <para attr="value">Third paragraph</para>
</document>
"""

        right = """<document>
  <section>First paragraph</section>
  <section attr="something else">Second paragraph</section>
  <section attr="something else">A different text</section>
</document>
"""

        differ = Differ()
        differ.set_trees(etree.fromstring(left), etree.fromstring(right))
        differ.match()

        # Make some choice comparisons here.
        left = differ.left.xpath("/document/para[1]")[0]
        right = differ.right.xpath("/document/section[1]")[0]

        # These have different tags, but should still match
        self.assertEqual(differ.leaf_ratio(left, right), 1.0)

        # These have different tags, and different attribute value,
        # but still similar enough
        left = differ.left.xpath("/document/para[2]")[0]
        right = differ.right.xpath("/document/section[2]")[0]

        # These have different tags, but should still match
        self.assertAlmostEqual(differ.leaf_ratio(left, right), 0.76190476190476)

        # These have different tags, and different attribute value,
        # but still similar enough
        left = differ.left.xpath("/document/para[3]")[0]
        right = differ.right.xpath("/document/section[3]")[0]

        # These are too different
        self.assertAlmostEqual(differ.leaf_ratio(left, right), 0.45161290322580)

    def test_compare_namespaces(self):
        left = """<document>
  <foo:para xmlns:foo="someuri">First paragraph</foo:para>
</document>
"""

        right = """<document>
  <foo:para xmlns:foo="otheruri">First paragraph</foo:para>
</document>
"""

        differ = Differ()
        differ.set_trees(etree.fromstring(left), etree.fromstring(right))
        differ.match()

        # Make some choice comparisons here.
        left = differ.left.xpath(
            "/document/foo:para[1]", namespaces={"foo": "someuri"}
        )[0]
        right = differ.right.xpath(
            "/document/foo:para[1]", namespaces={"foo": "otheruri"}
        )[0]

        # These have different namespaces, but should still match
        self.assertEqual(differ.leaf_ratio(left, right), 1.0)

    def test_different_ratio_modes(self):
        node1 = etree.Element("para")
        node1.text = "This doesn't match at all"
        node2 = etree.Element("para")
        node2.text = "It's completely different"
        node3 = etree.Element("para")
        node3.text = "Completely different from before"

        # These texts are very different
        differ = Differ(ratio_mode="accurate")
        self.assertAlmostEqual(differ.leaf_ratio(node1, node2), 0.24)
        # However, the quick_ratio doesn't catch that, and think they match
        differ = Differ(ratio_mode="fast")
        self.assertAlmostEqual(differ.leaf_ratio(node1, node2), 0.64)
        # It still realizes these sentences are different, though.
        differ = Differ(ratio_mode="fast")
        self.assertAlmostEqual(differ.leaf_ratio(node1, node3), 0.4561403508)
        # Faster thinks the first two are the same!
        differ = Differ(ratio_mode="faster")
        self.assertAlmostEqual(differ.leaf_ratio(node1, node2), 1.0)
        # And that the third is almost the same
        differ = Differ(ratio_mode="faster")
        self.assertAlmostEqual(differ.leaf_ratio(node1, node3), 0.8771929824)

        # Invalid modes raise error:
        with self.assertRaises(ValueError):
            differ = Differ(ratio_mode="allezlebleus")


class MatchTests(unittest.TestCase):
    def _match(self, left, right):
        left_tree = etree.fromstring(left)
        right_tree = etree.fromstring(right)
        differ = Differ()
        differ.set_trees(left_tree, right_tree)
        matches = differ.match()
        lpath = differ.left.getroottree().getpath
        rpath = differ.right.getroottree().getpath
        return [(lpath(item[0]), rpath(item[1])) for item in matches]

    def test_same_tree(self):
        xml = """<document>
    <story firstPageTemplate="FirstPage">
        <section xml:id="oldfirst" ref="3" single-ref="3">
            <para>First paragraph</para>
        </section>
        <section xml:id="oldlast" ref="4" single-ref="4">
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""
        result = self._match(xml, xml)
        nodes = list(utils.post_order_traverse(etree.fromstring(xml)))
        # Everything matches
        self.assertEqual(len(result), len(nodes))

    def test_no_xml_id_match(self):
        # Here we insert a section first, but because they contain numbering
        # it's easy to match section 1 in left with section 2 in right,
        # though it should be detected as an insert.

        # If the number of similar attributes are few it works fine, the
        # differing content of the ref="3" section means it's detected to
        # be an insert.
        left = """<document>
            <story firstPageTemplate="FirstPage">
            <section ref="3" single-ref="3">
            <para>First paragraph</para>
            </section>
            <section ref="4" single-ref="4">
            <para>Last paragraph</para>
            </section>
            </story>
    </document>
    """

        # We even detect that the first section is an insert without
        # xmlid, but that's less reliable.
        right = """<document>
            <story firstPageTemplate="FirstPage">
            <section ref="3" single-ref="3">
            <para>New paragraph</para>
            </section>
            <section ref="4" single-ref="4">
            <para>First paragraph</para>
            </section>
            <section ref="5" single-ref="5">
            <para>Last paragraph</para>
            </section>
            </story>
    </document>
    """

        result = self._match(left, right)
        self.assertEqual(
            result,
            [
                ("/document/story/section[1]/para", "/document/story/section[2]/para"),
                ("/document/story/section[1]", "/document/story/section[2]"),
                ("/document/story/section[2]/para", "/document/story/section[3]/para"),
                ("/document/story/section[2]", "/document/story/section[3]"),
                ("/document/story", "/document/story"),
                ("/document", "/document"),
            ],
        )

    def test_with_xmlid(self):
        # This first section contains attributes that are similar (and longer
        # than the content text. That would trick the matcher into matching
        # the oldfirst and the newfirst section to match, except that we
        # this time also have xml:id's, and they trump everything else!
        left = """<document>
    <story firstPageTemplate="FirstPage">
        <section ref="3" single-ref="3" xml:id="oldfirst"
                 description="This is to trick the differ">
            <para>First paragraph</para>
        </section>
        <section ref="4" single-ref="4" xml:id="oldsecond">
            <para>Second paragraph</para>
        </section>
        <section ref="5" single-ref="5" xml:id="oldlast">
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""

        # We even detect that the first section is an insert without
        # xmlid, but that's less reliable.
        right = """<document>
    <story firstPageTemplate="FirstPage">
        <section ref="3" single-ref="3" xml:id="newfirst"
                 description="This is to trick the differ">
            <para>New paragraph</para>
        </section>
        <section ref="4" single-ref="4" xml:id="oldfirst">
            <para>First paragraph</para>
        </section>
        <section ref="5" single-ref="5" xml:id="oldsecond">
            <para>Second paragraph</para>
        </section>
        <section ref="6" single-ref="6" xml:id="oldlast">
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""

        result = self._match(left, right)
        self.assertEqual(
            result,
            [
                ("/document/story/section[1]/para", "/document/story/section[2]/para"),
                ("/document/story/section[1]", "/document/story/section[2]"),
                ("/document/story/section[2]/para", "/document/story/section[3]/para"),
                ("/document/story/section[2]", "/document/story/section[3]"),
                ("/document/story/section[3]/para", "/document/story/section[4]/para"),
                ("/document/story/section[3]", "/document/story/section[4]"),
                ("/document/story", "/document/story"),
                ("/document", "/document"),
            ],
        )

    def test_change_attribs(self):

        left = """<document>
    <story firstPageTemplate="FirstPage">
        <section xml:id="oldfirst" ref="3" single-ref="3">
            <para>First</para>
        </section>
        <section xml:id="oldlast" ref="4" single-ref="4">
            <para>Last</para>
        </section>
    </story>
</document>
"""

        right = """<document>
    <story firstPageTemplate="FirstPage">
        <section xml:id="oldfirst" ref="4" single-ref="4">
            <para>First</para>
        </section>
        <section xml:id="oldlast" ref="5" single-ref="5">
            <para>Last</para>
        </section>
    </story>
</document>
"""
        # It matches everything straight, which means the attrib changes
        # should become updates, which makes sense.
        result = self._match(left, right)
        self.assertEqual(
            result,
            [
                ("/document/story/section[1]/para", "/document/story/section[1]/para"),
                ("/document/story/section[1]", "/document/story/section[1]"),
                ("/document/story/section[2]/para", "/document/story/section[2]/para"),
                ("/document/story/section[2]", "/document/story/section[2]"),
                ("/document/story", "/document/story"),
                ("/document", "/document"),
            ],
        )

    def test_move_paragraph(self):
        left = """<document>
    <story firstPageTemplate="FirstPage">
        <section ref="3" single-ref="3">
            <para>First paragraph</para>
            <para>Second paragraph</para>
        </section>
        <section ref="4" single-ref="4">
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""

        right = """<document>
    <story firstPageTemplate="FirstPage">
        <section ref="3" single-ref="3">
            <para>First paragraph</para>
        </section>
        <section ref="4" single-ref="4">
            <para>Second paragraph</para>
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""
        result = self._match(left, right)
        self.assertEqual(
            result,
            [
                (
                    "/document/story/section[1]/para[1]",
                    "/document/story/section[1]/para",
                ),
                (
                    "/document/story/section[1]/para[2]",
                    "/document/story/section[2]/para[1]",
                ),
                ("/document/story/section[1]", "/document/story/section[1]"),
                (
                    "/document/story/section[2]/para",
                    "/document/story/section[2]/para[2]",
                ),
                ("/document/story/section[2]", "/document/story/section[2]"),
                ("/document/story", "/document/story"),
                ("/document", "/document"),
            ],
        )

    def test_match_complex_text(self):
        left = """<wrap id="1533728456.41"><para>
            Consultant shall not indemnify and hold Company, its
            affiliates and their respective directors,
            officers, agents and employees harmless from and
            against all claims, demands, losses, damages and
            judgments, including court costs and attorneys'
            fees, arising out of or based upon (a) any claim
            that the Services provided hereunder or, any
            related Intellectual Property Rights or the
            exercise of any rights in or to any Company-Related
            Development or Pre-Existing Development or related
            Intellectual Property Rights infringe on,
            constitute a misappropriation of the subject matter
            of, or otherwise violate any patent, copyright,
            trade secret, trademark or other proprietary right
            of any person or breaches any person's contractual
            rights; This is strange, but <b>true</b>.
            </para></wrap>"""

        right = """<wrap id="1533728456.41"><para>

            Consultant <i>shall not</i> indemnify and hold
            Company, its affiliates and their respective
            directors, officers, agents and employees harmless
            from and against all claims, demands, losses,
            excluding court costs and attorneys' fees, arising
            out of or based upon (a) any claim that the
            Services provided hereunder or, any related
            Intellectual Property Rights or the exercise of any
            rights in or to any Company-Related Development or
            Pre-Existing Development or related Intellectual
            Property Rights infringe on, constitute a
            misappropriation of the subject matter of, or
            otherwise violate any patent, copyright, trade
            secret, trademark or other proprietary right of any
            person or breaches any person's contractual rights;
            This is very strange, but <b>true</b>.

            </para></wrap>"""

        result = self._match(left, right)
        self.assertEqual(
            result,
            [
                ("/wrap/para/b", "/wrap/para/b"),
                ("/wrap/para", "/wrap/para"),
                ("/wrap", "/wrap"),
            ],
        )

    def test_match_insert_node(self):
        left = """<document title="insert-node">
  <story id="id">

  </story>
</document>
"""
        right = """<document title="insert-node">
  <story id="id">

    <h1>Inserted <i>Node</i></h1>

  </story>
</document>"""
        result = self._match(left, right)
        self.assertEqual(
            result,
            [
                ("/document/story", "/document/story"),
                ("/document", "/document"),
            ],
        )

    def test_entirely_different(self):
        left = """<document title="insert-node">
  <story id="id">

  </story>
</document>
"""
        right = """<document title="something else">
    <h1>Inserted <i>Node</i></h1>
</document>"""
        result = self._match(left, right)
        self.assertEqual(
            result,
            [
                ("/document", "/document"),
            ],
        )


class BestFastMatchTests(unittest.TestCase):
    def _match(self, left, right, fast_match=False, best_match=False):
        left_tree = etree.fromstring(left)
        right_tree = etree.fromstring(right)
        differ = Differ(fast_match=fast_match, best_match=best_match)
        differ.set_trees(left_tree, right_tree)
        matches = differ.match()
        lpath = differ.left.getroottree().getpath
        rpath = differ.right.getroottree().getpath
        return [(lpath(item[0]), rpath(item[1])) for item in matches]

    def test_move_paragraph(self):
        left = """<document>
    <story firstPageTemplate="FirstPage">
        <section ref="3" single-ref="3">
            <para>First paragraph</para>
            <para>Second paragraph</para>
        </section>
        <section ref="4" single-ref="4">
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""

        right = """<document>
    <story firstPageTemplate="FirstPage">
        <section ref="3" single-ref="3">
            <para>First paragraph</para>
        </section>
        <section ref="4" single-ref="4">
            <para>Second paragraph</para>
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""
        # Same matches as the non-fast match test, but the matches are
        # a different order.
        slow_result = sorted(self._match(left, right))
        fast_result = sorted(self._match(left, right, fast_match=True))
        best_result = sorted(self._match(left, right, best_match=True))
        self.assertEqual(slow_result, fast_result)
        self.assertEqual(slow_result, best_result)

    def test_move_children(self):
        # Here the paragraphs are all so similar that that each paragraph
        # will match any other.
        left = """<document>
    <story firstPageTemplate="FirstPage">
        <section ref="3" single-ref="3">
            <para>First paragraph</para>
            <para>Second paragraph</para>
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""

        right = """<document>
    <story firstPageTemplate="FirstPage">
        <section ref="3" single-ref="3">
            <para>Second paragraph</para>
            <para>Last paragraph</para>
            <para>First paragraph</para>
        </section>
    </story>
</document>
"""
        # The slow match will match the nodes that match *best*, so it will
        # find that paragraphs have moved around.
        slow_result = sorted(self._match(left, right, False))
        self.assertEqual(
            slow_result,
            [
                ("/document", "/document"),
                ("/document/story", "/document/story"),
                ("/document/story/section", "/document/story/section"),
                ("/document/story/section/para[1]", "/document/story/section/para[3]"),
                ("/document/story/section/para[2]", "/document/story/section/para[1]"),
                ("/document/story/section/para[3]", "/document/story/section/para[2]"),
            ],
        )

        # But the fast match will just pick any that matches.
        fast_result = sorted(self._match(left, right, True))
        self.assertEqual(
            fast_result,
            [
                ("/document", "/document"),
                ("/document/story", "/document/story"),
                ("/document/story/section", "/document/story/section"),
                ("/document/story/section/para[1]", "/document/story/section/para[1]"),
                ("/document/story/section/para[2]", "/document/story/section/para[2]"),
                ("/document/story/section/para[3]", "/document/story/section/para[3]"),
            ],
        )

        # Best should be as good as slow (but slower)
        best_result = sorted(self._match(left, right, best_match=True))
        self.assertEqual(best_result, slow_result)

    def test_delete_node(self):
        # If you have a list of similar nodes, and delete one, that
        # confuses both the standard and the fast algorithm:
        left = """<root>
<node id="1"/>
<node id="2"/>
<node id="3"/>
<node id="4"/>
<node id="5"/>
</root>
"""
        right = """<root>
<node id="1"/>
<node id="2"/>
<node id="4"/>
<node id="5"/>
</root>
"""

        slow_result = sorted(self._match(left, right))
        fast_result = sorted(self._match(left, right, fast_match=True))
        best_result = sorted(self._match(left, right, best_match=True))
        self.assertEqual(
            slow_result,
            [
                ("/root", "/root"),
                ("/root/node[1]", "/root/node[1]"),
                ("/root/node[2]", "/root/node[2]"),
                ("/root/node[3]", "/root/node[3]"),
                ("/root/node[4]", "/root/node[4]"),
            ],
        )
        self.assertEqual(fast_result, slow_result)
        self.assertEqual(
            best_result,
            [
                ("/root", "/root"),
                ("/root/node[1]", "/root/node[1]"),
                ("/root/node[2]", "/root/node[2]"),
                ("/root/node[4]", "/root/node[3]"),
                ("/root/node[5]", "/root/node[4]"),
            ],
        )


class UpdateNodeTests(unittest.TestCase):
    """Testing only the update phase of the diffing"""

    def _match(self, left, right):
        left_tree = etree.fromstring(left)
        right_tree = etree.fromstring(right)
        differ = Differ()
        differ.set_trees(left_tree, right_tree)
        matches = differ.match()
        steps = []
        for left, right, m in matches:
            steps.extend(differ.update_node_attr(left, right))
            steps.extend(differ.update_node_text(left, right))

        return steps

    def test_same_tree(self):
        xml = """<document>
    <story firstPageTemplate="FirstPage">
        <section xml:id="oldfirst" ref="3" single-ref="3">
            <para>First paragraph</para>
        </section>
        <section xml:id="oldlast" ref="4" single-ref="4">
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""
        result = self._match(xml, xml)
        # Everything matches
        self.assertEqual(result, [])

    def test_attribute_changes(self):
        left = (
            """<root><node attr1="ohyeah" attr2="ohno" attr3="maybe" """
            """attr0="del">The contained text</node>And a tail!</root>"""
        )

        right = (
            """<root><node attr4="ohyeah" attr2="uhhuh" attr3="maybe" """
            """attr5="new">The new text</node>Also a tail!</root>"""
        )

        result = self._match(left, right)

        self.assertEqual(
            result,
            [
                UpdateAttrib("/root/node[1]", "attr2", "uhhuh"),
                RenameAttrib("/root/node[1]", "attr1", "attr4"),
                InsertAttrib("/root/node[1]", "attr5", "new"),
                DeleteAttrib("/root/node[1]", "attr0"),
                UpdateTextIn("/root/node[1]", "The new text"),
                UpdateTextAfter("/root/node[1]", "Also a tail!"),
            ],
        )


class AlignChildrenTests(unittest.TestCase):
    """Testing only the align phase of the diffing"""

    def _align(self, left, right):
        left_tree = etree.fromstring(left)
        right_tree = etree.fromstring(right)
        differ = Differ()
        differ.set_trees(left_tree, right_tree)
        matches = differ.match()
        steps = []
        for left, right, m in matches:
            steps.extend(differ.align_children(left, right))
        return steps

    def test_same_tree(self):
        xml = """<document>
    <story firstPageTemplate="FirstPage">
        <section xml:id="oldfirst" ref="3" single-ref="3">
            <para>First paragraph</para>
        </section>
        <section xml:id="oldlast" ref="4" single-ref="4">
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""
        result = self._align(xml, xml)
        # Everything matches
        self.assertEqual(result, [])

    def test_move_paragraph(self):
        left = """<document>
    <story firstPageTemplate="FirstPage">
        <section ref="3" single-ref="3">
            <para>First paragraph</para>
            <para>Second paragraph</para>
        </section>
        <section ref="4" single-ref="4">
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""

        right = """<document>
    <story firstPageTemplate="FirstPage">
        <section ref="3" single-ref="3">
            <para>First paragraph</para>
        </section>
        <section ref="4" single-ref="4">
            <para>Second paragraph</para>
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""
        result = self._align(left, right)
        # Everything matches
        self.assertEqual(result, [])

    def test_move_children(self):
        left = """<document>
    <story firstPageTemplate="FirstPage">
        <section ref="3" single-ref="3">
            <para>First paragraph</para>
            <para>Second paragraph</para>
            <para>Last paragraph</para>
        </section>
    </story>
</document>
"""

        right = """<document>
    <story firstPageTemplate="FirstPage">
        <section ref="3" single-ref="3">
            <para>Second paragraph</para>
            <para>Last paragraph</para>
            <para>First paragraph</para>
        </section>
    </story>
</document>
"""
        result = self._align(left, right)
        self.assertEqual(
            result,
            [
                MoveNode(
                    "/document/story/section/para[1]", "/document/story/section[1]", 2
                )
            ],
        )


class DiffTests(unittest.TestCase):
    """Testing only the align phase of the diffing"""

    def _diff(self, left, right):
        parser = etree.XMLParser(remove_blank_text=True)
        left_tree = etree.fromstring(left, parser)
        right_tree = etree.fromstring(right, parser)
        differ = Differ()
        differ.set_trees(left_tree, right_tree)
        editscript = list(differ.diff())
        compare_elements(differ.left, differ.right)
        return editscript

    def test_process(self):
        left = """<document>
    <story firstPageTemplate="FirstPage">
        <section ref="3" single-ref="3">
            <para>First paragraph</para>
            <para>Second paragraph</para>
            <para>Third paragraph</para>
        </section>
        <deleteme>
            <para>Delete it</para>
        </deleteme>
    </story>
</document>
"""

        right = """<document>
    <story firstPageTemplate="FirstPage">
        <section ref="3" single-ref="3">
            <para>First paragraph</para>
            <para>Second paragraph</para>
        </section>
        <section ref="4" single-ref="4">
            <para>Third paragraph</para>
            <para>Fourth paragraph</para>
        </section>
    </story>
</document>
"""
        result = self._diff(left, right)
        self.assertEqual(
            result,
            [
                InsertNode("/document/story[1]", "section", 1),
                InsertAttrib("/document/story/section[2]", "ref", "4"),
                InsertAttrib("/document/story/section[2]", "single-ref", "4"),
                MoveNode(
                    "/document/story/section[1]/para[3]",
                    "/document/story/section[2]",
                    0,
                ),
                InsertNode("/document/story/section[2]", "para", 1),
                UpdateTextIn("/document/story/section[2]/para[2]", "Fourth paragraph"),
                DeleteNode("/document/story/deleteme/para[1]"),
                DeleteNode("/document/story/deleteme[1]"),
            ],
        )

    def test_needs_align(self):
        left = "<root><n><p>1</p><p>2</p><p>3</p></n><n><p>4</p></n></root>"
        right = "<root><n><p>2</p><p>4</p></n><n><p>1</p><p>3</p></n></root>"
        result = self._diff(left, right)
        self.assertEqual(
            result,
            [
                MoveNode("/root/n[1]", "/root[1]", 1),
                MoveNode("/root/n[2]/p[2]", "/root/n[1]", 0),
            ],
        )

    def test_no_root_match(self):
        left = (
            '<root attr="val"><root><n><p>1</p><p>2</p><p>3</p></n>'
            "<n><p>4</p></n></root></root>"
        )
        right = "<root><n><p>2</p><p>4</p></n><n><p>1</p><p>3</p></n></root>"
        result = self._diff(left, right)
        self.assertEqual(
            result,
            [
                DeleteAttrib("/root[1]", "attr"),
                MoveNode("/root/root/n[2]", "/root[1]", 0),
                MoveNode("/root/root/n[1]", "/root[1]", 1),
                MoveNode("/root/n[2]/p[2]", "/root/n[1]", 0),
                DeleteNode("/root/root[1]"),
            ],
        )

    def test_rmldoc(self):
        here = os.path.split(__file__)[0]
        lfile = os.path.join(here, "test_data", "rmldoc.left.xml")
        rfile = os.path.join(here, "test_data", "rmldoc.right.xml")
        with open(lfile, encoding="utf8") as infile:
            left = infile.read()
        with open(rfile, encoding="utf8") as infile:
            right = infile.read()

        result = self._diff(left, right)
        self.assertEqual(
            result,
            [
                InsertNode(
                    "/document/story[1]",
                    "{http://namespaces.shoobx.com/application}section",
                    4,
                ),
                InsertAttrib("/document/story/app:section[4]", "hidden", "false"),
                InsertAttrib("/document/story/app:section[4]", "name", "sign"),
                InsertAttrib("/document/story/app:section[4]", "ref", "3"),
                InsertAttrib("/document/story/app:section[4]", "removed", "false"),
                InsertAttrib("/document/story/app:section[4]", "single-ref", "3"),
                InsertAttrib(
                    "/document/story/app:section[4]", "title", "Signing Bonus"
                ),
                UpdateAttrib("/document/story/app:section[5]", "ref", "4"),
                UpdateAttrib("/document/story/app:section[5]", "single-ref", "4"),
                UpdateAttrib("/document/story/app:section[6]", "ref", "5"),
                UpdateAttrib("/document/story/app:section[6]", "single-ref", "5"),
                UpdateAttrib("/document/story/app:section[7]", "ref", "6"),
                UpdateAttrib("/document/story/app:section[7]", "single-ref", "6"),
                UpdateAttrib("/document/story/app:section[8]", "ref", "7"),
                UpdateAttrib("/document/story/app:section[8]", "single-ref", "7"),
                UpdateAttrib("/document/story/app:section[9]", "ref", "8"),
                UpdateAttrib("/document/story/app:section[9]", "single-ref", "8"),
                UpdateAttrib("/document/story/app:section[10]", "ref", "9"),
                UpdateAttrib("/document/story/app:section[10]", "single-ref", "9"),
                UpdateAttrib("/document/story/app:section[11]", "ref", "10"),
                UpdateAttrib("/document/story/app:section[11]", "single-ref", "10"),
                UpdateAttrib("/document/story/app:section[12]", "ref", "11"),
                UpdateAttrib("/document/story/app:section[12]", "single-ref", "11"),
                UpdateAttrib("/document/story/app:section[14]", "ref", "12"),
                UpdateAttrib("/document/story/app:section[14]", "single-ref", "12"),
                InsertNode(
                    "/document/story/app:section[4]",
                    "{http://namespaces.shoobx.com/application}term",
                    0,
                ),
                InsertAttrib(
                    "/document/story/app:section[4]/app:term[1]", "name", "sign_bonus"
                ),
                InsertAttrib("/document/story/app:section[4]/app:term[1]", "set", "ol"),
                InsertNode("/document/story/app:section[4]", "para", 1),
                UpdateTextIn(
                    "/document/story/app:section[1]/para[2]/" "app:placeholder[1]",
                    "consectetur",
                ),
                InsertNode(
                    "/document/story/app:section[4]/para[1]",
                    "{http://namespaces.shoobx.com/application}ref",
                    0,
                ),
                InsertAttrib(
                    "/document/story/app:section[4]/para/app:ref[1]", "name", "sign"
                ),
                InsertAttrib(
                    "/document/story/app:section[4]/para/app:ref[1]",
                    "{http://namespaces.shoobx.com/preview}body",
                    "<Ref>",
                ),
                UpdateTextIn("/document/story/app:section[4]/para/app:ref[1]", "3"),
                UpdateTextAfter("/document/story/app:section[4]/para/app:ref[1]", "eu"),
                InsertNode("/document/story/app:section[4]/para[1]", "u", 1),
                UpdateTextAfter(
                    "/document/story/app:section[4]/para/u[1]",
                    "ntum augue.\n\nAliquam nec tortor diam. Ph",
                ),
                InsertNode(
                    "/document/story/app:section[4]/para[1]",
                    "{http://namespaces.shoobx.com/application}placeholder",
                    2,
                ),
                InsertAttrib(
                    "/document/story/app:section[4]/para/app:placeholder[1]",
                    "field",
                    "ol.sign_bonus_include_amt",
                ),
                InsertAttrib(
                    "/document/story/app:section[4]/para/app:placeholder[1]",
                    "missing",
                    "Signing Bonus Amount",
                ),
                UpdateTextAfter(
                    "/document/story/app:section[4]/para/app:placeholder[1]",
                    "asellus congue accumsan tempor. Donec vel risus se",
                ),
                UpdateTextIn("/document/story/app:section[5]/para/app:ref[1]", "4"),
                UpdateTextIn("/document/story/app:section[6]/para/app:ref[1]", "5"),
                UpdateTextIn("/document/story/app:section[7]/para/app:ref[1]", "6"),
                UpdateTextIn("/document/story/app:section[8]/para/app:ref[1]", "7"),
                UpdateTextIn("/document/story/app:section[9]/para/app:ref[1]", "8"),
                UpdateTextIn("/document/story/app:section[10]/para/app:ref[1]", "9"),
                UpdateTextIn("/document/story/app:section[11]/para/app:ref[1]", "10"),
                UpdateTextIn("/document/story/app:section[12]/para/app:ref[1]", "11"),
                InsertNode("/document/story/app:section[4]/para/u[1]", "b", 0),
                UpdateTextIn(
                    "/document/story/app:section[4]/para/u/b[1]", "ger nec ferme"
                ),
            ],
        )

    def test_sbt_template(self):
        here = os.path.split(__file__)[0]
        lfile = os.path.join(here, "test_data", "sbt_template.left.xml")
        rfile = os.path.join(here, "test_data", "sbt_template.right.xml")
        with open(lfile, encoding="utf8") as infile:
            left = infile.read()
        with open(rfile, encoding="utf8") as infile:
            right = infile.read()

        result = self._diff(left, right)

        bm_bm_bm = "/metal:block/metal:block/metal:block"
        self.assertEqual(
            result,
            [
                UpdateAttrib(
                    bm_bm_bm + "/app:section[1]",
                    "hidden",
                    "advisor.payment_type == 'none'",
                ),
                UpdateAttrib(
                    bm_bm_bm + "/app:section/tal:if[1]",
                    "condition",
                    "python: advisor.payment_type == 'stock_award'",
                ),
                InsertNode(
                    bm_bm_bm + "/app:section[1]",
                    "{http://xml.zope.org/namespaces/tal}if",
                    1,
                ),
                InsertAttrib(
                    bm_bm_bm + "/app:section/tal:if[2]",
                    "condition",
                    "python: advisor.payment_type == 'cash'",
                ),
                InsertNode(
                    bm_bm_bm + "/app:section[1]",
                    "{http://xml.zope.org/namespaces/tal}if",
                    2,
                ),
                InsertAttrib(
                    bm_bm_bm + "/app:section/tal:if[3]",
                    "condition",
                    "python: advisor.payment_type == 'stock_award_and_cash'",
                ),
                InsertNode(bm_bm_bm + "/app:section/tal:if[1]", "para", 0),
                UpdateTextIn(
                    bm_bm_bm + "/app:section/tal:if[1]/para[1]", "\n        A "
                ),
                InsertNode(bm_bm_bm + "/app:section/tal:if[2]", "para", 0),
                UpdateTextIn(
                    bm_bm_bm + "/app:section/tal:if[2]/para[1]",
                    "\n        More text for diffing purposes\n      ",
                ),
                InsertNode(bm_bm_bm + "/app:section/tal:if[3]", "para", 0),
                UpdateTextIn(
                    bm_bm_bm + "/app:section/tal:if[3]/para[1]",
                    "\n        Lorem hipster ipso facto\n      ",
                ),
                InsertNode(bm_bm_bm + "/app:section/tal:if[1]/para[1]", "i", 0),
                UpdateTextIn(bm_bm_bm + "/app:section/tal:if[1]/para[1]/i[1]", "whole"),
                UpdateTextAfter(
                    bm_bm_bm + "/app:section/tal:if[1]/para[1]/i[1]",
                    " load of formatted text and ",
                ),
                InsertNode(bm_bm_bm + "/app:section/tal:if[1]/para[1]", "br", 1),
                UpdateTextAfter(
                    bm_bm_bm + "/app:section/tal:if[1]/para[1]/br[1]",
                    " other stuff.\n      ",
                ),
                DeleteNode(bm_bm_bm + "/app:section/tal:if[1]/para[2]/b[1]"),
                DeleteNode(bm_bm_bm + "/app:section/tal:if[1]/para[2]"),
            ],
        )

    def test_namespace(self):
        # Test changing nodes and attributes with namespaces
        left = """<document xmlns:app="someuri">
    <story app:foo="FirstPage">
        <app:section>
            <foo:para xmlns:foo="otheruri">Lorem ipsum dolor sit amet,
                consectetur adipiscing elit. Pellentesque feugiat metus quam.
                Suspendisse potenti. Vestibulum quis ornare felis,
                ac elementum sem.</foo:para>
            <app:para xmlns:foo="otheruri">Second paragraph</app:para>
            <app:para>Third paragraph</app:para>
            <app:para>
                Paragraph to tweak the matching of the section node
            </app:para>
            <app:para>
                By making many matching children
            </app:para>
            <app:para>
               Until the node matches properly.
            </app:para>
        </app:section>
    </story>
</document>
"""

        right = """<document xmlns:app="someuri">
    <story app:foo="FirstPage">
        <app:section>
            <app:para>Lorem ipsum dolor sit amet,
                consectetur adipiscing elit. Pellentesque feugiat metus quam.
                Suspendisse potenti. Vestibulum quis ornare felis,
                ac elementum sem.</app:para>
            <app:para>Second paragraph</app:para>
            <app:para app:attrib="value">Third paragraph</app:para>
            <app:para>
                Paragraph to tweak the matching of the section node
            </app:para>
            <app:para>
                By making many matching children
            </app:para>
            <app:para>
               Until the node matches properly.
            </app:para>
         </app:section>
    </story>
</document>
"""
        result = self._diff(left, right)
        self.assertEqual(
            result,
            [
                RenameNode("/document/story/app:section/foo:para[1]", "{someuri}para"),
                InsertAttrib(
                    "/document/story/app:section/app:para[3]",
                    "{someuri}attrib",
                    "value",
                ),
            ],
        )

    def test_multiple_tag_deletes(self):
        left = """<document title="delte-node-ul">
    <story id="id">

        <ul>
            <li>One</li>
            <li>Two</li>
            <li>Three</li>
        </ul>

    </story>
</document>"""

        right = """<document title="delte-node-ul">
    <story id="id">
    </story>
</document>"""

        result = self._diff(left, right)
        self.assertEqual(
            result,
            [
                UpdateTextIn("/document/story[1]", "\n    "),
                DeleteNode("/document/story/ul/li[3]"),
                DeleteNode("/document/story/ul/li[2]"),
                DeleteNode("/document/story/ul/li[1]"),
                DeleteNode("/document/story/ul[1]"),
            ],
        )

    def test_insert_comment(self):
        left = "<doc><body>Something</body></doc>"
        right = "<doc><!-- New comment! --><body>Something</body></doc>"

        result = self._diff(left, right)
        self.assertEqual(result, [InsertComment("/doc[1]", 0, " New comment! ")])

    def test_issue_21_default_namespaces(self):
        # When you have a default namespace you get "*" instead of the
        # expected "tag" in the XPath. This is how libxml does it,
        # and they say it has to be like that, so we document it.
        left = '<tag xmlns="ns">old</tag>'
        right = '<tag xmlns="ns">new</tag>'
        result = self._diff(left, right)
        self.assertEqual(result[0].node, "/*[1]")

    def test_ignore_attribute(self):
        # this differ ignores the attribute 'skip' when diffing
        class IgnoringDiffer(Differ):
            def node_attribs(self, node):
                if "skip" in node.attrib:
                    attribs = dict(node.attrib)
                    del attribs["skip"]
                    return attribs
                return node.attrib

        left = '<a><b foo="bar" skip="boom">text</b></a>'
        right = '<a><b foo="bar" skip="different">text</b></a>'

        parser = etree.XMLParser(remove_blank_text=True)
        left_tree = etree.fromstring(left, parser)
        right_tree = etree.fromstring(right, parser)
        differ = IgnoringDiffer()
        differ.set_trees(left_tree, right_tree)
        editscript = list(differ.diff())
        self.assertEqual(editscript, [])

    def test_compare_with_ignore_attrs(self):
        left = dedent(
            """\
        <document>
            <a test="a" uuid="{0123}"/>
            <b test="b" uuid="{0123}"/>
            <c test="c"/>
        </document>
        """
        )

        right = dedent(
            """\
        <document>
            <a test="a" uuid="{3210}"/>
            <b test="b"/>
            <c test="c" uuid="{3210}"/>
        </document>
        """
        )

        parser = etree.XMLParser(remove_blank_text=True)
        left_tree = etree.fromstring(left, parser)
        right_tree = etree.fromstring(right, parser)
        differ = Differ(ignored_attrs=["uuid"])
        differ.set_trees(left_tree, right_tree)
        editscript = list(differ.diff())
        self.assertEqual(editscript, [])
