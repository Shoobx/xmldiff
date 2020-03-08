"""All major API points and command-line tools"""
import pkg_resources

from argparse import ArgumentParser, FileType
from lxml import etree
from xmldiff import diff, formatting, patch

__version__ = pkg_resources.require("xmldiff")[0].version

FORMATTERS = {
    "diff": formatting.DiffFormatter,
    "xml": formatting.XMLFormatter,
    "old": formatting.XmlDiffFormatter,
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
    normalize = bool(getattr(formatter, "normalize", 1) & formatting.WS_TAGS)
    parser = etree.XMLParser(remove_blank_text=normalize)
    left_tree = parse_method(left, parser)
    right_tree = parse_method(right, parser)
    return diff_trees(
        left_tree, right_tree, diff_options=diff_options, formatter=formatter
    )


def diff_texts(left, right, diff_options=None, formatter=None):
    """Takes two Unicode strings containing XML"""
    return _diff(
        etree.fromstring, left, right, diff_options=diff_options, formatter=formatter
    )


def diff_files(left, right, diff_options=None, formatter=None):
    """Takes two filenames or streams, and diffs the XML in those files"""
    return _diff(
        etree.parse, left, right, diff_options=diff_options, formatter=formatter
    )


def make_diff_parser():
    parser = ArgumentParser(
        description="Create a diff for two XML files.", add_help=False
    )
    parser.add_argument("file1", type=FileType("r"), help="The first input file.")
    parser.add_argument("file2", type=FileType("r"), help="The second input file.")
    parser.add_argument(
        "-h", "--help", action="help", help="Show this help message and exit."
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        help="Display version and exit.",
        version="xmldiff %s" % __version__,
    )
    parser.add_argument(
        "-f",
        "--formatter",
        default="diff",
        choices=list(FORMATTERS.keys()),
        help="Formatter selection.",
    )
    parser.add_argument(
        "-w",
        "--keep-whitespace",
        action="store_true",
        help="Do not strip ignorable whitespace.",
    )
    parser.add_argument(
        "-p",
        "--pretty-print",
        action="store_true",
        help="Try to make XML output more readable.",
    )
    parser.add_argument(
        "-F",
        type=float,
        help="A value between 0 and 1 that determines how "
        "similar nodes must be to match.",
    )
    parser.add_argument(
        "--unique-attributes",
        type=str,
        nargs="?",
        default="{http://www.w3.org/XML/1998/namespace}id",
        help="A comma separated list of attributes "
        "that uniquely identify a node. Can be empty. "
        "Unique attributes for certain elements can "
        "be specified in the format {NS}element@attr.",
    )
    parser.add_argument(
        "--ratio-mode",
        default="fast",
        choices={"accurate", "fast", "faster"},
        help="Choose the node comparison optimization.",
    )
    parser.add_argument(
        "--fast-match", action="store_true", help="A faster, less optimal match run."
    )
    return parser


def _parse_uniqueattrs(uniqueattrs):
    if uniqueattrs is None:
        return []
    return [
        attr if "@" not in attr else attr.split("@", 1)
        for attr in uniqueattrs.split(",")
    ]


def diff_command(args=None):
    parser = make_diff_parser()
    args = parser.parse_args(args=args)

    if args.keep_whitespace:
        normalize = formatting.WS_NONE
    else:
        normalize = formatting.WS_BOTH

    formatter = FORMATTERS[args.formatter](
        normalize=normalize, pretty_print=args.pretty_print
    )

    diff_options = {
        "ratio_mode": args.ratio_mode,
        "F": args.F,
        "fast_match": args.fast_match,
        "uniqueattrs": _parse_uniqueattrs(args.unique_attributes),
    }
    result = diff_files(
        args.file1, args.file2, diff_options=diff_options, formatter=formatter
    )
    print(result)


def patch_tree(actions, tree):
    """Takes an lxml root element or element tree, and a list of actions"""
    patcher = patch.Patcher()
    return patcher.patch(actions, tree)


def patch_text(actions, tree):
    """Takes a string with XML and a string with actions"""
    tree = etree.fromstring(tree)
    actions = patch.DiffParser().parse(actions)
    tree = patch_tree(actions, tree)
    return etree.tounicode(tree)


def patch_file(actions, tree):
    """Takes two filenames or streams, one with XML the other a diff"""
    tree = etree.parse(tree)

    if isinstance(actions, str):
        # It's a string, so it's a filename
        with open(actions) as f:
            actions = f.read()
    else:
        # We assume it's a stream
        actions = actions.read()

    actions = patch.DiffParser().parse(actions)
    tree = patch_tree(actions, tree)
    return etree.tounicode(tree)


def make_patch_parser():
    parser = ArgumentParser(
        description="Patch an XML file with an xmldiff", add_help=False
    )
    parser.add_argument("patchfile", type=FileType("r"), help="An xmldiff diff file.")
    parser.add_argument("xmlfile", type=FileType("r"), help="An unpatched XML file.")
    parser.add_argument(
        "-h", "--help", action="help", help="Show this help message and exit."
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        help="Display version and exit.",
        version="xmldiff %s" % __version__,
    )
    return parser


def patch_command(args=None):
    parser = make_patch_parser()
    args = parser.parse_args(args=args)

    result = patch_file(args.patchfile, args.xmlfile)
    print(result)
