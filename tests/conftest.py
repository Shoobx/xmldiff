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

import pytest
import xmldiff.difflib


if xmldiff.difflib.have_c_extension:
    lcs2_type_params = ['force_python', 'c']
else:
    lcs2_type_params = ['just_python']


# XXX: there are more functions defined in maplookup.c
#      which are NOT implemented in python!


@pytest.fixture(params=lcs2_type_params, scope='module')
def lcs2_type(request):
    save_lcs2 = xmldiff.difflib.lcs2
    if request.param == 'force_python':
        xmldiff.difflib.lcs2 = xmldiff.difflib.lcs2_python
    elif request.param == 'c':
        pass
    elif request.param == 'just_python':
        pass
    yield request.param
    xmldiff.difflib.lcs2 = save_lcs2
