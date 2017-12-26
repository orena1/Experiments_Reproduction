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


ca = 1.25 #CAline
k = 2.5
Mg = 1.0

var = 0.000001 # 0.000001 | 0.3 | 0.8

RunModeToNeurodamusPath = {'RunMode LoadBalance':['/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/hoclib','/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/powerpc64/special'], 
                           '#RunMode': ['/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/hoclib', '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/powerpc64/special']
                           }


remove_spon_minis = False
run = 'Groups_stims'

path_for_simulations = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Xue_Nature_2014/31_01_2017/Ca' +str(ca).replace('.','p') + '_K' + str(k).replace('.','p') +'/Run_' +str(run)  +  '/Remove_Minis_' +str(remove_spon_minis) +'/var_' + str(var).replace('.','p').replace('-','_')+'/'
hoc_lib = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/hoclib'
init_name = 'init.hoc'
special_path = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/powerpc64/special'

report = {'REPORT_TARGET':'mc2_Column',
          'START_TIME':str(1900),
          'END_TIME':str(9e9)}

simulation_time = "03:00:00"
nice_level = 0


opto_gen_stimstart = 2000
simulation_duration = 2100

seeds = [1]

amplitudes = [80,130,160,180,200,210,220,245,265,290,340,380,450] #Ca1p5 or Ca1p23
#amplitudes = [160,170,175,180,200,220] #Ca2p5



amplitudes = map(float,amplitudes)
stim_durations = [5] #Don't use 0.5 ms


model_folders = '../O1_v5/'
FilesToCopy = ['launchScript_bg_template.sh', 'inputs.dat', 'user.target', 'BlueConfig_template']
if not os.path.exists(path_for_simulations):
    os.makedirs(path_for_simulations)
    
for FtC in FilesToCopy:
    shutil.copyfile(model_folders + FtC, path_for_simulations + '/' + FtC )

shutil.copyfile(os.path.basename(__file__), path_for_simulations + '/' + os.path.basename(__file__) )




## This is for checking L23 firing rate


new_target = []
def create_partial_target(base_target,percent,seed):
    ''' percent is from 0-1'''

    rnd = np.random.RandomState(seed)
    f = open('/gpfs/bbp.cscs.ch/project/proj1/circuits/SomatosensoryCxS1-v5.r0/O1/merged_circuit/start.target','r')
    lines = f.readlines()
    for j,l in enumerate(lines):
        if 'Target Cell' in l and base_target in l:
            print 'dsf'
            l1 = lines[j+2]
            gids = l1.split()
            break
    new_gids = rnd.choice(gids,int(len(gids)*percent), replace=False)
    new_gids = ['a' + str(i) for i in np.sort([int(ii[1:]) for ii in new_gids])] 
    return([base_target + '_' + str(percent).replace('.','p'), new_gids])





num_gorups = 10
base_target = 'mc2_L4_PC'
targets = []
for i in range(num_gorups):
    targets.append(create_partial_target(base_target = base_target ,percent = 0.08,seed = 5*i))
    targets[-1][0] = targets[-1][0]  + str(i)
rnd = np.random.RandomState(12)
dur_percentes = [rnd.uniform(0.2,1.8) for i in range(num_gorups)]


for i in range(num_gorups):
    new_target = targets[i]
    f = open(path_for_simulations + 'user.target','a')
    f.write('Target Cell ' + new_target[0] + '\n{\n')
    [f.write(gid + ' ' ) for gid in new_target[1]];
    f.write('\n}\n\n')
    f.close()
    



run_names = []
for seed in seeds:
    for amp in amplitudes:
        for dur in stim_durations:
            BS = seed*100000 + int(amp*10) + int(dur*1000)
            run_name = 'amp' + `float(amp)`.replace('.','p') + '_dur' + `float(dur)`.replace('.','p') + '_BS' + `BS`
            
            stim_vars = {}
            morphs = []
            
            
            for i,target in enumerate(targets):
                stim_vars[target[0]] = [{'amp':amp*dur_percentes[i],'start':opto_gen_stimstart,'dur':dur, 'var':amp*var}]
                morphs.append(target[0])
            
            #stim_vars = {'Layer4Excitatory':[{'amp':amp,'start':opto_gen_stimstart,'dur':dur, 'var':amp*var}]}
            #morphs = ['Layer4Excitatory']
            
            f = open(path_for_simulations +'/BlueConfig_template','r')
            blue_out = crate_blueconfig(BlueConfig_file=f, CurrentDir = path_for_simulations, BS = BS, simulation_duration = simulation_duration,
                                                                    run_name=run_name, ca=ca, k=k, Mg=Mg, optogenetic_vars=['current_injections', morphs, stim_vars],report=report,
                                                                    remove_spon_minis=remove_spon_minis)
            f = open(path_for_simulations + 'BlueConfig_' + run_name, 'w')
            f.write(blue_out)
            f.close()
            
            
            f = open(path_for_simulations +'/launchScript_bg_template.sh','r')
            launch_out = create_launch_script(launchScript_file=f, hoc_lib=hoc_lib, init_name=init_name, special_path=special_path, simulation_time=simulation_time,
                                                                                run_name=run_name, nice_level=nice_level)
            f = open(path_for_simulations + 'launchScript_bg_' + run_name +'.sh', 'w')
            f.write(launch_out)
            f.close()
            if not os.path.exists(path_for_simulations + '/' + run_name): #If folder already exist do not send it.
                run_names.append('sbatch launchScript_bg_' + run_name +'.sh')

submit_jobs(run_names, path_for_simulations, MaxJobs = 8,  all_after_one=False)
                    
                    















