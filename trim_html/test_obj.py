#! /usr/bin/python3
import sys
import logging
import os
import fitz
import optparse

logging.basicConfig(format = '%(asctime)-15s %(levelname)s:%(message)s', level = logging.DEBUG)

def print_objs(pdf):
    
    doc = fitz.open(pdf, filetype = 'pdf')

    xrefs_cnt = doc.xrefLength()
    
    for cur_xref in range(xrefs_cnt):

        cur_obj = doc.xrefObject(cur_xref)
        
        logging.debug('=======================object %d========================' % cur_xref)
        logging.debug(repr(cur_obj))

def main():

    parser = optparse.OptionParser()
    parser.add_option('-i', '--input', dest = 'input', action = 'store', \
            type = 'string', help = 'the input directory that to be analyzed', default = None)

    (options, args) = parser.parse_args()

    assert options.input != None, 'Please input the pdf with (-i)'

    print_objs(options.input)

if __name__ == '__main__':
    main()
