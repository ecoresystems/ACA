# -*- coding: utf-8 -*-
"""
Umi

"""
import os
from subprocess import call
import pandas as pd
import numpy as np

combination = [[2, 64, 512]]
# combination = [[2,32,1024]]
# combination = [[4,16,512]]
# combination = [[4,32,256] ]
# combination = [[8,16,128]]
# combination = [[16, 8, 64]]
# combination = [[16, 4, 128]]
# combination = [[32, 4, 32]]
# combination = [[8,8,256]]

associativity = [2, 4, 8, 16, 32]


def access_time_calculator():
    for item in combination:
        for asso in associativity:
            cache_size = item[0] * item[2] * 1024
            with open("cache.cfg") as f:
                new_text = f.read().replace('-size (bytes) 134217728', '-size (bytes) %d' % cache_size)
                new_text = new_text.replace('-associativity 1', '-associativity %d' % asso)
                new_text = new_text.replace('-Core count 8', '-Core count %d' % item[0])
            with open("core%d_cache%dKB_asso%d.cfg" % (item[0], item[2] * item[0], asso), "w") as f:
                f.write(new_text)
            os.system('./cacti -infile core%d_cache%dKB_asso%d.cfg > cacti_result/core%d_cache%dKB_asso%d.txt' % (
                item[0], item[2] * item[0], asso, item[0], item[2] * item[0], asso))
    for item in combination:
        for asso in associativity:
            # print("core%d_cache%dKB_asso%d" % (item[0], item[1], asso))
            cache_size = item[1] * 1024
            with open("cache.cfg") as f:
                new_text = f.read().replace('-size (bytes) 134217728', '-size (bytes) %d' % cache_size)
                new_text = new_text.replace('-associativity 1', '-associativity %d' % asso)
                new_text = new_text.replace('-Core count 8', '-Core count %d' % item[0])
                # print(new_text)
            with open("core%d_cache%dKB_asso%d.cfg" % (item[0], item[1], asso), "w") as f:
                f.write(new_text)
            os.system('./cacti -infile core%d_cache%dKB_asso%d.cfg >  cacti_result/core%d_cache%dKB_asso%d.txt' % (
                item[0], item[1], asso, item[0], item[1], asso))


def data_collector():
    df = pd.DataFrame(columns=['cores', 'clock', 'l1d_size', 'l1d_assoc', 'l2_size', 'l2_assoc', 'l2_latency'])

    for item in combination:
        try:
            cores = item[0]  # This is the core number
            l1d_size = item[1]  # This is l1 cache size
            l2_size_pc = item[2]
            for l1_assoc in associativity:
                try:
                    with open("result/core%d_cache%dKB_asso%d.txt" % (cores, l1d_size, l1_assoc), 'r') as f:
                        for line in f:
                            line = line.strip()
                            if "Access time" in line:
                                l1_acc = float(line.split(': ')[1])
                except:
                    continue

                for l2_assoc in associativity:
                    try:
                        with open("result/core%d_cache%dKB_asso%d.txt" % (cores, l2_size_pc * cores, l2_assoc),
                                  'r') as f:
                            for line in f:
                                line = line.strip()
                                if "Access time" in line:
                                    l2_acc = float(line.split(': ')[1])
                    except:
                        continue
                    # print(np.array([cores, l1d_size, l1_assoc, l1_acc, l2_size, l2_assoc, l2_acc]))
                    clock = 1 / l1_acc
                    l2_latency = l2_acc / l1_acc
                    aux = pd.DataFrame(np.array([[cores, clock, l1d_size, l1_assoc, l2_size_pc, l2_assoc, l2_latency]]),
                                       columns=['cores', 'clock', 'l1d_size', 'l1d_assoc', 'l2_size', 'l2_assoc',
                                                'l2_latency'])
                    df = df.append(aux, ignore_index=True)
        except:
            pass

    print("Accessing data now")
    return df


def data_parser(core_data):
    print(core_data)
    for index, row in core_data.iterrows():
        cmd_assembler(int(row['cores']), row['clock'], row['l1d_size'], row['l1d_assoc'], row['l2_size'],
                      row['l2_assoc'], row['l2_latency'])


def cmd_assembler(cores, clock, l1d_size, l1d_assoc, l2_size, l2_assoc, l2_latency):
    cmd_dict = dict()
    cmd_dict['fmm'] = ('./splash2/fmm/FMM < ./splash2/fmm/inputs/input.2048.p%d' % cores)
    cmd_dict['ocean'] = './splash2/ocean/contiguous_partitions/OCEAN -o "-n130 -p%d"' % cores
    cmd_dict['raytrace'] = './splash2/raytrace/RAYTRACE -o "-p%d ./splash2/raytrace/inputs/teapot.env"' % cores
    cmd_dict['cholesky'] = './splash2/cholesky/CHOLESKY -o "-p%d  ./splash2/cholesky/inputs/d750.O"' % cores
    cmd_dict['fft'] = './splash2/fft/FFT -o "-p%d"' % cores
    cmd_dict['lu'] = './splash2/lu/contiguous_blocks/LU -o "-p%d"' % cores
    cmd_dict['radix'] = './splash2/radix/RADIX -o "-p%d"' % cores

    sub_cmd1 = './build/ALPHA/gem5.opt -d ./results/%d_%d_%d_%d_%d' % (
        cores, l1d_size, l1d_assoc, l2_size, l2_assoc)
    sub_cmd2 = '/ ./configs/example/se.py'
    sub_cmd3 = ' -n %d --cpu-type=detailed --cpu-clock=%.1fGHz --mem-type=SimpleMemory' % (cores, clock)
    sub_cmd4 = ' --caches --l2cache  --l1d_size=%dkB --l1d_assoc=%d' % (l1d_size, l1d_assoc)
    sub_cmd5 = ' --l2_size=%dkB --l2_assoc=%d --l2_latency=%d -c ' % (l2_size * cores, l2_assoc, l2_latency)

    for key, sp_cmd in cmd_dict.items():
        if key == 'fft':
            gem5_cmd = sub_cmd1 + '_' + key + sub_cmd2 + sub_cmd3 + sub_cmd4 + sub_cmd5 + sp_cmd
            # print('Executing ' + gem5_cmd + '\nThis may take a wile...\n\n')
            # os.system(gem5_cmd)
            print(gem5_cmd)
    pass


if __name__ == "__main__":
    # data_parser(data_collector())
    # access_time_calculator()
