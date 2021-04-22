'''
randomly pick n pairs pdfs
'''
import optparse
import subprocess
import os
import logging
from itertools import combinations
from random import shuffle

logging.basicConfig(format = "%(asctime)-15s %(levelname)s:%(message)s", level = logging.INFO)

def get_exchange_exe():
    f_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'exchange_objs')
    if not os.path.exists(f_path):
        logging.error("can't find <exchange_objs>! Please 'make' firstly!")
        exit(-2)
    return f_path

def read_dir(input_dir):
    file_map = dict()
    idx = 0
    for f in os.listdir(input_dir):
        file_map[idx] = f
        idx += 1

    logging.debug('scanning files in input directory %s: %d files' % (input_dir, len(file_map)))
    return file_map

def read_files(input_l):
    idx = 0
    file_map=dict()

    with open(input_l) as f:
        for l in f:
            if l.strip() == '':
                continue
            file_map[idx] = l.strip()
            idx += 1

    logging.debug('scanning files in input directory %s: %d files' % (input_l, len(file_map)))
    return file_map


def randomly_exchange(input_dir, output_dir, num_output):

    exe = get_exchange_exe()

    if os.path.isfile(input_dir):
        input_fs = read_files(input_dir)
        input_dir=""
    else:
        input_fs = read_dir(input_dir)

    input_len = len(input_fs)

    idxes_com = list(combinations(range(0, input_len), 2))

    cur_idx = 0
    
    # shuffle the index. so we can randomly pick the pair
    shuffle(idxes_com)
    
    for cur_pair in idxes_com:
        exe_cmd = '%s -o %s %s %s' % \
                (exe, output_dir, os.path.join(input_dir, input_fs[cur_pair[0]]), os.path.join(input_dir, input_fs[cur_pair[1]]))
        logging.debug("===============running %d: %s==================" % (cur_idx, exe_cmd))

        cur_run = subprocess.run(exe_cmd.split(), stdout = subprocess.PIPE, \
                stderr = subprocess.PIPE)

        if cur_run.returncode != 0:
            continue

        cur_idx += 2

        if cur_idx >= num_output:
            break

    logging.info("[*] Generate %d files in %s!" % (cur_idx, output_dir))




def main():
    parser = optparse.OptionParser()

    parser.add_option('-i', '--input', dest = 'input', action = 'store', \
            type = 'string', help = 'The input directory that to be analyzed', default = None)
    parser.add_option('-o', '--output', dest = 'output', action = 'store', \
            type = 'string', help = 'The output directory that store the result', default = None)
    parser.add_option('-n', '--num_output', dest = 'num_output', action = 'store', \
            type = 'int', help = 'The number of output that need to generated', default = None)

    (options, args) = parser.parse_args()

    if not options.input or not options.output or not options.num_output:
        parser.print_help()
        exit(-1)

    randomly_exchange(options.input, options.output, options.num_output)

if __name__ == '__main__':
    main()
