Advanced Usage
==============

Diffing Formatted Text
----------------------

You can write your own formatter that understands your XML format,
and therefore can apply some intelligence to the format.

One common use case for this is to have more intelligent text handling.
The standard formatters will treat any text as just a value,
and the resulting diff will simply replace one value with another:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> from xmldiff import main, formatting
  >>> left = '<body><p>Old Content</p></body>'
  >>> right = '<body><p>New Content</p></body>'
  >>> main.diff_texts(left, right)
  [UpdateTextIn(node='/body/p[1]', text='New Content', oldtext='Old Content')]

The ``xml`` formatter will set tags around the text marking it as inserted or deleted:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> formatter=formatting.XMLFormatter()
  >>>
  >>> left = '<body><p>Old Content</p></body>'
  >>> right = '<body><p>New Content</p></body>'
  >>> result = main.diff_texts(left, right, formatter=formatter)
  >>> print(result)
  <body xmlns:diff="http://namespaces.shoobx.com/diff">
  <p><diff:delete>Old</diff:delete><diff:insert>New</diff:insert> Content</p>
  </body>

But if your XML format contains text with formats,
the output can in some cases be less than useful,
especially in the case where formatting is added:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> left = '<body><p>My Fine Content</p></body>'
  >>> right = '<body><p><b>My <i>Fine</i> Content</b></p></body>'
  >>> result = main.diff_texts(left, right, formatter=formatter)
  >>> print(result)
  <body xmlns:diff="http://namespaces.shoobx.com/diff">
    <p diff:insert="">
      <b diff:insert="" diff:rename="p">My <i diff:insert="">Fine</i><diff:insert> Content</diff:insert></b>
    </p>
    <p diff:delete="">My Fine Content</p>
  </body>
  <BLANKLINE>

Notice how the the whole text was inserted with formatting,
and the whole unformatted text was deleted.
The XMLFormatter supports a better handling of text with the ``text_tags`` and ``formatting_tags`` parameters. Here is a simple and incomplete example with some common HTML tags:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> formatter=formatting.XMLFormatter(
  ...     text_tags=('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'),
  ...     formatting_tags=('b', 'u', 'i', 'strike', 'em', 'super',
  ...                      'sup', 'sub', 'link', 'a', 'span'))
  >>> result = main.diff_texts(left, right, formatter=formatter)
  >>> print(result)
  <body xmlns:diff="http://namespaces.shoobx.com/diff">
    <p>
      <b diff:insert-formatting="">My <i diff:insert-formatting="">Fine</i> Content</b>
    </p>
  </body>

This gives a result that flags the ``<i>`` tag as new formatting.
This more compact output is much more useful and easier to transform into a visual output.


Making a Visual Diff
--------------------

XML and HTML views will of course ignore all these ``diff:`` tags and attributes.
What we want with the HTML output above is to transform the ``diff:insert-formatting`` attribute into something that will make the change visible.
We can achieve that by applying XSLT before the ``render()`` method in the formatter.
This requires subclassing the formatter:


.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> import lxml.etree
  >>> XSLT = u'''<?xml version="1.0"?>
  ... <xsl:stylesheet version="1.0"
  ...    xmlns:diff="http://namespaces.shoobx.com/diff"
  ...    xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  ...
  ...    <xsl:template match="@diff:insert-formatting">
  ...        <xsl:attribute name="class">
  ...          <xsl:value-of select="'insert-formatting'"/>
  ...        </xsl:attribute>
  ...    </xsl:template>
  ...
  ...    <xsl:template match="diff:delete">
  ...        <del><xsl:apply-templates /></del>
  ...    </xsl:template>
  ...
  ...    <xsl:template match="diff:insert">
  ...        <ins><xsl:apply-templates /></ins>
  ...    </xsl:template>
  ...
  ...    <xsl:template match="@* | node()">
  ...      <xsl:copy>
  ...        <xsl:apply-templates select="@* | node()"/>
  ...      </xsl:copy>
  ...    </xsl:template>
  ... </xsl:stylesheet>'''
  >>> XSLT_TEMPLATE = lxml.etree.fromstring(XSLT)
  >>> class HTMLFormatter(formatting.XMLFormatter):
  ...     def render(self, result):
  ...         transform = lxml.etree.XSLT(XSLT_TEMPLATE)
  ...         result = transform(result)
  ...         return super(HTMLFormatter, self).render(result)

The XSLT template above of course only handles a few cases,
like inserted formatting and insert and delete tags (used below).
A more complete XSLT file is included `here <https://github.com/Shoobx/xmldiff/blob/master/docs/source/static/htmlformatter.xslt>`_.

Now use that formatter in the diffing:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> formatter = HTMLFormatter(
  ...     text_tags=('p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li'),
  ...     formatting_tags=('b', 'u', 'i', 'strike', 'em', 'super',
  ...                      'sup', 'sub', 'link', 'a', 'span'))
  >>> result = main.diff_texts(left, right, formatter=formatter)
  >>> print(result)
  <body xmlns:diff="http://namespaces.shoobx.com/diff">
    <p>
      <b class="insert-formatting">My <i class="insert-formatting">Fine</i> Content</b>
    </p>
  </body>

You can then add into your CSS files classes that make inserted text green,
deleted text red with an overstrike,
and formatting changes could for example be blue.
This makes it easy to see what has been changed in a HTML document.


Performance Options
-------------------

The performance options available will not just change the performance,
but can also change the result.
The result will not necessarily be worse,
it will just be less accurate.
In some cases the less accurate result might actually be preferrable.
As an example we take the following HTML codes:


.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> left = u"""<html><body>
  ...   <p>The First paragraph</p>
  ...   <p>A Second paragraph</p>
  ...   <p>Last paragraph</p>
  ... </body></html>"""
  >>> right = u"""<html><body>
  ...   <p>Last paragraph</p>
  ...   <p>A Second paragraph</p>
  ...   <p>The First paragraph</p>
  ... </body></html>"""
  >>> result = main.diff_texts(left, right)
  >>> result
  [MoveNode(node='/html/body/p[1]', target='/html/body[1]', position=2),
   MoveNode(node='/html/body/p[1]', target='/html/body[1]', position=1)]

We here see that the differ finds that two paragraphs needs to be moved.
Don't be confused that it says ``p[1]`` in both cases.
That just means to move the first paragraph,
and in the second case that first paragraph has already been moved and is now last.

If we format that diff to XML with the XMLFormatter,
we get output that marks these paragraphs as deleted and then inserted later.

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> formatter = HTMLFormatter(
  ...     normalize=formatting.WS_BOTH)
  >>> result = main.diff_texts(left, right, formatter=formatter)
  >>> print(result)
  <html xmlns:diff="http://namespaces.shoobx.com/diff">
    <body>
      <p diff:delete="">The First paragraph</p>
      <p diff:delete="">A Second paragraph</p>
      <p>Last paragraph</p>
      <p diff:insert="">A Second paragraph</p>
      <p diff:insert="">The First paragraph</p>
    </body>
  </html>

Let's try diffing the same HTML with the fast match algorithm:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> result = main.diff_texts(left, right,
  ...     diff_options={'fast_match': True})
  >>> result
  [UpdateTextIn(node='/html/body/p[1]', text='Last paragraph', oldtext='The First paragraph'),
   UpdateTextIn(node='/html/body/p[3]', text='The First paragraph', oldtext='Last paragraph')]

Now we instead got two update actions.
This means the resulting HTML is quite different:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> result = main.diff_texts(left, right,
  ...     diff_options={'fast_match': True},
  ...     formatter=formatter)
  >>> print(result)
  <html xmlns:diff="http://namespaces.shoobx.com/diff">
    <body>
      <p><del>The Fir</del><ins>La</ins>st paragraph</p>
      <p>A Second paragraph</p>
      <p><del>La</del><ins>The Fir</ins>st paragraph</p>
    </body>
  </html>

The texts are updated instead of deleting and then reinserting the whole paragraphs.
This makes the visual output more readable.
Also note that the XSLT in this case replaced the ``<diff:insert>`` and ``<diff:delete>`` tags with ``<ins>`` and ``<del>`` tags.

This is a contrived example, though.
If you are using ``xmldiff`` to generate a visual diff,
you have to experiment with performance flags to find the best combination of speed and output for your case.
