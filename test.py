#!/usr/bin/python

import unittest
import os
import sys
import shutil
import filecmp
import tempfile

from mail2calibre import *

test_email = 'test-calibre-email.txt'
test_book = 'test-book.mobi'

class TestMail2Calibre(unittest.TestCase):
    def setUp(self):
        # create empty library
        self.lib = tempfile.mkdtemp(prefix='mail2calibre-unittest')

    def tearDown(self):
        # remove the library
        shutil.rmtree(self.lib)

    def test_receiving(self):
        with open(test_email, 'r') as fh:
            sys.stdin = fh
            tempfile = receive_attachment()

        self.assertTrue(os.path.isfile(tempfile))
        self.assertGreater(os.path.getsize(tempfile), 0)
        self.assertTrue(filecmp.cmp(tempfile, test_book, shallow=False))

        sys.stdin = sys.__stdin__
        os.unlink(tempfile)

    def test_add_to_library(self):
        book = BookFile(test_book)
        book.library = self.lib

        # check library empty
        (o, e, r) = pipe([calibredb, 'list', '--with-library', self.lib])
        self.assertRegexpMatches(o, '[^\n]*\n[^\n]*\n')

        book.to_library()

        # check book inserted
        (o, e, r) = pipe([calibredb, 'list', '--with-library', self.lib])
        self.assertRegexpMatches(o, 'The Art of War')

        with self.assertRaises(RuntimeError):
            book.to_library()


if __name__ == '__main__':
    verbose_level = sys.argv.count('-v')
    logging.basicConfig(stream=sys.stderr,
       level={0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}[verbose_level])

    unittest.main()
