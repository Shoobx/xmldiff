Command line usage
==================

``xmldiff`` is both a command line tool and a Python library.
To use it from the commandline, just run ``xmldiff`` with two input files:

.. code-block:: bash

  $ xmldiff file1.xml file2.xml

There are a few extra options to modify the output,
but be aware that not all of the combinations are meaningful,
so don't be surprised of you add one and nothing happens.


Options
-------

.. argparse::
   :module: xmldiff.main
   :func: make_parser
   :prog: xmldiff
   :nodescription:

Formatters
----------

You can select different output formats with ``xmldiff``,
but beware that some formatters may assume certain things about the type of XML.

The two formatters named ``diff`` and ``xml`` are generic and will work for any type of XML,
but may not give you a useful output.
If you are using ``xmldiff`` as a library,
you can create your own formatters that is suited for your particular usage of XML.

Whitespace handling
-------------------

Formatters are also responsable for whitespace handling,
both in parsing and in output.

By default ``xmldiff`` will strip all whitespace that is between tags,
as opposed to inside tags.
That whitespace isn't a part of any data and can be ignored.
So this XML structure:

.. code-block:: xml

  <data count="1"></data><data count="2"></data>

Will be seen as the same document as this:

.. code-block:: xml

  <data count="1"></data>    <data count="2"></data>

Because the whitespace is between the tags.
However, this structure is different,
since the whitespace there occurs inside a tag:

.. code-block:: xml

  <data count="1">    </data><data count="2"></data>

In some XML formats, whitespace inside some tags is also not significant.
The ``html`` formatter is an example of this.
 It is aware of that ``<p>`` tags contain text where whitespace isn't significant,
and will by default normalize whitespace inside these tags before comparing it,
effectively replacing any whitespace inside those tags to a single space.
This is so that when diffing two versions of HTML files you will not see changes that would not be visible in the final document.

Both of these types of whitespace can be preserved with the ``--keep-whitespace`` argument.
The third case of whitespace,
whitespace that occurs inside tags that are *not* known to be formatted text tags,
will always be preserved.
Both the ``diff`` and ``xml`` formatters don't know of any text formatting,
and will therefore always preserve all whitespace inside tags.


Pretty printing
---------------

The term "pretty printing" refers to making an output a bit more human readable by structuring it with whitespace.
In the case of XML this means inserting ignorable whitespace into the XML,
yes, the same in-between whitespace that is ignored by ``xmldiff`` when detecting changes between two files.

``xmldiff``'s ``xml`` and ``html`` formatters understand the ``--pretty-print`` argument and will insert whitespace to make the output more readable.

For example, an XML output that would normally look like this:

  <document><story>Some content</story><story><para>This is some
  simple text with <i>formatting</i>.</para></story></document>

Will with the ``--pretty-print`` argument look like this:

.. code-block:: xml

  <document>
    <story>Some content</story>
    <story>
      <para>This is some simple text with <i>formatting</i>.</para>
    </story>
  </document>

This means you can actually use ``xmldiff`` to reformat XML, by using the
``xml`` formatter and passing in the same XML file twice::

  $ xmldiff -f xml -p uglyfile.xml uglyfile.xml

However, if you keep whitespace with ``--keep-whitespace`` or ``-w``,
no reformatting will be done.
