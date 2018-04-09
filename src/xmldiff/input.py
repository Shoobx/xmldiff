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

def tree_from_stream(stream, 
                     norm_sp=1, ext_ges=0, ext_pes=0, include_comment=1,
                     encoding='UTF-8', html=0):
    """
    create internal tree from xml stream (open file or IOString)
    if norm_sp = 1, normalize space and new line
    """
    from xml.sax import make_parser, SAXNotRecognizedException
    from xml.sax.handler import feature_namespaces, feature_external_ges, \
         feature_external_pes, property_lexical_handler
    from xmldiff.parser import SaxHandler
    handler = SaxHandler(norm_sp, include_comment, encoding)
    if html:
        parser = make_parser(["xml.sax.drivers2.drv_sgmlop_html"])
    else:
        parser = make_parser()
        # do not perform Namespace processing 
        parser.setFeature(feature_namespaces, 0)
    # do not include any external entities
    try:
        parser.setFeature(feature_external_ges, ext_ges)
        #xml.sax._exceptions.
    except SAXNotRecognizedException:
        print 'Unable to set feature external ges'
    try:
        parser.setFeature(feature_external_pes, ext_pes)
        #xml.sax._exceptions.
    except SAXNotRecognizedException:
        print 'Unable to set feature external pes'
    # add lexical handler for comments,  entities, dtd and cdata
    parser.setProperty(property_lexical_handler, handler)
    parser.setContentHandler(handler)
    parser.parse(stream)
    return handler.get_tree()


def tree_from_dom(root):
    """ create internal tree from DOM subtree """
    from xml.dom.ext.Dom2Sax import Dom2SaxParser 
    from xml.sax.handler import feature_namespaces, property_lexical_handler
    #from parser import DomParser
    parser = Dom2SaxParser()
    from xmldiff.parser import SaxHandler
    handler = SaxHandler(normalize_space=0, include_comment=1)
    # do not perform Namespace processing 
    parser.setFeature(feature_namespaces, 0)
    # add lexical handler for comments,  entities, dtd and cdata
    parser.setProperty(property_lexical_handler, handler)
    parser.setContentHandler(handler)
    parser.parse(root)
    return handler.get_tree()


if __name__ == '__main__':
    from xml.dom.ext import StripXml, PrettyPrint
    from xml.dom.ext.reader.Sax2 import Reader
    import sys
    reader = Reader()
    file = open(sys.argv[1],'r')
    fragment = reader.fromStream(file)
    d = StripXml(fragment)
    file.close()
    tree = tree_from_dom(d)
    file = open(sys.argv[2],'r')
    fragment = reader.fromStream(file)
    d = StripXml(fragment)
    file.close()
    tree2 = tree_from_dom(d)
    from xmldiff.objects import repr
    print 'Source tree', repr(tree)
    print 'Destination tree', repr(tree2)
    from xmldiff.fmes import FmesCorrector
    strategy = FmesCorrector(0.59, 0.5)
    actions = strategy.process_trees(tree, tree2)
    # from xmldiff.format import xupdate_dom
    # PrettyPrint(
    #     xupdate_dom(
    #     reader.fromString('<root/>'),
    #     actions))
