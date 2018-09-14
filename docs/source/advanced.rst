Advanced Usage
==============

Diffing Formatted Text
----------------------

You can write your own formatter that understands your XML format,
and therefore can apply som intelligence to the format.

One common use case for this is to have more intelligent text handling.
The standard formatters will treat any text as just a value,
and the resulting diff will simply replace one value with another:

.. doctest::
  :options: -ELLIPSIS, +NORMALIZE_WHITESPACE

  >>> from xmldiff import main, formatting
  >>> left = '<body><p>Old Content</p></body>'
  >>> right = '<body><p>New Content</p></body>'
  >>> main.diff_texts(left, right)
  [UpdateTextIn(node='/body/p[1]', text='New Content')]

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
  >>> right = '<body><p>My <i>Fine</i> Content</p></body>'
  >>> result = main.diff_texts(left, right, formatter=formatter)
  >>> print(result)
  <body xmlns:diff="http://namespaces.shoobx.com/diff">
    <p diff:insert="">My <i diff:insert="">Fine</i><diff:insert> Content</diff:insert></p>
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
    <p>My <i diff:insert-formatting="">Fine</i> Content</p>
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
  ...    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  ...    xmlns="http://www.w3.org/1999/xhtml">
  ...
  ...    <xsl:template match="@diff:insert-formatting">
  ...        <xsl:attribute name="class">
  ...          <xsl:value-of select="'insert-formatting'"/>
  ...        </xsl:attribute>
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

The XSLT template above of course only handles one case,
inserted formatting.
A more complete XSLT file is included `here <file:_static/htmlformatter.xslt>`_.

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
    <p>My <i class="insert-formatting">Fine</i> Content</p>
  </body>

You can then add into your CSS files classes that make inserted text green,
deleted text red with an overstrike,
and formatting changes could for example be blue.
This makes it easy to see what has been changed in a HTML document.
