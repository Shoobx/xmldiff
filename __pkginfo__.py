# -*- coding: utf-8 -*-
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
""" Copyright (c) 2001-2010 LOGILAB S.A. (Paris, FRANCE).
http://www.logilab.fr/ -- mailto:contact@logilab.fr
"""

modname = distname = 'xmldiff'

numversion = (0, 6, 10)
version = '.'.join(map(str, numversion))

description = "tree 2 tree correction between xml documents"
author = "Sylvain Thénault"
author_email = "sylvain.thenault@logilab.fr"
web = "http://www.logilab.org/project/%s" % modname
ftp = "ftp://ftp.logilab.org/pub/%s" % modname

license = 'LGPL'
copyright = '''Copyright © 2001-2010 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
http://www.logilab.fr/ -- mailto:contact@logilab.fr'''


long_description = """Xmldiff is a utility for extracting differences between two
xml files. It returns a set of primitives to apply on source tree to obtain
the destination tree.
.
The implementation is based on _Change detection in hierarchically structured
- information_, by S. Chawathe, A. Rajaraman, H. Garcia-Molina and J. Widom,
- Stanford University, 1996"""



mailinglist = 'xml-projects@logilab.org'

from os.path import join

scripts = [join('bin', 'xmldiff'), join('bin', 'xmlrev')]
include_dirs = [join('test', 'data')]

try:
    from distutils.core import Extension
    ext_modules = [Extension('xmldiff.maplookup',
                             ['extensions/maplookup.c'])]
except:
    pass

data_files = [("share/sgml/stylesheet/xmldiff",
               ['xsl/docbook_rev.xsl', 'xsl/xmlrev.xslt'])
              ]

pyversions = ['2.3']
