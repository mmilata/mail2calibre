#!/usr/bin/python

import unittest
import shutil
import filecmp

from mail2calibre import *

test_email = 'test-calibre-email.txt'
test_book = 'test-book.mobi'
test_book_author = 'Sunzi 6th cent. B.C.'
test_book_title = 'The Art of War'

class TestMail2Calibre(unittest.TestCase):
    def setUp(self):
        # create empty library
        self.libdir = tempfile.mkdtemp(prefix='mail2calibre-unittest')
        self.lib = Library(self.libdir)

    def tearDown(self):
        # remove the library
        shutil.rmtree(self.libdir)

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

        book.get_meta()
        self.assertTrue(self.lib.is_empty())

        self.lib.add_book(book)
        self.assertFalse(self.lib.is_empty())
        self.assertIsNotNone(self.lib.book_id(test_book_author, test_book_title))

        with self.assertRaises(RuntimeError):
            self.lib.add_book(book)

    def test_conversion(self):
        book = BookFile(test_book)
        newbook = book.convert_to('epub')

        self.assertTrue(os.path.isfile(newbook.fname))
        self.assertEqual(newbook.suffix, 'epub')
        self.assertNotEqual(book.fname, newbook.fname)
        self.assertFalse(filecmp.cmp(book.fname, newbook.fname, shallow=False))

        newbook.delete()

    def test_add_format(self):
        book = BookFile(test_book)

        self.lib.add_book(book)
        book_id = self.lib.book_id(test_book_author, test_book_title)

        self.assertIsNotNone(book_id)

        (formats1, _, _) = self.lib.command('list', '-f', 'formats')

        new_book = book.convert_to('epub')
        self.lib.add_format(book_id, new_book)

        (formats2, _, _) = self.lib.command('list', '-f', 'formats')

        # just test that the list of the formats is longer ...
        self.assertGreater(len(formats2), len(formats1))


if __name__ == '__main__':
    verbose_level = sys.argv.count('-v')
    logging.basicConfig(stream=sys.stderr,
        level={0: logging.ERROR, 1: logging.INFO, 2: logging.DEBUG}[verbose_level])

    unittest.main()
