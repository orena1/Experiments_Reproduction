#Xui_et al experment recreations
#Created by Oren Amsalem oren.a4@gmail.com
from __future__ import division
import os
import shutil
import sys
sys.path.append('../../Experiments_Reproduction/general_scripts/')
from HelpFuncs import SetCaKThresh, SetCaK, SetFacDep
from Cheetah.Template import Template
import subprocess
import numpy as np
import bluepy
import pickle
import h5py


execfile('../../Experiments_Reproduction/general_scripts/jobs_creation.py')
execfile('../../Experiments_Reproduction/general_scripts/opto_gen_protocols.py')
generalConfigPath = '/gpfs/bbp.cscs.ch/project/proj2/simulations/ThlInput/AudInput12_4_16/SSA/Ca1p23/EE0_EI0_IE0_II0_TM_0/Freq_Tono_4to16_FR_S100_W_S0p2_TwoStimsExp/BlueConfig6666_106686'

#for ca in [0.5,1.0,1.25,1.5,2.0,2.5]:
ca = float(1.25) #CAline
k = float(5.0)
Mg = float(1.0)
RunMode = 'RunMode LoadBalance'


change_gamma = True
core_neuron = True
knl = True
cluster = 'neuron_coreneuron' # bbpv1 # bbpviz1 # bbpv1core_neuron

if cluster == 'neuron_coreneuron':
    base_dir = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master_Core_22_9_18/soft'  # 'Master_Core_22_9_18' # use this Master_Core_28_12_18 to record voltage
    partition = 'prod'
    bbpviz_txt =  'module load neurodamus-neocortex/0.2/python3/parallel/serial \n'
    
    if knl == True:
        partition = 'prod_knl'
        bbpviz_txt =  'module load neurodamus-neocortex/0.3/knl/python3/parallel/serial \n'
    hoc_lib = ''
    init_name = 'init.hoc'
    special_path = ''' special -mpi '''
    ssh_path = 'bbpv1.epfl.ch'
    if knl == True:
        nodes = 30#55
        ntask_per_node = 64
    else:
        nodes = 96
        ntask_per_node = 36
        







simulation_time = "8:00:00"
nice_level = 3000
simulation_duration = 50000
circuit_target = 'mc2_Column'
RNGMode = 'Random123'
decouple = False
remove_spon_minis = False


reports = {}








def copy_files(path_for_simulations):
    print(path_for_simulations)
    model_folders = '../../Experiments_Reproduction/O1_v5/'
    FilesToCopy = ['launchScript_bg_template.sh', 'inputs.dat', 'user.target', 'BlueConfig_template']
    if not os.path.exists(path_for_simulations):
        os.makedirs(path_for_simulations)

    for FtC in FilesToCopy:
        shutil.copyfile(model_folders + FtC, path_for_simulations + '/' + FtC )

    shutil.copyfile(os.path.basename(__file__), path_for_simulations + '/' + os.path.basename(__file__) )

Circ = bluepy.Circuit(generalConfigPath)

run = '0'

seeds = range(10,30)#[1,2,3,4]

force_all_after_one=False
all_after_one=True
net_path = '/gpfs/bbp.cscs.ch/data/project/proj5/hub_attacks/networks/'
files = os.listdir(net_path)
##
#files = [i for i in files if 'random' not in i]
#hubs_attacked  = np.sort([int(i.split('_')[1].split('.')[0]) for i in files])
#attack_to_simulate = hubs_attacked
#files_to_simulate = [i for i in files if len([1 for j in attack_to_simulate if '{:05d}'.format(j)+'.(' in i])>0]


### random sample
rnd = np.random.RandomState(112) #112;70, 170;70, 70;45, 150;15 10,20 , 50, 35,120
files = [i for i in files if 'nodes' in i]
files_to_simulate = rnd.choice(files, size=70, replace =False)




run_names = []
paths_for_simulations = []
path_for_simulations = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/deep/8_10_19/Ca' + str(ca).replace('.','p') + '_K' + str(k).replace('.','p') +'/Spon/Run_' +str(run)  +  '/'
copy_files(path_for_simulations)


for seed in seeds:
    BS = seed*100000
    run_name = 'Spon_s' + str(BS)
    
    
    f = open(path_for_simulations +'/BlueConfig_template','r')
    blue_out = crate_blueconfig(BlueConfig_file=f, CurrentDir = path_for_simulations, BS = BS, simulation_duration = simulation_duration,
                                                            run_name=run_name, ca=ca, k=k, Mg=Mg, circuit_target = circuit_target , decouple=decouple,
                                                            optogenetic_vars=[],reports=reports,RunMode=RunMode, remove_spon_minis=remove_spon_minis,RNGMode=RNGMode, core_neuron=core_neuron)
    f = open(path_for_simulations + 'BlueConfig_' + run_name, 'w')
    f.write(blue_out)
    f.close()
    
    
    f = open(path_for_simulations +'/launchScript_bg_template.sh','r')
    launch_out = create_launch_script(launchScript_file=f, hoc_lib=hoc_lib, init_name=init_name, special_path=special_path, simulation_time=simulation_time,
                                                                        run_name=run_name, nice_level=nice_level, nodes=nodes, ntask_per_node=ntask_per_node, 
                                                                        bbpviz_txt = bbpviz_txt, partition=partition, core_neuron=core_neuron)
    f = open(path_for_simulations + 'launchScript_bg_' + run_name +'.sh', 'w')
    f.write(launch_out)
    f.close()

    if not os.path.exists(path_for_simulations + '/' + run_name): #If folder already exist do not send it.
        run_names.append('sbatch launchScript_bg_' + run_name +'.sh')
    else:
        print("simulation out directory already exist!")
    
    
    paths_for_simulations.append(path_for_simulations)
submit_jobs(run_names, paths_for_simulations, MaxJobs = 8,  all_after_one=all_after_one, ssh_path=ssh_path, force_all_after_one=force_all_after_one)


#neuron_reduce.subtree_reductor(..., total_segments_manual=-1)
