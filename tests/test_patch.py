import os
import unittest

from lxml import etree
from xmldiff.formatting import DiffFormatter, WS_NONE
from xmldiff.main import diff_trees, diff_texts, patch_text, patch_file
from xmldiff.patch import Patcher, DiffParser
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


class PatcherTests(unittest.TestCase):
    patcher = Patcher()

    def _test(self, start, action, end):
        tree = etree.fromstring(start)
        self.patcher.handle_action(action, tree)
        self.assertEqual(etree.tounicode(tree), end)

    def test_delete_node(self):
        self._test("<root><deleteme/></root>", DeleteNode("/root/deleteme"), "<root/>")

    def test_insert_node(self):
        self._test(
            "<root><anode/></root>",
            InsertNode("/root/anode", "newnode", 0),
            "<root><anode><newnode/></anode></root>",
        )

    def test_rename_node(self):
        self._test(
            "<root><oldname/></root>",
            RenameNode("/root/oldname", "newname"),
            "<root><newname/></root>",
        )

    def test_move_node(self):
        self._test(
            "<root><anode><moveme/></anode></root>",
            MoveNode("/root/anode/moveme", "/root", 1),
            "<root><anode/><moveme/></root>",
        )

    def test_update_text_in(self):
        self._test(
            "<root><anode/></root>",
            UpdateTextIn("/root/anode", "New text"),
            "<root><anode>New text</anode></root>",
        )

    def test_update_text_after(self):
        self._test(
            "<root><anode/></root>",
            UpdateTextAfter("/root/anode", "New text"),
            "<root><anode/>New text</root>",
        )

    def test_update_attrib(self):
        self._test(
            '<root><anode attrib="oldvalue" /></root>',
            UpdateAttrib("/root/anode", "attrib", "newvalue"),
            '<root><anode attrib="newvalue"/></root>',
        )

    def test_delete_attrib(self):
        self._test(
            '<root><anode attrib="oldvalue" /></root>',
            DeleteAttrib("/root/anode", "attrib"),
            "<root><anode/></root>",
        )

    def test_insert_attrib(self):
        self._test(
            "<root><anode/></root>",
            InsertAttrib("/root/anode", "attrib", "value"),
            '<root><anode attrib="value"/></root>',
        )

    def test_rename_attrib(self):
        self._test(
            '<root><anode oldname="value"/></root>',
            RenameAttrib("/root/anode", "oldname", "newname"),
            '<root><anode newname="value"/></root>',
        )

    def test_insert_comment(self):
        self._test(
            "<root><anode/></root>",
            InsertComment("/root", 1, "This is a new comment"),
            "<root><anode/><!--This is a new comment--></root>",
        )


class DiffPatch(unittest.TestCase):
    def test_diff_patch(self):
        here = os.path.split(__file__)[0]
        lfile = os.path.join(here, "test_data", "all_actions.left.xml")
        rfile = os.path.join(here, "test_data", "all_actions.right.xml")

        left = etree.parse(lfile)
        right = etree.parse(rfile)
        diff = diff_trees(left, right)
        result = Patcher().patch(diff, left)

        # This example has top level comments, and lxml doesn't deal well
        # with that, so the trees are not EXACTLY the same, the trailing
        # top level comment differs, but that's OK.
        compare_elements(result, right.getroot())

    def test_diff_default_namespace(self):
        here = os.path.split(__file__)[0]
        lfile = os.path.join(here, "test_data", "namespace.left.xml")
        rfile = os.path.join(here, "test_data", "namespace.right.xml")

        left = etree.parse(lfile)
        right = etree.parse(rfile)
        diff = diff_trees(left, right)
        result = Patcher().patch(diff, left)

        # This example has top level comments, and lxml doesn't deal well
        # with that, so the trees are not EXACTLY the same, the trailing
        # top level comment differs, but that's OK.
        compare_elements(result, right.getroot())


TEST_DIFF = """[delete, node]
[insert, target, tag, 0]
[rename, node, tag]
[move, node, target, 0]
[update-text, node, "text"]
[update-text-after, node, "text"]
[update-attribute, node, name, "value"]
[delete-attribute, node, name]
[insert-attribute, node, name, "value"]
[rename-attribute, node, oldname, newname]
[insert-comment, target, 0, "text"]
"""


class ParserTests(unittest.TestCase):
    def test_make_action(self):
        parser = DiffParser()

        self.assertEqual(parser.make_action("[delete, node]"), DeleteNode("node"))

        self.assertEqual(
            parser.make_action("[insert, target, tag, 0]"),
            InsertNode("target", "tag", 0),
        )

        self.assertEqual(
            parser.make_action("[rename, node, tag]"), RenameNode("node", "tag")
        )

        self.assertEqual(
            parser.make_action("[move, node, target, 0]"), MoveNode("node", "target", 0)
        )

        self.assertEqual(
            parser.make_action('[update-text, node, "text"]'),
            UpdateTextIn("node", "text"),
        )

        self.assertEqual(
            parser.make_action('[update-text-after, node, "text"]'),
            UpdateTextAfter("node", "text"),
        )

        self.assertEqual(
            parser.make_action('[update-attribute, node, name, "value"]'),
            UpdateAttrib("node", "name", "value"),
        )

        self.assertEqual(
            parser.make_action("[delete-attribute, node, name]"),
            DeleteAttrib("node", "name"),
        )

        self.assertEqual(
            parser.make_action('[insert-attribute, node, name, "value"]'),
            InsertAttrib("node", "name", "value"),
        )

        self.assertEqual(
            parser.make_action("[rename-attribute, node, oldname, newname]"),
            RenameAttrib("node", "oldname", "newname"),
        )

        self.assertEqual(
            parser.make_action('[insert-comment, target, 0, "text"]'),
            InsertComment("target", 0, "text"),
        )

    def test_parse(self):
        parser = DiffParser()
        actions = list(parser.parse(TEST_DIFF))
        self.assertEqual(len(actions), len(TEST_DIFF.splitlines()))

    def test_parse_broken(self):
        # Testing incorrect patch files
        parser = DiffParser()

        # Empty file, nothing happens
        actions = list(parser.parse(""))
        self.assertEqual(actions, [])

        # Not a diff raises error
        with self.assertRaises(ValueError):
            actions = list(parser.parse("Not a diff"))

        # It should handle lines that have been broken, say in an email
        actions = list(parser.parse('[insert-comment, target,\n 0, "text"]'))
        self.assertEqual(actions, [InsertComment("target", 0, "text")])

        # It should not handle broken files
        with self.assertRaises(ValueError):
            actions = list(parser.parse("[insert-comment, target,\n"))

    def test_diff_patch(self):
        here = os.path.split(__file__)[0]
        lfile = os.path.join(here, "test_data", "all_actions.left.xml")
        rfile = os.path.join(here, "test_data", "all_actions.right.xml")
        with open(lfile) as f:
            left = f.read()
        with open(rfile) as f:
            right = f.read()

        diff = diff_texts(left, right, formatter=DiffFormatter(normalize=WS_NONE))
        result = patch_text(diff, left)
        compare_elements(etree.fromstring(result), etree.fromstring(right))

    def test_patch_stream(self):
        here = os.path.join(os.path.split(__file__)[0], "test_data")
        xmlfile = os.path.join(here, "insert-node.left.html")
        patchfile = os.path.join(here, "insert-node.diff")
        result = patch_file(patchfile, xmlfile)

        expectedfile = os.path.join(here, "insert-node.right.html")
        with open(expectedfile) as f:
            expected = f.read()
        # lxml.etree.parse() will strip ending whitespace
        self.assertEqual(result, expected.rstrip())

    def test_parse_commas(self):
        parser = DiffParser()

        # There should be able to be a comma in the value
        actions = list(parser.parse('[update-text-after, /root/anode[1], "foo,bar"]'))
        self.assertEqual(
            actions,
            [UpdateTextAfter(node="/root/anode[1]", text="foo,bar", oldtext=None)],
        )
