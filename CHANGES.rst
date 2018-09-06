Changes
=======

2.0b2 (unreleased)
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
