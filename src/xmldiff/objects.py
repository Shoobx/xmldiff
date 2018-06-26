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
provides constantes for using node and action (list) and some functions
for these objects use

    /!\  /!\ do not call index, remove or compare two node with == since a
             node is a recursive list
"""

import sys

################ ACTIONS ######################################################

A_DESC = 0  # string describes the action
A_N1 = 1  # node on which the action applies
A_N2 = 2  # optional second action argument, maybe node or value


################## NODES CONSTANTES ###########################################
# BBB remove in 2.1

N_TYPE = 0  # node's type
N_NAME = 1  # node's label (to process xpath)
N_VALUE = 2  # node's value
N_CHILDS = 3  # nodes's childs list
N_PARENT = 4  # node's parent
N_ISSUE = 5  # node's total issue number
N_XNUM = 6  # to compute node's xpath
N_NSPREFIX = 7  # node's namespace prefix (if any)
N_INORDER = 8
N_MAPPED = 9

# number of items in a list which represent a node
# except N_INORDER and N_MAPPED (don't ask)
NSIZE = 8

# NODE TYPES
# NT_SYST = 0 # SYSTEM node (added by parser) /!\ deprecated
NT_NODE = 1  # ELEMENT node
NT_ATTN = 2  # ATTRIBUTE NAME node
NT_ATTV = 3  # ATTRIBUTE VALUE node
NT_TEXT = 4  # TEXT node
NT_COMM = 5  # COMMENT node
NT_ROOT = 6  # root node
NODES_TYPES = ('NT', 'NN', 'AN', 'AV', 'T', 'C', 'R')  # for printing


################## OPERATIONS EDITING NODES ###################################

def link_node(parent, child):
    """ link child to his parent """
    if child:
        parent.children.append(child)
        child.parent = parent


def insert_node(node, new, pos):
    """ insert child new on node at position pos (integer) """
    node.children.insert(pos, new)
    new.parent = node
    i, j = 0, 1
    while i < len(node.children):
        n = node.children[i]
        if n.name == new.name and n.type == new.type:
            n.xnum = j
            j += 1
        i += 1


def delete_node(node):
    """ delete a node from its tree """
    siblings = node.parent.children
    i = get_pos(node)
    siblings.pop(i)
    node.parent = None
    while i < len(siblings):
        n = siblings[i]
        if n.name == node.name and n.type == node.type:
            n.xnum -= 1
        i += 1


def rename_node(node, new_name):
    """ rename a node
    this is necessary for xpath
    """
    siblings = node.parent.children
    pos = get_pos(node)
    xnum = 1
    for i in range(len(siblings)):
        n = siblings[i]
        if i < pos:
            if n.name == new_name and n.type == node.type:
                xnum += 1
        elif i != pos:
            if n.name == node.name and n.type == node.type:
                n.xnum -= 1
            elif n.name == new_name and n.type == node.type:
                n.xnum += 1
    node.name = new_name
    node.xnum = xnum


################## OPERATIONS FORMATING NODES #################################

def caract(node):
    """ return a string which represent the node """
    return '%s:%s (%s) %s %s' % (NODES_TYPES[node.type], node.value,
                                 f_xpath(node), id(node), node.issue)


def f_xpath(node, x=''):
    """ compute node's xpath """
    name = node.name
    if '{' in name:
        # We have a namespace
        pre, rest = name.split('{', 1)
        uri, local_name = rest.split('}', 1)
        prefix = node.prefix
        if prefix is None:
            # Default namespace
            name = pre + local_name
        else:
            name = '%s%s:%s' % (pre, prefix, local_name)

    if name != '/':
        if node.type == NT_ATTN:
            return f_xpath(node.parent,
                           '/%s' % name[:len(name) - 4])
        if node.type == NT_ATTV:
            return f_xpath(node.parent)
        return f_xpath(node.parent, '/%s[%d]%s' % (
            name, node.xnum, x))

    elif not x:
        return '/'
    return x


def node_repr(node):
    """ return a string which represents the given node """
    s = '%s\n' % caract(node)
    for child in node.children:
        s = '%s%s' % (s, _indent(child, '  '))
    return s


def _indent(node, indent_str):
    s = '%s\-%s\n' % (indent_str, caract(node))
    if next_sibling(node) is not None:
        indent_str = '%s| ' % indent_str
    else:
        indent_str = '%s  ' % indent_str
    for child in node.children:
        s = '%s%s' % (s, _indent(child, indent_str))
    return s


def xml_print(node, indent='', stream=None):
    """
    recursive function which write the node in an xml form without the added
    nodes
    """
    if stream is None:
        stream = sys.stdout
    _xml_print_internal_format(node, indent, stream)


def _xml_print_internal_format(node, indent, stream):
    if node.type == NT_NODE:
        attrs_s = ''
        i = 0
        while i < len(node.children):
            n = node.children[i]
            if n.type == NT_ATTN:
                i += 1
                attrs_s = '%s %s="%s"' % (attrs_s, n.value,
                                          n.children[0].value)
            else:
                break
        if len(node.children) > i:
            stream.write('%s<%s%s>\n' % (indent, node.value, attrs_s))
            for _curr_node in node.children[i:]:
                _xml_print_internal_format(
                    _curr_node, indent + '  ', stream=stream)
            stream.write('%s</%s>\n' % (indent, node.value))
        else:
            stream.write('%s<%s%s/>\n' % (indent, node.value, attrs_s))
    elif node.type == NT_ATTN:
        stream.write('%s<@%s>\n' % (indent, node.value))
        stream.write(node.children[0].value + '\n')
        stream.write('%s</%s>\n' % (indent, node.value))
    elif node.type == NT_COMM:
        stream.write('%s<!-- %s -->\n' % (indent, node.value))
    elif node.type == NT_TEXT:
        stream.write(node.value + '\n')
    else:
        stream.write('unknown node type', str(node.type))


################## OPERATIONS GIVING INFOS ON NODES ###########################
def get_pos(node):
    """ return the index of a node in its parent's children list

    /!\  /!\ do not call index, remove or compare two node with == since a
             node is a recursive list
    """
    try:
        childs = node.parent.children
        for i, child in enumerate(childs):
            if child is node:
                return i
    except TypeError:
        return -1
    except ValueError:
        return -1


def nb_attrs(node):
    """ return the number of attributes of the given node """
    for i, child in enumerate(node.children):
        if child.type != NT_ATTN:
            break
    else:
        try:
            i += 1
        except UnboundLocalError:
            i = 0
    return i


################## MISCELLANEOUS OPERATIONS ON NODES ##########################
def next_sibling(node):
    """ return the node's right sibling """
    if node.parent is None:
        return None
    myindex = get_pos(node)
    if len(node.parent.children) > myindex + 1:
        return node.parent.children[myindex + 1]
    return None


def get_ancestors(node, l):
    """ append to l all the ancestors from node """
    while node.parent:
        l.append(node)
        node = node.parent
    return l


def get_labels(tree, labels, leaf_labels):
    """
    Chain all nodes with a given label l in tree T together, from left to
    right, by filling dictionnaries labels and leaf_labels (for leaf nodes).

    Label are keys pointing to a list of nodes with this type.
    Node x occurs after y in the list if x appears before y in the in-order
    traversal of T.
    /!\  /!\
    since this isn't binary tree, post order traversal (?)
    """
    if tree and tree.children:
        for node in tree.children:
            get_labels(node, labels, leaf_labels)
        labels.setdefault(NODES_TYPES[tree.type], []).append(tree)
    elif tree:
        leaf_labels.setdefault(NODES_TYPES[tree.type], []).append(tree)


def make_bfo_list(tree):
    """ create a list with tree nodes in breadth first order """
    queue = [tree]
    lst = [tree]
    while queue:
        node = queue.pop(0)
        lst.extend(node.children)
        queue.extend([n for n in node.children if n.children])
    return lst
