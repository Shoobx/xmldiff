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
this module provides classes to format the native tree2tree output
"""

import logging
import sys
try:
    from xml.dom import EMPTY_NAMESPACE as NO_NS
except ImportError:  # pragma: no cover
    NO_NS = None
from xmldiff.objects import A_N1, A_N2, A_DESC, xml_print, f_xpath
from xmldiff.parser import Node


## Formatter interface ########################################################
class AbstractFormatter(object):
    """
    Formatter interface
    """
    def __init__(self, stream=None):
        self.edit_s = []
        self._stream = stream

    def init(self, stream=None):
        """ method called before the begining of the tree 2 tree correction """
        logging.warning("The init() method of Formatters is deprecated. Set the "
                        "stream with __init__() instead.")
        if self._stream is None and stream is not None:
            self._stream = stream

    def add_action(self, action):
        """ method called when an action is added to the edit script """
        self.edit_s.append(action)

    def format_action(self, action):
        """ method called by end() to format each action in the edit script
        at least this method should be overridden
        """
        raise NotImplementedError()  # pragma: no cover

    def end(self):
        """ method called at the end of the tree 2 tree correction """
        if self._stream is None:
            self._stream = sys.stdout

        for action in self.edit_s:
            self.format_action(action)


## Internal Formatter #########################################################
class InternalPrinter(AbstractFormatter):
    """ print actions in the internal format """

    def add_action(self, action):
        """
        See AbstractFormatter interface
        """
        if len(action) > 2 and isinstance(action[A_N2], Node):
            if isinstance(action[A_N1], Node):
                # swap or move node
                action[A_N1] = f_xpath(action[A_N1])
                action[A_N2] = f_xpath(action[A_N2])
        super(InternalPrinter, self).add_action(action)

    def format_action(self, action):
        """
        See AbstractFormatter interface
        """
        if len(action) > 2 and isinstance(action[A_N2], Node):
            self._stream.write('[%s, %s,\n' % (action[A_DESC], action[A_N1]))
            xml_print(action[A_N2], stream=self._stream)
            self._stream.write("]\n")
        elif len(action) > 2:
            self._stream.write('[%s, %s, %s]\n' % (action[A_DESC],
                                                   action[A_N1],
                                                   action[A_N2]))
        else:
            self._stream.write('[%s, %s]\n' % (action[A_DESC], action[A_N1]))
