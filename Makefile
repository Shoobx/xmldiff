root_dir := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
bin_dir := $(root_dir)/ve/bin
dfm_source_2 := "https://raw.githubusercontent.com/google/diff-match-patch/master/python2/diff_match_patch.py"
dfm_source_3 := "https://raw.githubusercontent.com/google/diff-match-patch/master/python3/diff_match_patch.py"

all: check coverage

# The fullrelease script is a part of zest.releaser, which is the last
# package installed, so if it exists, the devenv is installed.
devenv:	ve/bin/fullrelease

ve/bin/fullrelease:
	virtualenv $(root_dir)/ve --python python3
	$(bin_dir)/pip install -e .[devenv]

check: devenv
	$(bin_dir)/ruff check xmldiff tests
	$(bin_dir)/pyroma -d .

coverage: devenv
	$(bin_dir)/coverage run -m unittest
	$(bin_dir)/coverage html
	$(bin_dir)/coverage report

test: devenv
	$(bin_dir)/python -bb -X dev -W ignore::UserWarning:setuptools.dist -m unittest --verbose

release: devenv
	$(bin_dir)/fullrelease

update-diff-match-patch:
	wget $(dfm_source_3) -O $(root_dir)/xmldiff/diff_match_patch.py

