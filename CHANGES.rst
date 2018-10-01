Changes
=======

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
