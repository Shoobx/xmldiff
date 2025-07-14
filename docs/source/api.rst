Python API
==========

Main diffing API
----------------

Using ``xmldiff`` from Python is very easy,
you just import and call one of the three main API methods.

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> from xmldiff import main
  >>> main.diff_files("../tests/test_data/insert-node.left.html",
  ...                 "../tests/test_data/insert-node.right.html",
  ...                 diff_options={'F': 0.5, 'ratio_mode': 'fast'})
  [UpdateTextIn(node='/body/div[1]', text=None, oldtext='\n  '),
   InsertNode(target='/body/div[1]', tag='p', position=0),
   UpdateTextIn(node='/body/div/p[1]', text='Simple text', oldtext=None)]

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

``check``:
  Return error code 1 if there are any differences between the files.

``diff_options``:
  A dictionary containing options that will be passed into the ``Differ()``:
    ``F``:
    A value between 0 and 1 that determines how similar two XML nodes must be to match as the same in both trees.
    Defaults to ``0.5``.

    A higher value requires a smaller difference between two nodes for them to match.
    Set the value high, and you will see more nodes inserted and deleted instead of being updated.
    Set the value low, and you will get more updates instead of inserts and deletes.

    ``uniqueattrs``:
    A list of XML node attributes that will uniquely identify a node.
    See `Unique Attributes`_ for more info.

    Defaults to ``['{http://www.w3.org/XML/1998/namespace}id']``.

    ``ratio_mode``:

    The ``ratio_mode`` determines how accurately the similarity between two nodes is calculated.
    The choices are ``'accurate'``, ``'fast'`` and ``'faster'``.
    Defaults to ``'fast'``.

    Using ``'faster'`` often results in less optimal edits scripts,
    in other words, you will have more actions to achieve the same result.
    Using ``'accurate'`` will be significantly slower,
    especially if your nodes have long texts or many attributes.

    ``ignored_attrs``:
    A list of XML node attributes that will be ignored in comparison.

``fast_match``:
  By default ``xmldiff`` will compare each node from one tree with all nodes from the other tree.
  It will then pick the one node that matches best as the match,
  if that match passes the match threshold ``F`` (see above).

  If fast_match is true ``xmldiff`` will first make a faster run,
  trying to find chains of matching nodes,
  during which any match better than ``F`` will count.
  This significantly cuts down on the time to match nodes,
  but means that the matches are no longer the best match,
  only "good enough" matches.

``formatter``:
  The formatter to use, see `Using Formatters`_.
  If no formatter is specified the function will return a list of edit actions,
  see `The Edit Script`_.

Result
......

If no formatter is specified the diff functions will return a list of actions.
Such a list is called an Edit Script and contains all changes needed to transform the "left" XML into the "right" XML.

If a formatter is specified that formatter determines the result.
The included formatters, ``diff``, ``xml``, and ``old`` all return a Unicode string.

``xmldiff`` is still under rapid development,
and no guarantees are done that the output of one version will be the same as the output of any previous version.
The actions of the edit script can be in a different order or replaced by equivalent actions dependingon the version of ``xmldiff``,
but if the Edit Script does not correctly transform one XML tree into another,
that is regarded as a bug.
This means that the output of the ``xml`` format also may change from version to version.
There is no "correct" solution to how that output should look,
as the same change can be represented in several different ways.


Unique Attributes
-----------------

The ``uniqueattrs`` argument is a list of strings or ``(tag, attribute)`` tuples
specifying attributes that uniquely identify a node in the document.
This is used by the differ when trying to match nodes.
If one node in the left tree has a this attribute,
the node in the right three with the same value for that attribute will match,
regardless of other attributes, child nodes or text content.
Respectively, if the values of the attribute on the nodes in question are different,
or if only one of the nodes has this attribute,
the nodes will not match regardless of their structural similarity.
In case the attribute is a tuple, the attribute match applies only if both nodes
have the given tag.

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

The three included formatters all return Unicode strings.

All formatters take two arguments:

:``normalize``: This argument determines whitespace normalizing.
                It can be one of the following values,
                all defined in ``xmldiff.formatting``:

                :``WS_NONE``: No normalizing

                :``WS_TAGS``: Normalize whitespace between tags

                :``WS_TEXT``: Normalize whitespace in text tags (only used by the ``XMLFormatter``).

                :``WS_BOTH``: Both ``WS_TAGS`` and ``WS_TEXT``.

:``pretty_print``: This argument determines if the output should be compact (``False``) or readable (``True``). Only the ``XMLFormatter`` currently uses this parameter,
                   but it's useful enough that it was included in the ``BaseFormatter`` class,
                   so that all subsequent formatters may use it.


DiffFormatter
.............

.. py:class:: xmldiff.formatting.DiffFormatter(normalize=WS_TAGS, pretty_print=False)

This formatter is the one used when you specify ``-f diff`` on the command line.
It will return a string with the edit script printed out,
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
  [update-text, /body/div[1], null, "\n  "]
  [insert, /body/div[1], p, 0]
  [update-text, /body/div/p[1], "Simple text", null]


XmlDiffFormatter
................

.. py:class:: xmldiff.formatting.XmlDiffFormatter(normalize=WS_TAGS, pretty_print=False)

This formatter works like the DiffFormatter,
but the output format is different and more similar to the ``xmldiff`` output in versions 0.x and 1.x.

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> from xmldiff import formatting
  >>> formatter = formatting.XmlDiffFormatter(normalize=formatting.WS_NONE)
  >>> print(main.diff_files("../tests/test_data/insert-node.left.html",
  ...                       "../tests/test_data/insert-node.right.html",
  ...                       formatter=formatter))
  [update, /body/div[1]/text()[1], "\n    "]
  [insert-first, /body/div[1],
  <p/>]
  [update, /body/div/p[1]/text()[1], "Simple text"]
  [update, /body/div/p[1]/text()[2], "\n  "]


XMLFormatter
............

.. py:class:: xmldiff.formatting.XMLFormatter(normalize=WS_NONE, pretty_print=True, text_tags=(), formatting_tags=())¶

  :param text_tags: A list of XML tags that contain human readable text,
                    ex ``('para', 'li')``

  :param formatting_tags: A list of XML tags that are tags that change text formatting,
                          ex ``('strong', 'i', 'u' )``

This formatter return XML with tags describing the changes.
These tags are designed so they easily can be changed into something that will render nicely,
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

If the move is within the same parent, the position can be ambiguous.
If you have a child that is in position 1,
but should be moved to position 3,
that position does not include the node being moved,
but signifies the position the node should end up at after the move.
When implementing a ``MoveNode()`` it is therefore easiest to remove the node from the parent first,
and then insert it at the given position.

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


``RenameAttrib(node, oldname, newname)``
........................................

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
  [UpdateTextIn(node='/document/node[1]', text='New Content', oldtext='Content')]


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
  [UpdateTextAfter(node='/document/node[1]', text='Trailing text', oldtext=None)]


``InsertComment(target, position, text)``
.........................................

Since comments doesn't have a tag,
the normal ``InsertNode()`` action doesn't work nicely with a comment.
Therefore comments get their own insert action.
Just like ``InsertNode()`` it takes a target node and a position.
It naturally has no tag but instead has a text argument,
as all comments have text and nothing else.

``UpdateTextIn()`` and ``DeleteNode()`` works as normal for comments.

Example:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> left = '<document><node>Content</node></document>'
  >>> right = '<document><!-- A comment --><node>Content</node></document>'
  >>> main.diff_texts(left, right)
  [InsertComment(target='/document[1]', position=0, text=' A comment ')]


``InsertNamespace(prefix, uri)``
................................

Adds a new namespace to the XML document. You need to have this before
adding a node that uses a namespace that is not in the original XML tree.

Example:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> left = '<document></document>'
  >>> right = '<document xmlns:new="http://theuri"></document>'
  >>> main.diff_texts(left, right)
  [InsertNamespace(prefix='new', uri='http://theuri')]


``DeleteNamespace(prefix)``
................................

Removes a namespace from the XML document. You don't need to handle this,
strictly speaking, nothing will break if there is an unused namespace,
but `xmldiff` will return this action.

Example:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> left = '<document xmlns:new="http://theuri"></document>'
  >>> right = '<document></document>'
  >>> main.diff_texts(left, right)
  [DeleteNamespace(prefix='new')]



The patching API
----------------

There is also an API to patch files using the diff output:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> from xmldiff import main
  >>> print(main.patch_file("../tests/test_data/insert-node.diff",
  ...                       "../tests/test_data/insert-node.left.html"))
  <body>
    <div id="id">
      <p>Simple text</p>
    </div>
  </body>

On the same line as for the patch API there are three methods:

* ``xmldiff.main.patch_file()`` takes as input paths to files, or file streams,
  and returns a string with the resulting XML.

* ``xmldiff.main.patch_text()`` takes as input Unicode strings,
  and returns a string with the resulting XML.

* ``xmldiff.main.patch_tree()`` takes as input one edit script,
  (ie a list of actions, see above) and one ``lxml`` tree,
  and returns a patched ``lxml`` tree.

They all return a string with the patched XML tree.
There are currently no configuration parameters for these commands.
