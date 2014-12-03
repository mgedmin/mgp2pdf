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


def test_suite():
    return unittest.TestSuite([
        doctest.DocTestSuite('mgp2pdf'),
        unittest.defaultTestLoader.loadTestsFromName(__name__),
    ])


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
