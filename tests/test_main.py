import io
import os
import sys
import unittest

from lxml import etree
from xmldiff import main, formatting

CURDIR = os.path.split(__file__)[0]
LEFT_FILE = os.path.join(CURDIR, "test_data", "rmldoc.left.xml")
RIGHT_FILE = os.path.join(CURDIR, "test_data", "rmldoc.right.xml")
EXPECTED_FILE = os.path.join(CURDIR, "test_data", "rmldoc.expected.xml")


class MainAPITests(unittest.TestCase):
    def test_api_diff_files(self):
        # diff_files can take filenames
        result1 = main.diff_files(LEFT_FILE, RIGHT_FILE)

        # Or open file streams:
        with open(LEFT_FILE, "rb") as linfile:
            with open(RIGHT_FILE, "rb") as rinfile:
                result2 = main.diff_files(linfile, rinfile)

        self.assertEqual(result1, result2)

        # Give something else, and it fails:
        with self.assertRaises(IOError):
            main.diff_files("<xml1/>", "<xml2/>")

    def test_api_diff_texts(self):
        # diff_text can take bytes
        with open(LEFT_FILE, "rb") as linfile:
            with open(RIGHT_FILE, "rb") as rinfile:
                left = linfile.read()
                right = rinfile.read()
                result1 = main.diff_texts(left, right)

                # And unicode
                result2 = main.diff_texts(left.decode("utf8"), right.decode("utf8"))

                self.assertEqual(result1, result2)

        with open(LEFT_FILE, "rb") as infile:
            with open(RIGHT_FILE, "rb") as infile:
                # Give something else, and it fails:
                with self.assertRaises(TypeError):
                    main.diff_texts(infile, infile)

    def test_api_diff_trees(self):
        # diff_tree can take ElementEtrees
        left = etree.parse(LEFT_FILE)
        right = etree.parse(RIGHT_FILE)
        result1 = main.diff_trees(left, right)

        # And Elements
        result2 = main.diff_trees(left.getroot(), right.getroot())
        self.assertEqual(result1, result2)

        # Give something else, and it fails:
        with self.assertRaises(TypeError):
            main.diff_trees(LEFT_FILE, RIGHT_FILE)

    def test_api_diff_files_with_formatter(self):
        formatter = formatting.XMLFormatter()
        # diff_files can take filenames
        result = main.diff_files(LEFT_FILE, RIGHT_FILE, formatter=formatter)
        # This formatter will insert a diff namespace:
        self.assertIn('xmlns:diff="http://namespaces.shoobx.com/diff"', result)


class MainCLITests(unittest.TestCase):
    def call_run(self, args, command=main.diff_command):
        output = io.StringIO()
        errors = io.StringIO()

        stdout = sys.stdout
        stderr = sys.stderr

        try:
            sys.stdout = output
            sys.stderr = errors

            command(args)
        finally:
            sys.stdout = stdout
            sys.stderr = stderr

        return output.getvalue(), errors.getvalue()

    def test_diff_cli_no_args(self):
        with self.assertRaises(SystemExit):
            stdout, stderr = self.call_run([])

    def test_diff_cli_simple(self):
        curdir = os.path.dirname(__file__)
        filepath = os.path.join(curdir, "test_data")
        file1 = os.path.join(filepath, "insert-node.left.html")
        file2 = os.path.join(filepath, "insert-node.right.html")

        output, errors = self.call_run([file1, file2])
        self.assertEqual(len(output.splitlines()), 3)
        # This should default to the diff formatter:
        self.assertEqual(output[0], "[")

    def test_diff_cli_BOM(self):
        """Test comparison of files encoded with UTF-8 prepended by Byte Order Mark"""
        curdir = os.path.dirname(__file__)
        filepath = os.path.join(curdir, "test_data")
        file1 = os.path.join(filepath, "bom_1.xml")
        file2 = os.path.join(filepath, "bom_2.xml")

        output, errors = self.call_run([file1, file2])
        self.assertEqual(len(output.splitlines()), 1)
        # This should default to the diff formatter:
        self.assertEqual(output[0], "[")

    def test_diff_cli_args(self):
        curdir = os.path.dirname(__file__)
        filepath = os.path.join(curdir, "test_data")
        file1 = os.path.join(filepath, "example.left.html")
        file2 = os.path.join(filepath, "example.right.html")

        # Select a formatter:
        output, errors = self.call_run([file1, file2, "--formatter", "xml"])
        # It gives a very compact output
        self.assertEqual(len(output.splitlines()), 2)
        # Now it's XML
        self.assertEqual(output[0], "<")

        # Don't strip the whitespace keeps the formatting from the source:
        output, errors = self.call_run(
            [file1, file2, "--keep-whitespace", "--formatter", "xml"]
        )
        self.assertEqual(len(output.splitlines()), 13)

        # And stripping and pretty printing gives a longer readable output
        output, errors = self.call_run(
            [file1, file2, "--pretty-print", "--formatter", "xml"]
        )
        self.assertEqual(len(output.splitlines()), 11)

        # The default output gives six lines for six actions
        output, errors = self.call_run([file1, file2, "--ratio-mode", "fast"])
        self.assertEqual(len(output.splitlines()), 6)

        # 'fast' is default, so it's the same output
        output2, errors = self.call_run([file1, file2, "--ratio-mode", "fast"])
        self.assertEqual(output, output2)

        # Accurate is the same in this case, although sometimes it isn't
        output2, errors = self.call_run([file1, file2, "--ratio-mode", "accurate"])
        self.assertEqual(output, output2)

        # But "faster" gives nine actions instead of six
        output, errors = self.call_run([file1, file2, "--ratio-mode", "faster"])
        self.assertEqual(len(output.splitlines()), 9)

        # You can specify unique attributes:
        output, errors = self.call_run(
            [file1, file2, "--unique-attributes", "id,foo,frotz"]
        )
        self.assertEqual(len(output.splitlines()), 6)

        # Or none
        output, errors = self.call_run([file1, file2, "--unique-attributes"])
        self.assertEqual(len(output.splitlines()), 6)

    def test_patch_cli_simple(self):
        curdir = os.path.dirname(__file__)
        filepath = os.path.join(curdir, "test_data")
        patchfile = os.path.join(filepath, "insert-node.diff")
        xmlfile = os.path.join(filepath, "insert-node.left.html")

        output, errors = self.call_run([patchfile, xmlfile], command=main.patch_command)

        expectedfile = os.path.join(filepath, "insert-node.right.html")
        with open(expectedfile) as f:
            expected = f.read()
        self.assertEqual(output, expected)
