#!/usr/bin/env python
# pylint: disable-msg=W0142, W0403,W0404, W0613,W0622,W0622, W0704, R0904
#
# Copyright (c) 2003-2010 LOGILAB S.A. (Paris, FRANCE).
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
"""Setup
"""
import os
from setuptools import setup, find_packages


def read(*rnames):
    with open(os.path.join(os.path.dirname(__file__), *rnames), 'rb') as f:
        return f.read().decode('utf-8')


def alltests():
    import os
    import sys
    import unittest
    # use the zope.testrunner machinery to find all the
    # test suites we've put under ourselves
    import zope.testrunner.find
    import zope.testrunner.options
    here = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
    args = sys.argv[:]
    defaults = ["--test-path", here]
    options = zope.testrunner.options.get_options(args, defaults)
    suites = list(zope.testrunner.find.find_suites(options))
    return unittest.TestSuite(suites)

TESTS_REQUIRE = [
    'coverage',
    'mock',
   ]

try:
    from distutils.core import Extension
    ext_modules = [Extension('xmldiff.maplookup',
                             ['extensions/maplookup.c'])]
except:
    ext_modules = []


setup(
    name='xmldiff',
    version='1.0.0.dev0',
    author="Shoobx Team",
    author_email="dev@shoobx.com",
    url='https://github.com/Shoobx/xmldiff',
    description=('Tree 2 tree correction between xml documents. '
                 'Extract differences between two xml files. '
                 'It returns a set of primitives to apply on source tree '
                 'to obtain the destination tree.'),
    long_description=(
        read('src', 'xmldiff', 'README.txt')
        + '\n\n' +
        read('CHANGES.txt')
    ),
    license='LGPL',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Framework :: ZODB',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    extras_require=dict(
        test=TESTS_REQUIRE,
        zope=(
            'zope.container',
        ),
    ),
    install_requires=[
        'future',
        'six',
        'setuptools',
    ],
    include_package_data=True,
    zip_safe=False,
    entry_points='''
    [console_scripts]
    xmldiff = xmldiff.main:run
    ''',
    ext_modules=ext_modules,
    tests_require=TESTS_REQUIRE,
    test_suite='__main__.alltests',
)
