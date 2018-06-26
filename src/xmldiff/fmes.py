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
 this file provides the fast match / edit script (fmes) tree to tree correction
 algorithm as described in "Change detection in hierarchically structured
 information" by S. Chawathe, A. Rajaraman, H. Garcia-Molina and J. Widom
 ([CRGMW95])
"""

from copy import copy
from xmldiff.objects import (
    NT_ROOT, NT_NODE, NT_ATTN, NT_ATTV, NT_TEXT)
from xmldiff.objects import (
    get_labels, get_ancestors, make_bfo_list, insert_node, delete_node,
    rename_node, get_pos, f_xpath, nb_attrs)
from xmldiff.difflib import lcs2, quick_ratio
from xmldiff.misc import intersection, in_ref, index_ref
from xmldiff.parser import Node

# BBB imports:
from xmldiff.objects import NSIZE, N_INORDER, N_MAPPED  # noqa


## FMES TREE 2 TREE ALGORITHM #################################################
class FmesCorrector:
    """
    Fast Match / Edit Script implementation

    See [CRGMW95] for reference.
    """

    def __init__(self, formatter, f=0.6, t=0.5):  # f=0,59
        # algorithm parameters
        if f > 1 or f < 0 or t > 1 or t < 0.5:
            raise Exception('Invalid parameters:  1 > f > 0 and 1 > t > 0.5')
        self.F = f
        self.T = t
        self._formatter = formatter

    def process_trees(self, tree1, tree2):
        """
        Process the two trees
        """
        # print '**** TREE 2'
        # print node_repr(tree2)
        # print '**** TREE 1'
        # print node_repr(tree1)
        # attributes initialisation
        self._mapping = []  # empty mapping
        self.add_action = self._formatter.add_action
        self._d1, self._d2 = {}, {}
        self._dict = {}
        self._tmp_attrs_dict = {}
        self._pending = []
        # step 0: mapping
        self._fast_match(tree1, tree2)
        del self._d1
        del self._d2
        # step 1: breadth first search tree2
        self._fmes_step1(tree2, tree1)
        # step 2: post order traversal tree1
        self._fmes_step2(tree1, tree2)
        # step 3: rename tmp attributes
        for tmp_name, real_name in self._tmp_attrs_dict.items():
            self.add_action(['rename', '//@%s' % tmp_name, real_name])
        self._formatter.end()

    ## Private functions ######################################################
    def _fast_match(self, tree1, tree2):
        """ the fast match algorithm
        try to resolve the 'good matching problem' """
        labl1, labl2 = {}, {}
        leaf_labl1, leaf_labl2 = {}, {}
        # chain all nodes with a given label l in tree T together
        get_labels(tree1, labl1, leaf_labl1)
        get_labels(tree2, labl2, leaf_labl2)
        # do the matching job
        self._match(leaf_labl1, leaf_labl2, self._l_equal)
        # remove roots ('/') from labels
        del labl1['R']
        del labl2['R']
        # append roots to mapping
        self._mapping.append((tree1, tree2))
        # mark node as mapped
        tree1.mapped = True
        self._match(labl1, labl2, self._fmes_node_equal)  # self._n_equal

    def _match(self, lab_l1, lab_l2, equal):
        """do the actual matching"""
        d1, d2 = self._d1, self._d2
        # for each leaf label in both tree1 and tree2
        # sort list to avoid differences between python version
        labls = sorted(intersection(lab_l1.keys(), lab_l2.keys()))
        for label in labls:
            s1 = lab_l1[label]
            s2 = lab_l2[label]
            # compute the longest common subsequence
            common = lcs2(s1, s2, equal)
            # for each pair of nodes (x,y) in the lcs
            for x, y in common:
                # add (x,y) to the mapping
                self._mapping.append((x, y))
                # mark node from tree 1 as mapped
                x.mapped = True
                # fill the mapping cache
                for n in get_ancestors(x, []):
                    d1[(id(n), id(x))] = 1
                for n in get_ancestors(y, []):
                    d2[(id(n), id(y))] = 1

    def _fmes_step1(self, tree2, tree1):
        """ first step of the edit script algorithm
        combines the update, insert, align and move phases
        """
        # x the current node in the breadth-first order traversal
        for x in make_bfo_list(tree2):
            y = x.parent
            z = self._partner(1, y)
            w = self._partner(1, x)
            # insert
            if not w:
                todo = 1
                # avoid to add existing attribute node
                if x.type == NT_ATTN:
                    for w in z.children:
                        if w.type != NT_ATTN:
                            break
                        elif w.value == x.value:
                            if not w.mapped:
                                todo = None
                                w.mapped = True
                                self._mapping.append((w, x))
                                # print 'delete 1'
                                # if not w.children[0]:
                                delete_node(w.children[0])
                            break

                if todo is not None:
                    x.inorder = True
                    k = self._find_pos(x)
                    # We don't need a deepcopy, since we replace the .children
                    w = copy(x)
                    w.children = []
                    self._mapping.append((w, x))
                    w.mapped = True
                    # avoid coalescing two text nodes
                    if w.type == NT_TEXT:
                        k = self._before_insert_text(z, w, k)
                    # real insert on tree 1
                    insert_node(z, w, k)
                    # make actions on subtree
                    self._dict[id(w)] = ww = copy(w)
                    ww.children = []
                    # preformat action
                    if id(z) not in self._dict:
                        if w.type == NT_ATTV:
                            action = ['update', f_xpath(z), w.value]
                        elif w.type == NT_ATTN:
                            action = ['append', f_xpath(z), ww]
                        elif z.type == NT_ROOT:
                            action = ['append-first', '/', ww]
                        else:
                            k = get_pos(w)
                            if k <= nb_attrs(z):
                                action = ['append-first',
                                          f_xpath(z), ww]
                            else:
                                action = ['insert-after',
                                          f_xpath(z.children[k - 1]), ww]
                        self.add_action(action)
                    else:
                        insert_node(self._dict[id(z)], ww, k)
            elif x.name != '/':
                v = w.parent
                # update
                if w.value != x.value:
                    needs_rename = True
                    # format action
                    if w.type == NT_NODE:
                        self.add_action(['rename', f_xpath(w), x.value])
                    elif w.type == NT_ATTN:
                        attr_name = self._before_attribute(w.parent, w,
                                                           x.value)
                        self.add_action(['rename', f_xpath(w), attr_name])
                        x.name = '@%sName' % attr_name
                        x.value = attr_name
                    else:
                        self.add_action(['update', f_xpath(w), x.value])
                        # We are simply replacing the main text node, so no
                        # need to rename.
                        needs_rename = False
                    # real update on t1
                    w.value = x.value
                    # this is necessary for xpath, but do not rename on simple
                    # text update.
                    if needs_rename:
                        rename_node(w, x.name)
                # move x if parents not mapped together
                if not self._has_couple(v, y):
                    x.inorder = True
                    k = self._find_pos(x)
                    self._make_move(w, z, k)
            # align children
            self._align_children(w, x)
            # print 'after', node_repr(tree1)

    def _fmes_step2(self, tree1, tree2):
        """ the delete_node phase of the edit script algorithm

        instead of the standard algorithm, walk on tree1 in pre order and
        add a remove action on node not marked as mapped.
        Avoiding recursion on these node allow to extract remove on subtree
        instead of leaf

        do not use next_sibling for performance issue
        """
        stack = []
        i = 0
        node = tree1
        while node is not None:
            if not node.mapped:
                if node.parent and len(node.parent.children) > i + 1:
                    next_node = node.parent.children[i + 1]

                    # if next node is a text node to remove, switch actions
                    if next_node.type == NT_TEXT and \
                       not next_node.mapped:
                        self.add_action(['remove', f_xpath(next_node)])
                        delete_node(next_node)
                        try:
                            next_node = node.parent.children[i + 1]
                        except IndexError:
                            next_node = None
                else:
                    next_node = None
                self.add_action(['remove', f_xpath(node)])
                delete_node(node)
                node = next_node
            elif node.children:
                # push next sibbling on the stack
                if node.parent and len(node.parent.children) > i + 1:
                    stack.append((node.parent.children[i + 1], i + 1))
                node = node.children[0]
                i = 0
            elif node.parent and len(node.parent.children) > i + 1:
                i += 1
                node = node.parent.children[i]  # next_sibling(node)
            else:
                node = None
            if node is None and stack:
                node, i = stack.pop()

    def _align_children(self, w, x):
        """ align children to correct misaligned nodes
        """
        # mark all children of w an d as "out of order"
        self._childs_out_of_order(w)
        self._childs_out_of_order(x)
        s1 = [n for n in w.children if in_ref(x.children, self._partner(0, n))]
        # s2: children of x whose partners are children of w
        s2 = [n for n in x.children if in_ref(w.children, self._partner(1, n))]
        # compute the longest common subsequence
        s = lcs2(s1, s2, self._has_couple)
        # mark each (a,b) from lcs in order
        for a, b in s:
            a.inorder = b.inorder = True
            s1.pop(index_ref(s1, a))
        # s: a E T1, b E T2, (a,b) E M, (a;b) not E s
        for a in s1:
            b = self._partner(0, a)
            # mark a and b in order
            a.inorder = b.inorder = True
            k = self._find_pos(b)
            self._make_move(a, w, k)

    def _find_pos(self, x):
        """ find the position of a node in the destination tree (tree2)

        do not use previous_sibling for performance issue
        """
        y = x.parent
        # if x is the leftmost child of y in order, return 1
        for v in y.children:
            if v.inorder:
                if v is x:
                    # return 0 instead of 1 here since the first element of a
                    # list have index 0
                    return 0
                break
        # looking for rightmost left sibling of y INORDER
        i = get_pos(x) - 1
        while i >= 0:
            v = y.children[i]
            if v.inorder:
                break
            i -= 1
        u = self._partner(1, v)
        if u is not None:
            return get_pos(u) + 1

    def _make_move(self, n1, n2, k):
        # avoid coalescing two text nodes
        act_node = self._before_delete_node(n1)
        if act_node is not None and act_node[0] is n2 and act_node[1] < k:
            k += 1
        if n1.type == NT_TEXT:
            k = self._before_insert_text(n2, n1, k)
            if k <= nb_attrs(n2):
                self.add_action(['move-first', n1, n2])
            else:
                self.add_action(['move-after', n1, n2.children[k - 1]])
        elif n1.type == NT_ATTN:
            # avoid to move an attribute node from a place to another on
            # the same node
            if n1.parent is not n2:
                old_name = n1.value
                new_name = self._before_attribute(n2, n1)
                if new_name != old_name:
                    self.add_action(['remove', f_xpath(n1)])
                    n1.name = '@%sName' % new_name
                    n1.value = new_name
                    self.add_action(['append', f_xpath(n2), n1])
                else:
                    self.add_action(['move-first', n1, n2])
        elif k <= nb_attrs(n2):
            self.add_action(['move-first', n1, n2])
        else:
            self.add_action(['move-after', n1, n2.children[k - 1]])
        # real move
        delete_node(n1)
        insert_node(n2, n1, k)

    def _before_attribute(self, parent_node, attr_node, new_name=None):
        attr_name = new_name or attr_node.value
        for w in parent_node.children:
            if w.type != NT_ATTN:
                break
            if w.value == attr_name:
                new_name = 'LogilabXmldiffTmpAttr%s' % attr_name.replace(':',
                                                                         '_')
                self._tmp_attrs_dict[new_name] = attr_name
                return new_name
        return attr_name

    FAKE_TAG = Node(NT_NODE, 'LogilabXMLDIFFFAKETag', 'LogilabXMLDIFFFAKETag',
                    [], None, 0, 0, True, False)

    def _before_insert_text(self, parent, new_text, k):
        """ check if a text node that will be remove has two sibbling text
        nodes to avoid coalescing two text nodes
        """
        if k > 1:
            if parent.children[k - 1].type == NT_TEXT:
                tag = copy(self.FAKE_TAG)
                self.add_action(['insert-after',
                                 f_xpath(parent.children[k - 1]), tag])
                insert_node(parent, tag, k)
                return k + 1
        if k < len(parent.children):
            if parent.children[k].type == NT_TEXT:
                tag = copy(self.FAKE_TAG)
                if k <= nb_attrs(parent):
                    self.add_action(['append-first', f_xpath(parent), tag])
                else:
                    self.add_action(['insert-after',
                                     f_xpath(parent.children[k - 1]), tag])
                insert_node(parent, tag, k)
        return k

    def _before_delete_node(self, node):
        """ check if a text node will be inserted with a sibbling text node to
        avoid coalescing two text nodes
        """
        k = get_pos(node)
        parent = node.parent
        if k >= 1 and k + 1 < len(parent.children):
            if parent.children[k - 1].type == NT_TEXT and \
               parent.children[k + 1].type == NT_TEXT:
                tag = copy(self.FAKE_TAG)
                self.add_action(['insert-after',
                                 f_xpath(parent.children[k - 1]), tag])
                insert_node(parent, tag, k)
                return parent, k
        return None

    def _childs_out_of_order(self, subtree):
        """ initialisation function : tag all the subtree as unordered """
        for child in subtree.children:
            child.inorder = False
            self._childs_out_of_order(child)

    def _l_equal(self, n1, n2):
        """ function to compare leafs during mapping """
        ratio = quick_ratio(n1.value, n2.value)
        if ratio > self.F:
            # print 'MATCH (%s): %s / %s' %(ratio, n1.value,n2.value)
            return True
        # print 'UNMATCH (%s): %s / %s' %(ratio, n1.value,n2.value)
        return False

    def _fmes_node_equal(self, n1, n2):
        """ function to compare subtree during mapping """
        mapping = self._mapping

        length = 0
        i = 0
        for a, b in mapping:
            i += 1
            if (id(n1), id(a)) in self._d1:
                if (id(n2), id(b)) in self._d2:
                    length += 1

        # factor 2.5 for tree expansion compensation
        fact = 2.5 * length / float(max(n1.issue, n2.issue))
        if fact >= self.T:
            return True
        return False

    def _partner(self, index, node):
        if node is None:
            return None
        partners = [e for e in self._mapping if e[index] is node]
        if not partners:
            return None

        return partners[0][1 - index]

    def _has_couple(self, a, b):
        for couple in self._mapping:
            if a is couple[0] and b is couple[1]:
                return True
        return False
