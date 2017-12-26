#Xui_et al experment recreations
#Created by Oren Amsalem oren.a4@gmail.com
import os
import shutil
import sys
sys.path.append('../general_scripts/')
from HelpFuncs import SetCaKThresh, SetCaK, SetFacDep
from Cheetah.Template import Template
import subprocess

execfile('../general_scripts/jobs_creation.py')
execfile('../general_scripts/opto_gen_protocols.py')


ca = 2.0 #CAline
k = 5.0
Mg = 1.0



RunModeToNeurodamusPath = {'RunMode LoadBalance':['/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/hoclib','/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/powerpc64/special'], 
                           '#RunMode': ['/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/hoclib', '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/powerpc64/special']
                           }


remove_spon_minis = True

path_for_simulations = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Xue_Nature_2014/31_01_2017/Ca' + str(ca).replace('.','p') + '/Run_1/Remove_Minis_' +str(remove_spon_minis) +'/'
hoc_lib = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/hoclib'
init_name = 'init.hoc'
special_path = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/powerpc64/special'

report = {'REPORT_TARGET':'mc2_Column',
          'START_TIME':str(1900),
          'END_TIME':str(2100)}

simulation_time = "03:00:00"
nice_level = 0


opto_gen_stimstart = 2000
simulation_duration = 2100

seeds = [1]
#seeds = [5,6]
#amplitudes = [0.3,0.5,0.9,1.1]
amplitudes = [30.0,50.0,90.0,110.0]

stim_durations = [0.5,2.5,5]

model_folders = '../O1_v5/'
FilesToCopy = ['launchScript_bg_template.sh', 'inputs.dat', 'user.target', 'BlueConfig_template']
if not os.path.exists(path_for_simulations):
    os.makedirs(path_for_simulations)
    
for FtC in FilesToCopy:
    shutil.copyfile(model_folders + FtC, path_for_simulations + '/' + FtC )

shutil.copyfile(os.path.basename(__file__), path_for_simulations + '/' + os.path.basename(__file__) )

run_names = []
for seed in seeds:
    for amp in amplitudes:
        for dur in stim_durations:
            BS = seed*100000 + int(amp*10) + int(dur*1000)
            run_name = 'amp' + `float(amp)`.replace('.','p') + '_dur' + `float(dur)`.replace('.','p') + '_BS' + `BS`
            stim_vars = {'Layer4Excitatory':[{'amp':amp,'start':opto_gen_stimstart,'dur':dur}]}
            morphs = ['Layer4Excitatory']
            
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
            
            run_names.append('sbatch launchScript_bg_' + run_name +'.sh')

submit_jobs(run_names, path_for_simulations, MaxJobs = 6,  all_after_one=True)
                    
                    















