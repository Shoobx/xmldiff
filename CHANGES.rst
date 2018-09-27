Changes
=======

2.1 (unreleased)
----------------

- Added options for faster node comparisons. The "middle" option is now
  default, it had very few changes in matches, but is much faster.

- Implemented a Fast Match algorithm for even faster diffing.

- Fixed a bug where MoveNode actions sometimes was in the wrong order


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
