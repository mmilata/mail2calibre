#!/usr/bin/python

import os
import re
import sys
import email
import logging
import tempfile
import subprocess

# settings
logfile = 'mail2calibre.log'
lib_path = '/calibre-library'
# formats that are accepted and the book is converted to
suffixes = ['mobi', 'epub']

calibredb = 'calibredb'
ebconvert = 'ebook-convert'
ebmeta = 'ebook-meta'

def pipe(args, stdin=None, can_fail=False):
    logging.debug('Running {0}'.format(args))
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (out, err) = p.communicate(stdin)

    logging.debug('Finished, return code: {0}'.format(p.returncode))
    if out:
        logging.debug('Standard output:\n{0}'.format(out))
    if err:
        logging.debug('Standard error :\n{0}'.format(err))

    if (not can_fail) and p.returncode != 0:
        raise RuntimeError('Child process returned exit code {0}'.format(p.returncode))

    return (out, err, p.returncode)

def fsuf(fname):
    return fname.split('.')[-1]

def receive_attachment():
    # read message
    e = email.message_from_file(sys.stdin)
    logging.info('Processing message: {0}'.format(e.get('Subject', '[no subject available]')))

    # find part that looks like a book
    for part in e.walk():
        fname = part.get_filename()
        ctype = part.get_content_type()
        if fname and ('.' in fname) and (fsuf(fname) in suffixes):
            logging.info('Found part "{0}" of type {1}'.format(fname, ctype))
            break
    else:
        logging.error('No suitable attachment found')
        raise RuntimeError('No attachment found')

    suf = fsuf(fname)

    # write it to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix=('.'+suf), delete=False) as f:
        f.write(part.get_payload(decode=True))

    return f.name

class Library(object):
    def __init__(self, dname):
        self.directory = dname

    def command(self, *args):
        cmd = [calibredb]
        cmd.extend(args)
        cmd.extend(['--with-library', self.directory])
        return pipe(cmd)

    # used in tests
    def is_empty(self):
        (o, _, _) = self.command(
            'list',
            '-f', 'uuid'
        )

        return (o == 'id uuid \n\n')

    def book_id(self, author, title):
        author = '"={0}"'.format(author) #TODO: proper escaping
        title  = '"={0}"'.format(title)
        (o, _, _) = self.command(
            'list',
            '-s', 'author:{0} title:{1}'.format(author, title),
            '-w', '9000',
            '-f', 'uuid'
        )

        lines = o.splitlines()

        if len(lines) > 3:
            raise RuntimeError('Query found more than one book')
        elif len(lines) == 3:
            return int(lines[1].split()[0])
        else:
            return None

    def add_book(self, book):
        logging.info('Adding {0} to library'.format(book.fname))
        (out, _, _) = self.command('add', book.fname)

        if 'following books were not added' in out.splitlines()[0]:
            logging.warning('Book not inserted - already exists in the library')
            raise RuntimeError('Book already exists in the library')

    # overwrites the format if it already exists
    def add_format(self, book_id, new_book):
        new_file = new_book.fname
        logging.info('Adding new format for book {0} from file {1}'.format(book_id, new_file))
        self.command('add_format', str(book_id), new_file)

class BookFile(object):
    """
    File containing book. Exists independently of the library.
    """
    def __init__(self, fname):
        self.fname = fname
        self.suffix = fsuf(fname)

        assert self.suffix in suffixes

    def convert_to(self, fmt):
        logging.info('Converting {0} to format {1}'.format(self.fname, fmt))
        newname = self.fname[:-len(self.suffix)]
        newname += fmt

        (_, _, r) = pipe([ebconvert, self.fname, newname], can_fail=True)
        if r != 0:
            raise RuntimeError('Conversion failed')

        return BookFile(newname)

    def get_meta(self):
        logging.info('Reading metadata for {0}'.format(self.fname))
        (o, _, _) = pipe([ebmeta, self.fname])

        res = dict()

        for line in o.splitlines():
            m = re.match('^Title\s+: (.*)$', line)
            if m:
                res['title'] = m.group(1)

            m = re.match('^Author\(s\)\s+: (.*)$', line)
            if m:
                res['author'] = m.group(1)

        if res.has_key('title') and res.has_key('author'):
            return res
        else:
            logging.warning('Required metadata not present')
            raise RuntimeError('Unable to parse metadata')

    def delete(self):
        os.unlink(self.fname)
        self.fname = None

if __name__ == '__main__':

    logging.basicConfig(filename=logfile, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

    try:
        attach = receive_attachment()

        lib = Library(lib_path)
        book = BookFile(attach)

        # add to calibre database
        lib.add_book(book)

        # get our book id
        meta = book.get_meta()
        book_id = lib.book_id(meta['author'], meta['title'])
        if book_id == None:
            raise RuntimeError('Inserted book not found, not adding other formats')

        # convert to other formats
        convert_formats = list(suffixes)
        convert_formats.remove(book.suffix)
        for suf in convert_formats:
            new_book = book.convert_to(suf)
            lib.add_format(book_id, new_book)
            new_book.delete()

        # delete the tempfile
        book.delete()

    except:
        logging.exception('Exception occured, exiting')

    else:
        logging.info('Exiting')
