Command-line Usage
==================

``xmldiff`` is both a command-line tool and a Python library.
To use it from the command-line, just run ``xmldiff`` with two input files:

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

The included formatters are generic and will work for any type of XML,
but may not give you a useful output.
If you are using ``xmldiff`` as a library,
you can create your own formatters that is suited for your particular usage of XML.

The ``diff`` formatter is default and will output a list of edit actions.
The  ``xml`` formatter will output XML with differences marked up by tags using the ``diff`` namespace.
The ``old`` formatter is a formatter that gives a list of edit actions in a format similar to ``xmldiff`` 0.6 or 1.0.

Whitespace Handling
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

By default the ``xml`` formatter will normalize this whitespace.
You can turn that off with the ``--keep-whitespace`` argument.

Pretty Printing
---------------

The term "pretty printing" refers to making an output a bit more human readable by structuring it with whitespace.
In the case of XML this means inserting ignorable whitespace into the XML,
yes, the same in-between whitespace that is ignored by ``xmldiff`` when detecting changes between two files.

``xmldiff``'s ``xml`` formatter understands the ``--pretty-print`` argument and will insert whitespace to make the output more readable.

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
