from __future__ import division
from numpy import *
import numpy as np
import time
import os
import subprocess
import sys
import pickle


if len(sys.argv)>1:
    BlueConfig = sys.argv[1]
    print('BlueConfig=' + BlueConfig)
else:
    BlueConfig = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Cardin_Nature_2009/31_07_2017/Ca1p23_K5p0/Run_2_LFP/Remove_Minis_False/var_1e_06/BlueConfig_freq40p0_amp3000p0_pulse_width2p5_BS1095000'
command = '--target mc2_Column --report=AllCompartmentsMembrane '


f = open(BlueConfig,'r')
for l in f: 
    if 'OutputRoot' in l: 
        out_dir = l.split()[1]
        os.chdir(out_dir)
    if 'Duration' in l: #get simulation time
        simulation_time = l.split()[1]
    if '}' in l:
        break
    


##################
##### This is for running one work using emsim
####################
def build_sbatch_script(points, file_name, number_of_files):
    """
    Build sbatch script for a certain frame range
    points - list of x y z points
    """

    values = {}
    out_file = BlueConfig.split('/')[-1][11:]
    point_txt = ''
    for point in points:
        point_txt += ' --sample-point ' + ','.join(map(str,point))
        
                                                                                                                                                        #There is a bug when it breaks at 29 ms before the end
    ptxt = '/gpfs/bbp.cscs.ch/home/chevtche/EMSimNew/Release/bin/emsim -i ' + BlueConfig + ' ' + command + ' --start-time 0 --end-time ' + str(int(simulation_time)-50) + ' -o ' + out_dir +'/' + file_name + ' '   + point_txt
    values['ptxt'] = ptxt
    
    values['job_name'] = out_file + file_name
    values['job_time'] = '48:00:00'
    values['queue'] = 'prod'
    values['account'] = 'proj2'
    values['nodes'] = 1
    values['tasks_per_node'] = 16
    values['output_dir'] = out_dir



    sbatch_script = '\n'.join((
        '#!/bin/bash',
        '#SBATCH --job-name="{job_name}"',
        '#SBATCH --time="{job_time}"',
        '#SBATCH --partition="{queue}"',
        '#SBATCH --account="{account}"',
        '#SBATCH --nodes="{nodes}"',
        '#SBATCH --ntasks-per-node="{tasks_per_node}"',
        '#SBATCH --output="{output_dir}/{job_name}_out.txt"',
        '#SBATCH --error="{output_dir}/{job_name}_err.txt"',
        '#SBATCH --exclusive',
        'cd {output_dir}',
        'module load BBP/viz/latest',
        '',
        '{ptxt}',
        'PATH="/gpfs/bbp.cscs.ch/home/amsalem/anaconda2/bin:$PATH"\n',
        'python /gpfs/bbp.cscs.ch/home/amsalem/Dropbox/Blue_Brain/Experiments_Reproduction/general_scripts/lfp_sample_point_clean_up.py ' + out_dir +' ' + str(number_of_files) +' ',
        
    )).format(**values)

    return sbatch_script


locs_to_save = pickle.load(open('/gpfs/bbp.cscs.ch/project/proj2/simulations/locs_for_lfp10_7_18.p','r'))['locs_to_save']

if os.path.exists('out.dat'):
    number_of_files = int(np.ceil(len(locs_to_save)/15))
    for i in range(number_of_files):
        sbatch_script = build_sbatch_script(locs_to_save[i*15:(i+1)*15], file_name='LFP_' + str(i+1), number_of_files=number_of_files)
        sbatch = subprocess.Popen(['sbatch'], stdin=subprocess.PIPE)
        print(sbatch_script)
        sbatch.communicate(input=sbatch_script)

    
    
else:
    print("Out file does not exist, LFP will not be calcualted.") 




