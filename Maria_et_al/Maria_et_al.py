#Xui_et al experment recreations
#Created by Oren Amsalem oren.a4@gmail.com
from __future__ import division
import os
import shutil
import sys
sys.path.append('../general_scripts/')
from HelpFuncs import SetCaKThresh, SetCaK, SetFacDep
from Cheetah.Template import Template
import subprocess
import numpy as np


execfile('../general_scripts/jobs_creation.py')
execfile('../general_scripts/opto_gen_protocols.py')

#for ca in [0.5,1.0,1.25,1.5,2.0,2.5]:
ca = 1.4 #CAline ?
k = 5.0
Mg = 1.0

var = 0.000001 # 0.000001 | 0.3 | 0.8

RunModeToNeurodamusPath = {'RunMode LoadBalance':['/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/hoclib','/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/powerpc64/special'], 
                        '#RunMode': ['/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/hoclib', '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/powerpc64/special']
                        }


bbpviz1 = False

if bbpviz1 == False:
## for bbpbg1
    hoc_lib = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master07_07_17/neurodamus/lib/hoclib'
    init_name = 'init.hoc'
    special_path = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master07_07_17/neurodamus/lib/powerpc64/special'
    nodes = 512
    ntask_per_node = 32
    partition = 'prod'
    bbpviz_txt= ''
    ssh_path = 'bbpbg2.cscs.ch'
else:
## for bbpviz1
    hoc_lib = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/hoclib'
    init_name = 'init.hoc'
    special_path = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/x86_64/special -mpi'
    nodes = 2
    ntask_per_node = 16
    partition = 'prod'
    bbpviz_txt = 'module load mvapich2/2.2b-slurm-nocuda-1 gcc/4.9.0 hdf5/1.8.16-1\n'\
                     'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/reportinglib/install/lib64\n\n'
    ssh_path = 'bbpviz1.cscs.ch'

    
    

remove_spon_minis = False
groups = False

groups='' if  groups == False else '_groups'
run = '1_LFP' + groups




path_for_simulations = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Maria_Neurophysiol_2010/18_08_2017/Ca' + \
                            str(ca).replace('.','p') + '_K' + str(k).replace('.','p') +'/Run_' +str(run)  +  '/Remove_Minis_' +str(remove_spon_minis) +'/var_' + str(var).replace('.','p').replace('-','_')+'/'

#hoc_lib = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/hoclib'
#init_name = 'init.hoc'
#special_path = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/powerpc64/special'



reports = {'soma_voltage':{
        'REPORT_TARGET':'mc2_Column',
        'START_TIME':str(0),
        'END_TIME':str(9e9)}}

RunMode = 'RunMode LoadBalance'
record_lfp = True
if record_lfp: 
    reports['LFP'] = {'START_TIME':str(0), 'END_TIME':str(9e9),'DT':str(0.1)}
    RunMode = 'RunMode WholeCell'


circuit_target = "mc2_Column"

simulation_time = "8:00:00"
nice_level = 0

opto_gen_stimstart = 2000
stim_durations = 3000 #Don't use 0.5 ms
simulation_duration = 5200

seeds = [1,2]

#amplitudes = [10, 30, 50, 100, 200, 500, 1500, 3000, 5000, 10000] 

#amplitudes = map(float,amplitudes)
#
#pulse_widths = [1.5,2.5]
#freqs = [2,4,8,16,32,40,48,60,70,80,100,200]


amplitudes = [0, -50]
amplitudes = map(float,amplitudes)


model_folders = '../O1_v5/'
FilesToCopy = ['launchScript_bg_template.sh', 'inputs.dat', 'user.target', 'BlueConfig_template']
if not os.path.exists(path_for_simulations):
    os.makedirs(path_for_simulations)
    
for FtC in FilesToCopy:
    shutil.copyfile(model_folders + FtC, path_for_simulations + '/' + FtC )

shutil.copyfile(os.path.basename(__file__), path_for_simulations + '/' + os.path.basename(__file__) )
print path_for_simulations
run_names = []
for seed in seeds:
    for amp in amplitudes:
        BS = seed*1000000 + int(amp*10) 
        run_name =  'amp_' + `float(amp)`.replace('.','p').replace('-','m') + '_BS' + `BS`
        stim_vars = {'PV_FS':[{'amp':amp,'start':opto_gen_stimstart,'dur':stim_durations, 'var':amp*var}]}
        morphs = ['PV_FS']
        
        f = open(path_for_simulations +'/BlueConfig_template','r')
        blue_out = crate_blueconfig(BlueConfig_file=f, CurrentDir = path_for_simulations, BS = BS, simulation_duration = simulation_duration,
                                                                run_name=run_name, ca=ca, k=k, Mg=Mg,circuit_target = circuit_target, optogenetic_vars=['current_injections', morphs, stim_vars],reports=reports,
                                                                RunMode = RunMode, remove_spon_minis=remove_spon_minis)
        f = open(path_for_simulations + 'BlueConfig_' + run_name, 'w')
        f.write(blue_out)
        f.close()
        
        
        f = open(path_for_simulations +'/launchScript_bg_template.sh','r')
        launch_out = create_launch_script(launchScript_file=f, hoc_lib=hoc_lib, init_name=init_name, special_path=special_path, simulation_time=simulation_time,
                                                                            run_name=run_name, nice_level=nice_level, nodes=nodes, ntask_per_node=ntask_per_node, 
                                                                            bbpviz_txt = bbpviz_txt, partition=partition)
        f = open(path_for_simulations + 'launchScript_bg_' + run_name +'.sh', 'w')
        f.write(launch_out)
        if record_lfp==True:
           f.write("\nssh bbpviz1.cscs.ch <<'ENDSSH' \n")
           f.write('PATH="/gpfs/bbp.cscs.ch/home/amsalem/anaconda2/bin:$PATH"\n')
           f.write('python /gpfs/bbp.cscs.ch/home/amsalem/Dropbox/Blue_Brain/Experiments_Reproduction/general_scripts/LFP_calculator.py ' + path_for_simulations + 'BlueConfig_' + run_name + "\nENDSSH")
           
        f.close()
        if not os.path.exists(path_for_simulations + '/' + run_name): #If folder already exist do not send it.
            run_names.append('sbatch launchScript_bg_' + run_name +'.sh')

submit_jobs(run_names, path_for_simulations, MaxJobs = 2,  all_after_one=True, ssh_path=ssh_path)
                    
                

BlueConfig = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Cardin_Nature_2009/31_07_2017/Ca1p23_K5p0/Run_2_LFP/Remove_Minis_False/var_1e_06/BlueConfig_freq40p0_amp3000p0_pulse_width2p5_BS1095000'





