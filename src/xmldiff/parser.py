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
This file contains a parser to transform xml document into an internal
tree in order to avoid adding new primitives with tree transformation

This operation represent all the document in a tree without attributes on
nodes nor text nodes, only nodes with a name and a child list

(the tree is composed by elements of type Node, defined below)
"""
from collections import MutableSequence, Sequence

from xmldiff.objects import NT_ROOT, NT_NODE, NT_ATTN, NT_ATTV, \
    NT_TEXT, NT_COMM, N_TYPE, N_NAME, N_VALUE, N_CHILDS, N_PARENT, N_ISSUE, \
    N_XNUM, N_NSPREFIX, N_INORDER, N_MAPPED, link_node
from xml.sax import ContentHandler


def _inc_xpath(h, xpath):
    try:
        h[xpath] = h[xpath] + 1
    except KeyError:
        h[xpath] = 1


class Node(MutableSequence):
    """A node object"""

    __slots__ = ('type', 'name', 'value', 'children', 'parent', 'issue',
                 'xnum', 'prefix', 'inorder', 'mapped')

    def __init__(self, type, name, value, children=None, parent=None,
                 issue=0, xnum=0, prefix=None, inorder=False, mapped=False):
        self.type = type
        self.name = name
        self.value = value
        if children:
            for child in children:
                child.parent = self
        self.children = children
        self.parent = parent
        self.issue = issue
        self.xnum = xnum
        self.prefix = prefix
        self.inorder = inorder
        self.mapped = mapped

    def tag(self):
        if self.type == NT_NODE:
            if not self.children:
                return '<%s/>' % self.value
            else:
                child_tags = ''.join(e.tag() for e in self.children)
                return '<%s>\n%s\n</%s>' % (self.value, child_tags, self.value)
        if self.type in (NT_TEXT, NT_ATTN, NT_ATTV):
            return self.value.strip()
        return self

    def __repr__(self):
        'Return a nicely formatted representation string'
        # Always return "None" for parent, since otherwise we get infinite
        # recursions.
        return 'Node(type=%r, name=%r, value=%r, children=%r, parent=%r, '\
               'issue=%r, xnum=%r, prefix=%r, inorder=%r, mapped=%r)' % (
                   self.type, self.name, self.value, self.children,
                   None, self.issue, self.xnum, self.prefix, self.inorder,
                   self.mapped)

    def __getitem__(self, index):
        # TODO: Log warning
        if index == N_TYPE:
            return self.type
        if index == N_NAME:
            return self.name
        if index == N_VALUE:
            return self.value
        if index == N_CHILDS:
            return self.children
        if index == N_PARENT:
            return self.parent
        if index == N_ISSUE:
            return self.issue
        if index == N_XNUM:
            return self.xnum
        if index == N_NSPREFIX:
            return self.prefix
        if index == N_INORDER:
            return self.inorder
        if index == N_MAPPED:
            return self.mapped

    def __setitem__(self, index, value):
        if index == N_TYPE:
            self.type = value
        if index == N_NAME:
            self.name = value
        if index == N_VALUE:
            self.value = value
        if index == N_CHILDS:
            self.children = value
        if index == N_PARENT:
            self.parent = value
        if index == N_ISSUE:
            self.issue = value
        if index == N_XNUM:
            self.xnum = value
        if index == N_NSPREFIX:
            self.prefix = value
        if index == N_INORDER:
            self.prefix = value
        if index == N_MAPPED:
            self.mapped = value

    def __delitem__(self, index):
        raise NotImplementedError

    def insert(self, index, value):
        raise NotImplementedError

    def __contains__(self, x):
        raise NotImplementedError

    def __iter__(self):
        yield self.type
        yield self.name
        yield self.value
        yield self.children
        yield self.parent
        yield self.issue
        yield self.xnum
        yield self.prefix
        yield self.inorder
        yield self.mapped

    def __len__(self):
        return 10

    def __eq__(self, other):
        """This should be comparable with lists, and we also need to
        ignore the issue of recursion with parents.
        """
        if isinstance(other, (Node)):
            # we don't check for parent, inorder or mapped,
            # they are allowed to be different
            for attr in ('type', 'name', 'value', 'children', 'issue',
                         'xnum', 'prefix'):
                if getattr(self, attr) != getattr(other, attr):
                    return False

            return True
        elif isinstance(other, (Sequence)):
            # It's a list! BBB
            if len(other) != len(self):
                return False
            for i, values in enumerate(zip(self, other)):
                # Don't compare parents, we'll get infinite recursion,
                # also inorder and skipped are not relevant for equality
                if i in (N_PARENT, N_INORDER, N_MAPPED):
                    continue
                if values[0] != values[1]:
                    return False

            return True

        # Other comparisons
        return NotImplemented


class SaxHandler(ContentHandler):
    """
    Sax handler to transform xml doc into basic tree
    """

    def __init__(self, normalize_space, include_comment):
        self._p_stack = [Node(NT_ROOT, '/', '', [], None, 0, 0, None, None, None)]
        self._norm_sp = normalize_space or None
        self._incl_comm = include_comment or None
        self._xpath = ''
        self._h = {}
        self._n_elmt = 0
        self._ns_mapping = {None: [None]}
        self._new_mappings = {}
        self._default_ns = None

    def startPrefixMapping(self, prefix, uri):
        self._new_mappings[prefix] = uri
        try:
            self._ns_mapping[prefix].append(uri)
        except KeyError:
            self._ns_mapping[prefix] = [uri]
        if prefix is None:
            self._default_ns = uri

    def endPrefixMapping(self, prefix):
        ns_uri_list = self._ns_mapping[prefix]
        if prefix is None:
            self._default_ns = ns_uri_list[-1]
            ns_uri_list.pop()

    def _buildTag(self, ns_name_tuple):
        ns_uri, local_name = ns_name_tuple
        if ns_uri:
            el_tag = "{%s}%s" % ns_name_tuple
        else:
            el_tag = local_name
        return el_tag

    def _getPrefix(self, ns_uri):
        if not ns_uri:
            return None
        for (prefix, uri) in self._ns_mapping.items():
            if ns_uri in uri:
                return prefix
        if ns_uri == 'http://www.w3.org/XML/1998/namespace':
            # It's the xml: namespace, undeclared.
            return 'xml'
        raise ValueError("No prefix found for namespace URI %s" % ns_uri)

    ## method of the ContentHandler interface #################################
    def startElement(self, name, attrs):
        self.startElementNS((None, name), None, attrs)

    def startElementNS(self, name, qname, attrs):
        tagName = self._buildTag(name)
        prefix = self._getPrefix(name[0])

        # process xpath
        self._xpath = "%s%s%s" % (self._xpath, '/', name)
        _inc_xpath(self._h, self._xpath)
        # nodes construction for element
        node = Node(NT_NODE, tagName, tagName, [], None, self._n_elmt + 1,
                    self._h[self._xpath], prefix, None, None)
        self._n_elmt += 1
        self._xpath = "%s%s%s%s" % (
            self._xpath, '[', self._h[self._xpath], ']')
        # nodes construction for element's attributes
        # sort attributes to avoid further moves
        for key, value in sorted(attrs.items()):
            self._n_elmt += 2
            attrName = self._buildTag(key)
            prefix = self._getPrefix(key[0])
            attr_node = Node(NT_ATTN, '@%sName' % attrName, attrName, [], None,
                             1, 0, prefix, None, None)
            link_node(node, attr_node)
            link_node(attr_node, Node(NT_ATTV, '@%s' % attrName, value,
                                      [], None, 0, 0, prefix, None, None))

        link_node(self._p_stack[-1], node)
        # set current element on the top of the father stack
        self._p_stack.append(node)

    def endElementNS(self, ns_name, qname):
        self.endElement(self._buildTag(ns_name))

    def endElement(self, name):
        # process xpath
        size = len(self._xpath)
        for i in range(size):
            size = size - 1
            if self._xpath[-i - 1] == '/':
                break
        self._xpath = self._xpath[:size]
        self._p_stack[-1].issue = self._n_elmt - self._p_stack[-1].issue
        # remove last element from stack
        self._p_stack.pop()

    def characters(self, ch):
        if self._norm_sp is not None:
            ch = ' '.join(ch.split())
        if len(ch) > 0 and ch != "\n" and ch != '  ':
            parent = self._p_stack[-1]
            # if sibling text nodes
            if parent.children and parent.children[-1].type == NT_TEXT:
                n = parent.children[-1]
                n.value = n.value + ch
            else:
                self._n_elmt += 1
                xpath = '%s/text()' % self._xpath
                _inc_xpath(self._h, xpath)
                # nodes construction for text
                node = Node(NT_TEXT, 'text()', ch, [], None, 0,
                            self._h[xpath], None, None, None)
                link_node(parent, node)

    ## method of the LexicalHandler interface #################################
    def comment(self, content):
        if self._incl_comm is None:
            return
        if self._norm_sp is not None:
            content = ' '.join(content.split())
        if len(content) > 0:
            self._n_elmt += 1
            xpath = '%s/comment()' % self._xpath
            _inc_xpath(self._h, xpath)
            # nodes construction for comment
            node = Node(NT_COMM, 'comment()', content, [], None,
                        0, self._h[xpath], None, None, None)
            link_node(self._p_stack[-1], node)

    # methods from xml.sax.saxlib.LexicalHandler (avoid dependency on pyxml)
    def startDTD(self, name, public_id, system_id):
        """Report the start of the DTD declarations, if the document
        has an associated DTD.

        A startEntity event will be reported before declaration events
        from the external DTD subset are reported, and this can be
        used to infer from which subset DTD declarations derive.

        name is the name of the document element type, public_id the
        public identifier of the DTD (or None if none were supplied)
        and system_id the system identfier of the external subset (or
        None if none were supplied)."""

    def endDTD(self):
        "Signals the end of DTD declarations."

    def startEntity(self, name):
        """Report the beginning of an entity.

        The start and end of the document entity is not reported. The
        start and end of the external DTD subset is reported with the
        pseudo-name '[dtd]'.

        Skipped entities will be reported through the skippedEntity
        event of the ContentHandler rather than through this event.

        name is the name of the entity. If it is a parameter entity,
        the name will begin with '%'."""

    def endEntity(self, name):
        """Reports the end of an entity. name is the name of the
        entity, and follows the same conventions as for
        startEntity."""

    def startCDATA(self):
        """Reports the beginning of a CDATA marked section.

        The contents of the CDATA marked section will be reported
        through the characters event."""

    def endCDATA(self):
        "Reports the end of a CDATA marked section."

    def get_tree(self):
        self._p_stack[0].issue = self._n_elmt
        return self._p_stack[0]
