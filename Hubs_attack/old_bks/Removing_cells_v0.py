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

execfile('../../Experiments_Reproduction/general_scripts/jobs_creation.py')
execfile('../../Experiments_Reproduction/general_scripts/opto_gen_protocols.py')
generalConfigPath = '/gpfs/bbp.cscs.ch/project/proj2/simulations/ThlInput/AudInput12_4_16/SSA/Ca1p23/EE0_EI0_IE0_II0_TM_0/Freq_Tono_4to16_FR_S100_W_S0p2_TwoStimsExp/BlueConfig6666_106686'

ca = 1.4 #CAline
k = 5.0
Mg = 1.0
var = 0.000001 # 0.000001 |0.3


bbpviz1 = True

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
    hoc_lib = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master07_04_18/neurodamus/lib/hoclib'
    init_name = 'init.hoc'
    special_path = '--mpi=pmi2 /gpfs/bbp.cscs.ch/project/proj2/Programs/Master07_04_18/neurodamus/lib/x86_64/special -mpi'
    nodes = 24
    ntask_per_node = 36
    partition = 'prod'
    bbpviz_txt = 'module load nix/hdf5/1.10.1 intel-parallel-studio/cluster.2018.1\n'\
                     'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/gpfs/bbp.cscs.ch/project/proj2/Programs/Master07_04_18/bbpviz1NeuRep/reportinglib/install/lib64\n\n'
    ssh_path = 'bbpv1.epfl.ch'

RunMode = 'RunMode LoadBalance'

def add_to_user_target(gids, target_name, path_for_simulations):
    for l in open(path_for_simulations + 'user.target','r'):
        if 'Target Cell ' + target_name + '\n{\n' in l:
            _ = raw_input('Target already exist, will not readd it ok?')
            return()
    gids = np.sort(gids).astype(int)
    f = open(path_for_simulations + 'user.target','a')
    f.write('Target Cell ' + target_name + '\n{\n')
    [f.write('a' + str(gid) + ' ' ) for gid in gids];
    f.write('\n}\n\n')
    f.close()



simulation_time = "8:00:00"
nice_level = 0
simulation_duration = 10000
circuit_target = 'mc2_Column'
decouple = False
remove_spon_minis = False

#reports = {'soma_voltage':{
        #'REPORT_TARGET':'mc2_Column',
        #'START_TIME':str(1900),
        #'END_TIME':str(9e9)}}

reports = {}


seeds = [1]

run = 'hubs' # hubs | random | remove_none



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

if 'hubs' in run: 
    gids_to_remove = pickle.load(open('/gpfs/bbp.cscs.ch/project/proj2/simulations/Hubs_attack/data_from_Noam_23_04_2018/hubs_dict2.pk1','r'))
    force_all_after_one=True
elif 'random' in run:
    gids_to_remove = pickle.load(open('/gpfs/bbp.cscs.ch/project/proj2/simulations/Hubs_attack/data_from_Noam_23_04_2018/random_nodes_dict2.pk1','r'))
    force_all_after_one=True
elif 'remove_none' in run:
    gids_to_remove = {'':''}
    force_all_after_one=False
    seeds = [1,2,3,4,5,6,7,8,9,10]



run_names = []
paths_for_simulations = []
for set_n in gids_to_remove:
    path_for_simulations = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Hubs_attack/23_04_2018/Ca' + str(ca).replace('.','p') + '_K' + str(k).replace('.','p') +'/Run_' +str(run)  +  '/' + set_n +'/'

    copy_files(path_for_simulations)
    gids_to_simulate = list(set(Circ.targets.targets[circuit_target].resolve_contents_gids()) - set(gids_to_remove[set_n]))
    add_to_user_target(gids_to_simulate, circuit_target + '_' + set_n, path_for_simulations)
    

    for seed in seeds:
        BS = seed*100000
        run_name = 'set_' + str(set_n) + '_r' + str(len(gids_to_remove[set_n])) +'_s' + str(BS)
        
        
        f = open(path_for_simulations +'/BlueConfig_template','r')
        blue_out = crate_blueconfig(BlueConfig_file=f, CurrentDir = path_for_simulations, BS = BS, simulation_duration = simulation_duration,
                                                                run_name=run_name, ca=ca, k=k, Mg=Mg, circuit_target = circuit_target + '_' + set_n, decouple=decouple,
                                                                optogenetic_vars=[],reports=reports,RunMode=RunMode, remove_spon_minis=remove_spon_minis)
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
        paths_for_simulations.append(path_for_simulations)

submit_jobs(run_names, paths_for_simulations, MaxJobs = 8,  all_after_one=False, ssh_path=ssh_path, force_all_after_one=force_all_after_one)
