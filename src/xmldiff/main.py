#!/usr/bin/python
# Copyright (c) 2001-2010 LOGILAB S.A. (Paris, FRANCE).
# http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.

import sys
import os
import getopt

def usage(pgm):
    """Print usage"""
    print 'USAGE:'
    print "\t"+pgm, '[OPTIONS] from_file to_file'
    print "\t"+pgm, '[OPTIONS] [-r] from_directory to_directory'
    print """
Extract differences between two xml files. It returns a set of
primitives to apply on source tree to obtain the destination tree.

OPTIONS:
  -h, --help
     display this help message and exit.
  -V, --version
     display version number and exit

  -H, --html
     input files are HTML instead of XML
  -r, --recursive
     when comparing directories, recursively compare any
     subdirectories found.

  -e encoding, --encoding=encoding
     specify the encoding to use for output. Default is UTF-8

  -n, --not-normalize-spaces
     do not normalize spaces and new lines in text and comment nodes.
  -c, --exclude-comments
     do not process comment nodes
  -g, --ext-ges
     include all external general (text) entities.
  -p, --ext-pes
     include all external parameter entities, including the external DTD
     subset.

  --profile=file
     display an execution profile (run slower with this option),
     profile saved to file (binarie form).
"""

def process_files(file1, file2, norm_sp, verbose,
                  ext_ges, ext_pes, include_comment, encoding,
                  html):
    """
    Computes the diff between two files.
    """
    from xml.sax import SAXParseException
    try:
        fh1, fh2 = open(file1, 'r'), open(file2, 'r')
    except IOError, msg :
        sys.stderr.write(str(msg) + '\n')
        return -1
    # convert xml files to tree
    try:
        from xmldiff.input import tree_from_stream
        tree1 = tree_from_stream(fh1, norm_sp, ext_ges,
                                 ext_pes, include_comment,
                                 encoding, html)
        tree2 = tree_from_stream(fh2, norm_sp, ext_ges,
                                 ext_pes, include_comment,
                                 encoding, html)
        fh1.close ()
        fh2.close ()
    except SAXParseException, msg:
        print msg
        return -1

    if verbose:
        from xmldiff.objects import node_repr, N_ISSUE, N_CHILDS
        print "Source tree\n", node_repr(tree1)
        print "Destination tree\n", node_repr(tree2)
        print 'Source tree has', tree1[N_ISSUE], 'nodes'
        print 'Destination tree has', tree2[N_ISSUE], 'nodes'
    # output formatter
    from xmldiff.format import InternalPrinter
    formatter = InternalPrinter()
    # choose and apply tree to tree algorithm
    from xmldiff.fmes import FmesCorrector
    # import gc
    # gc.set_debug(gc.DEBUG_LEAK|gc.DEBUG_STATS)
    strategy = FmesCorrector(formatter)
    strategy.process_trees(tree1, tree2)
    return len(formatter.edit_s)


def run(args=None):
    """
    Main. To be called with list of command-line arguments (if provided,
    args should not contain the executable as first item)

    FIXME: use optparse and remove usage() ?
    """
    if args is None:
        pgm = sys.argv[0]
        args = sys.argv[1:]
    else:
        pgm = 'xmldiff'
    s_opt = 'Hrncgpe:xzhvV'
    l_opt = ['html', 'recursive',
             'not-normalize-space','exclude-comments','ext-ges','ext-pes'
             'encoding=',
             'help', 'verbose', 'version', 'profile=']
    # process command line options
    try:
        (opt, args) = getopt.getopt(args, s_opt, l_opt)
    except getopt.error:
        sys.stderr.write('Unkwown option')
        sys.exit(-1)
    recursive, html = 0, 0
    xupd, ezs, verbose = 0, 0, 0
    norm_sp, include_comment, ext_ges, ext_pes = 1, 1, 0, 0
    encoding = 'UTF-8'
    prof = ''
    for o in opt:
        if o[0] == '-r' or o[0] == '--recursive':
            recursive = 1
        elif o[0] == '-H' or o[0] == '--html':
            html = 1
        elif o[0] == '-n' or o[0] == '--not-normalize-space':
            norm_sp = 0
        elif o[0] == '-c' or o[0] == '--exclude-comments':
            include_comment = 0
        elif o[0] == '-g' or o[0] == '--ext-ges':
            ext_ges = 1
        elif o[0] == '-p' or o[0] == '--ext-pes':
            ext_pes = 1
        elif o[0] == '-e' or o[0] == '--encoding':
            encoding = o[1]
        elif o[0] == '-v' or o[0] == '--verbose':
            verbose = 1
        elif o[0] == '-p' or o[0] == '--profile':
            prof = o[1]
        elif o[0] == '-h' or o[0] == '--help':
            usage(pgm)
            sys.exit(0)
        elif o[0] == '-V' or o[0] == '--version':
            from xmldiff.__pkginfo__ import modname, version
            print '%s version %s' % (modname, version)
            sys.exit(0)
    if len(args) != 2:
        usage(pgm)
        sys.exit(-2)
    fpath1, fpath2 = args[0], args[1]
    exit_status = 0
    # if args are directory
    if os.path.isdir(fpath1) and os.path.isdir(fpath2):
        from xmldiff.misc import process_dirs, list_print
        common, deleted, added = process_dirs(fpath1, fpath2, recursive)

        list_print(deleted[0], 'FILE:', 'deleted')
        list_print(deleted[1], 'DIRECTORY:', 'deleted')
        list_print(added[0], 'FILE:', 'added')
        list_print(added[1], 'DIRECTORY:', 'added')
        exit_status += sum((len(deleted[0]), len(deleted[1]),
                            len(added[0]), len(added[1])))
        for filename in common[0]:
            print '-'*80
            print 'FILE:', filename
            diffs = process_files(os.path.join(fpath1, filename),
                                  os.path.join(fpath2, filename),
                                  norm_sp, xupd, ezs, verbose,
                                  ext_ges, ext_pes, include_comment,
                                  encoding, html)
            if diffs:
                exit_status += diffs
    # if  args are files
    elif os.path.isfile(fpath1) and os.path.isfile(fpath2):
        if prof:
            import profile, pstats, time
            from maplookup import fmes_end,fmes_init, fmes_node_equal, has_couple, match_end, partner, lcs2
            import maplookup
            # replaces cfunction in maplookup by python wrappers
            def fmes_end_w(*args):
                return fmes_end(*args)
            maplookup.fmes_end = fmes_end_w

            def fmes_init_w(*args):
                return fmes_init(*args)
            maplookup.fmes_init = fmes_init_w

            def fmes_node_equal_w(*args):
                return fmes_node_equal(*args)
            maplookup.fmes_node_equal = fmes_node_equal_w

            def has_couple_w(*args):
                return has_couple(*args)
            maplookup.has_couple = has_couple_w

            def match_end_w(*args):
                return match_end(*args)
            maplookup.match_end = match_end_w

            def partner_w(*args):
                return partner(*args)
            maplookup.partner = partner_w

            def lcs2_w(*args):
                return lcs2(*args)
            maplookup.lcs2 = lcs2_w

            t = time.clock()
            profiler = profile.Profile()
            profiler.runctx('process_files(%r,%r,%r,%r,%r,%r,%r,%r,%r,%r,%r)'% (
              fpath1, fpath2, norm_sp, xupd, ezs, verbose, ext_ges, ext_pes,
              include_comment, encoding, html), globals(), locals() )
            profiler.dump_stats( prof )
            print 'Time:',`time.clock()-t`
            p = pstats.Stats(prof)
            p.sort_stats('time','calls').print_stats(.25)
            p.sort_stats('cum','calls').print_stats(.25)

        else:
            exit_status = process_files(fpath1, fpath2,
                                        norm_sp, xupd, ezs, verbose,
                                        ext_ges, ext_pes, include_comment,
                                        encoding, html)
    else:
        exit_status = -1
        print fpath1, 'and', fpath2, \
              'are not comparable, or not directory nor regular files'
    sys.exit(exit_status)

if __name__ == '__main__':
    run()
