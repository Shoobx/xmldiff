# -*- coding: UTF-8 -*-
import os
import unittest

from lxml import etree
from xmldiff import diff, formatting, main

from .testing import generate_filebased_cases

START = u'<document xmlns:diff="http://namespaces.shoobx.com/diff"><node'
END = u'</node></document>'


class PlaceholderMakerTests(unittest.TestCase):

    def test_get_placeholder(self):
        replacer = formatting.PlaceholderMaker()
        # Get a placeholder:
        ph = replacer.get_placeholder(
            etree.Element('tag'), formatting.T_OPEN, None)
        self.assertEqual(ph, u'\U000f0005')
        # Do it again:
        ph = replacer.get_placeholder(
            etree.Element('tag'), formatting.T_OPEN, None)
        self.assertEqual(ph, u'\U000f0005')
        # Get another one
        ph = replacer.get_placeholder(
            etree.Element('tag'), formatting.T_CLOSE, ph)
        self.assertEqual(ph, u'\U000f0006')

    def test_do_element(self):
        replacer = formatting.PlaceholderMaker(['p'], ['b'])

        # Formatting tags get replaced, and the content remains
        text = u'<p>This is a tag with <b>formatted</b> text.</p>'
        element = etree.fromstring(text)
        replacer.do_element(element)

        self.assertEqual(
            etree.tounicode(element),
            u'<p>This is a tag with \U000f0006formatted\U000f0005 text.</p>')

        replacer.undo_element(element)
        self.assertEqual(etree.tounicode(element), text)

        # Non formatting tags get replaced with content
        text = u'<p>This is a tag with <foo>formatted</foo> text.</p>'
        element = etree.fromstring(text)
        replacer.do_element(element)
        result = etree.tounicode(element)
        self.assertEqual(
            result,
            u'<p>This is a tag with \U000f0007 text.</p>')

        # Single formatting tags still get two placeholders.
        text = u'<p>This is a <b/> with <foo/> text.</p>'
        element = etree.fromstring(text)
        replacer.do_element(element)
        result = etree.tounicode(element)
        self.assertEqual(
            result,
            u'<p>This is a \U000f0009\U000f0008 with \U000f000a text.</p>')

    def test_do_undo_element(self):
        replacer = formatting.PlaceholderMaker(['p'], ['b'])

        # Formatting tags get replaced, and the content remains
        text = u'<p>This <is/> a <f>tag</f> with <b>formatted</b> text.</p>'
        element = etree.fromstring(text)
        replacer.do_element(element)

        self.assertEqual(
            element.text,
            u'This \U000f0005 a \U000f0006 with \U000f0008formatted'
            u'\U000f0007 text.')

        replacer.undo_element(element)
        result = etree.tounicode(element)
        self.assertEqual(result, text)

    def test_do_undo_element_double_format(self):
        replacer = formatting.PlaceholderMaker(['p'], ['b', 'u'])

        # Formatting tags get replaced, and the content remains
        text = u'<p>This is <u>doubly <b>formatted</b></u> text.</p>'
        element = etree.fromstring(text)
        replacer.do_element(element)

        self.assertEqual(
            element.text,
            u'This is \U000f0006doubly \U000f0008formatted\U000f0007'
            u'\U000f0005 text.')

        replacer.undo_element(element)
        result = etree.tounicode(element)
        self.assertEqual(result, text)

    def test_rml_bug(self):
        etree.register_namespace(formatting.DIFF_PREFIX, formatting.DIFF_NS)
        before_diff = u"""<document xmlns:diff="http://namespaces.shoobx.com/diff">
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
            text_tags=('para',), formatting_tags=('b', 'u', 'i',))
        replacer.do_tree(tree)
        after_diff = u"""<document xmlns:diff="http://namespaces.shoobx.com/diff">
  <section>
    <para>
      <insert>\U000f0005</insert>.
      \U000f0007\U000f0009At Will Employment\U000f0008\U000f0006
      .\u201c<insert>New </insert>Text\u201d
    </para>
  </section>
</document>"""

        # The diff formatting will find some text to insert.
        delete_attrib = u'{%s}delete-format' % formatting.DIFF_NS
        replacer.placeholder2tag[u'\U000f0006'
                                 ].element.attrib[delete_attrib] = ''
        replacer.placeholder2tag[u'\U000f0007'
                                 ].element.attrib[delete_attrib] = ''
        tree = etree.fromstring(after_diff)
        replacer.undo_tree(tree)
        result = etree.tounicode(tree)
        expected = u"""<document xmlns:diff="http://namespaces.shoobx.com/diff">
  <section>
    <para>
      <insert><ref>4</ref></insert>.
      <u diff:delete-format=""><b>At Will Employment</b></u>
      .\u201c<insert>New </insert>Text\u201d
    </para>
  </section>
</document>"""
        self.assertEqual(result, expected)


class XMLFormatTests(unittest.TestCase):

    def _format_test(self, left, action, expected):
        formatter = formatting.XMLFormatter(pretty_print=False)
        result = formatter.format([action], etree.fromstring(left))
        self.assertEqual(result, expected)

    def test_incorrect_xpaths(self):
        left = u'<document><node a="v"/><node>Text</node></document>'
        expected = START + u' diff:delete-attr="a">Text' + END

        with self.assertRaises(ValueError):
            action = diff.DeleteAttrib('/document/node', 'a')
            self._format_test(left, action, expected)

        with self.assertRaises(ValueError):
            action = diff.DeleteAttrib('/document/ummagumma', 'a')
            self._format_test(left, action, expected)

    def test_del_attr(self):
        left = u'<document><node a="v">Text</node></document>'
        action = diff.DeleteAttrib('/document/node', 'a')
        expected = START + u' diff:delete-attr="a">Text' + END

        self._format_test(left, action, expected)

    def test_del_node(self):
        left = u'<document><node attr="val">Text</node></document>'
        action = diff.DeleteNode('/document/node')
        expected = START + u' attr="val" diff:delete="">Text' + END

        self._format_test(left, action, expected)

    def test_del_text(self):
        left = u'<document><node attr="val">Text</node></document>'
        action = diff.UpdateTextIn('/document/node', None)
        expected = START + u' attr="val"><diff:delete>Text</diff:delete>' + END

        self._format_test(left, action, expected)

    def test_insert_attr(self):
        left = u'<document><node>We need more text</node></document>'
        action = diff.InsertAttrib('/document/node', 'attr', 'val')
        expected = START + u' attr="val" diff:add-attr="attr">'\
            u'We need more text' + END

        self._format_test(left, action, expected)

    def test_insert_node(self):
        left = u'<document></document>'
        action = diff.InsertNode('/document', 'node', 0)
        expected = START + u' diff:insert=""/></document>'

        self._format_test(left, action, expected)

    def test_move_attr(self):
        # The library currently only uses move attr for when attributes are
        # renamed:
        left = u'<document><node attr="val">Text</node></document>'
        action = diff.RenameAttrib('/document/node', 'attr', 'bottr')
        expected = START + u' bottr="val" diff:rename-attr="attr:bottr"'\
            u'>Text' + END

        self._format_test(left, action, expected)

    def test_move_node(self):
        # Move 1 down
        left = u'<document><node id="1" /><node id="2" /></document>'
        action = diff.MoveNode('/document/node[1]', '/document', 1)
        expected = START + u' id="1" diff:delete=""/><node id="2"/><node '\
            u'id="1" diff:insert=""/></document>'

        self._format_test(left, action, expected)

        # Move 2 up (same result, different diff)
        left = u'<document><node id="1" /><node id="2" /></document>'
        action = diff.MoveNode('/document/node[2]', '/document', 0)
        expected = START + u' id="2" diff:insert=""/><node id="1"/><node '\
            u'id="2" diff:delete=""/></document>'

        self._format_test(left, action, expected)

    def test_rename_node(self):
        left = u'<document><node><para>Content</para>Tail</node></document>'
        action = diff.RenameNode('/document/node[1]/para[1]', 'newtag')
        expected = START + u'><para diff:delete="">Content</para><newtag '\
            u'diff:insert="">Content</newtag>Tail' + END

        self._format_test(left, action, expected)

    def test_update_attr(self):
        left = u'<document><node attr="val"/></document>'
        action = diff.UpdateAttrib('/document/node', 'attr', 'newval')
        expected = START + u' attr="newval" diff:update-attr="attr:val"/>'\
            u'</document>'

        self._format_test(left, action, expected)

    def test_update_text_in(self):
        left = u'<document><node attr="val"/></document>'
        action = diff.UpdateTextIn('/document/node', 'Text')
        expected = START + u' attr="val"><diff:insert>Text</diff:insert>' + END

        self._format_test(left, action, expected)

        left = u'<document><node>This is a bit of text, right' + END
        action = diff.UpdateTextIn('/document/node',
                                   'Also a bit of text, rick')
        expected = START + u'><diff:delete>This is</diff:delete><diff:insert>'\
            u'Also</diff:insert> a bit of text, ri<diff:delete>ght'\
            u'</diff:delete><diff:insert>ck</diff:insert>' + END

        self._format_test(left, action, expected)

    def test_update_text_after_1(self):
        left = u'<document><node/><node/></document>'
        action = diff.UpdateTextAfter('/document/node[1]', 'Text')
        expected = START + u'/><diff:insert>Text</diff:insert>'\
            u'<node/></document>'

        self._format_test(left, action, expected)

    def test_update_text_after_2(self):
        left = u'<document><node/>This is a bit of text, right</document>'
        action = diff.UpdateTextAfter('/document/node',
                                      'Also a bit of text, rick')
        expected = START + u'/><diff:delete>This is</diff:delete>'\
            u'<diff:insert>Also</diff:insert> a bit of text, ri<diff:delete>'\
            u'ght</diff:delete><diff:insert>ck</diff:insert></document>'

        self._format_test(left, action, expected)


class DiffFormatTests(unittest.TestCase):

    def _format_test(self, action, expected):
        formatter = formatting.DiffFormatter()
        result = formatter.format([action], None)
        self.assertEqual(result, expected)

    def test_del_attr(self):
        action = diff.DeleteAttrib('/document/node', 'a')
        expected = '[delete-attribute, /document/node, a]'
        self._format_test(action, expected)

    def test_del_node(self):
        action = diff.DeleteNode('/document/node')
        expected = '[delete, /document/node]'
        self._format_test(action, expected)

    def test_del_text(self):
        action = diff.UpdateTextIn('/document/node', None)
        expected = '[update-text, /document/node, null]'
        self._format_test(action, expected)

    def test_insert_attr(self):
        action = diff.InsertAttrib('/document/node', 'attr', 'val')
        expected = '[insert-attribute, /document/node, attr, "val"]'
        self._format_test(action, expected)

    def test_insert_node(self):
        action = diff.InsertNode('/document', 'node', 0)
        expected = '[insert, /document, node, 0]'
        self._format_test(action, expected)

    def test_rename_attr(self):
        action = diff.RenameAttrib('/document/node', 'attr', 'bottr')
        expected = '[move-attribute, /document/node, attr, bottr]'
        self._format_test(action, expected)

    def test_move_node(self):
        # Move 1 down
        action = diff.MoveNode('/document/node[1]', '/document', 1)
        expected = '[move, /document/node[1], /document, 1]'
        self._format_test(action, expected)

        # Move 2 up (same result, different diff)
        action = diff.MoveNode('/document/node[2]', '/document', 0)
        expected = '[move, /document/node[2], /document, 0]'

        self._format_test(action, expected)

    def test_rename_node(self):
        # Move 1 down
        action = diff.RenameNode('/document/node[1]', 'newtag')
        expected = '[rename, /document/node[1], newtag]'
        self._format_test(action, expected)

        # Move 2 up (same result, different diff)
        action = diff.MoveNode('/document/node[2]', '/document', 0)
        expected = '[move, /document/node[2], /document, 0]'

        self._format_test(action, expected)

    def test_update_attr(self):
        action = diff.UpdateAttrib('/document/node', 'attr', 'newval')
        expected = '[update-attribute, /document/node, attr, "newval"]'
        self._format_test(action, expected)

    def test_update_text_in(self):
        action = diff.UpdateTextIn('/document/node', 'Text')
        expected = '[update-text, /document/node, "Text"]'
        self._format_test(action, expected)

        action = diff.UpdateTextIn('/document/node',
                                   'Also a bit of text, "rick"')
        expected = '[update-text, /document/node, '\
            u'"Also a bit of text, \\"rick\\""]'
        self._format_test(action, expected)

    def test_update_text_after_1(self):
        action = diff.UpdateTextAfter('/document/node[1]', 'Text')
        expected = '[update-text-after, /document/node[1], "Text"]'
        self._format_test(action, expected)

    def test_update_text_after_2(self):
        action = diff.UpdateTextAfter('/document/node',
                                      'Also a bit of text, rick')
        expected = '[update-text-after, /document/node, '\
            u'"Also a bit of text, rick"]'
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
        action = diff.DeleteAttrib('/document/node', 'a')
        expected = '[remove, /document/node/@a]'
        self._format_test(action, expected)

    def test_del_node(self):
        action = diff.DeleteNode('/document/node')
        expected = '[remove, /document/node]'
        self._format_test(action, expected)

    def test_del_text(self):
        action = diff.UpdateTextIn('/document/node', None)
        expected = '[update, /document/node/text()[1], null]'
        self._format_test(action, expected)

    def test_insert_attr(self):
        action = diff.InsertAttrib('/document/node', 'attr', 'val')
        expected = '[insert, /document/node, \n<@attr>\nval\n</@attr>]'
        self._format_test(action, expected)

    def test_insert_node(self):
        action = diff.InsertNode('/document', 'node', 0)
        expected = '[insert-first, /document, \n<node/>]'
        self._format_test(action, expected)

    def test_rename_node(self):
        # Move 1 down
        action = diff.RenameNode('/document/node[1]', 'newtag')
        expected = '[rename, /document/node[1], newtag]'
        self._format_test(action, expected)

        # Move 2 up (same result, different diff)
        action = diff.MoveNode('/document/node[2]', '/document', 0)
        expected = '[move-first, /document/node[2], /document]'
        self._format_test(action, expected)

    def test_update_attr(self):
        action = diff.UpdateAttrib('/document/node', 'attr', 'newval')
        expected = '[update, /document/node/@attr, "newval"]'
        self._format_test(action, expected)

    def test_update_text_in(self):
        action = diff.UpdateTextIn('/document/node', 'Text')
        expected = '[update, /document/node/text()[1], "Text"]'
        self._format_test(action, expected)

        action = diff.UpdateTextIn('/document/node',
                                   'Also a bit of text, "rick"')
        expected = '[update, /document/node/text()[1], '\
            u'"Also a bit of text, \\"rick\\""]'
        self._format_test(action, expected)

    def test_update_text_after_1(self):
        action = diff.UpdateTextAfter('/document/node[1]', 'Text')
        expected = '[update, /document/node[1]/text()[2], "Text"]'
        self._format_test(action, expected)

    def test_update_text_after_2(self):
        action = diff.UpdateTextAfter('/document/node',
                                      'Also a bit of text, rick')
        expected = '[update, /document/node/text()[2], '\
            u'"Also a bit of text, rick"]'
        self._format_test(action, expected)

    def test_all_actions(self):
        here = os.path.split(__file__)[0]
        lfile = os.path.join(here, 'test_data', 'all_actions.left.xml')
        rfile = os.path.join(here, 'test_data', 'all_actions.right.xml')

        formatter = formatting.XmlDiffFormatter()
        result = main.diff_files(lfile, rfile, formatter=formatter)
        expected = (
            u'[move-after, /document/node[2], /document/tag[1]]\n'
            u'[update, /document/node[1]/@name, "was updated"]\n'
            u'[remove, /document/node[1]/@attribute]\n'
            u'[insert, /document/node[1], \n'
            u'<@newtribute>\n'
            u'renamed\n'
            u'</@newtribute>]\n'
            u'[insert, /document/node[1], \n'
            u'<@this>\n'
            u'is new\n'
            u'</@this>]\n'
            u'[remove, /document/node[1]/@attr]\n'
            u'[update, /document/node[1]/text()[1], "\\n    Modified\\n  "]\n'
            u'[update, /document/node[1]/text()[2], "\\n    '
            u'New tail content\\n  "]\n'
            u'[rename, /document/node[2], nod]\n'
            u'[insert-after, /document/node[2], \n'
            u'<new/>]\n'
            u'[remove, /document/tail[1]]'
        )
        self.assertEqual(result, expected)


class FormatterFileTests(unittest.TestCase):

    formatter = None  # Override this
    maxDiff = None

    def process(self, left, right):
        return main.diff_files(left, right, formatter=self.formatter)


class XMLFormatterFileTests(FormatterFileTests):

    # The XMLFormatter has no text or formatting tags, so
    formatter = formatting.XMLFormatter(pretty_print=False,
                                        normalize=formatting.WS_TEXT)


# Also test the bits that handle text tags:

class HTMLFormatterFileTests(FormatterFileTests):

    # We use a few tags for the placeholder tests.
    # <br/> is intentionally left out, to test an edge case
    # with empty non-formatting tags in text.
    formatter = formatting.XMLFormatter(
        normalize=formatting.WS_BOTH,
        pretty_print=True,
        text_tags=('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'),
        formatting_tags=('b', 'u', 'i', 'strike', 'em', 'super',
                         'sup', 'sub', 'link', 'a', 'span'))


# Add tests that use no placeholder replacement (ie plain XML)
data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
generate_filebased_cases(data_dir, XMLFormatterFileTests)

# Add tests that use placeholder replacement (ie HTML)
data_dir = os.path.join(os.path.dirname(__file__), 'test_data')
generate_filebased_cases(data_dir, HTMLFormatterFileTests, suffix='html')
