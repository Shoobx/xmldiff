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
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""
provides constantes for using node and action (list) and some functions
for these objects use

    /!\  /!\ do not call index, remove or compare two node with == since a
             node is a recursive list
"""

from xmldiff.misc import TRUE, FALSE
from sys import stdout, stderr

################ ACTIONS #######################################################

A_DESC = 0  # string describes the action
A_N1 = 1  # node on which the action applies
A_N2 = 2  # optionnal second action argument, maybe node or value


def actp(act):
    """ print an internal action (debugging purpose) """
    if len(act) > 2:
        if act[A_DESC][0] == 'm':
            print >> stderr,  act[A_DESC], caract(act[A_N1])
            print >> stderr, '    ', caract(act[A_N2])
            print >> stderr, '    ', caract(act[-2]), act[-3], get_pos(act[-1])
        else:
            print >> stderr, act[A_DESC], caract(act[A_N1]),\
                caract(act[A_N2]),\
                act[A_N2][N_VALUE]
    else:
        print >> stderr, act[A_DESC], caract(act[A_N1])


################## NODES CONSTANTES ############################################

N_TYPE = 0  # node's type
N_NAME = 1  # node's label (to process xpath)
N_VALUE = 2  # node's value
N_CHILDS = 3  # nodes's childs list
N_PARENT = 4  # node's parent
N_ISSUE = 5  # node's total issue number
N_XNUM = 6  # to compute node's xpath
NSIZE = 7  # number of items in a list which represent a node

# NODE TYPES
# NT_SYST = 0 # SYSTEM node (added by parser) /!\ deprecated
NT_NODE = 1  # ELEMENT node
NT_ATTN = 2  # ATTRIBUTE NAME node
NT_ATTV = 3  # ATTRIBUTE VALUE node
NT_TEXT = 4  # TEXT node
NT_COMM = 5  # COMMENT node
NT_ROOT = 6  # root node
NODES_TYPES = ('NT', 'NN', 'AN', 'AV', 'T', 'C', 'R')  # for printing


################## OPERATIONS EDITING NODES ####################################

def link_node(parent, child):
    """ link child to his parent """
    if child:
        parent[N_CHILDS].append(child)
        child[N_PARENT] = parent


def insert_node(node, new, pos):
    """ insert child new on node at position pos (integer) """
    node[N_CHILDS].insert(pos, new)
    new[N_PARENT] = node
    i, j = 0, 1
    while i < len(node[N_CHILDS]):
        n = node[N_CHILDS][i]
        if n[N_NAME] == new[N_NAME] and n[N_TYPE] == new[N_TYPE]:
            n[N_XNUM] = j
            j += 1
        i += 1


def delete_node(node):
    """ delete a node from its tree """
    siblings = node[N_PARENT][N_CHILDS]
    i = get_pos(node)
    siblings.pop(i)
    node[N_PARENT] = None
    while i < len(siblings):
        n = siblings[i]
        if n[N_NAME] == node[N_NAME] and n[N_TYPE] == node[N_TYPE]:
            n[N_XNUM] -= 1
        i += 1


def rename_node(node, new_name):
    """ rename a node
    this is necessary for xpath
    """
    siblings = node[N_PARENT][N_CHILDS]
    pos = get_pos(node)
    xnum = 1
    for i in range(len(siblings)):
        n = siblings[i]
        if i < pos:
            if n[N_NAME] == new_name and n[N_TYPE] == node[N_TYPE]:
                xnum += 1
        elif i != pos:
            if n[N_NAME] == node[N_NAME] and n[N_TYPE] == node[N_TYPE]:
                n[N_XNUM] -= 1
            elif n[N_NAME] == new_name and n[N_TYPE] == node[N_TYPE]:
                n[N_XNUM] += 1
    node[N_NAME] = new_name
    node[N_XNUM] = xnum


################## OPERATIONS FORMATING NODES ##################################

def caract(node):
    """ return a string which represent the node """
    return '%s:%s (%s) %s %s' % (NODES_TYPES[node[N_TYPE]], node[N_VALUE],
                                 f_xpath(node), id(node), node[N_ISSUE])


def f_xpath(node, x=''):
    """ compute node's xpath """
    if node[N_NAME] != '/':
        if node[N_TYPE] == NT_ATTN:
            return f_xpath(node[N_PARENT],
                           '/%s' % node[N_NAME][:len(node[N_NAME])-4])
        if node[N_TYPE] == NT_ATTV:
            return f_xpath(node[N_PARENT])  # [N_PARENT], '/%s'%node[N_NAME])
        return f_xpath(node[N_PARENT], '/%s[%d]%s' % (
            node[N_NAME], node[N_XNUM], x))
    elif not x:
        return '/'
    return x


def node_repr(node):
    """ return a string which represents the given node """
    s = '%s\n' % caract(node)
    for child in node[N_CHILDS]:
        s = '%s%s' % (s, _indent(child, '  '))
    return s


def _indent(node, indent_str):
    s = '%s\-%s\n' % (indent_str, caract(node))
    if next_sibling(node) is not None:
        indent_str = '%s| ' % indent_str
    else:
        indent_str = '%s  ' % indent_str
    for child in node[N_CHILDS]:
        s = '%s%s' % (s, _indent(child, indent_str))
    return s


def xml_print(node, indent='', stream=stdout):
    """
    recursive function which write the node in an xml form without the added
    nodes
    """
    _xml_print_internal_format(node, indent, stream)


def _xml_print_internal_format(node, indent, stream):
    if node[N_TYPE] == NT_NODE:
        attrs_s = ''
        i = 0
        while i < len(node[N_CHILDS]):
            n = node[N_CHILDS][i]
            if n[N_TYPE] == NT_ATTN:
                i += 1
                attrs_s = '%s %s="%s"' % (attrs_s, n[N_VALUE],
                                          n[N_CHILDS][0][N_VALUE])
            else:
                break
        if len(node[N_CHILDS]) > i:
            stream.write('%s<%s%s>\n' % (indent, node[N_VALUE], attrs_s))
            for _curr_node in node[N_CHILDS][i:]:
                _xml_print_internal_format(
                    _curr_node, indent + '  ', stream=stream)
            stream.write('%s</%s>\n' % (indent, node[N_VALUE]))
        else:
            stream.write('%s<%s%s/>\n' % (indent, node[N_VALUE], attrs_s))
    elif node[N_TYPE] == NT_ATTN:
        stream.write('%s<@%s>\n' % (indent, node[N_VALUE]))
        stream.write(node[N_CHILDS][0][N_VALUE] + '\n')
        stream.write('%s</%s>\n' % (indent, node[N_VALUE]))
    elif node[N_TYPE] == NT_COMM:
        stream.write('%s<!-- %s -->\n' % (indent, node[N_VALUE]))
    elif node[N_TYPE] == NT_TEXT:
        stream.write(node[N_VALUE] + '\n')
    else:
        stream.write('unknown node type', str(node[N_TYPE]))


def to_dom(node, doc, uri=None, prefix=None):
    """
    recursive function to convert internal tree in an xml dom tree without
    the added nodes
    """
    if node[N_TYPE] == NT_NODE:
        dom_n = doc.createElementNS(uri, '%selement' % prefix)
        dom_n.setAttributeNS(None, 'name', node[N_VALUE])
        for n in node[N_CHILDS]:
            if n[N_TYPE] == NT_ATTN:
                dom_n = doc.createElementNS(uri, '%sattribute' % prefix)
                v = unicode(n[N_CHILDS][0][N_VALUE], 'UTF-8')
                dom_n.setAttributeNS(None, 'name', n[N_VALUE])
                dom_n.appendChild(doc.createTextNode(v))
            else:
                dom_n.appendChild(to_dom(n, doc, uri))
    elif node[N_TYPE] == NT_ATTN:
        dom_n = doc.createElementNS(uri, '%sattribute' % prefix)
        dom_n.setAttributeNS(None, 'name', node[N_VALUE])
        v = unicode(node[N_CHILDS][0][N_VALUE], 'UTF-8')
        dom_n.appendChild(doc.createTextNode(v))
    elif node[N_TYPE] == NT_COMM:
        dom_n = doc.createElementNS(uri, '%scomment' % prefix)
        v = unicode(node[N_VALUE], 'UTF-8')
        dom_n.appendChild(doc.createTextNode(v))
    elif node[N_TYPE] == NT_TEXT:
        dom_n = doc.createElementNS(uri, '%stext' % prefix)
        v = unicode(node[N_VALUE], 'UTF-8')
        dom_n.appendChild(doc.createTextNode(v))
    return dom_n


################## OPERATIONS GIVING INFOS ON NODES ############################

def get_pos(node):
    """ return the index of a node in its parent's children list

    /!\  /!\ do not call index, remove or compare two node with == since a
             node is a recursive list
    """
    try:
        childs = node[N_PARENT][N_CHILDS]
        for i, child in enumerate(childs):
            if child is node:
                return i
    except TypeError:
        return -1
    except ValueError:
        return -1


def nb_childs(node):
    """ return the number of childs (without attribute childs) of the given node
    """
    return len(filter(lambda n: n[N_CHILDS][0][N_TYPE] != NT_ATTN,
                      node[N_CHILDS]))


def nb_attrs(node):
    """ return the number of attributes of the given node """
    for i, child in enumerate(node[N_CHILDS]):
        if child[N_TYPE] != NT_ATTN:
            break
    else:
        try:
            i += 1
        except UnboundLocalError:
            i = 0
    return i


################## MISCELLANEOUS OPERATIONS ON NODES ###########################

def next_sibling(node):
    """ return the node's right sibling """
    if node[N_PARENT] is None:
        return None
    myindex = get_pos(node)
    if len(node[N_PARENT][N_CHILDS]) > myindex+1:
        return node[N_PARENT][N_CHILDS][myindex+1]
    return None


def previous_sibling(node):
    """ return the node's left sibling """
    myindex = get_pos(node)
    if node[N_PARENT] and myindex > 0:
        return node[N_PARENT][N_CHILDS][myindex-1]
    return None


def get_ancestors(node, l):
    """ append to l all the ancestors from node """
    while node[N_PARENT]:
        l.append(node)
        node = node[N_PARENT]
    return l


def get_labels(tree, labels, leaf_labels):
    """
    Chain all nodes with a given label l in tree T together, from left to right,
    by filling dictionnaries labels and leaf_labels (for leaf nodes).

    Label are keys pointing to a list of nodes with this type.
    Node x occurs after y in the list if x appears before y in the in-order
    traversal of T.
    /!\  /!\
    since this isn't binary tree, post order traversal (?)
    """
    if tree and tree[N_CHILDS]:
        for node in tree[N_CHILDS]:
            get_labels(node,  labels, leaf_labels)
        labels.setdefault(NODES_TYPES[tree[N_TYPE]], []).append(tree)
    elif tree:
        leaf_labels.setdefault(NODES_TYPES[tree[N_TYPE]], []).append(tree)


def make_bfo_list(tree):
    """ create a list with tree nodes in breadth first order """
    l, queue = [], []
    if tree:
        l.append(tree)
        if tree[N_CHILDS]:
            node = tree[N_CHILDS][0]
            while node:
                l.append(node)
                if node[N_CHILDS]:
                    queue.append(node)
                node = next_sibling(node)
                if not node and queue:
                    node = queue.pop(0)[N_CHILDS][0]
    return l


def make_bfo_list(tree):
    """ create a list with tree nodes in breadth first order """
    queue = [tree]
    lst = [tree]
    while queue:
        node = queue.pop(0)
        lst.extend(node[N_CHILDS])
        queue.extend([n for n in node[N_CHILDS] if n[N_CHILDS]])
    return lst

# no more used
# def make_po_list(tree):
##     """ create a list with tree nodes in post order """
##     l, stack, poped = [], [], 0
# if tree:
# if tree[N_CHILDS]:
##             node = tree[N_CHILDS][0]
# while node:
# if node[N_CHILDS] and not poped:
# stack.append(node)
##                     node = node[N_CHILDS][0]
# else:
# l.append(node)
##                     node = next_sibling(node)
##                 poped = 0
# if not node and stack:
##                     node = stack.pop()
##                     poped = 1
# l.append(tree)
# return l
# def make_preo_list(tree):
##     """ create a list with tree nodes in pre order """
##     l, stack, poped = [], [], 0
# if tree:
# l.append(tree)
# if tree[N_CHILDS]:
##             node = tree[N_CHILDS][0]
# xl.append(node)
# while node:
# if node[N_CHILDS] and not poped:
# stack.append(node)
##                     node = node[N_CHILDS][0]
# else:
##                     node = next_sibling(node)
# l.append(node)
##                 poped = 0
# if not node and stack:
##                     node = stack.pop()
##                     poped = 1
# return l
# def get_leafs(tree, l):
##     """ return a list with all leaf nodes from left to right """
# if tree and tree[N_CHILDS]:
##         node = tree[N_CHILDS][0]
# while node:
##             get_leafs(node, l)
##             node = next_sibling(node)
# elif tree:
# l.append(tree)
# def get_issue(node, l):
##     """ append to l all the descendants from node """
# for child in node[N_CHILDS]:
# l.append(child)
# if child[N_CHILDS]:
##             get_issue(child, l)
# def contains(ancestor, node):
##     """ return true if node is descendent of ancestor """
# if node is None:
# return FALSE
# if ancestor is node:
# return TRUE
# return contains(ancestor, node[N_PARENT])
