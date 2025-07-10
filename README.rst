xmldiff
========

.. image:: https://travis-ci.org/Shoobx/xmldiff.svg?branch=master
  :target: https://travis-ci.org/Shoobx/xmldiff

.. image:: https://coveralls.io/repos/github/Shoobx/xmldiff/badge.svg
  :target: https://coveralls.io/github/Shoobx/xmldiff

``xmldiff`` is a library and a command-line utility for making diffs out of XML.
This may seem like something that doesn't need a dedicated utility,
but change detection in hierarchical data is very different from change detection in flat data.
XML type formats are also not only used for computer readable data,
it is also often used as a format for hierarchical data that can be rendered into human readable formats.
A traditional diff on such a format would tell you line by line the differences,
but this would not be be readable by a human.
``xmldiff`` provides tools to make human readable diffs in those situations.

Full documentation is on `xmldiff.readthedocs.io <https://xmldiff.readthedocs.io>`_

``xmldiff`` is still under rapid development,
and no guarantees are done that the output of one version will be the same as the output of any previous version.


Quick usage
-----------

``xmldiff`` is both a command-line tool and a Python library.
To use it from the command-line, just run ``xmldiff`` with two input files::

  $ xmldiff file1.xml file2.xml

There is also a command to patch a file with the output from the ``xmldiff`` command::

  $ xmlpatch file.diff file1.xml

There is a simple API for using ``xmldiff`` as a library::

  from lxml import etree
  from xmldiff import main, formatting

  diff = main.diff_files('file1.xml', 'file2.xml',
                         formatter=formatting.XMLFormatter())

There is also a method ``diff_trees()`` that take two lxml trees,
and a method ``diff_texts()`` that will take strings containing XML.
Similarly, there is ``patch_file()`` ``patch_text()`` and ``patch_tree()``::

  result = main.patch_file('file.diff', 'file1.xml')


Changes from ``xmldiff`` 0.6/1.x
--------------------------------

  * A complete, ground up, pure-Python rewrite

  * Easier to maintain, the code is less complex and more Pythonic,
    and uses more custom classes instead of just nesting lists and dicts.

  * Fixes the problems with certain large files and solves the memory leaks.

  * A nice, easy to use Python API for using it as a library.

  * Adds support for showing the diffs in different formats,
    mainly one where differences are marked up in the XML,
    useful for making human readable diffs.

    These formats can show text differences in a semantically meaningful way.

  * An output format compatible with 0.6/1.x is also available.

  * 2.0 is currently significantly slower than ``xmldiff`` 0.6/1.x,
    but this will change in the future.
    Currently we make no effort to make ``xmldiff`` 2.0 fast,
    we concentrate on making it correct and usable.


Contributors
------------

 * Lennart Regebro, regebro@gmail.com (main author)

 * Stephan Richter, srichter@shoobx.com

 * Albertas Agejevas, alga@shoobx.com

 * Greg Kempe, greg@laws.africa

 * Filip Demski, glamhoth@protonmail.com

 * Jacek Chałupka, krunchfrompoland@gmail.com

 * Thomas Pfitzinger, thpfitzinger@web.de

 * Alexandre Detiste

The diff algorithm is based on
"`Change Detection in Hierarchically Structured Information <http://infolab.stanford.edu/c3/papers/html/tdiff3-8/tdiff3-8.html>`_",
and the text diff is using Google's ``diff_match_patch`` algorithm.
