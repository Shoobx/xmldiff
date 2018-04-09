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
#
"""
 this file provides the fast match / edit script (fmes) tree to tree correction
 algorithm as described in "Change detection in hierarchically structured
 information" by S. Chawathe, A. Rajaraman, H. Garcia-Molina and J. Widom
 ([CRGMW95])
"""

from xmldiff.objects import NT_ROOT, NT_NODE, NT_ATTN, NT_ATTV, \
    NT_TEXT, NT_COMM, N_TYPE, N_NAME, N_VALUE, N_CHILDS, N_PARENT, N_ISSUE, \
    N_XNUM, NSIZE, A_DESC, A_N1, A_N2, FALSE, TRUE, \
    node_repr, get_labels, get_ancestors, caract, make_bfo_list, \
    insert_node, delete_node, rename_node, get_pos, \
    f_xpath, nb_attrs, xml_print
from xmldiff.difflib import lcs2, quick_ratio
from xmldiff.misc import intersection, in_ref, index_ref
# c extensions
from xmldiff.maplookup import has_couple, partner, fmes_init, \
    fmes_node_equal, match_end, fmes_end

# node's attributes for fmes algorithm
N_INORDER = NSIZE
N_MAPPED = N_INORDER + 1


def _init_tree(tree, map_attr=None):
    """ recursively append N_INORDER attribute to tree
    optionnaly add the N_MAPPED attribute (for node from tree 1)
    """
    tree.append(FALSE)
    if not map_attr is None:
        tree.append(FALSE)
    for child in tree[N_CHILDS]:
        _init_tree(child, map_attr)

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
        # add needed attribute (INORDER)
        _init_tree(tree1, map_attr=1)
        _init_tree(tree2)
# print '**** TREE 2'
# print node_repr(tree2)
# print '**** TREE 1'
# print node_repr(tree1)
        # attributes initialisation
        self._mapping = []  # empty mapping
        self.add_action = self._formatter.add_action
        self._d1, self._d2 = {}, {}
        # give references to the C extensions specific to fmes
        fmes_init(self._mapping, self._d1, self._d2, self.T)
        self._dict = {}
        self._tmp_attrs_dict = {}
        self._pending = []
        self._formatter.init()
        # step 0: mapping
        self._fast_match(tree1, tree2)
        # free matching variables
        match_end()
        del self._d1
        del self._d2
        # step 1: breadth first search tree2
        self._fmes_step1(tree2, tree1)
        # step 2: post order traversal tree1
        self._fmes_step2(tree1, tree2)
        # step 3: rename tmp attributes
        for tmp_name, real_name in self._tmp_attrs_dict.items():
            self.add_action(['rename', '//%s' % tmp_name, real_name])
        # free mapping ref in C extensions
        fmes_end()
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
        tree1[N_MAPPED] = TRUE
        self._match(labl1, labl2, fmes_node_equal)  # self._n_equal

    def _match(self, lab_l1, lab_l2, equal):
        """do the actual matching"""
        d1, d2 = self._d1, self._d2
        mapping = self._mapping
        # for each leaf label in both tree1 and tree2
        l = intersection(lab_l1.keys(), lab_l2.keys())
        # sort list to avoid differences between python version
        l.sort()
        for label in l:
            s1 = lab_l1[label]
            s2 = lab_l2[label]
            # compute the longest common subsequence
            common = lcs2(s1, s2, equal)
            # for each pair of nodes (x,y) in the lcs
            for x, y in common:
                # add (x,y) to the mapping
                mapping.append((x, y))
                # mark node from tree 1 as mapped
                x[N_MAPPED] = TRUE
                # fill the mapping cache
                for n in get_ancestors(x, []):
                    d1[(id(n), id(x))] = 1
                for n in get_ancestors(y, []):
                    d2[(id(n), id(y))] = 1

    def _fmes_step1(self, tree2, tree1):
        """ first step of the edit script algorithm
        combines the update, insert, align and move phases
        """
        mapping = self._mapping
        fp = self._find_pos
        al = self._align_children
        _partner = partner
        # x the current node in the breadth-first order traversal
        for x in make_bfo_list(tree2):
            y = x[N_PARENT]
            z = _partner(1, y)
            w = _partner(1, x)
            # insert
            if not w:
                todo = 1
                # avoid to add existing attribute node
                if x[N_TYPE] == NT_ATTN:
                    for w in z[N_CHILDS]:
                        if w[N_TYPE] != NT_ATTN:
                            break
                        elif w[N_VALUE] == x[N_VALUE]:
                            # FIXME: what if w or w[N_CHILDS][0] yet mapped ??
                            if not w[N_MAPPED]:
                                ##                                 old_value = x[N_VALUE]
                                ##                                 x[N_VALUE] = 'xmldiff-%s'%old_value
                                ##                                 self._tmp_attrs_dict[x[N_VALUE]] = old_value
                                ##                                 old_x = _partner(0, w)
                                ##                                 i = 0
                                # for i in range(len(mapping)):
                                # if mapping[i][0] is w:
                                # print mapping[i][1]
                                ##                                         mapping[i][1][N_MAPPED] = FALSE
                                # mapping.pop(i)
                                # break
                                # else:
                                todo = None
                                w[N_MAPPED] = TRUE
                                mapping.append((w, x))
                                # print 'delete 1'
                                # if not w[N_CHILDS][0]:
                                delete_node(w[N_CHILDS][0])
                            break

                if todo is not None:
                    x[N_INORDER] = TRUE
                    k = fp(x)
                    # w = copy(x)
                    w = x[:]
                    w[N_CHILDS] = []
                    w.append(TRUE)  # <-> w[N_MAPPED] = TRUE
                    mapping.append((w, x))
                    # avoid coalescing two text nodes
                    if w[N_TYPE] == NT_TEXT:
                        k = self._before_insert_text(z, w, k)
                    # real insert on tree 1
                    insert_node(z, w, k)
                    # make actions on subtree
                    self._dict[id(w)] = ww = w[:]
                    ww[N_CHILDS] = []
                    # preformat action
                    if not self._dict.has_key(id(z)):
                        if w[N_TYPE] == NT_ATTV:
                            action = ['update', f_xpath(z), w[N_VALUE]]
                        elif w[N_TYPE] == NT_ATTN:
                            action = ['append', f_xpath(z), ww]
                        elif z[N_TYPE] == NT_ROOT:
                            action = ['append-first', '/', ww]
                        else:
                            k = get_pos(w)
                            if k <= nb_attrs(z):
                                action = ['append-first',
                                          f_xpath(z), ww]
                            else:
                                action = ['insert-after',
                                          f_xpath(z[N_CHILDS][k-1]), ww]
                        self.add_action(action)
                    else:
                        insert_node(self._dict[id(z)], ww, k)
            elif x[N_NAME] != '/':
                v = w[N_PARENT]
                # update
                if w[N_VALUE] != x[N_VALUE]:
                    needs_rename = True
                    # format action
                    if w[N_TYPE] == NT_NODE:
                        self.add_action(['rename', f_xpath(w), x[N_VALUE]])
                    elif w[N_TYPE] == NT_ATTN:
                        attr_name = self._before_attribute(w[N_PARENT], w,
                                                           x[N_VALUE])
                        self.add_action(['rename', f_xpath(w), attr_name])
                        x[N_NAME] = '@%sName' % attr_name
                        x[N_VALUE] = attr_name
                    else:
                        self.add_action(['update', f_xpath(w), x[N_VALUE]])
                        # We are simply replacing the main text node, so no
                        # need to rename.
                        needs_rename = False
                    # real update on t1
                    w[N_VALUE] = x[N_VALUE]
                    # this is necessary for xpath, but do not rename on simple
                    # text update.
                    if needs_rename:
                        rename_node(w, x[N_NAME])
                # move x if parents not mapped together
                if not has_couple(v, y):
                    x[N_INORDER] = TRUE
                    k = fp(x)
                    self._make_move(w, z, k)
            # align children
            al(w, x)
#            print 'after', node_repr(tree1)

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
            if node[N_MAPPED] != TRUE:
                if node[N_PARENT] and len(node[N_PARENT][N_CHILDS]) > i+1:
                    next_node = node[N_PARENT][N_CHILDS][i+1]
                    # if next node is a text node to remove, switch actions
                    if next_node[N_TYPE] == NT_TEXT and \
                       next_node[N_MAPPED] != TRUE:
                        self.add_action(['remove', f_xpath(next_node)])
                        delete_node(next_node)
                        try:
                            next_node = node[N_PARENT][N_CHILDS][i+1]
                        except:
                            next_node = None
                else:
                    next_node = None
                self.add_action(['remove', f_xpath(node)])
                delete_node(node)
                node = next_node
            elif node[N_CHILDS]:
                # push next sibbling on the stack
                if node[N_PARENT] and len(node[N_PARENT][N_CHILDS]) > i+1:
                    stack.append((node[N_PARENT][N_CHILDS][i+1], i+1))
                node = node[N_CHILDS][0]
                i = 0
            elif node[N_PARENT] and len(node[N_PARENT][N_CHILDS]) > i+1:
                i += 1
                node = node[N_PARENT][N_CHILDS][i]  # next_sibling(node)
            else:
                node = None
            if node is None and stack:
                node, i = stack.pop()

    def _align_children(self, w, x):
        """ align children to correct misaligned nodes
        """
        _partner = partner
        # mark all children of w an d as "out of order"
        self._childs_out_of_order(w)
        self._childs_out_of_order(x)
        # s1: children of w whose partner is children of x
        s1 = [n for n in w[N_CHILDS] if in_ref(x[N_CHILDS], _partner(0, n))]
        # s2: children of x whose partners are children of w
        s2 = [n for n in x[N_CHILDS] if in_ref(w[N_CHILDS], _partner(1, n))]
        # compute the longest common subsequence
        s = lcs2(s1, s2, has_couple)
        # mark each (a,b) from lcs in order
        for a, b in s:
            a[N_INORDER] = b[N_INORDER] = TRUE
            s1.pop(index_ref(s1, a))
        # s: a E T1, b E T2, (a,b) E M, (a;b) not E s
        for a in s1:
            b = _partner(0, a)
            # mark a and b in order
            a[N_INORDER] = b[N_INORDER] = TRUE
            k = self._find_pos(b)
            self._make_move(a, w, k)

    def _find_pos(self, x):
        """ find the position of a node in the destination tree (tree2)

        do not use previous_sibling for performance issue
        """
        y = x[N_PARENT]
        # if x is the leftmost child of y in order, return 1
        for v in y[N_CHILDS]:
            if v[N_INORDER]:
                if v is x:
                    # return 0 instead of 1 here since the first element of a
                    # list have index 0
                    return 0
                break
        # looking for rightmost left sibling of y INORDER
        i = get_pos(x) - 1
        while i >= 0:
            v = y[N_CHILDS][i]
            if v[N_INORDER]:
                break
            i -= 1
        u = partner(1, v)
        if u is not None:
            return get_pos(u)+1

    def _make_move(self, n1, n2, k):
        # avoid coalescing two text nodes
        act_node = self._before_delete_node(n1)
        if act_node is not None and act_node[0] is n2 and act_node[1] < k:
            k += 1
        if n1[N_TYPE] == NT_TEXT:
            k = self._before_insert_text(n2, n1, k)
            if k <= nb_attrs(n2):
                self.add_action(['move-first', n1, n2])
            else:
                self.add_action(['move-after', n1, n2[N_CHILDS][k-1]])
        elif n1[N_TYPE] == NT_ATTN:
            # avoid to move an attribute node from a place to another on
            # the same node
            if not n1[N_PARENT] is n2:
                n1_xpath = f_xpath(n1)
                old_name = n1[N_VALUE]
                new_name = self._before_attribute(n2, n1)
                if new_name != old_name:
                    self.add_action(['remove', f_xpath(n1)])
                    n1[N_NAME] = '@%sName' % new_name
                    n1[N_VALUE] = new_name
                    self.add_action(['append', f_xpath(n2), n1])
                else:
                    self.add_action(['move-first', n1, n2])
        elif k <= nb_attrs(n2):
            self.add_action(['move-first', n1, n2])
        else:
            self.add_action(['move-after', n1, n2[N_CHILDS][k-1]])
        # real move
        delete_node(n1)
        insert_node(n2, n1, k)

    def _before_attribute(self, parent_node, attr_node, new_name=None):
        attr_name = new_name or attr_node[N_VALUE]
        for w in parent_node[N_CHILDS]:
            if w[N_TYPE] != NT_ATTN:
                break
            if w[N_VALUE] == attr_name:
                new_name = 'LogilabXmldiffTmpAttr%s' % attr_name.replace(':',
                                                                         '_')
                self._tmp_attrs_dict[new_name] = attr_name
                return new_name
        return attr_name

    FAKE_TAG = [NT_NODE, 'LogilabXMLDIFFFAKETag', 'LogilabXMLDIFFFAKETag',
                [], None, 0, 0, TRUE, FALSE]

    def _before_insert_text(self, parent, new_text, k):
        """ check if a text node that will be remove has two sibbling text
        nodes to avoid coalescing two text nodes
        """
        if k > 1:
            if parent[N_CHILDS][k-1][N_TYPE] == NT_TEXT:
                tag = self.FAKE_TAG[:]
                self.add_action(['insert-after',
                                 f_xpath(parent[N_CHILDS][k-1]), tag])
                insert_node(parent, tag, k)
                return k+1
        if k < len(parent[N_CHILDS]):
            if parent[N_CHILDS][k][N_TYPE] == NT_TEXT:
                tag = self.FAKE_TAG[:]
                if k <= nb_attrs(parent):
                    self.add_action(['append-first', f_xpath(parent), tag])
                else:
                    self.add_action(['insert-after',
                                     f_xpath(parent[N_CHILDS][k-1]), tag])
                insert_node(parent, tag, k)
        return k

    def _before_delete_node(self, node):
        """ check if a text node will be inserted with a sibbling text node to
        avoid coalescing two text nodes
        """
        k = get_pos(node)
        parent = node[N_PARENT]
        if k >= 1 and k+1 < len(parent[N_CHILDS]):
            if parent[N_CHILDS][k-1][N_TYPE] == NT_TEXT and \
               parent[N_CHILDS][k+1][N_TYPE] == NT_TEXT:
                tag = self.FAKE_TAG[:]
                self.add_action(['insert-after',
                                 f_xpath(parent[N_CHILDS][k-1]), tag])
                insert_node(parent, tag, k)
                return parent, k
        return None

    def _childs_out_of_order(self, subtree):
        """ initialisation function : tag all the subtree as unordered """
        for child in subtree[N_CHILDS]:
            child[N_INORDER] = FALSE
            self._childs_out_of_order(child)

    def _l_equal(self, n1, n2):
        """ function to compare leafs during mapping """
        ratio = quick_ratio(n1[N_VALUE], n2[N_VALUE])
        if ratio > self.F:
            #            print 'MATCH (%s): %s / %s' %(ratio, n1[N_VALUE],n2[N_VALUE])
            return TRUE
#        print 'UNMATCH (%s): %s / %s' %(ratio, n1[N_VALUE],n2[N_VALUE])
        return FALSE


try:
    import os
    if os.environ.get('PYLINT_IMPORT') != '1':  # avoid erros with pylint
        import psyco
        psyco.bind(FmesCorrector._fmes_step1)
        psyco.bind(FmesCorrector._align_children)
# psyco.bind(FmesCorrector._fmes_step2)
        psyco.bind(FmesCorrector._match)
        psyco.bind(FmesCorrector._find_pos)
except Exception, e:
    pass
