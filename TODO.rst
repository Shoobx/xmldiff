TO DOs
======

Version 1.0 To Dos
------------------

- Code cleanup:
  * PEP8, especially docstrings

- Modernize package:
  * lxml-based SAX parser.
  * Allow code to be run without C extensions
    (See Zope packages with PyPy support for help.)
    need to reimplement a bunch of C only code in python
    also, the C code gets variables "passed" with `fmes_init`
  * Proper LGPL file headers with copyright notice.

- Systematic test setup.
  * Use Shoobx approach for XML-processing-based testing.

- Bonus: Make some of the variables more readable and rem


Old TODO List for xmldiff
-------------------------

_ report namespaces declaration !
_ support Processing Instruction nodes, CDATA
_ support for XML namespaces
_ option for case insensitive
_ data/document modes ?
_ translate HELP.txt and API.txt to docbook
_ update ezs to make it work with the new internal representation
_ optimizations:
  use tuple instead of list when it's possible
