import pandas as pd
import os
import numpy as np
from matplotlib import pyplot as plt

res_dir = 'cb_results'
data_dir = os.path.join(os.getcwd(), res_dir)

df = pd.DataFrame(columns=['cores', 'l1d_size', 'l1d_assoc', 'l2_size', 'l2_assoc', 'sim_name', 'sim_ticks'])

for subdir, dirs, files in os.walk(data_dir):
    for file in files:
        if file.endswith(".txt"):
            cores = (subdir.split('\\' + res_dir + '\\')[1]).split('_')[0]
            l1d_size = (subdir.split('\\' + res_dir + '\\')[1]).split('_')[1]
            l1d_assoc = (subdir.split('\\' + res_dir + '\\')[1]).split('_')[2]
            l2_size = (subdir.split('\\' + res_dir + '\\')[1]).split('_')[3]
            l2_assoc = (subdir.split('\\' + res_dir + '\\')[1]).split('_')[4]
            sim_name = (subdir.split('\\' + res_dir + '\\')[1]).split('_')[5]

            with open(os.path.join(subdir, file)) as res_file:
                sim_ticks = 0
                for line in res_file:
                    line = line.strip()
                    if "sim_ticks" in line:
                        for temp in line.split():
                            if temp.isdigit():
                                sim_ticks = int(temp)
            if sim_ticks != 0:
                aux = pd.DataFrame(np.array([[cores, l1d_size, l1d_assoc, l2_size, l2_assoc, sim_name, sim_ticks]]),
                                   columns=['cores', 'l1d_size', 'l1d_assoc', 'l2_size', 'l2_assoc', 'sim_name',
                                            'sim_ticks'])
                df = df.append(aux, ignore_index=True)

fmm_data = df.loc[df['sim_name'] == 'fmm']
ocean_data = df.loc[df['sim_name'] == 'ocean']
fft_data = df.loc[df['sim_name'] == 'fft']
result = pd.merge(fmm_data, ocean_data, on=['cores', 'l1d_size', 'l1d_assoc', 'l2_size', 'l2_assoc'])
result = pd.merge(result, fft_data, on=['cores', 'l1d_size', 'l1d_assoc', 'l2_size', 'l2_assoc'])
print(result)
result.to_csv("merged.csv")
