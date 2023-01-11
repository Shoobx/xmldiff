xmldiff
=======

``xmldiff`` is a library and a command-line utility for making diffs out of XML.
This may seem like something that doesn't need a dedicated utility,
but change detection in hierarchical data is very different from change detection in flat data.
XML type formats are also not only used for computer readable data,
it is also often used as a format for hierarchical data that can be rendered into human readable formats.
A traditional diff on such a format would tell you line by line the differences,
but this would not be be readable by a human.
This library provides tools to make human readable diffs in those situations.

Contents:

.. toctree::
   :maxdepth: 2

   installation
   commandline
   api
   advanced
   contributing


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
