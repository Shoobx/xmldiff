Contributing to ``xmldiff``
===========================

``xmldiff`` welcomes your help. Replies and responses may be slow, but don't
despair, we will get to you, we will answer your questions and we will
review your pull requests, but nobody has "Maintain ``xmldiff``" as their job
description, so it may take a long time. That's open source.

There are some extremely complex issues deep down in ``xmldiff``, but don't
let that scare you away, there's easy things to do as well.


Setting up a dev environment
----------------------------

To set up a development environment you need a github account, git, and
of course Python with pip installed. You also should have the Python tools
``coverage`` and ``flake8`` installed::

  pip install coverage flake8

Then you need to clone the repository, and install it's dependencies::

  git clone git@github.com:Shoobx/xmldiff.git
  cd xmldiff
  pip install -e .

You should now be able to test your setup by running a few ``make`` commands::

  make test
  make flake

These should both pass with no errors, and then you are set!


Testing
-------

``xmldiff``'s tests are written using ``unittest`` and are discoverable by most test runners.
There is also a ``test`` target in the make file.
The following test runners/commands are known to work:

  * ``make test``

  * ``python setup.py test``

  * ``nosetests``

  * ``pytest``

There is no support for ``tox`` to run test under different Python versions.
This is because Travis will run all supported versions on pull requests in any case,
and having yet another list of supported Python versions to maintain seems unnecessary.
You can either create your own tox.ini file,
or you can install ```spiny`` <https://pypi.org/project/spiny/>`_,
which doesn't require any extra configuration in the normal case,
and will run the tests on all versions that are defined as supported in ``setup.py``:


Pull requests
-------------

Even if you have write permissions to the repository we discourage pushing changes to master.
Make a branch and a pull request, and we'll merge that.

You pull requests should:

  * Add a test that fails before the change is made

  * Keep test coverage at 100%

  * Include an description of the change in ``CHANGES.txt``

  * Sdd you to the contributors list in ``README.txt`` if you aren't already there.


Code quality and conventions
----------------------------

``xmldiff`` aims to have 100% test coverage.
You run a coverage report with ``$ make coverage``.
This will generate a HTML coverage report in ``htmlcov/index.html``

We run flake8 as a part of all Travis test runs,
the correct way to run it is ``$ make flake``,
as this includes only the files that should be covered.


Documentation
-------------

The documentation is written with ``sphinx``.
It and any other files using the ReStructuredText format,
such as README's etc,
are using a one line per sub-sentence structure.
This is so that adding one word to a paragraph will not cause several lines of changes,
as that will make any pull request harder to read.

That means that every sentence and most commas should be followed by a new line,
except in cases where this obviously do not make sense.
As a result of this there is no limits on line length,
but if a line becomes very long you might consider rewriting it to make it more understandable.

You generate the documentation with a make command::

  cd docs
  make html

We will be using (but aren't yet) `Read the Docs <https://readthedocs.org/>`_ to host the documentation.


Implementation details
----------------------

``xmldiff`` is based on `"Change Detection in Hierarchically StructuredS Information" <http://ilpubs.stanford.edu/115/1/1995-46.pdf>`_
by Sudarshan S. Chawathe, Anand Rajaraman, Hector Garcia-Molina, and Jennifer Widom, 1995.
It's not necessary to read and understand that paper in all it's details to help with ``xmldiff``,
but if you want to improve the actual diffing algorithm it is certainly helpful.

I hope to extend this section with an overview of how this library does it's thing.
