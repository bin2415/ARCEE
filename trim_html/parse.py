#! /usr/bin/python3
import sys
import logging
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from dom_traverse import *
import optparse
import subprocess
import os
import random
import string

sys.setrecursionlimit(100000)

logging.basicConfig(format = "%(asctime)-15s %(levelname)s:%(message)s", level=logging.DEBUG)

# global variables that are related to running the fuzzed binary
AFL_SHOWMAP = None
FUZZED_BINARY = None
BINARY_ARGS = None
MEM_LIMIT = None
TIME_OUT = None
OUTPUT = None

ORIG_MEM_MAP = None

SAME_INPUT = None
SAME_OUTPUT= None

SUCCEED_CNT = 0
SUCCEED_CNT_ATTR = 0
SUCCEED_CNT_STR = 0
SUCCEED_CNT_STR_TRIM = 0

ORIG_HTML_SIZE = 0
TRIMED_HTML_SIZE = 0
ORIG_PDF_SIZE = 0
TRIMED_PDF_SIZE = 0

def init_global_vars(options):
    '''
    initialize some global variables

    Args:
        options: options

    Returns:
        None
    '''
    global AFL_SHOWMAP, FUZZED_BINARY, BINARY_ARGS, MEM_LIMIT, TIMEOUT, OUTPUT

    AFL_SHOWMAP = options.showmap
    FUZZED_BINARY = options.binary
    BINARY_ARGS = options.args
    MEM_LIMIT = options.memory
    TIME_OUT = options.timeout
    OUTPUT = options.output

def get_converted_pdf_size(i_html):
    '''
    convert html firstly, and then
    get the size of converted pdf

    Args:
        i_html: html file

    Returns:
        True is converted process succeed
        return code
    '''
    (return_code, pdf_output) = convert_html_to_pdf(i_html)

    size = 0
    if return_code == 0:
        size = os.path.getsize(pdf_output)

    os.system('rm %s' % pdf_output)

    return (return_code, size)


def convert_html_to_pdf(i_html):
    '''
    convert html to pdf.

    Args:
        i_html: html file

    Returns:
        True is converted process succeed
        converted pdf file
    '''
    tmp_output = get_random_string(8)
    pdf_output = '/tmp/%s.pdf' % tmp_output
    convert_cmd = 'google-chrome --headless --disable-gpu --print-to-pdf=%s %s' % (pdf_output, i_html)
    #print(convert_cmd)
    #convert_cmd = 'xvfb-run wkhtmltopdf -l %s %s' % (i_html, pdf_output)

    cmds_list = convert_cmd.split()

    convert_run = subprocess.run(cmds_list, stdout = subprocess.PIPE, \
            stderr = subprocess.PIPE)

    if convert_run.returncode != 0:
        logging.error(convert_run.returncode)
        logging.error('input file is %s' % i_html)
        exit(-1)

    return_code = 1
    if os.path.exists(pdf_output):
        return_code = 0

    #logging.debug(convert_run.stderr)
    #logging.debug(convert_run.stdout)
    return (return_code, pdf_output)

def parse_body(body, soup):
    """
    parse the body tag
    """
    dom_body = DomParser(body, None, 0)

    #dom_body.recursive_parse()

    recursive_remove(dom_body, soup)


def test_valid_trim(trimed_str):
    """
    test if the trimmed string is valid. That is it does not affect the covs

    Args:
        trimed_str: trimmed string

    Returns:
        True if the trim is valid
    """
    #tmp_input = get_random_string(8)
    tmp_input = SAME_INPUT
    tmp_output = get_random_string(8)
    tmp_output = ('/tmp/%s' % tmp_output)
    #tmp_input = '/tmp/%s.html' % tmp_input

    with open(tmp_input, 'w') as t_i:
        t_i.write(trimed_str)

    if not run_showmap(tmp_input, tmp_output):
        os.system('rm %s' % tmp_output)
        os.system('rm %s' % tmp_input)
        return False

    with open(tmp_output, 'r+') as s_o:
        cur_mem_map = s_o.read()

    result = False

    # TODO. (binpang) This may be slow. Optimize it later
    if len(cur_mem_map) == len(ORIG_MEM_MAP):
        result = True

    os.system('rm %s' % tmp_output)
    os.system('rm %s' % tmp_input)
    return result

def recursive_remove(dom_parser, soup):
    """
    resursivly remove elements from tree to sub-tree

    If you want to remove the elements begin from leaf nodes.
    Please modify this function

    Args:
        dom_parser: DomParser
        soup: BeautifulSoup Object
    Returns:
        None
    """

    if dom_parser.parent:
        dom_parser.remove_child_element()
        if not test_valid_trim(soup.prettify()):
            dom_parser.recover_child_element()

            # remove attributes, sequencelly
            remove_attributes(dom_parser, soup)
            # remove string sequencelly
            remove_string(dom_parser, soup)
        else:
            # the subtree is removed. So skip this subtree
            global SUCCEED_CNT
            SUCCEED_CNT += 1
            logging.debug("[Trim valid Tag]: remove %s" % str(dom_parser.dom_element))
            return True

    if dom_parser.is_leaf:
        return False

    children = list()
    for child in dom_parser.dom_element.findChildren():
        children.append(child)

    last_parent = dom_parser.dom_element
    for (idx, child) in enumerate(children):
        cur_dom_parent = DomParser(child, last_parent, idx)
        recursive_remove(cur_dom_parent, soup)
        last_parent = cur_dom_parent.parent

'''
    for child in dom_parser.children:

        if not child.parent:
            continue
        resursive_remove(child, soup)
'''

def remove_string(dom_parser, soup):
    '''
    remove string sequencelly.

    Args:
        dom_parser: DomParser
        soup: BeautifulSoup

    Returns:
        None
    '''
    removed_idx = list()
    for (idx, ele) in enumerate(dom_parser.dom_element.contents):
        if isinstance(ele, NavigableString):
            removed_idx.append(idx)

    succeed_cnt = 0

    for idx in removed_idx:
        removed_str = dom_parser.remove_str(idx - succeed_cnt)
        if not test_valid_trim(soup.prettify()):
            dom_parser.recover_str(idx - succeed_cnt, removed_str)

            # try replacing the string with shorter one
            shorter_str = '0'
            replaced_str = dom_parser.replace_str(idx - succeed_cnt, shorter_str)

            if not test_valid_trim(soup.prettify()):
                dom_parser.recover_replace_str(idx - succeed_cnt, replaced_str)
            else:
                global SUCCEED_CNT_STR_TRIM
                SUCCEED_CNT_STR_TRIM += 1
                logging.debug('[Trim valid Str Replacing]: replace %s with %s'\
                        % (repr(replaced_str), shorter_str))
        else:
            global SUCCEED_CNT_STR
            SUCCEED_CNT_STR += 1
            logging.debug('[Trim valid Str]: removed %s'\
                    % (repr(removed_str)))
            succeed_cnt += 1


def remove_attributes(dom_parser, soup):
    '''
    remove attributes sequencelly.

    Args:
        dom_parser: DomParser
        soup: BeautifulSoup

    Returns:
        None
    '''

    if not dom_parser.dom_element:
        return

    keys = set()
    #copy.deepcopy(dom_parser.dom_element.attrs.keys()
    [keys.add(key) for key in dom_parser.dom_element.attrs.keys()]


    for key in keys:
        removed_val = dom_parser.remove_attr(key)
        if not removed_val:
            continue

        if not test_valid_trim(soup.prettify()):
            dom_parser.recover_attr(key, removed_val)
        else:
            global SUCCEED_CNT_ATTR
            SUCCEED_CNT_ATTR += 1
            logging.debug('[Trim valid Attr]: removed key: %s, value %s'\
                    % (key, removed_val))


def save_trimed_file(soup):
    '''
    save trimed file

    Args:
        soup: beautifulsoup object

    Returns:
        None
    '''
    global TRIMED_HTML_SIZE
    global TRIMED_PDF_SIZE
    with open(OUTPUT, 'w+') as o:
        o.write(soup.prettify())

    TRIMED_HTML_SIZE = os.path.getsize(OUTPUT)
    (_, TRIMED_PDF_SIZE) = get_converted_pdf_size(OUTPUT)

    logging.info('Summary: trime valid cnt is %d' % SUCCEED_CNT)
    logging.info('Summary: trime valid ATTR cnt is %d' % SUCCEED_CNT_ATTR)
    logging.info('Summary: trime valid STR cnt is %d' % SUCCEED_CNT_STR)
    logging.info('Summary: trime valid STR Replacing cnt is %d' % SUCCEED_CNT_STR_TRIM)
    logging.info('Summary: HTML size(original): %d bytes' % ORIG_HTML_SIZE)
    logging.info('Summary: HTML size(after trimming): %d bytes' % TRIMED_HTML_SIZE)
    logging.info('Summary: pdf size(original): %d bytes' % ORIG_PDF_SIZE)
    logging.info('Summary: pdf size(after trimming): %d bytes' % TRIMED_PDF_SIZE)


    logging.info('Save the output into %s' % OUTPUT)


def parse_html(html):
    """
    parse html with bs4


    Args: 
        html: the html file
    """

    try:
        with open(html) as o_h:
            content = o_h.read()
    except IOError:
        logging.error("File %s could not be opened!" % html)
        exit(-1)


    soup = BeautifulSoup(content, 'html.parser')
    bodies = soup.find_all('body')

    html = soup.find_all('html')

    if len(html) > 0:
        html = html[0]
        for ele in html.next_siblings:
            if isinstance(ele, NavigableString):
                continue
            try:
                parse_body(ele, soup)
            except:
                pass


    for body in bodies:
        if not body:
            continue
        try:
            parse_body(body, soup)
        except:
            pass


    save_trimed_file(soup)


def check_binary(binary):
    '''
    check if binary exists

    Args:
        binary: binary

    Returns:
        True if the binary exists
    '''
    c_output = subprocess.run(['which', binary], stdout = subprocess.PIPE)

    if os.path.exists(c_output.stdout.strip()):
        return True
    return False

def pre_check(options):
    '''
    pre check if required arguments exist

    Args:
        options: option

    Returns:
        None
    '''
    assert options.seed != None, "Please input the seed to be analyzed with (-i)!"
    assert options.binary != None, "Please input the binary file that is fuzzed with (-b)!"

    # check the path of afl-showmap and binary is valid
    if not check_binary(options.showmap):
        logging.error('Please input the path of afl-showmap with (-s)!')
        exit(-1)

    # check the pat of tested binary is valid
    if not check_binary(options.binary):
        logging.error('Please input the path of tested binary with (-b)!')
        exit(-1)

def get_random_string(length):
    '''
    generate random string with specific length

    Args:
        length

    Returns:
        random string
    '''
    letters = string.ascii_lowercase
    result_str = ''.join((random.choice(letters) for i in range(length)))
    return result_str

def run_showmap(seed, output):
    '''
    run afl-showmap with specified seed

    Args:
        seed: the input file
        output: output file that store covs

    Returns:
        True if running correctly
    '''
    t_arg = ''

    if TIME_OUT:
        t_arg = ('-t %s' % TIME_OUT) 

    (r_code, pdf_input) = convert_html_to_pdf(seed)

    if r_code != 0:
        logging.error('Convert %s error!' % seed)
        os.system('rm %s' % pdf_input)
        return False

    running_args = ('%s -m %s %s -Z -o %s -- %s %s %s' % 
            (AFL_SHOWMAP, MEM_LIMIT, t_arg, output, FUZZED_BINARY, pdf_input, BINARY_ARGS))

    args_list = running_args.split()

    showmap_run = subprocess.run(args_list, stdout = subprocess.PIPE, \
            stderr = subprocess.PIPE)

    if showmap_run.returncode:
        logging.error('Errors when running afl-showmap firstly!\n \
                The output message is %s\n, The error message is %s\n' % 
                (showmap_run.stdout, showmap_run.stderr))
        os.system('rm %s' % pdf_input)
        return False
    os.system('rm %s' % pdf_input)
    return True

def first_run(seed):
    '''
    first running of the fuzzed binary.
    check if afl-whowmap runs normally
    and collect the covs of seed

    Args:
        seed: the input file that to be analyzed

    Returns:
        True if afl-showmap runs normally
    '''

    global ORIG_MEM_MAP
    global SAME_INPUT
    global ORIG_HTML_SIZE
    global ORIG_PDF_SIZE


    tmp_output = ('/tmp/%s' % get_random_string(8))
    SAME_INPUT = ('/tmp/%s.html' % get_random_string(8))

    try:
        with open(seed) as o_h:
            content = o_h.read()
    except IOError:
        logging.error("File %s could not be opened!" % seed)
        return False

    soup = BeautifulSoup(content, 'html.parser')

    with open(SAME_INPUT, 'w+') as f:
        f.write(soup.prettify())

    ORIG_HTML_SIZE = os.path.getsize(SAME_INPUT)
    (_, ORIG_PDF_SIZE) = get_converted_pdf_size(SAME_INPUT)

    #os.system('cp %s %s' % (seed, SAME_INPUT))

    if not run_showmap(SAME_INPUT, tmp_output):
        os.system('rm %s' % tmp_output)
        return False


    with open(tmp_output, 'r+') as s_o:
        ORIG_MEM_MAP = s_o.read()

    os.system('rm %s' % tmp_output)

    return True
    

def main():

    parser = optparse.OptionParser()

    parser.add_option('-i', '--seed', dest = 'seed', action = 'store', \
            type = 'string', help = 'the input html that to be analyzed', default = None)
    parser.add_option('-b', '--binary', dest = 'binary', action = 'store', \
            type = 'string', help = 'the binary file that is fuzzed', default = None)
    parser.add_option('-s', '--showmap', dest = 'showmap', action = 'store', \
            type = 'string', help = 'the path of afl-showmap', default = 'afl-showmap')
    parser.add_option('-a', '--args', dest = 'args', action = 'store', \
            type = 'string', help = 'the args of fuzzed binary', default = '')
    parser.add_option('-m', '--memory', dest = 'memory', action = 'store', \
            type = 'string', help = '[args of afl-showmap]: memory limit', default = 'None')
    parser.add_option('-t', '--timeout', dest = 'timeout', action = 'store', \
            type = 'string', help = '[args of afl-showmap]:time out', default = None)
    parser.add_option('-o', '--output', dest = 'output', action = 'store', \
            type = 'string', help = 'output of minimized string', default = '/tmp/tmin_dom')

    (options, args) = parser.parse_args()

    pre_check(options)

    init_global_vars(options)

    if not first_run(options.seed):
        logging.error('Try running afl-showmap error!')
        exit(-1)


    parse_html(options.seed)

if __name__ == '__main__':
    main()
