#!/usr/bin/python

import os
import sys
import email
import logging
import tempfile
import subprocess

# settings
tmp_dir = '/tmp'
logfile = 'mail2calibre.log'
lib_path = '/calibre-library'
calibredb = 'calibredb'

suffixes = ['mobi']
logging.basicConfig(filename=logfile, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')

def receive_attachment():
    # read message
    e = email.message_from_file(sys.stdin)
    logging.info('Processing message: {0}'.format(e.get('Subject', '[no subject available]')))

    # find part that looks like a book
    for part in e.walk():
        fname = part.get_filename()
        ctype = part.get_content_type()
        if fname and ('.' in fname) and (fname.split('.')[-1] in suffixes):
            logging.info('Found part "{0}" of type {1}'.format(fname, ctype))
            break
    else:
        logging.error('No suitable attachment found')
        raise RuntimeError('No attachment found')

    # write it to temporary file
    with tempfile.NamedTemporaryFile(mode='w', dir=tmp_dir, suffix='.mobi', delete=False) as f:
        f.write(part.get_payload(decode=True))

    return f.name

class BookFile(object):
    def __init__(self, fname):
        self.fname = fname

    def to_library(self):
        logging.info('Adding {0} to library'.format(self.fname))
        args = [calibredb, 'add']
        args.extend(['--with-library', lib_path])
        args.append(self.fname)

        p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out, _) = p.communicate()
        logging.info('Child process finished with return code {0} and following output\n{1}'.format(p.returncode, out))

    def to_library_format(self, uuid):
        pass

    def convert_to(self, fmt):
        pass

    def delete(self):
        os.unlink(self.fname)
        self.fname = None

if __name__ == '__main__':

    attach = receive_attachment()

    book = BookFile(attach)

    # call calibredb
    book.to_library()

    # delete the tempfile
    book.delete()

    logging.info('Exiting')
