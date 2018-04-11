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
