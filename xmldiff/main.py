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


def diff_trees(left, right, diff_options=None, formatter=None):
    """Takes two lxml root elements or element trees"""
    if formatter is not None:
        formatter.prepare(left, right)
    if diff_options is None:
        diff_options = {}
    differ = diff.Differ(**diff_options)
    diffs = differ.diff(left, right)

    if formatter is None:
        return list(diffs)

    return formatter.format(diffs, left)


def _diff(parse_method, left, right, diff_options=None, formatter=None):
    normalize = bool(getattr(formatter, 'normalize', 1) & formatting.WS_TAGS)
    parser = etree.XMLParser(remove_blank_text=normalize)
    left_tree = parse_method(left, parser)
    right_tree = parse_method(right, parser)
    return diff_trees(left_tree, right_tree, diff_options=diff_options,
                      formatter=formatter)


def diff_texts(left, right, diff_options=None, formatter=None):
    """Takes two Unicode strings containing XML"""
    return _diff(etree.fromstring, left, right,
                 diff_options=diff_options, formatter=formatter)


def diff_files(left, right, diff_options=None, formatter=None):
    """Takes two filenames or streams, and diffs the XML in those files"""
    return _diff(etree.parse, left, right,
                 diff_options=diff_options, formatter=formatter)


def make_parser():
    parser = ArgumentParser(description='Create a diff for two XML files.')
    parser.add_argument('file1', type=FileType('r'),
                        help='the first input file')
    parser.add_argument('file2', type=FileType('r'),
                        help='the second input file')
    parser.add_argument('-v', '--version', action='version',
                        help='display version and exit.',
                        version="xmldiff %s" % __version__)
    parser.add_argument('-f', '--formatter', default='diff',
                        choices=list(FORMATTERS.keys()),
                        help='formatter selection')
    parser.add_argument('-w', '--keep-whitespace', action='store_true',
                        help="do not strip ignorable whitespace")
    parser.add_argument('-p', '--pretty-print', action='store_true',
                        help="try to make XML output more readable")
    parser.add_argument('-F', type=float,
                        help="determines how similar nodes must be to match")
    parser.add_argument('--ratio-mode', default='fast',
                        choices={'accurate', 'fast', 'faster'},
                        help="choose the node comparison optimization")
    parser.add_argument('--fast-match', action='store_true',
                        help="a faster, less optimal match run")
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
    diff_options = {'ratio_mode': args.ratio_mode,
                    'F': args.F,
                    'fast_match': args.fast_match}
    result = diff_files(args.file1, args.file2, diff_options=diff_options,
                        formatter=formatter)
    print(result)
