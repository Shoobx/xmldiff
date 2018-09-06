import sys
if sys.version_info[0] == 3:
    from xmldiff._diff_match_patch_py3 import *
else:
    from xmldiff._diff_match_patch_py2 import *
