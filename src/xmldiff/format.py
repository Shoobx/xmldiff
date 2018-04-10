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
this module provides classes to format the native tree2tree output
"""

import types
try:
    from xml.dom import EMPTY_NAMESPACE as NO_NS
except:
    NO_NS = None
from xmldiff.objects import A_N1, A_N2, A_DESC, xml_print, f_xpath
from sys import stdout


def get_attrs_string(attrs):
    """ extract and return a string corresponding to an attributes list """
    attr_s = []
    for attr_n, attr_v in attrs:
        attr_s.append('%s="%s" ' % (attr_n, attr_v))
    return ' '.join(attr_s)


## Formatter interface ########################################################
class AbstractFormatter:
    """
    Formatter interface
    """

    def init(self, stream=stdout):
        """ method called before the begining of the tree 2 tree correction """
        self.edit_s = []
        self._stream = stream

    def add_action(self, action):
        """ method called when an action is added to the edit script """
        self.edit_s.append(action)

    def format_action(self, action):
        """ method called by end() to format each action in the edit script
        at least this method should be overridden
        """
        raise NotImplementedError()

    def end(self):
        """ method called at the end of the tree 2 tree correction """
        for action in self.edit_s:
            self.format_action(action)


## Internal Formatter ##########################################################

class InternalPrinter(AbstractFormatter):
    """ print actions in the internal format """

    def add_action(self, action):
        """
        See AbstractFormatter interface
        """
        if len(action) > 2 and isinstance(action[A_N2], list):
            if isinstance(action[A_N1], list):
                # swap or move node
                action[A_N1] = f_xpath(action[A_N1])
                action[A_N2] = f_xpath(action[A_N2])
        AbstractFormatter.add_action(self, action)

    def format_action(self, action):
        """
        See AbstractFormatter interface
        """
        if len(action) > 2 and isinstance(action[A_N2], list):
            self._stream.write('[%s, %s,\n' % (action[A_DESC], action[A_N1]))
            xml_print(action[A_N2])
            self._stream.write("]\n")
        elif len(action) > 2:
            self._stream.write('[%s, %s, %s]\n' % (action[A_DESC],
                                                   action[A_N1],
                                                   action[A_N2]))
        else:
            self._stream.write('[%s, %s]\n' % (action[A_DESC], action[A_N1]))
