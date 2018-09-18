import json
import os
import re
import six

from collections import namedtuple
from copy import deepcopy
from lxml import etree
from xmldiff.diff_match_patch import diff_match_patch
from xmldiff import utils


DIFF_NS = 'http://namespaces.shoobx.com/diff'
DIFF_PREFIX = 'diff'
XSLT_FILE = os.path.join(os.path.split(__file__)[0], 'htmlformatter.xslt')

INSERT_NAME = '{%s}insert' % DIFF_NS
DELETE_NAME = '{%s}delete' % DIFF_NS

# Flags for whitespace handling in the text aware formatters:
WS_BOTH = 3  # Normalize ignorable whitespace and text whitespace
WS_TEXT = 2  # Normalize whitespace only inside text tags
WS_TAGS = 1  # Delete ignorable whitespace (between tags)
WS_NONE = 0  # Preserve all whitespace

# Placeholder tag type
T_OPEN = 0
T_CLOSE = 1
T_SINGLE = 2


# These Bases can be abstract baseclasses, but it's a pain to support
# Python 2.7 in that case, because there is no abc.ABC. Right now this
# is just a description of the API.

class BaseFormatter(object):

    def __init__(self, normalize=WS_TAGS, pretty_print=False):
        """Formatters must as a minimum have a normalize parameter

        This is used by the main API to decide is whitespace between the
        tags should be stripped (the remove_blank_text flag in lxml) and
        if tags that are known texts tags should be normalized before
        comparing. String content in non-text tags will not be
        normalized with the included formatters.

        pretty_print is used to choose between a compact and a pretty output.
        This is currently only used by the XML and HTML formatters.

        Formatters may of course have more options than these, but these
        two are the ones that can be set from the command-line.
        """

    def prepare(self, left_tree, right_tree):
        """Allows the formatter to prepare the trees before diffing

        That preparing may need some "unpreparing", but it's then done
        by the formatters format() method, and is not a part of the
        public interface."""

    def format(self, diff, orig_tree):
        """Formats the diff and returns a unicode string

        A formatter that returns XML with diff markup will need the original
        tree available to do it's job, so there is an orig_tree parameter,
        but it may be ignored by differs that don't need it.
        """


PlaceholderEntry = namedtuple('PlaceholderEntry', 'element ttype close_ph')


class PlaceholderMaker(object):
    """Replace tags with unicode placeholders

    This class searches for certain tags in an XML tree and replaces them
    with unicode placeholders. The idea is to replace structured content
    (in this case XML elements) with unicode characters which then
    participate in the regular text diffing algorithm. This makes text
    diffing easier and faster.

    The code can then unreplace the unicode placeholders with the tags.
    """

    def __init__(self, text_tags=(), formatting_tags=()):
        self.text_tags = text_tags
        self.formatting_tags = formatting_tags
        self.placeholder2tag = {}
        self.tag2placeholder = {}
        # This number represents the beginning of the largest private-use
        #  block (13,000 characters) in the unicode space.
        self.placeholder = 0xf0000

        insert_elem = etree.Element(INSERT_NAME)
        insert_close = self.get_placeholder(
            insert_elem, T_CLOSE, None)
        insert_open = self.get_placeholder(
            insert_elem, T_OPEN, insert_close)

        delete_elem = etree.Element(DELETE_NAME)
        delete_close = self.get_placeholder(
            delete_elem, T_CLOSE, None)
        delete_open = self.get_placeholder(
            delete_elem, T_OPEN, delete_close)

        self.diff_tags = {
            'insert': (insert_open, insert_close),
            'delete': (delete_open, delete_close)}

    def get_placeholder(self, element, ttype, close_ph):
        tag = etree.tounicode(element)
        ph = self.tag2placeholder.get((tag, ttype, close_ph))
        if ph is not None:
            return ph

        self.placeholder += 1
        ph = six.unichr(self.placeholder)
        self.placeholder2tag[ph] = PlaceholderEntry(element, ttype, close_ph)
        self.tag2placeholder[tag, ttype, close_ph] = ph
        return ph

    def is_placeholder(self, char):
        return len(char) == 1 and char in self.placeholder2tag

    def is_formatting(self, element):
        return element.tag in self.formatting_tags

    def do_element(self, element):
        for child in element:
            # Resolve all formatting text by allowing the inside text to
            # participate in the text diffing.
            tail = child.tail or u''
            child.tail = u''
            new_text = element.text or u''

            if self.is_formatting(child):
                ph_close = self.get_placeholder(child, T_CLOSE, None)
                ph_open = self.get_placeholder(child, T_OPEN, ph_close)
                # If it's known text formatting tags, do this hierarchically
                self.do_element(child)
                text = child.text or u''
                child.text = u''
                # Stick the placeholder in instead of the start and end tags:
                element.text = new_text + ph_open + text + ph_close + tail
            else:
                ph_single = self.get_placeholder(child, T_SINGLE, None)
                # Replace the whole tag including content:
                element.text = new_text + ph_single + tail

            # Remove the element from the tree now that we have inserted a
            # placeholder.
            element.remove(child)

    def do_tree(self, tree):
        if self.text_tags:
            for elem in tree.xpath('//'+'|//'.join(self.text_tags)):
                self.do_element(elem)

    def split_string(self, text):
        regexp = u'([%s])' % u''.join(self.placeholder2tag)
        return re.split(regexp, text, flags=re.MULTILINE)

    def undo_string(self, text):
        result = etree.Element('wrap')
        element = None

        segments = self.split_string(text)
        while segments:
            seg = segments.pop(0)
            if not seg:
                continue

            # Segments can be either plain string or placeholders.
            if self.is_placeholder(seg):
                entry = self.placeholder2tag[seg]
                element = deepcopy(entry.element)
                # Is this a open/close segment?
                if entry.ttype == T_OPEN:
                    # Yup
                    next_seg = segments.pop(0)
                    new_text = u''
                    while next_seg != entry.close_ph:
                        new_text += next_seg
                        next_seg = segments.pop(0)
                    element.text = new_text or None
                    element.tail = None

                self.undo_element(element)
                result.append(element)
            else:
                if element is not None:
                    element.tail = element.tail or u'' + seg
                else:
                    result.text = result.text or u'' + seg

        return result

    def undo_element(self, elem):
        if self.placeholder2tag:
            if elem.text:
                index = 0
                content = self.undo_string(elem.text)
                if elem.text != content.text:
                    # Placeholders was replaced
                    elem.text = content.text
                    for child in content:
                        self.undo_element(child)
                        elem.insert(index, child)
                        index += 1

            for child in elem:
                self.undo_element(child)

            if elem.tail:
                content = self.undo_string(elem.tail)
                if elem.tail != content.text:
                    # Placeholders was replaced
                    elem.tail = content.text
                    parent = elem.getparent()
                    index = parent.index(elem) + 1
                    for child in content:
                        self.undo_element(child)
                        parent.insert(index, child)
                        index += 1

    def undo_tree(self, tree):
        self.undo_element(tree)

    def mark_diff(self, ph, action):
        entry = self.placeholder2tag[ph]
        if entry.ttype == T_CLOSE:
            # Close tag, nothing to mark
            return ph

        # Mark the tag as having a diff-action. We do need to
        # make a copy of it and get a new placeholder:
        elem = entry.element
        elem = deepcopy(elem)
        if self.is_formatting(elem):
            # Formatting element, add a diff attribute
            action += '-formatting'
        elem.attrib['{%s}%s' % (DIFF_NS, action)] = ''

        # And make a new placeholder for this new entry:
        return self.get_placeholder(elem, entry.ttype, entry.close_ph)

    def wrap_diff(self, text, action):
        open_ph, close_ph = self.diff_tags[action]
        return open_ph + text + close_ph


class XMLFormatter(BaseFormatter):
    """A formatter that also replaces formatting tags with unicode characters

    The idea of this differ is to replace structured content (in this case XML
    elements) with unicode characters which then participate in the regular
    text diffing algorithm. This is done in the prepare() step.

    Each identical XML element will get a unique unicode character. If the
    node is changed for any reason, a new unicode character is assigned to the
    node. This allows identity detection of structured content between the
    two text versions while still allowing customization during diffing time,
    such as marking a new formatting node. The latter feature allows for
    granular style change detection independently of text changes.

    In order for the algorithm to not go crazy and convert entire XML
    documents to text (though that is perfectly doable), a few rules have been
    defined.

    - The `textTags` attribute lists all the XML nodes by name which can
      contain text. All XML nodes within those text nodes are converted to
      unicode placeholders. If you want better control over which parts of
      your XML document are considered text, you can simply override the
      ``insert_placeholders(tree)`` function. It is purposefully kept small to
      allow easy subclassing.

    - By default, all tags inside text tags are treated as immutable
      units. That means the node itself including its entire sub-structure is
      assigned one unicode character.

    - The ``formattingTags`` attribute is used to specify tags that format the
      text. For these tags, the opening and closing tags receive unique
      unicode characters, allowing for sub-structure change detection and
      formatting changes. During the diff markup phase, formatting notes are
      annotated to mark them as inserted or deleted allowing for markup
      specific to those formatting changes.

    The diffed version of the structural tree is passed into the
    ``finalize(tree)`` method to convert all the placeholders back into
    structural content before formatting.

    The ``normalize`` parameter decides how to normalize whitespace.
    WS_TEXT normalizes only inside text_tags, WS_TAGS will remove ignorable
    whitespace between tags, WS_BOTH do both, and WS_NONE will preserve
    all whitespace.
    """

    def __init__(self, normalize=WS_NONE, pretty_print=True,
                 text_tags=(), formatting_tags=()):
        # Mapping from placeholders -> structural content and vice versa.
        self.normalize = normalize
        self.pretty_print = pretty_print
        self.text_tags = text_tags
        self.formatting_tags = formatting_tags
        self.placeholderer = PlaceholderMaker(
            text_tags=text_tags, formatting_tags=formatting_tags)

    def prepare(self, left_tree, right_tree):
        """prepare() is run on the trees before diffing

        This is so the formatter can apply magic before diffing."""
        # We don't want to diff comments:
        self._remove_comments(left_tree)
        self._remove_comments(right_tree)

        self.placeholderer.do_tree(left_tree)
        self.placeholderer.do_tree(right_tree)

    def finalize(self, result_tree):
        """finalize() is run on the resulting tree before returning it

        This is so the formatter cab apply magic after diffing."""
        self.placeholderer.undo_tree(result_tree)

    def format(self, diff, orig_tree, differ=None):
        # Make a new tree, both because we want to add the diff namespace
        # and also because we don't want to modify the original tree.
        result = deepcopy(orig_tree)
        if isinstance(result, etree._ElementTree):
            root = result.getroot()
        else:
            root = result

        etree.register_namespace(DIFF_PREFIX, DIFF_NS)

        for action in diff:
            self.handle_action(action, root)

        self.finalize(root)

        etree.cleanup_namespaces(result, top_nsmap={DIFF_PREFIX: DIFF_NS})
        return self.render(result)

    def render(self, result):
        return etree.tounicode(result, pretty_print=self.pretty_print)

    def handle_action(self, action, result):
        action_type = type(action)
        method = getattr(self, '_handle_' + action_type.__name__)
        method(action, result)

    def _remove_comments(self, tree):
        comments = tree.xpath('//comment()')

        for element in comments:
            element.getparent().remove(element)

    def _xpath(self, node, xpath):
        # This method finds an element with xpath and makes sure that
        # one and exactly one element is found. This is to protect against
        # formatting a diff on the wrong tree, or against using ambigous
        # edit script xpaths.
        if xpath[0] == '/':
            root = True
            xpath = xpath[1:]
        else:
            root = False

        if '/' in xpath:
            path, rest = xpath.split('/', 1)
        else:
            path = xpath
            rest = ''

        if '[' in path:
            path, index = path[:-1].split('[')
            index = int(index) - 1
            multiple = False
        else:
            index = 0
            multiple = True

        if root:
            path = '/' + path

        matches = []
        for match in node.xpath(path, namespaces=node.nsmap):
            # Skip nodes that have been deleted
            if DELETE_NAME not in match.attrib:
                matches.append(match)

        if index >= len(matches):
            raise ValueError('xpath %s[%s] not found at %s.' % (
                path, index + 1, utils.getpath(node)))
        if len(matches) > 1 and multiple:
            raise ValueError('Multiple nodes found for xpath %s at %s.' % (
                path, utils.getpath(node)))
        match = matches[index]
        if rest:
            return self._xpath(match, rest)
        return match

    def _extend_diff_attr(self, node, action, value):
        diffattr = '{%s}%s-attr' % (DIFF_NS, action)
        oldvalue = node.attrib.get(diffattr, '')
        if oldvalue:
            value = oldvalue + ';' + value
        node.attrib[diffattr] = value

    def _delete_attrib(self, node, name):
        del node.attrib[name]
        self._extend_diff_attr(node, 'delete', name)

    def _handle_DeleteAttrib(self, action, tree):
        node = self._xpath(tree, action.node)
        self._delete_attrib(node, action.name)

    def _delete_node(self, node):
        insert_attr = INSERT_NAME
        if insert_attr in node.attrib:
            # This happens is a node is first moved
            # then renamed. Perhaps those should be the same?
            del node.attrib[insert_attr]
        node.attrib[DELETE_NAME] = ''

    def _handle_DeleteNode(self, action, tree):
        node = self._xpath(tree, action.node)
        self._delete_node(node)

    def _insert_attrib(self, node, name, value):
        node.attrib[name] = value
        self._extend_diff_attr(node, 'add', name)

    def _handle_InsertAttrib(self, action, tree):
        node = self._xpath(tree, action.node)
        self._insert_attrib(node, action.name, action.value)

    def _insert_node(self, target, node, position):
        node.attrib[INSERT_NAME] = ''
        target.insert(position, node)

    def _get_real_insert_position(self, target, position):
        # Find the real position:
        pos = 0
        offset = 0
        for child in target.getchildren():
            if DELETE_NAME in child.attrib:
                offset += 1
            else:
                pos += 1
            if pos > position:
                # We found the right offset
                break
        # Real position
        return position + offset

    def _handle_InsertNode(self, action, tree):
        # Insert node as a child. However, position is the position in the
        # new tree, and the diff tree may have deleted children, so we must
        # adjust the position for that.
        target = self._xpath(tree, action.target)
        position = self._get_real_insert_position(target, action.position)
        new_node = target.makeelement(action.tag, nsmap=target.nsmap)
        self._insert_node(target, new_node, position)

    def _rename_attrib(self, node, oldname, newname):
        node.attrib[newname] = node.attrib[oldname]
        del node.attrib[oldname]
        self._extend_diff_attr(node, 'rename', '%s:%s' % (oldname, newname))

    def _handle_RenameAttrib(self, action, tree):
        node = self._xpath(tree, action.node)
        self._rename_attrib(node, action.oldname, action.newname)

    def _handle_MoveNode(self, action, tree):
        node = self._xpath(tree, action.node)
        inserted = deepcopy(node)
        target = self._xpath(tree, action.target)
        self._delete_node(node)
        position = self._get_real_insert_position(target, action.position)
        self._insert_node(target, inserted, position)

    def _handle_RenameNode(self, action, tree):
        node = self._xpath(tree, action.node)
        # Make a copy of the node and set it's tag to the new tag
        new_node = deepcopy(node)
        new_node.tag = action.tag
        # The old node that are to be deleted must now have no tail, the new
        # node keeps the tail.
        node.tail = None
        parent = node.getparent()
        pos = parent.index(node) + 1
        self._delete_node(node)
        self._insert_node(parent, new_node, pos)

    def _update_attrib(self, node, name, value):
        oldval = node.attrib[name]
        node.attrib[name] = value
        self._extend_diff_attr(node, 'update', '%s:%s' % (name, oldval))

    def _handle_UpdateAttrib(self, action, tree):
        node = self._xpath(tree, action.node)
        self._update_attrib(node, action.name, action.value)

    def _realign_placeholders(self, diff):
        # Since the differ always deletes first and insert second,
        # placeholders that represent XML open and close tags will get
        # misaligned. This method will fix that order.
        new_diff = []  # Diff list with proper tree structure.
        stack = []  # Current node path.

        def _stack_pop():
            return stack.pop() if stack else (None, None)

        for op, text in diff:
            segments = self.placeholderer.split_string(text)
            for seg in segments:
                if not seg:
                    continue
                # There is nothing to do for regular text.
                if not self.placeholderer.is_placeholder(seg):
                    new_diff.append((op, seg))
                    continue
                # Handle all structural replacement elements.
                entry = self.placeholderer.placeholder2tag[seg]
                if entry.ttype == T_SINGLE:
                    # There is nothing to do for singletons since they are
                    # fully self-contained.
                    new_diff.append((op, seg))
                    continue
                elif entry.ttype == T_OPEN:
                    # Opening tags are added to the stack, so we know what
                    # needs to be closed when. We are assuming that tags are
                    # opened in the desired order.
                    stack.append((op, entry))
                    new_diff.append((op, seg))
                    continue
                elif entry.ttype == T_CLOSE:
                    # Due to the nature of the text diffing algorithm, closing
                    # tags can be out of order. But since we know what we need
                    # to close, we simply glean at the stack to know what
                    # needs to be closed before the requested node closure can
                    # happen.
                    stack_op, stack_entry = _stack_pop()
                    while (
                            stack_entry is not None and
                            stack_entry.close_ph != seg
                           ):
                        new_diff.append((stack_op, stack_entry.close_ph))
                        stack_op, stack_entry = _stack_pop()

                    # Stephan: We have situations where the opening tag
                    # remains in place but the closing text moves from on
                    # position to another. In those cases, we will have two
                    # closing tags for one opening one. Since we want to
                    # prefer the new version over the old in terms of
                    # formatting, we ignore the deletion and close the tag
                    # where it was inserted.
                    # Lennart: I could not make any case that made
                    # stack_op > op, so I removed the handling, and
                    # put in an assert
                    if stack_entry is not None:
                        assert stack_op <= op
                        new_diff.append((op, seg))
        return new_diff

    def _make_diff_tags(self, left_value, right_value, node, target=None):
        if bool(self.normalize & WS_TEXT):
            left_value = utils.cleanup_whitespace(left_value or u'').strip()
            right_value = utils.cleanup_whitespace(right_value or u'').strip()

        text_diff = diff_match_patch()
        diff = text_diff.diff_main(left_value or '', right_value or '')
        text_diff.diff_cleanupSemantic(diff)

        diff = self._realign_placeholders(diff)

        cur_child = None
        if target is None:
            target = node
        else:
            cur_child = node

        for op, text in diff:
            if op == 0:
                if cur_child is None:
                    node.text = (node.text or u'') + text
                else:
                    cur_child.tail = (cur_child.tail or u'') + text
                continue

            if op == -1:
                action = 'delete'
            elif op == 1:
                action = 'insert'

            if self.placeholderer.is_placeholder(text):
                ph = self.placeholderer.mark_diff(text, action)

                if cur_child is None:
                    node.text = (node.text or u'') + ph

            else:
                new_text = self.placeholderer.wrap_diff(text, action)

                if cur_child is None:
                    node.text = (node.text or u'') + new_text
                else:
                    cur_child.tail = (cur_child.tail or u'') + new_text

    def _handle_UpdateTextIn(self, action, tree):
        node = self._xpath(tree, action.node)
        if INSERT_NAME in node.attrib:
            # The whole node is already marked as inserted,
            # we don't need to diff-wrap the text.
            node.text = action.text
            return node
        left_value = node.text
        right_value = action.text
        node.text = None

        self._make_diff_tags(left_value, right_value, node)

        return node

    def _handle_UpdateTextAfter(self, action, tree):
        node = self._xpath(tree, action.node)
        left_value = node.tail
        right_value = action.text
        node.tail = None

        self._make_diff_tags(left_value, right_value, node, node.getparent())

        return node


class DiffFormatter(BaseFormatter):

    def __init__(self, normalize=WS_TAGS, pretty_print=False):
        self.normalize = normalize
        # No pretty print support, nothing to be pretty about

    # Nothing to prepare or finalize (one-liners for code coverage)
    def prepare(self, left, right): return

    def finalize(self, left, right): return

    def format(self, diff, orig_tree):
        # This Formatter don't need the left tree, but the XMLFormatter
        # does, so the parameter is required.
        res = u'\n'.join(self._format_action(action) for action in diff)
        return res

    def _format_action(self, action, ):
        return u'[%s]' % self.handle_action(action)

    def handle_action(self, action):
        action_type = type(action)
        method = getattr(self, '_handle_' + action_type.__name__)
        return u', '.join(method(action))

    def _handle_DeleteAttrib(self, action):
        return u"delete-attribute", action.node, action.name

    def _handle_DeleteNode(self, action):
        return u"delete", action.node

    def _handle_InsertAttrib(self, action):
        return (u"insert-attribute", action.node, action.name,
                json.dumps(action.value))

    def _handle_InsertNode(self, action):
        return u"insert", action.target, action.tag, str(action.position)

    def _handle_RenameAttrib(self, action):
        return (u"move-attribute", action.node, action.oldname, action.newname)

    def _handle_MoveNode(self, action):
        return u"move", action.node, action.target, str(action.position)

    def _handle_UpdateAttrib(self, action):
        return (u"update-attribute", action.node, action.name,
                json.dumps(action.value))

    def _handle_UpdateTextIn(self, action):
        return u"update-text", action.node, json.dumps(action.text)

    def _handle_UpdateTextAfter(self, action):
        return u"update-text-after", action.node, json.dumps(action.text)

    def _handle_RenameNode(self, action):
        return u"rename", action.node, action.tag


class XmlDiffFormatter(BaseFormatter):
    """A formatter for an output trying to be xmldiff 0.6 compatible"""

    def __init__(self, normalize=WS_TAGS, pretty_print=False):
        self.normalize = normalize
        # No pretty print support, nothing to be pretty about

    # Nothing to prepare or finalize (one-liners for code coverage)
    def prepare(self, left, right): return

    def finalize(self, left, right): return

    def format(self, diff, orig_tree):
        # This Formatter don't need the left tree, but the XMLFormatter
        # does, so the parameter is required.
        actions = []
        for action in diff:
            actions.extend(self.handle_action(action, orig_tree))
        res = u'\n'.join(self._format_action(action) for action in actions)
        return res

    def _format_action(self, action):
        return u'[%s]' % ', '.join(action)

    def handle_action(self, action, orig_tree):
        action_type = type(action)
        method = getattr(self, '_handle_' + action_type.__name__)
        for item in method(action, orig_tree):
            yield item

    def _handle_DeleteAttrib(self, action, orig_tree):
        yield u"remove", '%s/@%s' % (action.node, action.name)

    def _handle_DeleteNode(self, action, orig_tree):
        yield u"remove", action.node

    def _handle_InsertAttrib(self, action, orig_tree):
        value_text = "\n<@{0}>\n{1}\n</@{0}>".format(action.name, action.value)
        yield u"insert", action.node, value_text

    def _handle_InsertNode(self, action, orig_tree):
        if action.position == 0:
            yield u"insert-first", action.target, '\n<%s/>' % action.tag
            return
        sibling = orig_tree.xpath(action.target)[0][action.position - 1]
        yield u"insert-after", utils.getpath(sibling), '\n<%s/>' % action.tag

    def _handle_RenameAttrib(self, action, orig_tree):
        node = orig_tree.xpath(action.node)[0]
        value = node.attrib[action.oldname]
        value_text = "\n<@{0}>\n{1}\n</@{0}>".format(action.newname, value)
        yield u"remove", '%s/@%s' % (action.node, action.oldname)
        yield u"insert", action.node, value_text

    def _handle_MoveNode(self, action, orig_tree):
        if action.position == 0:
            yield u"move-first", action.node, action.target
            return
        node = orig_tree.xpath(action.node)[0]
        target = orig_tree.xpath(action.target)[0]
        # Get the position of the previous sibling
        position = action.position - 1
        if node.getparent() is target:
            # Moving to a new lower position in the same target,
            # adjust previous sibling position:
            if target.index(node) <= position:
                position += 1

        sibling = target[position]
        yield u"move-after", action.node, utils.getpath(sibling)

    def _handle_UpdateAttrib(self, action, orig_tree):
        yield (u"update", '%s/@%s' % (action.node, action.name),
               json.dumps(action.value))

    def _handle_UpdateTextIn(self, action, orig_tree):
        yield u"update", action.node + '/text()[1]', json.dumps(action.text)

    def _handle_UpdateTextAfter(self, action, orig_tree):
        yield u"update", action.node + '/text()[2]', json.dumps(action.text)

    def _handle_RenameNode(self, action, orig_tree):
        yield u"rename", action.node, action.tag
