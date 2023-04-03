Changes
=======

2.6 (2023-04-03)
----------------

- Added `InsertNamespace` and `DeleteNamespace` actions for better handling
  of changing namespaces. Should improve any "Unknown namespace prefix"
  errors. Changing the URI of a a namespace prefix is not supported, and will
  raise an error.

2.6b1 (2023-01-12)
------------------

- Used geometric mean for the node_ratio, for better handling of simple nodes.

- Added an experimental --best-match method that is slower, but generate
  smaller diffs when you have many nodes that are similar.

- The -F argument now also affects the --fast-match stage.


2.5 (2023-01-11)
----------------

- Make it possible to adjust the attributes considered when comparing nodes.

- Python versions 3.7 to 3.11 are now supported.

- Improved node matching method, that puts more emphasis similarities than
  differences when weighing attributes vs children.

- Added a parameter to return error code 1 when there are differences between the files

- Added a parameter for ignoring attributes in comparison.

- Solved a bug in xmlpatch in certain namespace situations.

- Added a --diff-encoding parameter to xmlpatch, to support diff-files that are
  not in your system default encoding.


2.4 (2019-10-09)
----------------

- Added an option to pass pairs of (element, attr) as unique
  attributes for tree matching.  Exposed this option on the command
  line, too.


2.3 (2019-02-27)
----------------

- Added a simple ``xmlpatch`` command and API.

- Multiple updates to documentation and code style


2.2 (2018-10-12)
----------------

- A workaround for dealing with top level comments and the xml formatter


2.1 (2018-10-03)
----------------

- Changed the substitution unicode character area to use the Private Use Area
  in BMP(0), to support narrow Python builds

- Added --unique-attributes argument.


2.1b1 (2018-10-01)
------------------

- Added options for faster node comparisons. The "middle" option is now
  default, it had very few changes in matches, but is much faster.

- Implemented a Fast Match algorithm for even faster diffing.

- Speed improvements through caching

- Fixed a bug where MoveNode actions sometimes was in the wrong order

- Added an InsertComment action, as comments require different handling,
  so it's easier to deal with them this way. You can still use DeleteNode and
  UpdateTextIn for them with no special handling.

- When renaming tags the XMLFormatter will mark them with "diff:rename"
  instead of making a new tag and deleting the old.

- Tags will now be moved first, and updated and renamed later, as the new
  tag name or attributes might not be valid in the old location.


2.0 (2018-09-25)
----------------

- A complete, bottom-up, pure-python rewrite

- New easy API

- 100% test coverage

- New output formats:

  - A new default output format with new actions

  - A format intended to be parseable by anyone parsing the old format.

  - XML with changes marked though tags and attributes

- xmldiff 2.0 is significantly slower than xmldiff 0.6 or 1.0,
  the emphasis so far is on correctness, not speed.
