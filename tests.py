import doctest
import unittest
from cStringIO import StringIO

import mock

import mgp2pdf


sample_mgp = """\
# This is an MGP file
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
                'A cow says:\n',
                'Filtering through "cowsay" disabled, use --unsafe to enable\n',
                '# ta-dah!\n',
            ])


def test_suite():
    return unittest.TestSuite([
        doctest.DocTestSuite('mgp2pdf'),
        unittest.defaultTestLoader.loadTestsFromName(__name__),
    ])


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
