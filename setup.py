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
"""Setup
"""
import os
from setuptools import setup, find_packages


def read(*rnames):
    with open(os.path.join(os.path.dirname(__file__), *rnames), 'rb') as f:
        return f.read().decode('utf-8')


TESTS_REQUIRE = [
    'coverage',
    'lxml',
    'mock',
    'pytest',
    'pytest-cov',
    'flake8',
   ]

try:
    from distutils.core import Extension
    ext_modules = [Extension('xmldiff.maplookup',
                             ['extensions/maplookup.c'])]
except:
    ext_modules = []


setup(
    name='xmldiff',
    version='1.0.1.dev0',
    author="Logilab and Shoobx Team",
    author_email="dev@shoobx.com",
    url='https://github.com/Shoobx/xmldiff',
    description=('Tree 2 tree correction between xml documents. '
                 'Extract differences between two xml files. '
                 'It returns a set of primitives to apply on source tree '
                 'to obtain the destination tree.'),
    long_description=(
        read('README.rst') +
        '\n\n' +
        read('CHANGES.rst')
    ),
    license='LGPL',
    keywords=['xml', 'diff', 'xmldiff', 'tree 2 tree'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Framework :: ZODB',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Natural Language :: English',
        'Operating System :: OS Independent'],
    packages=find_packages('src'),
    package_dir={'': 'src'},
    extras_require=dict(
        test=TESTS_REQUIRE,
    ),
    install_requires=[
        'future',
        'lxml',
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
)
