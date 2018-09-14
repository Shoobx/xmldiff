Python API
==========

Main API
--------

Using ``xmldiff`` from Python is very easy,
you just import and call one of the three main API methods.

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> from xmldiff import main
  >>> main.diff_files("../tests/test_data/insert-node.left.html",
  ...                 "../tests/test_data/insert-node.right.html")
  [UpdateTextIn(node='/body/div[1]', text=None),
   InsertNode(target='/body/div[1]', tag='p', position=0),
   UpdateTextIn(node='/body/div/p[1]', text='Simple text')]

Which one you choose depends on if the XML is contained in files,
text strings or ``lxml`` trees.

* ``xmldiff.main.diff_files()`` takes as input paths to files, or file streams.

* ``xmldiff.main.diff_texts()`` takes as input Unicode strings.

* ``xmldiff.main.diff_trees()`` takes as input lxml trees.


The arguments to these functions are the same:


Parameters
..........

``left``:
  The "left", "old" or "from" XML.
  The diff will show the changes to transform this XML to the "right" XML.

``right``:
  The "right", "new" or "target" XML.

``F``:
  A value between 0 and 1 that determines how similar two XML nodes must be to match as the same in both trees. Defaults to 0.5.

``uniqueattrs``:
  A list of XML node attributes that will uniquely identify a node.
  Defaults to ``['{http://www.w3.org/XML/1998/namespace}id']``.
  See `Unique Attributes`_

``formatter``:
  The formatter to use, see `Using Formatters`_.
  If no formatter is specified the function will return a list of edit actions,
  see `The Edit Script`_.


Result
......

If no formatter is specified the diff functions will return a list of actions.
Such a list is called an edit script and contains all changes needed to transform the "left" XML into the "right" XML.

If a formatter is specified that formatter determines the result.
The included formatters, ``diff``, ``xml``, and ``old`` all return a Unicode string.


Unique Attributes
-----------------

The ``uniqueattrs`` argument is a list of strings specifying attributes that uniquely identify a node in the document.
This is used by the differ when trying to match nodes.
If one node in the left tree has a this attribute,
the node in the right three with the same value for that attribute will match,
regardless of other attributes, child nodes or text content.

The default is ``['{http://www.w3.org/XML/1998/namespace}id']``,
which is the ``xml:id`` attribute.
But if your document have other unique identifiers,
you can pass them in instead.
If you for some reason do not want the differ to look at the ``xml:id`` attribute,
pass in an empty list.


Using Formatters
----------------

By default the diff functions will return an edit script,
but if you pass in a formatter the result will be whatever that formatter returns.

The three included formatters, ``diff``, ``xml`` and ``old``,
all return Unicode strings.
The ``diff`` formatter will return a string with the edit script printed out,
one action per line.
Each line is enclosed in brackets and consists of a string describing the action,
and the actions arguments.
This is the output format of xmldiff 0.6/1.x,
however, the actions and arguments are not the same,
so the output is not compatible.

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> from xmldiff import formatting
  >>> formatter = formatting.DiffFormatter()
  >>> print(main.diff_files("../tests/test_data/insert-node.left.html",
  ...                       "../tests/test_data/insert-node.right.html",
  ...                       formatter=formatter))
  [update-text, /body/div[1], null]
  [insert, /body/div[1], p, 0]
  [update-text, /body/div/p[1], "Simple text"]


The other two differs return XML with tags describing the changes.
These formats are designed so they easily can be changed into something that will render nicely,
for example with XSLT replacing the tags with the format you need.

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> from xmldiff import formatting
  >>> formatter = formatting.XMLFormatter(normalize=formatting.WS_BOTH)
  >>> print(main.diff_files("../tests/test_data/insert-node.left.html",
  ...                       "../tests/test_data/insert-node.right.html",
  ...                       formatter=formatter))
  <body xmlns:diff="http://namespaces.shoobx.com/diff">
    <div id="id">
      <p diff:insert="">Simple text</p>
    </div>
  </body>


The Edit Script
---------------

The default result of the diffing methods is to return an edit script,
which is a list of Python objects called edit actions.
Those actions tell you how to turn the "left" tree into the "right" tree.

``xmldiff`` has nine different actions.
These specify one or two nodes in the XML tree,
called ``node`` or ``target``.
They are specified with an XPATH expression that will uniquely identify the node.

The other arguments vary depending on the action.


``InsertNode(target, tag, position)``
......................................

The ``InsertNode`` action means that the node specified in ``target`` needs a new subnode.
``tag`` specifies which tag that node should have.
The ``position`` argument specifies which position the new node should have,
``0`` means that the new node will be inserted as the first child of the target.
Note that this is different from XPATH, where the first node is ``1``.
This is for ease of use, since Python is zero-indexed.

Example:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> left = '<document><node>Content</node></document>'
  >>> right = '<document><node>Content</node><newnode/></document>'
  >>> main.diff_texts(left, right)
  [InsertNode(target='/document[1]', tag='newnode', position=1)]


``DeleteNode(node)``
....................

The ``DeleteNode`` action means that the node specified in ``node`` should be deleted.

Example:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> left = '<document><node>Content</node></document>'
  >>> right = '<document/>'
  >>> main.diff_texts(left, right)
  [DeleteNode(node='/document/node[1]')]


``MoveNode(node, target, position)``
....................................

The ``MoveNode`` action means that the node specified in ``node`` should be moved to be a child under the target node.
The ``position`` argument specifies which position it should have,
``0`` means that the new node will be inserted as the first child of the target.
Note that this is different from XPATH, where the first node is ``1``.
This is for ease of use, since Python is zero-indexed.

Example:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> left = '<document><node>Content</node><movenode/></document>'
  >>> right = '<document><movenode/><node>Content</node></document>'
  >>> main.diff_texts(left, right)
  [MoveNode(node='/document/node[1]', target='/document[1]',
            position=1)]


``InsertAttrib(node, name, value)``
.....................................

The ``InsertAttrib`` action means that the node specified in ``node`` should get a new attribute.
The ``name `` and ``value`` arguments specify the name and value of that attribute.

Example:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> left = '<document><node/></document>'
  >>> right = '<document newattr="newvalue"><node/></document>'
  >>> main.diff_texts(left, right)
  [InsertAttrib(node='/document[1]', name='newattr',
                value='newvalue')]


``DeleteAttrib(node, name)``
............................

The ``DeleteAttrib`` action means that an attribute of the node specified in ``target`` should be deleted.
The ``name`` argument specify which attribute.

Example:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> left = '<document newattr="newvalue"><node/></document>'
  >>> right = '<document><node/></document>'
  >>> main.diff_texts(left, right)
  [DeleteAttrib(node='/document[1]', name='newattr')]


``RenameAttrib(node, name)``
............................

The ``RenameAttrib`` action means that an attribute of the node specified in ``node`` should be renamed.
The ``oldname`` and ``newname`` arguments specify which attribute and it's new name.

Example:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> left = '<document attrib="value"><node/></document>'
  >>> right = '<document newattrib="value"><node/></document>'
  >>> main.diff_texts(left, right)
  [RenameAttrib(node='/document[1]', oldname='attrib',
                newname='newattrib')]


``UpdateAttrib(node, name)``
............................

The ``UpdateAttrib`` action means that an attribute of the node specified in ``node`` should get a new value.
The ``name`` and ``value`` arguments specify which attribute and it's new value.

Example:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> left = '<document attrib="value"><node/></document>'
  >>> right = '<document attrib="newvalue"><node/></document>'
  >>> main.diff_texts(left, right)
  [UpdateAttrib(node='/document[1]', name='attrib', value='newvalue')]


``UpdateTextIn(node, name)``
............................

The ``UpdateTextIn`` action means that an text content of the node specified in ``node`` should get a new value.
The ``text`` argument specify the new value of that text.

Example:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> left = '<document><node>Content</node></document>'
  >>> right = '<document><node>New Content</node></document>'
  >>> main.diff_texts(left, right)
  [UpdateTextIn(node='/document/node[1]', text='New Content')]


``UpdateTextAfter(node, name)``
...............................

The ``UpdateTextAfter`` action means that an text that trails the node specified in ``node`` should get a new value.
The ``text`` argument specify the new value of that text.

Example:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> left = '<document><node>Content</node></document>'
  >>> right = '<document><node>Content</node>Trailing text</document>'
  >>> main.diff_texts(left, right)
  [UpdateTextAfter(node='/document/node[1]', text='Trailing text')]
