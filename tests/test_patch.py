import os
import unittest

from lxml import etree
from xmldiff.main import diff_trees
from xmldiff.patch import Patcher
from xmldiff.actions import (UpdateTextIn, InsertNode, MoveNode,
                             DeleteNode, UpdateAttrib, InsertAttrib,
                             RenameAttrib, DeleteAttrib, UpdateTextAfter,
                             RenameNode, InsertComment)

from .testing import compare_elements


class PatcherTests(unittest.TestCase):

    patcher = Patcher()

    def _test(self, start, action, end):
        tree = etree.fromstring(start)
        self.patcher.handle_action(action, tree)
        self.assertEqual(etree.tounicode(tree), end)

    def test_delete_node(self):
        self._test('<root><deleteme/></root>',
                   DeleteNode('/root/deleteme'),
                   '<root/>')

    def test_insert_node(self):
        self._test('<root><anode/></root>',
                   InsertNode('/root/anode', 'newnode', 0),
                   '<root><anode><newnode/></anode></root>')

    def test_rename_node(self):
        self._test('<root><oldname/></root>',
                   RenameNode('/root/oldname', 'newname'),
                   '<root><newname/></root>')

    def test_move_node(self):
        self._test('<root><anode><moveme/></anode></root>',
                   MoveNode('/root/anode/moveme', '/root', 1),
                   '<root><anode/><moveme/></root>')

    def test_update_text_in(self):
        self._test('<root><anode/></root>',
                   UpdateTextIn('/root/anode', 'New text'),
                   '<root><anode>New text</anode></root>')

    def test_update_text_after(self):
        self._test('<root><anode/></root>',
                   UpdateTextAfter('/root/anode', 'New text'),
                   '<root><anode/>New text</root>')

    def test_update_attrib(self):
        self._test('<root><anode attrib="oldvalue" /></root>',
                   UpdateAttrib('/root/anode', 'attrib', 'newvalue'),
                   '<root><anode attrib="newvalue"/></root>')

    def test_delete_attrib(self):
        self._test('<root><anode attrib="oldvalue" /></root>',
                   DeleteAttrib('/root/anode', 'attrib'),
                   '<root><anode/></root>')

    def test_insert_attrib(self):
        self._test('<root><anode/></root>',
                   InsertAttrib('/root/anode', 'attrib', 'value'),
                   '<root><anode attrib="value"/></root>')

    def test_rename_attrib(self):
        self._test('<root><anode oldname="value"/></root>',
                   RenameAttrib('/root/anode', 'oldname', 'newname'),
                   '<root><anode newname="value"/></root>')

    def test_insert_comment(self):
        self._test('<root><anode/></root>',
                   InsertComment('/root', 1, "This is a new comment"),
                   '<root><anode/><!--This is a new comment--></root>')


class DiffPatch(unittest.TestCase):

    def test_diff_patch(self):
        here = os.path.split(__file__)[0]
        lfile = os.path.join(here, 'test_data', 'all_actions.left.xml')
        rfile = os.path.join(here, 'test_data', 'all_actions.right.xml')

        left = etree.parse(lfile)
        right = etree.parse(rfile)
        diff = diff_trees(left, right)
        result = Patcher().patch(diff, left)

        # This example has top level comments, and lxml doesn't deal well
        # with that, so the trees are not EXACTLY the same, the trailing
        # top level comment differs, but that's OK.
        compare_elements(result.getroot(), right.getroot())
