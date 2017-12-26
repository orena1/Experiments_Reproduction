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


ca = 2.0 #CAline
k = 2.5
Mg = 1.0
var = 0.3 # 0.00001|0.3


bbpviz1 = False

if bbpviz1 == False:
## for bbpbg1
    hoc_lib = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/hoclib'
    init_name = 'init.hoc'
    special_path = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/powerpc64/special'
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
    partition = 'test'
    bbpviz_txt = 'module load mvapich2/2.2b-slurm-nocuda-1 gcc/4.9.0 hdf5/1.8.16-1\n'\
                     'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/reportinglib/install/lib64\n\n'
    ssh_path = 'bbpviz1.cscs.ch'





simulation_time = "02:25:00"
nice_level = 0
opto_gen_stimstart = 2000
simulation_duration = 2250
circuit_target = 'mc2_Column'
decouple = False
remove_spon_minis = False

reports = {'soma_voltage':{
        'REPORT_TARGET':'mc2_Column',
        'START_TIME':str(1900),
        'END_TIME':str(9e9)}}


seeds = [1]
amplitudes = [250,280,310,340,370,400] # Ca1p5 # Ca2p0



amplitudes = map(float,amplitudes)


new_target = []
run = 1

## This is for checking L23 firing rate
#exp_num =2
#circuit_target = 'mc2_L23_PC'

#def create_partial_target(base_target,percent,seed):
    #''' percent is from 0-1'''

    #rnd = np.random.RandomState(seed)
    #f = open('/gpfs/bbp.cscs.ch/project/proj1/circuits/SomatosensoryCxS1-v5.r0/O1/merged_circuit/start.target','r')
    #lines = f.readlines()
    #for j,l in enumerate(lines):
        #if 'Target Cell' in l and circuit_target in l:
            #print 'dsf'
            #l1 = lines[j+2]
            #gids = l1.split()
            #break
    #new_gids = rnd.choice(gids,int(len(gids)*percent), replace=False)
    #new_gids = ['a' + str(i) for i in np.sort([int(ii[1:]) for ii in new_gids])] 
    #return([base_target + '_' + str(percent).replace('.','p'), new_gids])

#new_target = create_partial_target(base_target ='mc2_L23_PC' ,percent = 0.05,seed = 5)
#circuit_target  = new_target[0]
#decouple = False

## Step


path_for_simulations = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Pouille_2009/02_03_2017/Ca' + str(ca).replace('.','p') + '_K' + str(k).replace('.','p') +'/Run_' +str(run)  +  '_step/Remove_Minis_' +str(remove_spon_minis) +'/var_' + str(var).replace('.','p').replace('-','_')+'/'
print(path_for_simulations)
model_folders = '../O1_v5/'
FilesToCopy = ['launchScript_bg_template.sh', 'inputs.dat', 'user.target', 'BlueConfig_template']
if not os.path.exists(path_for_simulations):
    os.makedirs(path_for_simulations)

for FtC in FilesToCopy:
    shutil.copyfile(model_folders + FtC, path_for_simulations + '/' + FtC )

if len(new_target)!=0:
    f = open(path_for_simulations + 'user.target','a')
    f.write('Target Cell ' + new_target[0] + '\n{\n')
    [f.write(gid + ' ' ) for gid in new_target[1]];
    f.write('\n}')
    f.close()

shutil.copyfile(os.path.basename(__file__), path_for_simulations + '/' + os.path.basename(__file__) )

stim_durations = [5]
run_names = []
for seed in seeds:
    for amp in amplitudes:
        for dur in stim_durations:
            BS = seed*100000 + int(amp*10) + int(dur*1000)
            run_name = 'amp' + `float(amp)`.replace('.','p') + '_dur' + `float(dur)`.replace('.','p') + '_BS' + `BS`
            stim_vars = {'mc2_L23_PC':[{'amp':amp,'start':opto_gen_stimstart,'dur':dur, 'var':amp*var}]}
            morphs = ['mc2_L23_PC']
            
            f = open(path_for_simulations +'/BlueConfig_template','r')
            blue_out = crate_blueconfig(BlueConfig_file=f, CurrentDir = path_for_simulations, BS = BS, simulation_duration = simulation_duration,
                                                                    run_name=run_name, ca=ca, k=k, Mg=Mg, circuit_target = circuit_target, decouple=decouple,
                                                                    optogenetic_vars=['current_injections', morphs, stim_vars],reports=reports, remove_spon_minis=remove_spon_minis)
            f = open(path_for_simulations + 'BlueConfig_' + run_name, 'w')
            f.write(blue_out)
            f.close()
            
            
            f = open(path_for_simulations +'/launchScript_bg_template.sh','r')
            launch_out = create_launch_script(launchScript_file=f, hoc_lib=hoc_lib, init_name=init_name, special_path=special_path, simulation_time=simulation_time,
                                                                                run_name=run_name, nice_level=nice_level, nodes=nodes, ntask_per_node=ntask_per_node, 
                                                                                bbpviz_txt = bbpviz_txt, partition=partition)
            f = open(path_for_simulations + 'launchScript_bg_' + run_name +'.sh', 'w')
            f.write(launch_out)
            f.close()
            if not os.path.exists(path_for_simulations + '/' + run_name): #If folder already exist do not send it.
                run_names.append('sbatch launchScript_bg_' + run_name +'.sh')

submit_jobs(run_names, path_for_simulations, MaxJobs = 8,  all_after_one=True, ssh_path=ssh_path)
                    
print('dfsdfdsf')



#### Ramp

if var!=0.00001:
    raise Exception("No var is not 0.00001 no need to run ramp, as ramp does not have var!")

#path_for_simulations = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Pouille_2009/02_03_2017/Ca'  \
                           #+ str(ca).replace('.','p') + '_K' + str(k).replace('.','p') +'/Run_' +str(run)  +  '_ramp/Remove_Minis_' +str(remove_spon_minis) +'/var_' + str(var).replace('.','p').replace('-','_')+'/'
#model_folders = '../O1_v5/'
#FilesToCopy = ['launchScript_bg_template.sh', 'inputs.dat', 'user.target', 'BlueConfig_template']
#if not os.path.exists(path_for_simulations):
    #os.makedirs(path_for_simulations)
    
#for FtC in FilesToCopy:
    #shutil.copyfile(model_folders + FtC, path_for_simulations + '/' + FtC )

#if len(new_target)!=0:
    #f = open(path_for_simulations + 'user.target','a')
    #f.write('Target Cell ' + new_target[0] + '\n{\n')
    #[f.write(gid + ' ' ) for gid in new_target[1]];
    #f.write('\n}')
    #f.close()
#shutil.copyfile(os.path.basename(__file__), path_for_simulations + '/' + os.path.basename(__file__) )

#stim_durations = [10]
#run_names = []
#for seed in seeds:
    #for amp in amplitudes:
        #for dur in stim_durations:
            #BS = seed*100000 + int(amp*10) + int(dur*1000)
            #run_name = 'amp' + `float(amp)`.replace('.','p') + '_dur' + `float(dur)`.replace('.','p') + '_BS' + `BS`
            #stim_vars = {'L23_PC':[{'amp_start':0,'amp_end':amp,'start':opto_gen_stimstart,'dur':dur}]}
            #morphs = ['L23_PC']
            
            #f = open(path_for_simulations +'/BlueConfig_template','r')
            #blue_out = crate_blueconfig(BlueConfig_file=f, CurrentDir = path_for_simulations, BS = BS, simulation_duration = simulation_duration,
                                                                    #run_name=run_name, ca=ca, k=k, Mg=Mg, circuit_target=circuit_target, decouple=decouple,
                                                                    #optogenetic_vars=['ramp_current_injections', morphs, stim_vars],reports=reports, remove_spon_minis=remove_spon_minis)
            #f = open(path_for_simulations + 'BlueConfig_' + run_name, 'w')
            #f.write(blue_out)
            #f.close()
            
            
            #f = open(path_for_simulations +'/launchScript_bg_template.sh','r')
            #launch_out = create_launch_script(launchScript_file=f, hoc_lib=hoc_lib, init_name=init_name, special_path=special_path, simulation_time=simulation_time,
                                                                                #run_name=run_name, nice_level=nice_level, nodes=nodes, ntask_per_node=ntask_per_node, 
                                                                                #bbpviz_txt = bbpviz_txt, partition=partition)
            #f = open(path_for_simulations + 'launchScript_bg_' + run_name +'.sh', 'w')
            #f.write(launch_out)
            #f.close()
            #if not os.path.exists(path_for_simulations + '/' + run_name):
                #run_names.append('sbatch launchScript_bg_' + run_name +'.sh')

#submit_jobs(run_names, path_for_simulations, MaxJobs = 7,  all_after_one=True, ssh_path=ssh_path)
                    

  
