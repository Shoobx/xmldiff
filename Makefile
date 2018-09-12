root_dir := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
dfm_source_2 := "https://raw.githubusercontent.com/google/diff-match-patch/master/python2/diff_match_patch.py"
dfm_source_3 := "https://raw.githubusercontent.com/google/diff-match-patch/master/python3/diff_match_patch.py"

update-diff-match-patch:
	wget $(dfm_source_2) -O $(root_dir)/xmldiff/_diff_match_patch_py2.py
	wget $(dfm_source_3) -O $(root_dir)/xmldiff/_diff_match_patch_py3.py

flake:
	flake8 tests xmldiff --exclude *diff_match_patch*.py

coverage:
	coverage run setup.py test
	coverage html
	coverage report

test:
	python setup.py test
