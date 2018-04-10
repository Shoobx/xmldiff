"""
miscellaneous functions
"""
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

import os

##### interface ###
TRUE = 1
FALSE = 0


def process_dirs(dir1, dir2, recursive):
    """
    function which return common, added, deleted file from dir1 to dir2
    and remove initial directory from paths
    """
    dir1 = normalize_dir(dir1)
    dir2 = normalize_dir(dir2)
    common, deleted, added = _process_dirs(dir1, dir2, recursive)
    # remove prefix
    deleted[0] = list(map(_remove_prefix(len(dir1)),  deleted[0]))
    deleted[1] = list(map(_remove_prefix(len(dir1)),  deleted[1]))
    added[0] = list(map(_remove_prefix(len(dir2)),  added[0]))
    added[1] = list(map(_remove_prefix(len(dir2)),  added[1]))
    common[0] = list(map(_remove_prefix(len(dir1)), common[0]))
    common[1] = list(map(_remove_prefix(len(dir1)), common[1]))
    return common, deleted, added


def divide_files(dir):
    """ return a list with subdir of dir and another one with files """
    import os
    dirs = []
    regs = []
    # os.path.normpath(dir)
    for filename in os.listdir(dir):
        if os.path.isfile(os.path.join(dir, filename)):
            regs.append(filename)
        elif os.path.isdir(os.path.join(dir, filename)):
            dirs.append(filename)
    return dirs, regs


def extract(list1, list2):
    """ extract common, added, deleted item from list1 to list2 """
    common, deleted, added = [], [], []
    for item in list1:
        if item in list2:
            common.append(item)
            list2.remove(item)
        else:
            deleted.append(item)
    for item in list2:
        if not item in list1:
            added.append(item)
    return common, deleted, added


def union(list1, list2):
    """ return list1 union list2 """
    tmp = {}
    for i in list1:
        tmp[i] = 1
    for i in list2:
        tmp[i] = 1
    return tmp.keys()


def intersection(list1, list2):
    """ return common items in list1 and list2 """
    tmp, l = {}, []
    for i in list1:
        tmp[i] = 1
    for i in list2:
        if i in tmp:
            l.append(i)
    return l


def init_matrix(nbrows, nbcols, default_value):
    """
    return a 2d matrix list2d[nbrows][nbcols] initialised with
    default_value (carefull for side effect with references...)
    """
    list2d = []
    for i in range(nbrows):
        tmpl = []
        for j in range(nbcols):
            tmpl.append(default_value)
        list2d.append(tmpl)
    return list2d


def in_ref(list, item):
    """ return true if list contains a reference on item """
    for it in list:
        if it is item:
            return TRUE
    return FALSE


def index_ref(list, item):
    """
    return the index of item in list by reference comparison
    raise Exception if not found
    """
    index = 0
    for it in list:
        if it is item:
            return index
        index += 1
    raise Exception('No item '+item)


def list_print(list, s1='', s2=''):
    for item in list:
        if item:
            print('-'*80)
            print("%s %s %s" % (s1, item, s2))


def append_list(list, a_list):
    """ append a_list items to list """
    for item in a_list:
        list.append(item)


def normalize_dir(directory):
    """remove trailing path separator from the directory name
    """
    while directory[-1] == os.sep:
        directory = directory[:-1]
    return directory


def _process_dirs(dir1, dir2, recursive):
    """
    function which return common, added, deleted file from dir1 to dir2
    if recursive, enter in subdirectory
    """
    #/!\ sym links /!\#

    # extract common files and directory
    d_list1, f_list1 = divide_files(dir1)
    d_list2, f_list2 = divide_files(dir2)
    common, deleted, added = [[], []], [[], []], [[], []]
    common[0], deleted[0], added[0] = extract(f_list1, f_list2)
    common[1], deleted[1], added[1] = extract(d_list1, d_list2)
    # add prefix
    deleted[0] = map(_add_prefix(dir1),  deleted[0])
    deleted[1] = map(_add_prefix(dir1),  deleted[1])
    added[0] = map(_add_prefix(dir2),  added[0])
    added[1] = map(_add_prefix(dir2),  added[1])
    common[0] = map(_add_prefix(dir1), common[0])
    if recursive:
        import os
        # for all common subdirs
        for dir in common[1]:
            if dir == 'CVS':
                continue
            # recursion
            comm, dele, adde = _process_dirs(os.path.join(dir1, dir),
                                             os.path.join(dir2, dir),
                                             recursive)
            # add subdir items
            append_list(deleted[0], dele[0])
            append_list(deleted[1], dele[1])
            append_list(added[0], adde[0])
            append_list(added[1], adde[1])
            append_list(common[0], comm[0])
    return common, deleted, added


def _remove_prefix(prfx_size):
    """ return a function to add remove with map() """
    return lambda s, len=prfx_size: s[len+1:]


def _add_prefix(prefix):
    """ return a function to add prefix with map() """
    return lambda s, prfx=prefix, join=os.path.join: join(prfx, s)
