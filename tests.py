import doctest
import unittest


def test_suite():
    return doctest.DocTestSuite('mgp2pdf')


if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
