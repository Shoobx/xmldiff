""" Provides functions for converting DOM tree or xml file in order to process
it with xmldiff functions. """
# Copyright (c) 2001 LOGILAB S.A. (Paris, FRANCE).
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

from xml.sax import make_parser, SAXNotRecognizedException
from xml.sax.handler import feature_namespaces, feature_external_ges
from xml.sax.handler import feature_external_pes, property_lexical_handler

from xmldiff.parser import SaxHandler


def tree_from_stream(stream,
                     norm_sp=1, ext_ges=0, ext_pes=0, include_comment=1,
                     html=0):
    """
    create internal tree from xml stream (open file or StringIO)
    if norm_sp = 1, normalize space and new line
    """
    handler = SaxHandler(norm_sp, include_comment)
    if html:
        parser = make_parser(["xml.sax.drivers2.drv_sgmlop_html"])
    else:
        parser = make_parser()
        # do perform Namespace processing
        parser.setFeature(feature_namespaces, 1)
    # do not include any external entities
    try:
        parser.setFeature(feature_external_ges, ext_ges)
    except SAXNotRecognizedException:
        print('Unable to set feature external ges')
    try:
        parser.setFeature(feature_external_pes, ext_pes)
    except SAXNotRecognizedException:
        print('Unable to set feature external pes')

    # add lexical handler for comments,  entities, dtd and cdata
    parser.setProperty(property_lexical_handler, handler)
    parser.setContentHandler(handler)
    parser.parse(stream)
    return handler.get_tree()


def tree_from_lxml(tree, norm_sp=True, include_comment=True):
    handler = SaxHandler(norm_sp, include_comment)
    import lxml.sax
    lxml.sax.saxify(tree, handler)
    return handler.get_tree()
