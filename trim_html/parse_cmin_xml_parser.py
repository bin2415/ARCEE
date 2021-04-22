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
import time

sys.setrecursionlimit(100000)

logging.basicConfig(format = "%(asctime)-15s %(levelname)s:%(message)s", level=logging.INFO)

BLACKLIST_TAG = dict()
TAGS_CNT = dict()
RATE_TAKEN = 1.5
MAX_TIME_OUT = 400 # set timeout as 400ms
BLACK_TIME_OUT = set()

# global variables that are related to running the fuzzed binary
TEST_VALID_TRIM_CNT = 0
AFL_SHOWMAP = None
FUZZED_BINARY = None
BINARY_ARGS = None
MEM_LIMIT = None
TIME_OUT = None
OUTPUT = None

ORIG_MEM_MAP = None

SAME_INPUT = None
SAME_OUTPUT= None
TMP_DIR = '/dev/shm'

SUCCEED_CNT = 0
SUCCEED_CNT_ATTR = 0
SUCCEED_CNT_STR = 0
SUCCEED_CNT_STR_TRIM = 0

ORIG_HTML_SIZE = 0
TRIMED_HTML_SIZE = 0
ORIG_PDF_SIZE = 0
TRIMED_PDF_SIZE = 0

ALL_COVS = dict()
CUR_COVS = set()
CUR_UNIQ_COVS = set()

WKHTML = False
BLACKLIST = set()

PDF_SIZE_RATE = dict()
PDF_SIZE_CACHE = dict()

CUR_NOTHING_CNT = 0
TEST_VALID_CNT = 0

######################## HTML Parser Related Global Variables ################
ALL_COVS_HTML = dict()
CUR_COVS_HTML = set()
CUR_UNIQ_COVS_HTML = set()
HTML_PARSER = None
HTML_ARGS = None
############################################################################



def init_global_vars(options, args):
    '''
    initialize some global variables

    Args:
        options: options

    Returns:
        None
    '''
    global AFL_SHOWMAP, FUZZED_BINARY, BINARY_ARGS, MEM_LIMIT, TIME_OUT, OUTPUT, SAME_INPUT, WKHTML, TMP_DIR, RATE_TAKEN
    global HTML_PARSER, HTML_ARGS

    AFL_SHOWMAP = options.showmap
    FUZZED_BINARY = options.binary
    BINARY_ARGS = ' '.join(args)
    MEM_LIMIT = options.memory
    TIME_OUT = options.timeout
    OUTPUT = options.output
    HTML_ARGS = options.html_args
    HTML_PARSER = options.html_parser

    WKHTML = options.wkhtml

    if WKHTML:
        RATE_TAKEN = 1.0

    #TMP_DIR = os.getenv("TMPDIR")

    if TMP_DIR == '' or not TMP_DIR:
        TMP_DIR = '/tmp'

    SAME_INPUT = ('%s/%s.html' % (TMP_DIR, get_random_string(8)))

    if '@@' not in BINARY_ARGS:
        logging.error("Only support the input file with @@!")
        exit(-1)

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
    pdf_output = '%s/%s.pdf' % (TMP_DIR, tmp_output)
    if WKHTML:
        convert_cmd = 'timeout 3s wkhtmltopdf --enable-local-file-access %s %s' % (i_html, pdf_output)
    else:
        convert_cmd = 'timeout 3s google-chrome --headless --no-sandbox --disable-gpu --print-to-pdf=%s %s' % (pdf_output, i_html)
    #print(convert_cmd)

    cmds_list = convert_cmd.split()
    try:
        convert_run = subprocess.run(cmds_list, stdout = subprocess.PIPE, \
                stderr = subprocess.PIPE, timeout = 5)
    except subprocess.TimeoutExpired:
        return (1, pdf_output)

    return_code = 1

    if os.path.exists(pdf_output):
        return_code = 0

    return (return_code, pdf_output)

def parse_body(body, soup):
    """
    parse the body tag
    """
    dom_body = DomParser(body, None, 0)

    #dom_body.recursive_parse()

    recursive_remove(dom_body, soup)


def read_cov(tmp_output, all_covs):
    cur_cov = set()
    with open(tmp_output, 'r+') as s_o:
        for line in s_o.readlines():
            if line.strip().isdigit():
                cur_edge = int(line.strip())
                if cur_edge in all_covs:
                    all_covs[cur_edge] += 1
                else:
                    all_covs[cur_edge] = 1
                cur_cov.add(cur_edge)
    return cur_cov

def pre_test_trim(input_f, tmp_output):
    """
    pre testing the trim is valid or not by using html parser

    Args: input_f

    Returns:
        True if the trim is valid
    """

    if not run_showmap_purely(HTML_PARSER, HTML_ARGS, input_f, tmp_output):
        logging.error('run html parser cmin error %s' % input_f)
        return False

    covs = set()
    with open(tmp_output, 'r+') as s_o:
        for line in s_o.readlines():
            if line.strip().isdigit():
                covs.add(int(line.strip()))

    if len(covs) > 0 and len(CUR_UNIQ_COVS_HTML.difference(covs)) == 0:
        return True
    return False


def test_valid_trim(trimed_str):
    """
    test if the trimmed string is valid. That is it does not affect the covs

    Args:
        trimed_str: trimmed string

    Returns:
        True if the trim is valid
    """
    global TEST_VALID_CNT
    TEST_VALID_CNT += 1
    #tmp_input = get_random_string(8)
    tmp_input = SAME_INPUT
    tmp_output = get_random_string(8)
    tmp_output = ('%s/%s' % (TMP_DIR, tmp_output))
    #tmp_input = '/tmp/%s.html' % tmp_input

    with open(tmp_input, 'w') as t_i:
        t_i.write(trimed_str)

    if HTML_PARSER:
        if not pre_test_trim(tmp_input, tmp_output):
            os.system('rm %s' % tmp_input)
            os.system('rm %s' % tmp_output)
            logging.info("Filted by Html parser!")
            return 0

    (r_code, pdf_input) = convert_html_to_pdf(tmp_input)
    

    if r_code != 0:
        logging.error('Convert %s error!' % seed)
        os.system('rm %s' % pdf_input)
        return 0

    if os.path.getsize(pdf_input) > ORIG_PDF_SIZE - 100:
        os.system('rm %s' % pdf_input)
        return -1

    if not run_showmap_purely(FUZZED_BINARY, BINARY_ARGS, pdf_input, tmp_output):
        logging.error('run_showmap error of %s' % tmp_input)
        os.system('rm %s' % tmp_output)
        os.system('rm %s' % tmp_input)
        os.system('rm %s' % pdf_input)
        return 0

    covs = set()
    with open(tmp_output, 'r+') as s_o:
        for line in s_o.readlines():
            if line.strip().isdigit():
                covs.add(int(line.strip()))

    result = 0

    if len(covs) > 0 and len(CUR_UNIQ_COVS.difference(covs)) == 0:
        result = 1

    os.system('rm %s' % tmp_output)
    os.system('rm %s' % tmp_input)
    os.system('rm %s' % pdf_input)
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
        global BLACKLIST_TAG
        global TAGS_CNT
        global TEST_VALID_TRIM_CNT
        global CUR_NOTHING_CNT
        TEST_VALID_TRIM_CNT += 1
        dom_parser.remove_child_element()
        tmp_r_code = test_valid_trim(soup.prettify())
        blk_name = dom_parser.dom_element.name

        if blk_name in TAGS_CNT:
            TAGS_CNT[blk_name] += 1
        else:
            TAGS_CNT[blk_name] = 1

        if not tmp_r_code:
            if blk_name in BLACKLIST_TAG:
                BLACKLIST_TAG[blk_name] += 1
            else:
                BLACKLIST_TAG[blk_name] += 1
            dom_parser.recover_child_element()

            # remove attributes, sequencelly
            # binpang. disable attribute removing
            # remove_attributes(dom_parser, soup)

            # remove string sequencelly
            remove_string(dom_parser, soup)
        elif tmp_r_code == 1:

            # the subtree is removed. So skip this subtree
            if blk_name in BLACKLIST_TAG:
                BLACKLIST_TAG[blk_name] -= 2
                if BLACKLIST_TAG[blk_name] < 0:
                    BLACKLIST_TAG[blk_name] = 0

            global SUCCEED_CNT
            SUCCEED_CNT += 1
            logging.debug("[Trim valid Tag]: remove %s" % str(dom_parser.dom_element))
            return True
        else:
            CUR_NOTHING_CNT += 1
            if blk_name in BLACKLIST_TAG:
                BLACKLIST_TAG[blk_name] += 1
            else:
                BLACKLIST_TAG[blk_name] = 1

            dom_parser.recover_child_element()
            return False

    if dom_parser.is_leaf:
        return False

    children = list()
    for child in dom_parser.dom_element.findChildren():
        children.append(child)

    last_parent = dom_parser.dom_element
    for (idx, child) in enumerate(children):
        cur_dom_parent = DomParser(child, last_parent, idx)

        cur_child_name = child.name

        # randomly remove according history
        if cur_child_name in TAGS_CNT and cur_child_name in BLACKLIST_TAG:
            not_take_rate = (float)(BLACKLIST_TAG[cur_child_name]) / (float)(TAGS_CNT[cur_child_name] + 10)
            # not token
            if not_take_rate > random.random():
                logging.debug("skip tag %s" % cur_child_name)
                continue


        recursive_remove(cur_dom_parent, soup)

        # do not waste much time in this file
        if CUR_NOTHING_CNT > 5 or TEST_VALID_CNT >= 10:
            return False


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
            if ele.strip() != '' and len(ele.strip()) > 10:
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


def save_trimed_file(orig_html, soup):
    '''
    save trimed file

    Args:
        soup: beautifulsoup object

    Returns:
        None
    '''
    global TRIMED_HTML_SIZE
    global TRIMED_PDF_SIZE
    global CUR_COVS

    html = os.path.basename(orig_html)
    output = os.path.join(OUTPUT, html)
    with open(output, 'w+') as o:
        o.write(soup.prettify())

    TRIMED_HTML_SIZE = os.path.getsize(output)
    (_, TRIMED_PDF_SIZE) = get_converted_pdf_size(output)

    (_, output_covs) = get_covs(output)

    deleted_covs = CUR_COVS.difference(output_covs)

    if TRIMED_PDF_SIZE > ORIG_PDF_SIZE:
        TRIMED_PDF_SIZE = ORIG_PDF_SIZE
        os.system("cp %s %s" % (orig_html, output))

    else:
        # delete covs from ALL_COVS
        for cur_cov in deleted_covs:
            if cur_cov not in ALL_COVS:
                continue
            ALL_COVS[cur_cov] -= 1

            if ALL_COVS[cur_cov] == 0:
                del ALL_COVS[cur_cov]

    logging.info('Summary of %s: trime valid cnt is %d' % (html, SUCCEED_CNT))
    logging.info('Summary of %s: trime valid ATTR cnt is %d' % (html, SUCCEED_CNT_ATTR))
    logging.info('Summary of %s: trime valid STR cnt is %d' % (html, SUCCEED_CNT_STR))
    logging.info('Summary of %s: trime valid STR Replacing cnt is %d' % (html, SUCCEED_CNT_STR_TRIM))
    logging.info('Summary of %s: HTML size(original): %d bytes' % (html, ORIG_HTML_SIZE))
    logging.info('Summary of %s: HTML size(after trimming): %d bytes' % (html, TRIMED_HTML_SIZE))
    logging.info('Summary of %s: pdf size(original): %d bytes' % (html, ORIG_PDF_SIZE))
    logging.info('Summary of %s: pdf size(after trimming): %d bytes' % (html, TRIMED_PDF_SIZE))
    logging.info('Summary of %s: cnt of testing trim: %d' % (html, TEST_VALID_TRIM_CNT))
    logging.info('Summary of blacklist tag: {}'.format(BLACKLIST_TAG))


    logging.info('Save the output into %s' % output)

def parse_html(input_f, rate):
    """
    parse html with bs4


    Args: 
        html: the html file
    """

    global SUCCEED_CNT, SUCCEED_CNT_ATTR, SUCCEED_CNT_STR, SUCCEED_CNT_STR_TRIM, ORIG_HTML_SIZE, ORIG_PDF_SIZE, CUR_NOTHING_CNT, TEST_VALID_CNT

    SUCCEED_CNT = 0
    SUCCEED_CNT_ATTR = 0
    SUCCEED_CNT_STR = 0
    SUCCEED_CNT_STR_TRIM = 0
    CUR_NOTHING_CNT = 0
    TEST_VALID_CNT = 0

    try:
        with open(input_f) as o_h:
            content = o_h.read()
    except IOError:
        logging.error("File %s could not be opened!" % html)
        exit(-1)


    soup = BeautifulSoup(content, 'html.parser')



    with open(SAME_INPUT, 'w+') as f:
        f.write(soup.prettify())

    ORIG_HTML_SIZE = os.path.getsize(SAME_INPUT)
    ORIG_PDF_SIZE = PDF_SIZE_CACHE[input_f]

    if ORIG_HTML_SIZE > 15000:
        logging.info("skip it!")
        save_trimed_file(input_f, soup)
        return

    if rate < RATE_TAKEN or input_f in BLACK_TIME_OUT:
        logging.info("skip it!")
        save_trimed_file(input_f, soup)
        return

    global TEST_VALID_TRIM_CNT
    TEST_VALID_TRIM_CNT = 0

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

    save_trimed_file(input_f, soup)


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
    assert options.input != None, "Please input the seed to be analyzed with (-i)!"
    assert options.binary != None, "Please input the binary file that is fuzzed with (-b)!"
    assert options.output != None, "Please input the directory of output with (-o)!"


    # check the path of afl-showmap and binary is valid
    if not check_binary(options.showmap):
        logging.error('Please input the path of afl-showmap with (-s)!')
        exit(-1)

    # check the pat of tested binary is valid
    if not check_binary(options.binary):
        logging.error('Please input the path of tested binary with (-b)!')
        exit(-1)

    if not os.path.isdir(options.input):
        logging.error('Please input the directory of input files with (-i)!')
        exit(-1)

    if not os.path.isdir(options.output):
        mk_cmd = ('mkdir -p %s' % (options.output))
        mk_run = subprocess.run(mk_cmd.split(), stdout = subprocess.PIPE,\
                stderr = subprocess.PIPE)
        if mk_run.returncode != 0:
            logging.error('Error when mkdirring directory of output: %s' % options.output)
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

def run_showmap_purely(binary, binary_args, pdf_input, output):
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


    input_args = binary_args.replace('@@', pdf_input)

    running_args = ('%s -m %s %s -Z -o %s -- %s %s' % 
            (AFL_SHOWMAP, MEM_LIMIT, t_arg, output, binary, input_args))

    args_list = running_args.split()


    showmap_run = subprocess.run(args_list, stdout = subprocess.PIPE, \
            stderr = subprocess.PIPE)

    if showmap_run.returncode:
        logging.error('Errors when running afl-showmap firstly!\n \
                The output message is %s\n, The error message is %s\n' % 
                (showmap_run.stdout, showmap_run.stderr))
        return False

    return True

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

    input_args = BINARY_ARGS.replace('@@', pdf_input)

    if r_code != 0:
        logging.error('Convert %s error!' % seed)
        os.system('rm %s' % pdf_input)
        return False

    running_args = ('%s -m %s %s -Z -o %s -- %s %s' % 
            (AFL_SHOWMAP, MEM_LIMIT, t_arg, output, FUZZED_BINARY, input_args))

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

def parse_seeds(input_dir, all_covs_map, all_covs_map_html):
    global CUR_UNIQ_COVS, CUR_COVS
    global CUR_UNIQ_COVS_HTML, CUR_COVS_HTML
    global PDF_SIZE_RATE
    global PDF_SIZE_CACHE

    PDF_SIZE_RATE = sorted(PDF_SIZE_RATE.items(), key=lambda x: x[1], reverse = True)

    for (seed, rate) in PDF_SIZE_RATE:
        logging.info('current seed is %s' % seed)
        logging.info(rate)

        # (r_code, cur_covs) = get_covs(seed)
        # get it from cache
        CUR_UNIQ_COVS = set()
        CUR_UNIQ_COVS_HTML = set()
        CUR_COVS = all_covs_map[seed]
        #CUR_COVS_HTML = all_covs_map_html[seed]

        assert len(CUR_COVS) > 0, 'the length of cur_covs equals to 0!'


        #[CUR_UNIQ_COVS.add(cov) for cov in CUR_COVS if cov not in ALL_COVS or ALL_COVS[cov] == 1]
        #[CUR_UNIQ_COVS_HTML.add(cov) for cov in CUR_COVS_HTML if cov not in ALL_COVS_HTML or ALL_COVS_HTML[cov] == 1] 


        for cov in CUR_COVS:
            if cov not in ALL_COVS or ALL_COVS[cov] == 1:
                CUR_UNIQ_COVS.add(cov)
        parse_html(seed, rate)

'''
        for cov in CUR_COVS_HTML:
            if cov not in ALL_COVS_HTML or ALL_COVS_HTML[cov] == 1:
                CUR_UNIQ_COVS_HTML.add(cov)
'''




def get_covs(seed):
    '''
    first running of the fuzzed binary.
    check if afl-whowmap runs normally
    and collect the covs of seed

    Args:
        seed: the input file that to be analyzed

    Returns:
        True if afl-showmap runs normally
    '''

    try:
        with open(seed) as o_h:
            content = o_h.read()
    except IOError:
        logging.error("File %s could not be opened!" % seed)

    covs = set()
    tmp_output = '%s/%s' % (TMP_DIR, get_random_string(8))

    soup = BeautifulSoup(content, 'html.parser')

    with open(SAME_INPUT, 'w+') as f:
        f.write(soup.prettify())

    if not run_showmap(SAME_INPUT, tmp_output):
        os.system('rm %s' % tmp_output)
        return (False, covs)

    with open(tmp_output, 'r+') as s_o:
        for line in s_o.readlines():
            if line.strip().isdigit():
                covs.add(int(line.strip()))

    os.system('rm %s' % tmp_output)

    return (True, covs)

def collect_covs_of_seeds(input_dir):
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
    global BLACKLIST
    global BLACK_TIME_OUT
    global PDF_SIZE_RATE, PDF_SIZE_CACHE

    all_covs = dict()
    all_covs_map = dict()
    all_covs_html = dict()
    all_covs_map_html = dict()

    tmp_output = ('%s/%s' % (TMP_DIR, get_random_string(8)))

    logging.info('collecting covs...')

    for seed in os.listdir(input_dir):

        seed = os.path.join(input_dir, seed)
        logging.info("current seed is %s" % seed)

        if os.path.isdir(seed):
            continue

        try:
            with open(seed) as o_h:
                content = o_h.read()
        except IOError:
            logging.error("File %s could not be opened!" % seed)
            return (False, all_covs)

        soup = BeautifulSoup(content, 'html.parser')

        with open(SAME_INPUT, 'w+') as f:
            f.write(soup.prettify())

        cur_html_size = os.path.getsize(seed)
        cur_start_time = int(round(time.time() * 1000))
        (r_code, pdf_input) = convert_html_to_pdf(SAME_INPUT)
        cur_end_time = int(round(time.time() * 1000))


        if cur_end_time - cur_start_time > MAX_TIME_OUT:
            BLACK_TIME_OUT.add(seed)

        if r_code !=0 or not run_showmap_purely(FUZZED_BINARY, BINARY_ARGS, pdf_input, tmp_output):
            os.system('rm %s' % tmp_output)
            os.system('rm %s' % pdf_input)
            logging.error('[Convert error]: add %s to blacklist' % seed)
            BLACKLIST.add(os.path.basename(seed))
            continue

        converted_pdf_size = os.path.getsize(pdf_input)
        if cur_html_size != 0:
            PDF_SIZE_RATE[seed] = (float)(converted_pdf_size/(float)(cur_html_size))
            PDF_SIZE_CACHE[seed] = converted_pdf_size

        cur_cov = read_cov(tmp_output, all_covs)
        all_covs_map[seed] = cur_cov

        if HTML_PARSER:
            if not run_showmap_purely(HTML_PARSER, HTML_ARGS, SAME_INPUT, tmp_output):
                os.system('rm %s' % tmp_output)
                os.system('rm %s' % pdf_input)
                continue

            cur_html_cov = read_cov(tmp_output, all_covs_html)
            all_covs_map_html[seed] = cur_html_cov



    os.system('rm %s' % tmp_output)
    return (True, all_covs, all_covs_map, all_covs_html, all_covs_map_html)
    

def main():

    parser = optparse.OptionParser()

    parser.add_option('-i', '--input', dest = 'input', action = 'store', \
            type = 'string', help = 'the input directory that to be analyzed', default = None)
    parser.add_option('-b', '--binary', dest = 'binary', action = 'store', \
            type = 'string', help = 'the binary file that is fuzzed', default = None)
    parser.add_option('-s', '--showmap', dest = 'showmap', action = 'store', \
            type = 'string', help = 'the path of afl-showmap', default = 'afl-showmap')
    parser.add_option('-m', '--memory', dest = 'memory', action = 'store', \
            type = 'string', help = '[args of afl-showmap]: memory limit', default = 'none')
    parser.add_option('-t', '--timeout', dest = 'timeout', action = 'store', \
            type = 'string', help = '[args of afl-showmap]:time out', default = None)
    parser.add_option('-o', '--output', dest = 'output', action = 'store', \
            type = 'string', help = 'directory of output', default = None)
    parser.add_option('-w', '--wkhtml', dest = 'wkhtml', action="store_true", \
            help = "Convertor is wkhtml or not", default = False)
    parser.add_option('-x', '--html_parser', dest = 'html_parser', action="store", \
            help = "The path of html parser", default = None)
    parser.add_option('-A', '--html_args', dest = 'html_args', action = 'store', \
            help = "The arguments of html parser", default = None)

    (options, args) = parser.parse_args()

    pre_check(options)

    init_global_vars(options, args)

    global ALL_COVS, ALL_COVS_HTML
    
    (r_code, ALL_COVS, all_covs_map, ALL_COVS_HTML, all_covs_map_html) = collect_covs_of_seeds(options.input)

    if not r_code:
        logging.error('Try running afl-showmap error!')
        exit(-1)

    logging.info("Collect covs done!")

    parse_seeds(options.input, all_covs_map, all_covs_map_html)

if __name__ == '__main__':
    main()
