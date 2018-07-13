# Copyright (c) 2000-2010 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
# Copyright (c) 2018 Shoobx.com.
# https://www.shoobx.com/ -- mailto:dev@shoobx.com
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import logging
import sys
import os
import pkg_resources

from xmldiff.fmes import FmesCorrector
from xmldiff.format import InternalPrinter
from xmldiff.input import tree_from_stream
from xmldiff.misc import process_dirs, list_print
from xmldiff.objects import node_repr, N_ISSUE
from xml.sax import SAXParseException

logging.basicConfig()

def process_files(file1, file2, norm_sp, verbose,
                  ext_ges, ext_pes, include_comment,
                  html):
    """
    Computes the diff between two files.
    """
    trees = []
    for fname in (file1, file2):
        with open(fname, 'r') as fhandle:
            try:
                tree = tree_from_stream(fhandle, norm_sp, ext_ges,
                                        ext_pes, include_comment, html)
            except SAXParseException as err:
                print(err)
                return -1
            trees.append(tree)

    if verbose:
        print('Source tree:\n%s' % node_repr(trees[0]))
        print('Destination tree:\n%s' % node_repr(trees[1]))
        print('Source tree has %d nodes' % trees[0][N_ISSUE])
        print('Destination tree has %d nodes' % trees[1][N_ISSUE])

    # output formatter
    formatter = InternalPrinter()
    # choose and apply tree to tree algorithm
    strategy = FmesCorrector(formatter)
    strategy.process_trees(*trees)
    return len(formatter.edit_s)


def parse_args(argv):
    package = pkg_resources.get_distribution("xmldiff")

    parser = argparse.ArgumentParser(
        description=('Tree 2 tree correction between xml documents. '
                     'Extract differences between two xml files. '
                     'It returns a set of primitives to apply on source tree '
                     'to obtain the destination tree.'))
    parser.add_argument('-V', '--version', action='version',
                        version=package.version)
    parser.add_argument('-H', '--html', action='store_true', default=False,
                        help=('input files are HTML instead of XML.'))
    parser.add_argument('-r', '--recursive', action='store_true',
                        default=False,
                        help=('when comparing directories, recursively '
                              'compare any subdirectories found.'))
    parser.add_argument('-v', '--verbose', action='store_true', default=False)
    parser.add_argument('-n', '--not-normalize-spaces', action='store_true',
                        default=False,
                        help=('do not normalize spaces and new lines in text '
                              'and comment nodes.'))
    parser.add_argument('-c', '--exclude-comments', action='store_true',
                        default=False,
                        help=('do not process comment nodes.'))
    parser.add_argument('-g', '--ext-ges', action='store_true', default=False,
                        help=('include all external general (text) entities.'))
    parser.add_argument('-p', '--ext-pes', action='store_true', default=False,
                        help=('include all external parameter entities, '
                              'including the external DTD subset.'))

    parser.add_argument('from_file_or_dir',
                        help=('in'))
    parser.add_argument('to_file_or_dir',
                        help=('out'))

    args = parser.parse_args(argv)
    return args


def run(argv=None):
    """
    Main. To be called with list of command-line arguments (if provided,
    args should not contain the executable as first item)
    """
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)

    fpath1 = args.from_file_or_dir
    fpath2 = args.to_file_or_dir
    normalize_spaces = not args.not_normalize_spaces
    include_comments = not args.exclude_comments
    exit_status = 0
    # if args are directory
    if os.path.isdir(fpath1) and os.path.isdir(fpath2):
        common, deleted, added = process_dirs(fpath1, fpath2, args.recursive)

        list_print(deleted[0], 'FILE:', 'deleted')
        list_print(deleted[1], 'DIRECTORY:', 'deleted')
        list_print(added[0], 'FILE:', 'added')
        list_print(added[1], 'DIRECTORY:', 'added')
        exit_status += sum((len(deleted[0]), len(deleted[1]),
                            len(added[0]), len(added[1])))
        for filename in common[0]:
            print('-' * 80)
            print('FILE: %s' % filename)
            diffs = process_files(
                os.path.join(fpath1, filename),
                os.path.join(fpath2, filename),
                normalize_spaces, args.verbose,
                args.ext_ges, args.ext_pes, include_comments, args.html)
            if diffs:
                exit_status += diffs
    # if args are files
    elif os.path.isfile(fpath1) and os.path.isfile(fpath2):
        exit_status = process_files(
            fpath1, fpath2,
            normalize_spaces, args.verbose,
            args.ext_ges, args.ext_pes, include_comments, args.html)
    else:
        exit_status = -1
        print('%s and %s are not comparable, or not directory '
              'nor regular files' % (fpath1, fpath2))
    sys.exit(exit_status)


if __name__ == '__main__':
    run()
