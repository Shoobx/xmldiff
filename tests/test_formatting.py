import os
import sys
import unittest

from lxml import etree
from xmldiff import formatting, main, actions

from .testing import generate_filebased_cases

START = '<document xmlns:diff="http://namespaces.shoobx.com/diff"><node'
END = "</node></document>"


class PlaceholderMakerTests(unittest.TestCase):
    def test_get_placeholder(self):
        replacer = formatting.PlaceholderMaker()
        # Get a placeholder:
        ph = replacer.get_placeholder(etree.Element("tag"), formatting.T_OPEN, None)
        self.assertEqual(ph, "\ue007")
        # Do it again:
        ph = replacer.get_placeholder(etree.Element("tag"), formatting.T_OPEN, None)
        self.assertEqual(ph, "\ue007")
        # Get another one
        ph = replacer.get_placeholder(etree.Element("tag"), formatting.T_CLOSE, ph)
        self.assertEqual(ph, "\ue008")

    def test_do_element(self):
        replacer = formatting.PlaceholderMaker(["p"], ["b"])

        # Formatting tags get replaced, and the content remains
        text = "<p>This is a tag with <b>formatted</b> text.</p>"
        element = etree.fromstring(text)
        replacer.do_element(element)

        self.assertEqual(
            etree.tounicode(element),
            "<p>This is a tag with \ue008formatted\ue007 text.</p>",
        )

        replacer.undo_element(element)
        self.assertEqual(etree.tounicode(element), text)

        # Non formatting tags get replaced with content
        text = "<p>This is a tag with <foo>formatted</foo> text.</p>"
        element = etree.fromstring(text)
        replacer.do_element(element)
        result = etree.tounicode(element)
        self.assertEqual(result, "<p>This is a tag with \ue009 text.</p>")

        # Single formatting tags still get two placeholders.
        text = "<p>This is a <b/> with <foo/> text.</p>"
        element = etree.fromstring(text)
        replacer.do_element(element)
        result = etree.tounicode(element)
        self.assertEqual(result, "<p>This is a \ue00b\ue00a with \ue00c text.</p>")

    def test_do_undo_element(self):
        replacer = formatting.PlaceholderMaker(["p"], ["b"])

        # Formatting tags get replaced, and the content remains
        text = "<p>This <is/> a <f>tag</f> with <b>formatted</b> text.</p>"
        element = etree.fromstring(text)
        replacer.do_element(element)

        self.assertEqual(
            element.text, "This \ue007 a \ue008 with \ue00aformatted\ue009 text."
        )

        replacer.undo_element(element)
        result = etree.tounicode(element)
        self.assertEqual(result, text)

    def test_do_undo_element_double_format(self):
        replacer = formatting.PlaceholderMaker(["p"], ["b", "u"])

        # Formatting tags get replaced, and the content remains
        text = "<p>This is <u>doubly <b>formatted</b></u> text.</p>"
        element = etree.fromstring(text)
        replacer.do_element(element)

        self.assertEqual(
            element.text, "This is \ue008doubly \ue00aformatted\ue009\ue007 text."
        )

        replacer.undo_element(element)
        result = etree.tounicode(element)
        self.assertEqual(result, text)

    def test_rml_bug(self):
        etree.register_namespace(formatting.DIFF_PREFIX, formatting.DIFF_NS)
        before_diff = """<document xmlns:diff="http://namespaces.shoobx.com/diff">
  <section>
    <para>
      <ref>4</ref>.
      <u><b>At Will Employment</b></u>
      .\u201cText\u201d
    </para>
  </section>
</document>"""
        tree = etree.fromstring(before_diff)
        replacer = formatting.PlaceholderMaker(
            text_tags=("para",),
            formatting_tags=(
                "b",
                "u",
                "i",
            ),
        )
        replacer.do_tree(tree)
        after_diff = """<document xmlns:diff="http://namespaces.shoobx.com/diff">
  <section>
    <para>
      <insert>\ue007</insert>.
      \ue009\ue00bAt Will Employment\ue00a\ue008
      .\u201c<insert>New </insert>Text\u201d
    </para>
  </section>
</document>"""

        # The diff formatting will find some text to insert.
        delete_attrib = "{%s}delete-format" % formatting.DIFF_NS
        replacer.placeholder2tag["\ue008"].element.attrib[delete_attrib] = ""
        replacer.placeholder2tag["\ue009"].element.attrib[delete_attrib] = ""
        tree = etree.fromstring(after_diff)
        replacer.undo_tree(tree)
        result = etree.tounicode(tree)
        expected = """<document xmlns:diff="http://namespaces.shoobx.com/diff">
  <section>
    <para>
      <insert><ref>4</ref></insert>.
      <u diff:delete-format=""><b>At Will Employment</b></u>
      .\u201c<insert>New </insert>Text\u201d
    </para>
  </section>
</document>"""
        self.assertEqual(result, expected)

    def test_placeholder_overflow(self):
        # PY3: This whole test is Python 2 support.
        # Test what happens when we have more than 6400 placeholders,
        # by patching the placeholder:
        try:
            orig_start = formatting.PLACEHOLDER_START
            # This is the last character of the Private use area
            formatting.PLACEHOLDER_START = 0xF8FF

            replacer = formatting.PlaceholderMaker(["p"], ["b"])

            # Formatting tags get replaced, and the content remains
            text = "<p>This <is/> a <f>tag</f> with <b>some</b> text.</p>"
            element = etree.fromstring(text)
            replacer.do_element(element)

            #
            self.assertEqual(
                element.text, "This \uf906 a \uf907 with \uf909some\uf908 text."
            )

            try:
                # If this is a wide build, also test what happens if we
                # get over 8192 substitutions, and overflow the 2-byte code.
                # (On narrow builds this will give an error)
                formatting.PLACEHOLDER_START = 0xFFFF

                replacer = formatting.PlaceholderMaker(["p"], ["b"])

                # Formatting tags get replaced, and the content remains
                text = "<p>This <is/> a <f>tag</f> with <b>some</b> text.</p>"
                element = etree.fromstring(text)
                replacer.do_element(element)

                # This should raise an error on a narrow build
                self.assertEqual(
                    element.text,
                    "This \U00010006 a \U00010007 with \U00010009some\U00010008 text.",
                )
            except ValueError:
                if sys.maxunicode > 0x10000:
                    # This is a wide build, we should NOT get an error
                    raise

        finally:
            # Set it back
            formatting.PLACEHOLDER_START = orig_start


class XMLFormatTests(unittest.TestCase):
    def _format_test(self, left, action, expected, use_replace=False):
        formatter = formatting.XMLFormatter(pretty_print=False, use_replace=use_replace)
        result = formatter.format([action], etree.fromstring(left))
        self.assertEqual(result, expected)

    def test_incorrect_xpaths(self):
        left = '<document><node a="v"/><node>Text</node></document>'
        expected = START + ' diff:delete-attr="a">Text' + END

        with self.assertRaises(ValueError):
            action = actions.DeleteAttrib("/document/node", "a")
            self._format_test(left, action, expected)

        with self.assertRaises(ValueError):
            action = actions.DeleteAttrib("/document/ummagumma", "a")
            self._format_test(left, action, expected)

    def test_del_attr(self):
        left = '<document><node a="v">Text</node></document>'
        action = actions.DeleteAttrib("/document/node", "a")
        expected = START + ' diff:delete-attr="a">Text' + END

        self._format_test(left, action, expected)

    def test_del_node(self):
        left = '<document><node attr="val">Text</node></document>'
        action = actions.DeleteNode("/document/node")
        expected = START + ' attr="val" diff:delete="">Text' + END

        self._format_test(left, action, expected)

    def test_del_text(self):
        left = '<document><node attr="val">Text</node></document>'
        action = actions.UpdateTextIn("/document/node", None)
        expected = START + ' attr="val"><diff:delete>Text</diff:delete>' + END

        self._format_test(left, action, expected)

    def test_insert_attr(self):
        left = "<document><node>We need more text</node></document>"
        action = actions.InsertAttrib("/document/node", "attr", "val")
        expected = START + ' attr="val" diff:add-attr="attr">We need more text' + END

        self._format_test(left, action, expected)

    def test_insert_node(self):
        left = "<document></document>"
        action = actions.InsertNode("/document", "node", 0)
        expected = START + ' diff:insert=""/></document>'

        self._format_test(left, action, expected)

    def test_move_attr(self):
        # The library currently only uses move attr for when attributes are
        # renamed:
        left = '<document><node attr="val">Text</node></document>'
        action = actions.RenameAttrib("/document/node", "attr", "bottr")
        expected = START + ' bottr="val" diff:rename-attr="attr:bottr">Text' + END

        self._format_test(left, action, expected)

    def test_move_node(self):
        # Move 1 down
        left = '<document><node id="1" /><node id="2" /></document>'
        action = actions.MoveNode("/document/node[1]", "/document", 1)
        expected = (
            START + ' id="1" diff:delete=""/><node id="2"/><node '
            'id="1" diff:insert=""/></document>'
        )

        self._format_test(left, action, expected)

        # Move 2 up (same result, different diff)
        left = '<document><node id="1" /><node id="2" /></document>'
        action = actions.MoveNode("/document/node[2]", "/document", 0)
        expected = (
            START + ' id="2" diff:insert=""/><node id="1"/><node '
            'id="2" diff:delete=""/></document>'
        )

        self._format_test(left, action, expected)

    def test_rename_node(self):
        left = "<document><node><para>Content</para>Tail</node></document>"
        action = actions.RenameNode("/document/node[1]/para[1]", "newtag")
        expected = START + '><newtag diff:rename="para">Content</newtag>Tail' + END

        self._format_test(left, action, expected)

    def test_update_attr(self):
        left = '<document><node attr="val"/></document>'
        action = actions.UpdateAttrib("/document/node", "attr", "newval")
        expected = START + ' attr="newval" diff:update-attr="attr:val"/></document>'

        self._format_test(left, action, expected)

    def test_update_text_in(self):
        left = '<document><node attr="val"/></document>'
        action = actions.UpdateTextIn("/document/node", "Text")
        expected = START + ' attr="val"><diff:insert>Text</diff:insert>' + END

        self._format_test(left, action, expected)

        left = "<document><node>This is a bit of text, right" + END
        action = actions.UpdateTextIn("/document/node", "Also a bit of text, rick")
        expected = (
            START + "><diff:delete>This is</diff:delete><diff:insert>"
            "Also</diff:insert> a bit of text, ri<diff:delete>ght"
            "</diff:delete><diff:insert>ck</diff:insert>" + END
        )

        self._format_test(left, action, expected)

    def test_update_text_after_1(self):
        left = "<document><node/><node/></document>"
        action = actions.UpdateTextAfter("/document/node[1]", "Text")
        expected = START + "/><diff:insert>Text</diff:insert><node/></document>"

        self._format_test(left, action, expected)

    def test_update_text_after_2(self):
        left = "<document><node/>This is a bit of text, right</document>"
        action = actions.UpdateTextAfter("/document/node", "Also a bit of text, rick")
        expected = (
            START + "/><diff:delete>This is</diff:delete>"
            "<diff:insert>Also</diff:insert> a bit of text, ri<diff:delete>"
            "ght</diff:delete><diff:insert>ck</diff:insert></document>"
        )

        self._format_test(left, action, expected)

    def test_replace_text_in(self):
        left = '<document><node attr="val"/></document>'
        action = actions.UpdateTextIn("/document/node", "Text")
        expected = START + ' attr="val"><diff:insert>Text</diff:insert>' + END

        self._format_test(left, action, expected, use_replace=True)

        left = "<document><node>This is a bit of text, right" + END
        action = actions.UpdateTextIn("/document/node", "Also a bit of text, rick")
        expected = (
            START + '><diff:replace old-text="This is">Also</diff:replace>'
            ' a bit of text, ri<diff:replace old-text="ght">ck'
            "</diff:replace>" + END
        )

        self._format_test(left, action, expected, use_replace=True)

    def test_replace_text_after_1(self):
        left = "<document><node/><node/></document>"
        action = actions.UpdateTextAfter("/document/node[1]", "Text")
        expected = START + "/><diff:insert>Text</diff:insert><node/></document>"

        self._format_test(left, action, expected, use_replace=True)

    def test_replace_text_after_2(self):
        left = "<document><node/>This is a bit of text, right</document>"
        action = actions.UpdateTextAfter("/document/node", "Also a bit of text, rick")
        expected = (
            START + '/><diff:replace old-text="This is">Also</diff:replace>'
            ' a bit of text, ri<diff:replace old-text="ght">ck'
            "</diff:replace></document>"
        )

        self._format_test(left, action, expected, use_replace=True)

    def test_replace_complete_text(self):
        left = "<document><node>aaaaaaa bbbbbb</node></document>"
        action = actions.UpdateTextIn("/document/node", "ccccc dddd eee")
        expected = (
            START + '><diff:replace old-text="aaaaaaa bbbbbb">ccccc dddd eee'
            "</diff:replace>" + END
        )

        self._format_test(left, action, expected, use_replace=True)


class DiffFormatTests(unittest.TestCase):
    def _format_test(self, action, expected):
        formatter = formatting.DiffFormatter()
        result = formatter.format([action], None)
        self.assertEqual(result, expected)

    def test_del_attr(self):
        action = actions.DeleteAttrib("/document/node", "a")
        expected = "[delete-attribute, /document/node, a]"
        self._format_test(action, expected)

    def test_del_node(self):
        action = actions.DeleteNode("/document/node")
        expected = "[delete, /document/node]"
        self._format_test(action, expected)

    def test_del_text(self):
        action = actions.UpdateTextIn("/document/node", None)
        expected = "[update-text, /document/node, null, null]"
        self._format_test(action, expected)

    def test_insert_attr(self):
        action = actions.InsertAttrib("/document/node", "attr", "val")
        expected = '[insert-attribute, /document/node, attr, "val"]'
        self._format_test(action, expected)

    def test_insert_node(self):
        action = actions.InsertNode("/document", "node", 0)
        expected = "[insert, /document, node, 0]"
        self._format_test(action, expected)

    def test_rename_attr(self):
        action = actions.RenameAttrib("/document/node", "attr", "bottr")
        expected = "[rename-attribute, /document/node, attr, bottr]"
        self._format_test(action, expected)

    def test_move_node(self):
        # Move 1 down
        action = actions.MoveNode("/document/node[1]", "/document", 1)
        expected = "[move, /document/node[1], /document, 1]"
        self._format_test(action, expected)

        # Move 2 up (same result, different diff)
        action = actions.MoveNode("/document/node[2]", "/document", 0)
        expected = "[move, /document/node[2], /document, 0]"

        self._format_test(action, expected)

    def test_rename_node(self):
        # Move 1 down
        action = actions.RenameNode("/document/node[1]", "newtag")
        expected = "[rename, /document/node[1], newtag]"
        self._format_test(action, expected)

        # Move 2 up (same result, different diff)
        action = actions.MoveNode("/document/node[2]", "/document", 0)
        expected = "[move, /document/node[2], /document, 0]"

        self._format_test(action, expected)

    def test_update_attr(self):
        action = actions.UpdateAttrib("/document/node", "attr", "newval")
        expected = '[update-attribute, /document/node, attr, "newval"]'
        self._format_test(action, expected)

    def test_update_text_in(self):
        action = actions.UpdateTextIn("/document/node", "Text")
        expected = '[update-text, /document/node, "Text", null]'
        self._format_test(action, expected)

        action = actions.UpdateTextIn("/document/node", 'Also a bit of text, "rick"')
        expected = (
            '[update-text, /document/node, "Also a bit of text, \\"rick\\"", null]'
        )
        self._format_test(action, expected)

    def test_update_text_after_1(self):
        action = actions.UpdateTextAfter("/document/node[1]", "Text")
        expected = '[update-text-after, /document/node[1], "Text", null]'
        self._format_test(action, expected)

    def test_update_text_after_2(self):
        action = actions.UpdateTextAfter("/document/node", "Also a bit of text, rick")
        expected = (
            '[update-text-after, /document/node, "Also a bit of text, rick", null]'
        )
        self._format_test(action, expected)

    def test_insert_comment(self):
        action = actions.InsertComment("/document/node", 2, "Commentary")
        expected = '[insert-comment, /document/node, 2, "Commentary"]'
        self._format_test(action, expected)


class XmlDiffFormatTests(unittest.TestCase):
    # RenameAttr and MoveNode requires an orig_tree, so they
    # are not tested in the _format_test tests, but in the
    # all_actions test, which uses test_data files.

    def _format_test(self, action, expected):
        formatter = formatting.XmlDiffFormatter()
        result = formatter.format([action], None)
        self.assertEqual(result, expected)

    def test_del_attr(self):
        action = actions.DeleteAttrib("/document/node", "a")
        expected = "[remove, /document/node/@a]"
        self._format_test(action, expected)

    def test_del_node(self):
        action = actions.DeleteNode("/document/node")
        expected = "[remove, /document/node]"
        self._format_test(action, expected)

    def test_del_text(self):
        action = actions.UpdateTextIn("/document/node", None)
        expected = "[update, /document/node/text()[1], null]"
        self._format_test(action, expected)

    def test_insert_attr(self):
        action = actions.InsertAttrib("/document/node", "attr", "val")
        expected = "[insert, /document/node, \n<@attr>\nval\n</@attr>]"
        self._format_test(action, expected)

    def test_insert_node(self):
        action = actions.InsertNode("/document", "node", 0)
        expected = "[insert-first, /document, \n<node/>]"
        self._format_test(action, expected)

    def test_rename_node(self):
        # Move 1 down
        action = actions.RenameNode("/document/node[1]", "newtag")
        expected = "[rename, /document/node[1], newtag]"
        self._format_test(action, expected)

        # Move 2 up (same result, different diff)
        action = actions.MoveNode("/document/node[2]", "/document", 0)
        expected = "[move-first, /document/node[2], /document]"
        self._format_test(action, expected)

    def test_update_attr(self):
        action = actions.UpdateAttrib("/document/node", "attr", "newval")
        expected = '[update, /document/node/@attr, "newval"]'
        self._format_test(action, expected)

    def test_update_text_in(self):
        action = actions.UpdateTextIn("/document/node", "Text")
        expected = '[update, /document/node/text()[1], "Text"]'
        self._format_test(action, expected)

        action = actions.UpdateTextIn("/document/node", 'Also a bit of text, "rick"')
        expected = (
            '[update, /document/node/text()[1], "Also a bit of text, \\"rick\\""]'
        )
        self._format_test(action, expected)

    def test_update_text_after_1(self):
        action = actions.UpdateTextAfter("/document/node[1]", "Text")
        expected = '[update, /document/node[1]/text()[2], "Text"]'
        self._format_test(action, expected)

    def test_update_text_after_2(self):
        action = actions.UpdateTextAfter("/document/node", "Also a bit of text, rick")
        expected = '[update, /document/node/text()[2], "Also a bit of text, rick"]'
        self._format_test(action, expected)

    def test_all_actions(self):
        here = os.path.split(__file__)[0]
        lfile = os.path.join(here, "test_data", "all_actions.left.xml")
        rfile = os.path.join(here, "test_data", "all_actions.right.xml")

        formatter = formatting.XmlDiffFormatter()
        result = main.diff_files(lfile, rfile, formatter=formatter)
        expected = (
            "[insert-namespace, space, http://namespaces.shoobx.com/outerspace]\n"
            "[delete-namespace, name]\n"
            "[move-after, /document/node[2], /document/tag[1]]\n"
            "[insert-comment, /document[1], 0,  Insert a new comment ]\n"
            '[update, /document/node[1]/@name, "was updated"]\n'
            "[remove, /document/node[1]/@attribute]\n"
            "[insert, /document/node[1], \n"
            "<@newtribute>\n"
            "renamed\n"
            "</@newtribute>]\n"
            "[insert, /document/node[1], \n"
            "<@this>\n"
            "is new\n"
            "</@this>]\n"
            "[remove, /document/node[1]/@attr]\n"
            '[update, /document/node[1]/text()[1], "\\n    Modified\\n  "]\n'
            '[update, /document/node[1]/text()[2], "\\n    '
            'New tail content\\n  "]\n'
            "[rename, /document/node[2], nod]\n"
            "[rename, /document/name:space[1], {http://namespaces.shoobx.com/outerspace}name]\n"
            '[update, /document/space:name[1]/text()[2], "\\n  "]\n'
            "[remove, /document/tail[1]]"
        )
        self.assertEqual(result, expected)


class FormatterFileTests(unittest.TestCase):
    formatter = None  # Override this
    maxDiff = None

    def process(self, left, right):
        return main.diff_files(left, right, formatter=self.formatter)


class XMLFormatterFileTests(FormatterFileTests):
    # The XMLFormatter has no text or formatting tags, so
    formatter = formatting.XMLFormatter(
        pretty_print=False, normalize=formatting.WS_TEXT
    )


# Also test the bits that handle text tags:


class HTMLFormatterFileTests(FormatterFileTests):
    # We use a few tags for the placeholder tests.
    # <br/> is intentionally left out, to test an edge case
    # with empty non-formatting tags in text.
    formatter = formatting.XMLFormatter(
        normalize=formatting.WS_BOTH,
        pretty_print=True,
        text_tags=("p", "h1", "h2", "h3", "h4", "h5", "h6", "li"),
        formatting_tags=(
            "b",
            "u",
            "i",
            "strike",
            "em",
            "super",
            "sup",
            "sub",
            "link",
            "a",
            "span",
        ),
    )


# Add tests that use no placeholder replacement (ie plain XML)
data_dir = os.path.join(os.path.dirname(__file__), "test_data")
generate_filebased_cases(data_dir, XMLFormatterFileTests)

# Add tests that use placeholder replacement (ie HTML)
data_dir = os.path.join(os.path.dirname(__file__), "test_data")
generate_filebased_cases(data_dir, HTMLFormatterFileTests, suffix="html")
