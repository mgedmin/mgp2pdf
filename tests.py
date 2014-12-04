import doctest
import unittest
from cStringIO import StringIO

import mock

import mgp2pdf


sample_mgp = """\
# This is an MGP file
%%%%%%%%%%% This is also a comment
%page
%nodefault
%left
Hello
%center
Ancient
%right
World!
"""


class SmokeTests(unittest.TestCase):

    def test_conversion(self):
        p = mgp2pdf.Presentation(StringIO(sample_mgp), title="Sample")
        pdf = StringIO()
        p.makePDF(pdf)


class TestSimpleChunk(unittest.TestCase):

    def test_drawOn(self):
        canvas = mock.Mock()
        chunk = mgp2pdf.SimpleChunk()
        x, y = chunk.drawOn(canvas, 10, 20, 100, 200)
        self.assertEqual((x, y), (10, 20))

    def test_split(self):
        canvas = mock.Mock()
        chunk = mgp2pdf.SimpleChunk()
        bits = chunk.split(canvas, 100, 50, 200)
        self.assertEqual(bits, [chunk])

    def test_repr(self):
        chunk = mgp2pdf.SimpleChunk()
        self.assertEqual(str(chunk), '<SimpleChunk>')


class TestImage(unittest.TestCase):

    @mock.patch('mgp2pdf.ImageReader')
    @mock.patch('mgp2pdf.log')
    def test_drawOn_error_handling(self, mock_log, mock_ImageReader):
        mock_ImageReader().getSize.return_value = 50, 75
        canvas = mock.Mock()
        canvas.drawImage.side_effect = IOError('no such file')
        img = mgp2pdf.Image('image.png')
        x, y = img.drawOn(canvas, 10, 20, 100, 200)
        self.assertEqual((x, y), (60, 20))


class TestTextChunk(unittest.TestCase):

    def test_split_when_it_cant(self):
        canvas = mock.Mock()
        canvas.stringWidth = lambda s, font, size: len(s) * 7
        chunk = mgp2pdf.TextChunk("this-is-a-very-long, unsplittable, word",
                                  "Arial", 6, 0, mgp2pdf.parse_color("black"))
        bits = chunk.split(canvas, 1024, 768, 130)
        self.assertEqual(len(bits), 2)
        self.assertEqual(bits[0].text, "this-is-a-very-long,")
        self.assertEqual(bits[1].text, "unsplittable, word")


class TestPresentation(unittest.TestCase):

    def test_preprocess_errors(self):
        p = mgp2pdf.Presentation()
        # %filter expects an argument that is a quoted string
        self.assertRaises(mgp2pdf.MgpSyntaxError, list, p.preprocess(['%filter bad\n', '%endfilter\n']))
        self.assertRaises(mgp2pdf.MgpSyntaxError, list, p.preprocess(['%filter "bad\n', '%endfilter\n']))
        # %endfilter without a matching %filter
        self.assertRaises(mgp2pdf.MgpSyntaxError, list, p.preprocess(['%endfilter\n']))
        # two %filter directives in a row
        self.assertRaises(mgp2pdf.MgpSyntaxError, list, p.preprocess(['%filter "cat"\n', '%filter "mouse"\n', '%endfilter\n']))
        # missing %endfilter at the end
        self.assertRaises(mgp2pdf.MgpSyntaxError, list, p.preprocess(['%filter "cat"\n']))

    @mock.patch('mgp2pdf.log')
    def test_preprocess_safe_mode(self, mock_log):
        p = mgp2pdf.Presentation()
        self.assertEqual(
            list(p.preprocess([
                'A cow says:\n',
                '%filter "cowsay"\n',
                'Hello\n',
                '%endfilter\n',
                '# ta-dah!\n',
            ])), [
                (1, 'A cow says:\n'),
                (2, 'Filtering through "cowsay" disabled, use --unsafe to enable\n'),
                (5, '# ta-dah!\n'),
            ])

    def test_special_directives(self):
        p = mgp2pdf.Presentation()
        args = []
        p._handleSpecialDirective_test = args.append
        p._handleDirectives('%test 5 foo x y, bar "a, b", baz')
        self.assertEqual(args,
                         [['test', '5', 'foo x y', 'bar "a, b"', 'baz']])

    @mock.patch('mgp2pdf.log')
    def test_empty_directive(self, mock_log):
        p = mgp2pdf.Presentation()
        # XXX: "%page,,size 5" doesn't trigger this because _splitDirectives()
        # is buggy and collapses runs of commas.
        p._handleDirectives('%page, ,size 5')

    @mock.patch('mgp2pdf.log')
    def test_unknown_directives(self, mock_log):
        p = mgp2pdf.Presentation()
        p._handleDirectives('%vfcap "foo"')
        p._handleDirectives('%nosuchdirectiveactually')

    @mock.patch('mgp2pdf.log')
    def test_noop_directives(self, mock_log):
        p = mgp2pdf.Presentation()
        p._handleDirectives('%noop')
        p._handleDirectives('%ccolor "#444"')
        p._handleDirectives('%pcache 1 1 0 1"')

    def test_newimage_with_unsupported_flag(self):
        p = mgp2pdf.Presentation()
        self.assertRaises(mgp2pdf.MgpSyntaxError, p._handleDirectives,
                          '%newimage -foo 42 "fail.gif"')

    def test_again_without_mark(self):
        p = mgp2pdf.Presentation()
        self.assertRaises(mgp2pdf.MgpSyntaxError, p._handleDirectives,
                          '%page, again')

    def test_arg_parsing_string_or_number(self):
        p = mgp2pdf.Presentation()
        self.assertEqual(p._parseArgs(["test", '"foo"', '10'], 'SS'), ("foo", 10))

    def test_bad_arguments(self):
        p = mgp2pdf.Presentation()
        self.assertRaises(mgp2pdf.MgpSyntaxError, p._handleDirectives,
                          '%size')
        self.assertRaises(mgp2pdf.MgpSyntaxError, p._handleDirectives,
                          '%font no-quotes')
        self.assertRaises(mgp2pdf.MgpSyntaxError, p._handleDirectives,
                          '%font "no-quote')
        self.assertRaises(mgp2pdf.MgpSyntaxError, p._handleDirectives,
                          '%font no-quote"')

    def test_deffont(self):
        p = mgp2pdf.Presentation()
        p._handleDirectives('%deffont "mono" xfont "Monospace"')
        p._handleDirectives('%deffont "bold" xfont "Sans-bold"')
        p._handleDirectives('%deffont "bolditalic" xfont "Sans-bold-i"')
        p._handleDirectives('%page')
        self.assertRaises(mgp2pdf.MgpSyntaxError, p._handleDirectives,
                          '%deffont "italic" xfont "Sans-regular-i"')

    def test_deffont_unsupported_engine(self):
        p = mgp2pdf.Presentation()
        self.assertRaises(NotImplementedError, p._handleDirectives,
                          '%deffont "B0rk" tex "Computer Modern"')

    @mock.patch('subprocess.Popen')
    def test_deffont_unsupported_font(self, mock_Popen):
        p = mgp2pdf.Presentation()
        # This is seriously theoretical, since fc-match usually picks something
        # as a fallback even if you're missing a font!  This is why we mock.
        mock_Popen().communicate.return_value = ('', '')
        self.assertRaises(SystemExit, p._handleDirectives,
                          '%deffont "B0rk" xfont "No Such Font Srsly No"')

    def test_default(self):
        p = mgp2pdf.Presentation()
        p._handleDirectives('%default 1')
        self.assertEqual(p.defaultDirectives[1], [])
        p._handleDirectives('%default 3 fore "black", center, font "bold", size 6')
        self.assertEqual(p.defaultDirectives[3],
                         ['fore "black"', 'center', 'font "bold"', 'size 6'])
        p._handleDirectives('%page')
        self.assertRaises(mgp2pdf.MgpSyntaxError, p._handleDirectives,
                          '%default 1 left')

    def test_tab(self):
        p = mgp2pdf.Presentation()
        p._handleDirectives('%tab 1')
        self.assertEqual(p.tabDirectives[1], [])
        p._handleDirectives('%tab 2 prefix "  ", icon box black 50')
        self.assertEqual(p.tabDirectives[2],
                         ['prefix "  "', 'icon box black 50'])
        p._handleDirectives('%tab 2 prefix "  ", icon box black 50')
        self.assertEqual(p.tabDirectives[2],
                         ['prefix "  "', 'icon box black 50'])
        p._handleDirectives('%page')
        self.assertRaises(mgp2pdf.MgpSyntaxError, p._handleDirectives,
                          '%tab 1 left')

    def test_text_in_preamble(self):
        p = mgp2pdf.Presentation()
        self.assertRaises(mgp2pdf.MgpSyntaxError, p._handleText, 'text in preamble')

    def test_backslash_escaping(self):
        p = mgp2pdf.Presentation()
        p._handleDirectives('%page')
        p._handleText("\\# This starts with a hash and has a \\\\")
        self.assertEqual(str(p),
                         "--- Slide 1 ---\n"
                         "# This starts with a hash and has a \\\n")
        # The test is incomplete: \xHH is not yet supported


@mock.patch('sys.stdout', StringIO())
@mock.patch('sys.stderr', StringIO())
class TestMain(unittest.TestCase):

    def test_no_args(self):
        self.assertRaises(SystemExit, mgp2pdf.main, [])

    def test_output_file_when_multiple_args(self):
        self.assertRaises(SystemExit, mgp2pdf.main,
                          ['x.mgp', 'y.mgp', '-o', 'z.pdf'])

    @mock.patch('mgp2pdf.Presentation')
    def test_input_error_handling(self, mock_Presentation):
        mock_Presentation().load.side_effect = mgp2pdf.MgpSyntaxError('no split infinitives plz')
        mgp2pdf.main(['file1.mgp'])

    @mock.patch('mgp2pdf.Presentation')
    def test_output_error_handling(self, mock_Presentation):
        mock_Presentation().makePDF.side_effect = IOError('cannot write there')
        mgp2pdf.main(['file1.mgp', '-o', '/tmp/file1.pdf'])


def test_suite():
    return unittest.TestSuite([
        doctest.DocTestSuite('mgp2pdf'),
        unittest.defaultTestLoader.loadTestsFromName(__name__),
    ])


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
