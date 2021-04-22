import optparse
from collections import defaultdict
import os
import glob
from graphviz import Digraph


FOLDER = None

def output_dot(sync_reason, mutate_reason, output):
    keys = set(sync_reason.keys())
    keys = keys.union(set((mutate_reason.keys())))

    key_map = dict()

    for l in sync_reason.values():
        [keys.add(i) for i in l]

    for l in mutate_reason.values():
        [keys.add(i) for i in l]

    dot = Digraph(comment='The Relationship of seed')

    for (i, k) in enumerate(keys):
        cur_node = ('node_%d' % (i))
        key_map[k] = cur_node
        dot.node(cur_node, k)

    for (k, v_l) in sync_reason.items():
        cur_node = key_map[k]
        [dot.edge(cur_node, key_map[v], fillcolor = 'green') for v in v_l]

    for (k, v_l) in mutate_reason.items():
        cur_node = key_map[k]
        [dot.edge(cur_node, key_map[v], fillcolor = 'black') for v in v_l]

    with open(output, 'w+') as output_result:
        output_result.write(dot.source)

def distribute(sync_reason, mutate_reason, seeds):

    todo = list()
    todo.extend(seeds)

    while len(todo) > 0:
        cur_seed = todo.pop(0)
        seed_dict = os.path.join(FOLDER, os.path.dirname(cur_seed))
        file_name = os.path.basename(cur_seed)
        if 'sync' in file_name:
            split_res = file_name.split(':')
            id = split_res[-1]
            slave = split_res[-2].split(',')[0]
            id = id.split(',')[0]
            
            sync_folder = os.path.join(FOLDER, slave)
            for name in glob.glob('%s/queue/id:%s*' % (sync_folder, id)):
                rel_path = os.path.relpath(name, FOLDER)
                sync_file_name = os.path.basename(rel_path)
                print('sync: %s -> %s' % (file_name, sync_file_name))
                if 'domato' in sync_file_name:
                    output_name = rel_path.replace('/queue', '')
                    sync_reason[file_name].append(output_name)
                else:
                    sync_reason[file_name].append(sync_file_name)
                todo.append(rel_path)

        elif 'src' in file_name:
            split_res = file_name.split(',')[1]
            ids = split_res.split(':')[1]
            id_list = list()
            if '+' in ids:
                [id_list.append(id) for id in ids.split('+')]
            else:
                id_list.append(ids)

            for cur_id in id_list:
                for name in glob.glob('%s/id:%s*' % (seed_dict, cur_id)):
                    rel_path = os.path.relpath(name, FOLDER)
                    mutate_file_name = os.path.basename(rel_path)
                    print('mutate: %s -> %s' % (file_name, mutate_file_name))
                    mutate_reason[file_name].append(mutate_file_name)
                    todo.append(rel_path)

def pre_process(seed, mutate_reason):
    id_list = list()
    seeds_list = list()
    file_name = os.path.basename(seed)
    seed_dict = os.path.join(os.path.dirname(seed), '../queue')

    print(seed_dict)
    if 'src' in file_name:
        split_res = file_name.split(',')[2]
        ids = split_res.split(':')[1]
        id_list = list()
        if '+' in ids:
            [id_list.append(id) for id in ids.split('+')]
        else:
            id_list.append(ids)

    for cur_id in id_list:
        for name in glob.glob('%s/id:%s*' % (seed_dict, cur_id)):
            rel_path = os.path.relpath(name, FOLDER)
            mutate_file_name = os.path.basename(rel_path)
            print('pre processing: %s' % (mutate_file_name))
            mutate_reason[file_name].append(mutate_file_name)
            seeds_list.append(rel_path)

    return seeds_list

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option("-s", "--seed", dest = "seed", action = "store", \
                type = "string", help = "the seed that to be analyzed", default = None)
    parser.add_option("-f", "--folder", dest = "folder", action = "store", \
            type = "string", help = "the afl output dirctory", default = None)
    parser.add_option("-o", "--output", dest = "output", action = "store", \
            type = "string", help = "the dot file that saved the result", default = '/tmp/tmp.dot')
    (options, args) = parser.parse_args()
    assert options.seed != None, "Please input seed with (-s)!"
    assert options.folder != None, "Please input output folder of afl with (-f)!"
    FOLDER = options.folder
    sync_reason = defaultdict(list)
    mutate_reason = defaultdict(list)
    seeds = pre_process(options.seed, mutate_reason)
    distribute(sync_reason, mutate_reason, seeds)
    output_dot(sync_reason, mutate_reason, options.output)
