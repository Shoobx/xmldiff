"""All major API points and command-line tools"""
import pkg_resources

from argparse import ArgumentParser, FileType
from lxml import etree
from xmldiff import diff, formatting

__version__ = pkg_resources.require("xmldiff")[0].version

FORMATTERS = {
    'diff': formatting.DiffFormatter,
    'xml': formatting.XMLFormatter,
    'old': formatting.XmlDiffFormatter,
}


def diff_trees(left, right, F=None, uniqueattrs=None, formatter=None):
    """Takes two lxml root elements or element trees"""
    if formatter is not None:
        formatter.prepare(left, right)
    differ = diff.Differ(F=F, uniqueattrs=uniqueattrs)
    diffs = differ.diff(left, right)

    if formatter is None:
        return list(diffs)

    return formatter.format(diffs, left)


def diff_texts(left, right, F=None, uniqueattrs=None, formatter=None):
    """Takes two Unicode strings containing XML"""
    normalize = bool(getattr(formatter, 'normalize', 1) & formatting.WS_TAGS)
    parser = etree.XMLParser(remove_blank_text=normalize)
    left_tree = etree.fromstring(left, parser)
    right_tree = etree.fromstring(right, parser)
    return diff_trees(left_tree, right_tree, F=F, uniqueattrs=uniqueattrs,
                      formatter=formatter)


def diff_files(left, right, F=None, uniqueattrs=None, formatter=None):
    """Takes two filenames or streams, and diffs the XML in those files"""
    normalize = bool(getattr(formatter, 'normalize', 1) & formatting.WS_TAGS)
    parser = etree.XMLParser(remove_blank_text=normalize)
    left_tree = etree.parse(left, parser)
    right_tree = etree.parse(right, parser)
    return diff_trees(left_tree, right_tree, F=F, uniqueattrs=uniqueattrs,
                      formatter=formatter)


def make_parser():
    parser = ArgumentParser(description='Create a diff for two XML files.')
    parser.add_argument('file1', type=FileType('r'),
                        help='the first input file')
    parser.add_argument('file2', type=FileType('r'),
                        help='the second input file')
    parser.add_argument('-f', '--formatter', default='diff',
                        choices=list(FORMATTERS.keys()),
                        help='formatter selection')
    parser.add_argument('-w', '--keep-whitespace', action='store_true',
                        help="do not strip ignorable whitespace")
    parser.add_argument('-p', '--pretty-print', action='store_true',
                        help="try to make XML output more readable")
    parser.add_argument('-v', '--version', action='version',
                        help='display version and exit.',
                        version="xmldiff %s" % __version__)
    return parser


def run(args=None):
    parser = make_parser()
    args = parser.parse_args(args=args)

    if args.keep_whitespace:
        normalize = formatting.WS_NONE
    else:
        normalize = formatting.WS_BOTH

    formatter = FORMATTERS[args.formatter](normalize=normalize,
                                           pretty_print=args.pretty_print)
    result = diff_files(args.file1, args.file2, formatter=formatter)
    print(result)
