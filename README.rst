========
XML Diff
========

.. image:: https://travis-ci.org/Shoobx/xmldiff.png?branch=master
   :target: https://travis-ci.org/Shoobx/xmldiff

.. image:: https://coveralls.io/repos/github/Shoobx/xmldiff/badge.svg?branch=master
   :target: https://coveralls.io/github/Shoobx/xmldiff?branch=master

.. image:: https://img.shields.io/pypi/v/xmldiff.svg
    :target: https://pypi.python.org/pypi/xmldiff

.. image:: https://img.shields.io/pypi/pyversions/xmldiff.svg
    :target: https://pypi.python.org/pypi/xmldiff/

.. image:: https://api.codeclimate.com/v1/badges/b5a94d8f61fdff1e3214/maintainability
   :target: https://codeclimate.com/github/Shoobx/xmldiff/maintainability
   :alt: Maintainability

Xmldiff is a utility for extracting differences between two xml files. It
returns a set of primitives to apply on source tree to obtain the destination
tree.

The implementation is based on `Change detection in hierarchically structured
information`, by S. Chawathe, A. Rajaraman, H. Garcia-Molina and J. Widom,
Stanford University, 1996

Installation
------------

To install the latest release:

.. code:: bash

    pip install xmldiff


To install the development version:

.. code:: bash

    git clone https://github.com/Shoobx/xmldiff.git
    cd xmldiff
    virtualenv ./.venv
    ./.venv/bin/python setup.py install

Then to compare two given XML files:

.. code:: bash

    ./.venv/bin/xmldiff 1.xml 2.xml


Running tests
-------------

To run the test suite for all python versions:

.. code:: bash

    tox
