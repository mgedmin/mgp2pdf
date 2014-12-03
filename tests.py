import doctest
import unittest
from cStringIO import StringIO

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


class Tests(unittest.TestCase):

    def test_conversion(self):
        p = mgp2pdf.Presentation(StringIO(sample_mgp), title="Sample")
        pdf = StringIO()
        p.makePDF(pdf)


def test_suite():
    return unittest.TestSuite([
        doctest.DocTestSuite('mgp2pdf'),
        unittest.defaultTestLoader.loadTestsFromName(__name__),
    ])


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
