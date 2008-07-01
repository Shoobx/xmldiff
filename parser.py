# Copyright (c) 2000 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details?
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""
This file contains a parser to transform xml document into an internal
tree in order to avoid adding new primitives with tree transformation

This operation represent all the document in a tree without attributes on
nodes nor text nodes, only nodes with a name and a child list

(the tree is composed by elements of type Node, defined below)
"""

from xmldiff.objects import NT_ROOT, NT_NODE, NT_ATTN, NT_ATTV, \
     NT_TEXT, NT_COMM, N_TYPE, N_ISSUE, N_CHILDS, N_VALUE, link_node
from xml.sax import ContentHandler

def _inc_xpath(h, xpath):
    try:
        h[xpath] = h[xpath] + 1
    except KeyError:
        h[xpath] = 1

class SaxHandler(ContentHandler):
    """
    Sax handler to transform xml doc into basic tree
    """

    def __init__(self, normalize_space, include_comment, encoding='UTF-8'): 
        self.encoding = encoding
        self._p_stack = [[NT_ROOT, '/', '', [], None, 0, 0]]
        self._norm_sp = normalize_space or None
        self._incl_comm = include_comment or None
        self._xpath = ''
        self._h = {}
        self._n_elmt = 0

    ## method of the ContentHandler interface #################################
    def startElement(self, name, attrs):
        name = name.encode(self.encoding)
        # process xpath 
        self._xpath = "%s%s%s" % (self._xpath, '/',  name)
        _inc_xpath(self._h, self._xpath)
        # nodes construction for element
        node = [NT_NODE, name, name, [], None, self._n_elmt+1,
                self._h[self._xpath]]
        self._n_elmt += 1
        self._xpath = "%s%s%s%s" % (self._xpath, '[', self._h[self._xpath], ']')
        # nodes construction for element's attributes
        keys = attrs.keys()
        # sort attributes to avoid further moves
        keys.sort()
        for key in keys:
            key = key.encode(self.encoding)
            self._n_elmt += 2
            attr_node = [NT_ATTN, '@%sName'%key, key, [], None, 1, 0]
            link_node(node, attr_node)
            link_node(attr_node, [NT_ATTV, '@%s'%key,
                                  attrs.get(key, '').encode(self.encoding),
                                  [],None,0,0])

        link_node(self._p_stack[-1], node)
        # set current element on the top of the father stack
        self._p_stack.append(node)
        
    def endElement(self, name):
        # process xpath 
        size = len(self._xpath)
        for i in range(size):
            size = size - 1
            if self._xpath[-i - 1] == '/':
                break
        self._xpath = self._xpath[:size]
        self._p_stack[-1][N_ISSUE] = self._n_elmt - self._p_stack[-1][N_ISSUE]
        # remove last element from stack
        self._p_stack.pop()

    def characters(self, ch):
        if self._norm_sp is not None:
            ch = ' '.join(ch.split())
        if len(ch) > 0 and ch != "\n" and ch != '  ':
            ch = ch.encode(self.encoding)
            parent = self._p_stack[-1]
            # if sibling text nodes
            if parent[N_CHILDS] and parent[N_CHILDS][-1][N_TYPE] == NT_TEXT:
                n = parent[N_CHILDS][-1]
                n[N_VALUE] = n[N_VALUE] + ch
            else:
                self._n_elmt += 1
                xpath = '%s/text()' % self._xpath
                _inc_xpath(self._h, xpath)
                # nodes construction for text
                node = [NT_TEXT, 'text()', ch, [],None,0, self._h[xpath]]
                link_node(parent, node)

    ## method of the LexicalHandler interface ##################################
    def comment(self, content):
        if self._incl_comm is None:
            return
        if self._norm_sp is not None:
            content = ' '.join(content.split())
        if len(content) > 0:
            self._n_elmt += 1
            content = content.encode(self.encoding)
            xpath = '%s/comment()' % self._xpath
            _inc_xpath(self._h, xpath)
            # nodes construction for comment
            node = [NT_COMM,  'comment()', content, [], None, 0, self._h[xpath]]
            link_node(self._p_stack[-1], node)

    # methods from xml.sax.saxlib.LexicalHandler (avoid dependencie to pyxml)
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
        self._p_stack[0][N_ISSUE] = self._n_elmt
        return self._p_stack[0]
