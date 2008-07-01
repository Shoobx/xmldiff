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
 this file provides the Zhang and Shasha tree to tree correction algorithm
 extended by Barnard, Clark and Duncan  
"""

from xmldiff.objects import *
from xmldiff.misc import init_matrix

####### Actions used by ezs algorithm #######
EZS_A_TYPE  = 0
EZS_A_COST  = 1
EZS_A_FCOST = 2
EZS_A_N1    = 3
EZS_A_N2    = 4
EZS_A_DEL   = 5
# node's attributes for ezs algorithm
N_KEYROOT  = NSIZE # 1 if node is a keyroot, either 0 
N_LEFTMOST = N_KEYROOT+1 # index of leftmost child (see tree2tree)

def _nodes_equal(n1, n2):
    """ compare name and value of 2 xml nodes n1 and n2 """
    if n1 is None:
        return n2 is None
    elif n2 is None:
        return FALSE    
    return n1[N_VALUE] == n2[N_VALUE] 

def trees_equal(n1, n2):
    """ return true if the node n1 and n2 are equivalent subtrees """
    if not _nodes_equal(n1, n2):
        return FALSE
    elif n1 is not None:
        # recursion on each n1 and n2's child
        if n1[N_ISSUE] != n2[N_ISSUE]:
            return FALSE
        else:
            for child1, child2 in zip(n1[N_CHILDS], n2[N_CHILDS]):
                if not trees_equal(child1, child2):
                    return FALSE
    return TRUE

def choose(f_actions, desc_list):
    """
    return the best action (min forest distance) in the description list
    desc_list : [index1, index2, Action]
    """
    best_action = [C_INFINI]
    for i, j, action in desc_list:
        fcost = f_actions[i][j][-1][EZS_A_FCOST] + action[EZS_A_COST]
        if fcost < best_action[0]:
            best_action = [fcost, i, j, action]
    actions_stack = f_actions[best_action[1]][best_action[2]][:]
    best_action[3][EZS_A_FCOST]  = best_action[0]
    add_action(actions_stack, best_action[3])
    return actions_stack

def add_action(actions_list, action):
    """ Test action and add it to the list if it's a real action """
    if action[EZS_A_COST] > 0:
        actions_list.append(action)

######## COST CALCUL ########
C_INFINI = 9999999
C_SWAP   = 1
C_APPEND = 1
C_REMOVE = 1

def gamma(ni, nj):
    """
    return a cost which represents the differents betwen ni and nj
    today, return 0 if ni.nodeName equal nj.nodeName, 1 else
    """
    if ni == nj :
        return 0
    elif ni is not None and nj is not None and ni[N_VALUE] == nj[N_VALUE]:
        return 0
    else:
        return C_INFINI

def swap_trees(ni, sib_o_fi, nj, sib_o_fj):
    """
    return the cost to swap subtree ni et nj
    (sib_o_fi and sib_o_fi are the next sibbling node
     respectively for n1 and nj)
    """
    if trees_equal(ni, sib_o_fj) and trees_equal(sib_o_fi, nj) \
       and ni[N_NAME] != '/' and nj[N_NAME] != '/':
        return C_SWAP
    else:
        return C_INFINI    

def remove_tree(ni):
    """ return the cost to remove subtree ni """
    return (ni[N_ISSUE] + 1) * C_REMOVE

def append_tree(ni):
    """ return the cost to append subtree ni """
    return (ni[N_ISSUE] + 1) * C_APPEND

##### TREE 2 TREE ALGORITHMs ###
class EzsCorrector:
    """
    this class uses the Zhang and Shasha algorithm extended by Barnard, Clark 
    and Duncan 
    """
## * x, y                        -> postordered number of nodes being processed
## * nl1, nl2: node[MAXNODES]    -> nodes list ordered in the post-ordered 
##    number extracted respectively from tree1 and tree2 (size1 and size2 elmts)
## * actions[MAXNODES][MAXNODES] -> actions table working as tree distances
##     table (consideres only descendants). actions[i][j] finally contain a
##     list of actions which represents the best way to transform node
##     post-numbered i (from source tree) into node post-numbered j (from
##     destination tree)
## * f_actions[FDSIZE][FDSIZE]   -> actions table working as forest distances
##     table (forest distance is the distance between 2 nodes in their left
##     siblings context)
## since nodes are post numbered, nl[nl[i]->leftmost]-1] = root of the previous
## subtree for nl[i]
    
    def __init__(self, formatter):
        self._formatter = formatter

    def process_trees(self, tree1, tree2):
        """
        the Extended Zhang and Shasha tree 2 tree correction algorithm
        (Barnard, Clarke, Duncan)
        """
        ### initialisations ###
        nl1, nl2 = [], []
        self._formatter.init()
        # add attributes to trees
        self._post_order(tree1, nl1, TRUE)
        self._post_order(tree2, nl2, TRUE)
        # numbered tree with required attributes
        size1, size2 = len(nl1), len(nl2)
        # actions tables init
        f_actions = init_matrix(size1+1, size2+1, [[0, 0, C_INFINI, None]])
        actions = init_matrix(size1+1, size2+1, None)
        # insert None elmt to have index from 1 to size instead of 0,size-1
        nl1.insert(0, None)
        nl2.insert(0, None)
        
        ## after that, let's go !! ###
        for x in range(1, size1+1):
            if nl1[x][N_KEYROOT]:
                for y in range(1, size2+1):
                    if nl2[y][N_KEYROOT]:
                        # all the job is in function below
                        self._process_nodes(x, y, nl1, nl2, f_actions, actions) 
                    
        self._mainformat(actions[size1][size2])
        self._formatter.end()

    #### private functions ####
    def _process_nodes(self, x, y, nl1, nl2, f_actions, actions):
        """
        job for each keyroot nodes
        after round for nodes (nl1[x], nl2[y]), actions[x][y] will contain 
        the best list of actions to transform nl1[x] into nl2[y]
        (f_actions[x][y] too but it may be override in the next round)
        """
        lx = nl1[x][N_LEFTMOST]
        ly = nl2[y][N_LEFTMOST]
        f_actions[lx - 1][ly - 1] = [[0, 0, 0, None]]
        
        # init forrest distance array by the cost of removing and appending
        # each subtree on a cumulative basis
        for i in range(lx, x+1):
            f_actions[i][ly - 1] = f_actions[nl1[i][N_LEFTMOST] - 1][ly - 1][:]
            cost = remove_tree(nl1[i])
            add_action(f_actions[i][ly - 1],
                       [AT_REMOVE, cost,
                        f_actions[i][ly - 1][-1][EZS_A_FCOST]+cost,
                        nl1[i]
                        ])

        for j in range(ly, y+1):
            f_actions[lx - 1][j] = f_actions[lx - 1][nl2[j][N_LEFTMOST] - 1][:]
            cost = append_tree(nl2[j])
            add_action(f_actions[lx - 1][j],
                       [AT_APPEND, cost,
                        f_actions[lx - 1][j][-1][EZS_A_FCOST]+cost,
                        nl2[j], nl1[x]
                        ])
    
        # look for the shortest way
        for i in range(lx, x+1):
            for j in range(ly, y+1):
                li = nl1[i][N_LEFTMOST]
                lj = nl2[j][N_LEFTMOST]

                # min cost between gamma, remove(nl1[i]), append(nl2[j], nl1[i])
                f_actions[i][j] = choose(f_actions,
                 [
                 [i-1, j, [AT_REMOVE, gamma(nl1[i], None), 0, nl1[i]]],
                 [i, j-1, [AT_APPEND, gamma(None, nl2[j]), 0, nl2[j], nl1[x]]],
                 [li-1, j, [AT_REMOVE, remove_tree(nl1[i]), 0, nl1[i]]],
                 [i, lj-1, [AT_APPEND, append_tree(nl2[j]), 0, nl2[j], nl1[x]]]
                 ])

                if li == lx and lj == ly:
                    # min between just calculed and last loop + change
                    f_actions[i][j] = choose(f_actions,
                     [
                      [i, j, [0, 0, 0]],
                      [i-1, j-1, [0, gamma(nl1[i], nl2[j]), 0, nl1[i], nl2[j]]]
                     ])
                    # now we got the best way from nl1[i] to nl2[j, save it
                    actions[i][j] = f_actions[i][j][:]
                
                else:
                    if nl1[i][N_KEYROOT] and nl2[j][N_KEYROOT] \
                       and nl1[i][N_NAME] != '/' and nl2[j][N_NAME] != '/':
                        # min between just calculed and swap
                        f_actions[i][j] = choose(f_actions, [
                            [i, j, [0, 0, 0]],
                            [nl1[li-1][N_LEFTMOST] - 1,
                             nl2[lj-1][N_LEFTMOST] - 1,
                             [AT_SWAP, swap_trees(nl1[i], nl1[li-1],
                                                  nl2[j], nl2[lj-1]),
                              0, nl1[i], nl1[li-1]
                              ]
                             ]
                            ]) 

                        # min between just calculed and last forest distance
                        val = f_actions[li-1][lj-1][-1][EZS_A_FCOST] + \
                              actions[i][j][-1][EZS_A_FCOST]
                        if f_actions[i][j][-1][EZS_A_FCOST] > val:
                            # concat the 2 actions list
                            f_actions[i][j] = actions[i][j][:]
                            sibl_cost = f_actions[i][j][-1][EZS_A_FCOST]
                            if li-1 > 0 and lj-1 > 0:
                                for action in f_actions[li-1][lj-1]:
                                    action = action[:]
                                    action[EZS_A_FCOST] = action[EZS_A_FCOST] +\
                                                          sibl_cost
                                    f_actions[i][j].append(action)
    
    def _mainformat(self, action_list):
        """ transform ezs output in standard format """
        # remove actions with cost = 0
        action_list = filter(lambda x: x[EZS_A_COST]!=0, action_list)
        for action in action_list:
            n_action = action #None
            # step1: transform the 3 operations SWAP, REMOVE, APPEND
            # from ezs output to SWAP, REMOVE, APPEND, UPDATE according
            # to the node and action type
            #        print '-'*80
            #        print 'action',action
##             # if the action main node have been added
##             if action[EZS_A_N1][N_TYPE] == NT_SYST:
##                 if action[EZS_A_TYPE] in (AT_APPEND, AT_SWAP):
##                     node2 = action[EZS_A_N2][N_CHILDS][0]
##                 else:
##                     try:
##                         node2 = action[EZS_A_N2]
##                     except: node2 = None
##                 n_action = [action[EZS_A_TYPE], 1, 0, action[EZS_A_N1][N_CHILDS][0], node2,
##                             node2]             
##             # action main node is from the original document
##             else: # action[EZS_A_N1][N_TYPE] != NT_SYST
            # those nodes should only be remove + append (= update)
##             if action[EZS_A_TYPE] == AT_APPEND:
##                 if action[EZS_A_N2][N_VALUE] in ['N','T','C']:
##                     delete = action[EZS_A_N2]
##                 elif action[EZS_A_N2][N_PARENT]:
##                     delete = action[EZS_A_N2][N_CHILDS][get_pos(action[EZS_A_N1][N_PARENT])]
## ##                     delete = action[EZS_A_N2][N_PARENT][N_CHILDS][get_pos(action[EZS_A_N1][N_PARENT])][N_CHILDS][0]
##                 else:
##                     # the root has changed
##                     delete = action[EZS_A_N2]
##                 # attribute node
## ##                 if action[EZS_A_N1][N_TYPE] in (NT_ATTN, NT_ATTV):
## ##                     node2 = action[EZS_A_N2][N_PARENT][N_CHILDS][0]
##                 if action[EZS_A_N1][N_TYPE] == NT_ATTN:
##                     node2 = action[EZS_A_N2][N_PARENT]
##                 elif action[EZS_A_N1][N_TYPE] == NT_ATTV:
##                     node2 = action[EZS_A_N2][N_PARENT][N_PARENT]
##                 # element node
##                 elif action[EZS_A_N1][N_TYPE] == NT_NODE:
##                     node2 = action[EZS_A_N2]#[N_CHILDS][0]
##                 # comment or textnode
##                 else: #if action[EZS_A_N1][EZS_A_TYPE] == NT_TEXT:
##                     node2 = action[EZS_A_N2] 
##                 n_action = [AT_UPDATE, 1, 0, action[EZS_A_N1], node2, delete]
        
##             # step2: transform the 4 operations SWAP, REMOVE, APPEND, UPDATE from step1
##             # output to SWAP, REMOVE, APPEND, UPDATE, INSERT_AFTER, INSERT_BEFORE and
##             # RENAME according to the nodes and action type, and convert it to list
##             if n_action:
            if n_action[EZS_A_TYPE] == AT_UPDATE:
                if n_action[EZS_A_N1][N_TYPE] in (NT_NODE, NT_ATTN) :
                    action_l = ['rename',
                                f_xpath(n_action[EZS_A_DEL]),
                                n_action[EZS_A_N1][N_VALUE]]
                else:
                    action_l = ['update',
                                f_xpath(n_action[EZS_A_DEL]),
                                n_action[EZS_A_N1][N_VALUE]]

            elif n_action[EZS_A_TYPE] == AT_SWAP:
                action_l = ['swap', n_action[EZS_A_N1], n_action[EZS_A_N2]]
            elif n_action[EZS_A_TYPE] == AT_REMOVE:
                action_l = ['remove', f_xpath(n_action[EZS_A_N1])]
            elif n_action[EZS_A_TYPE] == AT_APPEND:
                if n_action[EZS_A_N1][N_TYPE] == NT_ATTN:
                    action_l = ['append',
                                f_xpath(n_action[EZS_A_N2]),
                                n_action[EZS_A_N1]]
                elif n_action[EZS_A_N2][N_PARENT] and \
                         nb_childs(n_action[EZS_A_N2][N_PARENT]) > 1:
                    index = get_pos(n_action[EZS_A_N1][N_PARENT])
                    if index == 1 and \
                           nb_childs(n_action[EZS_A_DEL][N_PARENT]) > 1:
                        action_l = ['append-first',
                                    f_xpath(n_action[EZS_A_N1][N_PARENT][N_PARENT][N_CHILDS][0]),
                                    n_action[EZS_A_N1]]                        
                    elif index > 1:
                        action_l = ['insert-after',
                                    f_xpath(n_action[EZS_A_N1][N_PARENT][N_PARENT][N_CHILDS][index-1]), 
                                    n_action[EZS_A_N1]]                        
                    else:
                        action_l = ['append-last',
                                    f_xpath(n_action[EZS_A_DEL][N_PARENT]),
                                    n_action[EZS_A_N1]]
                else:
                    action_l = ['append', f_xpath(n_action[EZS_A_N2]), n_action[EZS_A_N1]]                
            # fully format this action
            self._formatter.add_action(action_l)

    def _post_order(self, node, nodes_list, keyroot, nodes=1):
        '''
        recursivre function which add following attributes to the tree:
        * "number",    the post ordered number of the node (integer),
        * "left most", the post ordered number of the left most child
        (or itself if none)
        * "keyroot",   a boolean (all nodes are keyroot except each
        leftmost nodes)   
        each element node is post ordered numbered
        return the current number (equal the number of nodes when all
        the tree has been processed)
        '''
        if node is not None:
            # add keyroot and leftmost attributes
            node.append(keyroot)
            node.append(nodes)
            for child in node[N_CHILDS]:
                nodes = self._post_order(child, nodes_list,
                                   child is not node[N_CHILDS][0], nodes)
            nodes_list.append(node)
            return nodes + 1
        
        return nodes
