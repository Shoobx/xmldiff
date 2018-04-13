CHANGES
=======

1.0.0a7 (unreleased)
--------------------

- pep8 cleanup, added flake8 checking to tox


1.0.0a6 (2018-04-12)
--------------------

- Removed encoding, because python does unicode just fine

- Switched on namespace handling for XML input


1.0.0a5 (2018-04-11)
--------------------

- Brownbag release to make up for bad previous ones.

1.0.0a2 (2018-04-11)
--------------------

- Temporary disabling of encoding text (hopefully permanent).

- Reverted bug fix: Do not remove newlines from text while parsing
  the XML.


1.0.0a1 (2018-04-10)
--------------------

- Bug: Fix a off-by-one issue with `insert-after` action.

- Bug: Do not rename children on text node updates.

- Bug: Text moves were not recorded as part of the fmes edit script.

- Remove only partially implemented xmlrev script.

- Removed support for xupdate, which never became a standard.

- Removed deprecated ezs optional algorithm.

- Removed support for Debian and RedHat packaging.

- Removed Windows support

- LOTS of package cleanup (setup.py, MANIFEST, proper console script, etc)

- tests moved to py.test and cleaned, added tox, travis, coverage support


0.6.10 (2010-08-27)
-------------------

- apply Daiki Ueno patch: fails when comparing minimal trees on i386


0.6.9 (2009-04-02)
------------------

- Fixed xmldiff-xmlrev compilation error


0.6.8 (2006-06-15)
------------------

- Fixed 64bit cleanness issues


0.6.7 (2005-05-04)
------------------

- WARNING: xmldiff is no longer a logilab subpackage. Users may have to
  manually remove the old logilab/xmldiff directory.

- fixed debian bug #275750, also reported by Christopher R Newman on the
  xml-projects mailing list

- fixed --profile option, wrap function from maplookup when profiling so that
  they appear in the profile information

- fixed setup.py to ignore the xmlrev shell script under windows platforms

- small improvements (remove recursion in object.py, minor enhancement in
  mydifflib.py, rewrite of lcs4 in C)


0.6.6 (2004-12-23)
------------------

- Applied patch by Bastian Kleineidam <calvin@debian.org> which

  - corrects the typo in  ML_DIR

  - fixes the TMPFILE_XSLT/TMPFILE_XSL typo

  - makes sure the files are XML or SGML files, else prints an error

  - adds various missing quotes around filenames which could have
    spaces or begin with a hyphen

  - fixes typos in the usage() function

  Thanks a lot, Bastian.

- Fixed some problems in the xmlrev.xslt stylesheet

- Fixed problems in xmlrev caused by the exit status of xmldiff when
  successful

- Added a man page for xmldiff and xmlrev


0.6.5 (2004-09-02)
------------------

- xmlrev bugfixes

- Fixed packaging problems (missing xsl stylesheets and MANIFEST file)


0.6.4 (2003-10-02)
------------------

- fix recursive mode

- rewrite regression test, add test for the recursive mode

- add --help option to xlmrev

- packaging fixes

- turn API.txt and HELP.txt to correct ReST


0.6.3 (2002-11-06)
------------------

- fix wrong xpath for attributes

- fix bug with temporary duplicate attribute node

- fix for xupdate

- fix ext_pes option bug

- update changelog to new format


0.6.2 (2002-09-23)
------------------

- return number of differences on command line

- reintroduce misc.list_print which caused recursive mode
  to fail

- use psyco if available (http://psyco.sf.net)

- little changes in C extension


0.6.1 (2002-08-29)
------------------

- fix packaging problems


0.6.0 (2002-08-23)
------------------

- change of the internal representation

- remove support for the EZS algorithm (no more maintened
  for the moment)

- add command line options to parse html and to control
  entities inclusion and output encoding

- fixing coalescing text nodes bug

- many other bugs fixes

- great speed improvement


0.5.3 (2002-01-31)
------------------

- add __init__.py in "logilab" directory


0.5.2 (2001-10-29)
------------------

- bug fixes in xupdate formatting and in the dom interface.


0.5.1 (2001-09-07)
------------------

- Fast Match / Edit Scritp algorithm, now fully usable

- fixes Unicode problem


0.2.1 (2001-08-10)
------------------

- bug fixes, optimizations for ezs algorithm


0.1.1 (2001-08-04)
------------------

- original revision
