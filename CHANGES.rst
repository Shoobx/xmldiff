Changes
=======

2.0b6 (2018-09-13)
------------------

- Release of 2.0b5 failed, re-releasing.


2.0b5 (2018-09-13)
------------------

- Many more edge case bugs


2.0b4 (2018-09-12)
------------------

- Fixed some edge case bugs


2.0b3 (2018-09-11)
------------------

- Replaced the example RMLFormatter with a more generic HTML formatter,
  although it only handles HTML snippets at the moment.

- Added a RenameNodeAction, to get rid of an edge case of a node
  tail appearing twice.


2.0b2 (2018-09-06)
------------------

- Documentation

- The diff formatter now handles the --keep-whitespace argument

- Added a ``--version`` argument


2.0b1 (2018-09-03)
------------------

- A complete, bottom-up, pure-python rewrite

- New easy API

- New output formats:

  - A list of actions (similar but not compatible with the old format)

  - XML with changes marked though tags and attributes

  - RML aware XML where tags containing text are semantically diffed, useful
    for human output such as converting to HTML or PDF

- 100% test coverage
