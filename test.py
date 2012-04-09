#!/usr/bin/python

import unittest
import os
import sys

from mail2calibre import *

test_file = 'test-calibre-email.txt'

class TestMail2Calibre(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_receiving(self):
        with open(test_file, 'r') as fh:
            sys.stdin = fh
            tempfile = receive_attachment()

        self.assertTrue(os.path.isfile(tempfile))
        self.assertGreater(os.path.getsize(tempfile), 0)

        sys.stdin = sys.__stdin__
        os.unlink(tempfile)


if __name__ == '__main__':
    verbose_level = sys.argv.count('-v')
    logging.basicConfig(stream=sys.stderr,
       level={0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}[verbose_level])

    unittest.main()
