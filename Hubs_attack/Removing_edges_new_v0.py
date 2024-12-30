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
ca = float(1.4) #CAline
k = float(5.0)
Mg = float(1.0)
RunMode = 'RunMode LoadBalance'


change_gamma = True
core_neuron = True
knl = True
cluster = 'neuron_coreneuron' # bbpv1 # bbpviz1 # bbpv1core_neuron

loadmodule='''export ARCHIVE_MODULE_DATE="2019-09"
export MODULEPATH=/gpfs/bbp.cscs.ch/apps/hpc/jenkins//modules/compilers/${ARCHIVE_MODULE_DATE}/tcl/linux-rhel7-x86_64
export MODULEPATH=$MODULEPATH:/gpfs/bbp.cscs.ch/apps/hpc/jenkins//modules/tools/${ARCHIVE_MODULE_DATE}/tcl/linux-rhel7-x86_64
export MODULEPATH=$MODULEPATH:/gpfs/bbp.cscs.ch/apps/hpc/jenkins//modules/external-libraries/${ARCHIVE_MODULE_DATE}/tcl/linux-rhel7-x86_64
export MODULEPATH=$MODULEPATH:/gpfs/bbp.cscs.ch/apps/hpc/jenkins//modules/serial-libraries/${ARCHIVE_MODULE_DATE}/tcl/linux-rhel7-x86_64
export MODULEPATH=$MODULEPATH:/gpfs/bbp.cscs.ch/apps/hpc/jenkins//modules/parallel-libraries/${ARCHIVE_MODULE_DATE}/tcl/linux-rhel7-x86_64
export MODULEPATH=$MODULEPATH:/gpfs/bbp.cscs.ch/apps/hpc/jenkins//modules/applications/${ARCHIVE_MODULE_DATE}/tcl/linux-rhel7-x86_64'''

if cluster == 'neuron_coreneuron':
    base_dir = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master_Core_22_9_18/soft'  # 'Master_Core_22_9_18' # use this Master_Core_28_12_18 to record voltage
    partition = 'prod'
    #Not tested with non-knl!!!
    bbpviz_txt =  loadmodule + '\nmodule load neurodamus-neocortex/0.3/python3/parallel/serial \n . /gpfs/bbp.cscs.ch/home/amsalem/damus_venv/bin/activate'
    
    if knl == True:
        partition = 'prod_knl'
        bbpviz_txt =  loadmodule + '\nmodule load neurodamus-neocortex/0.3/knl/python3/parallel/serial \n . /gpfs/bbp.cscs.ch/home/amsalem/damus_venv/bin/activate'
    hoc_lib = ''
    init_name = ''
    special_path = ''' special -mpi -python attack_run.py'''
    ssh_path = 'bbpv1.epfl.ch'
    if knl == True:
        nodes = 30#55
        ntask_per_node = 64
    else:
        nodes = 96
        ntask_per_node = 36
        





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



simulation_time = "4:00:00"
nice_level = 0
simulation_duration = 10000
circuit_target = 'mc2_Column'
RNGMode = 'Random123'
decouple = False
remove_spon_minis = False


reports = {}







def create_hard_coded_python_run(path_for_simulations, attack_path):
    f = open(path_for_simulations + '/' + 'attack_run.py','r')
    txt = ''
    for line in f:
        if '@attack_path' in line:
            txt += line.replace('@attack_path', "'" + attack_path + "'")
        else:
            txt +=line
    f.close()
    f = open(path_for_simulations + '/' + 'attack_run.py','w')
    f.write(txt)
    f.close()
    
    
def copy_files(path_for_simulations):
    print(path_for_simulations)
    model_folders = '../../Experiments_Reproduction/O1_v5/'
    FilesToCopy = ['launchScript_bg_template.sh', 'inputs.dat', 'user.target', 'BlueConfig_template', 'attack_run.py']
    if not os.path.exists(path_for_simulations):
        os.makedirs(path_for_simulations)

    for FtC in FilesToCopy:
        shutil.copyfile(model_folders + FtC, path_for_simulations + '/' + FtC )

    shutil.copyfile(os.path.basename(__file__), path_for_simulations + '/' + os.path.basename(__file__) )

Circ = bluepy.Circuit(generalConfigPath)

run = '0'

seeds = [1,2]#,3]

force_all_after_one=False
all_after_one=True
net_path = '/gpfs/bbp.cscs.ch/data/project/proj5/hub_attacks/networks/'
files = os.listdir(net_path)
## DONT USE THIS BELOW!!!
# files = [i for i in files if 'random' not in i]
# hubs_attacked  = np.sort([int(i.split('_')[1].split('.')[0]) for i in files])
# attack_to_simulate = hubs_attacked
# files_to_simulate = [i for i in files if len([1 for j in attack_to_simulate if '{:05d}'.format(j)+'.(' in i])>0]


### random sample
rnd = np.random.RandomState(273) # 271:40270:100,170:70 
files = [i for i in files if 'edges' in i]# and ('ihub' in i or 'ehub' in i)]
files_to_simulate = rnd.choice(files, size=80, replace =False)



for attack in files_to_simulate:
    clean_attack = attack.replace('(','_').replace(')','_')[:-3]
    run_names = []
    paths_for_simulations = []
    path_for_simulations = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/29_7_19/Ca' + str(ca).replace('.','p') + '_K' + str(k).replace('.','p') +'/Run_' +str(run)  +  '/' + clean_attack +'/'
    if os.path.exists(path_for_simulations):#if base_folder exist, skip
        print("simulation exist!")
        continue
    copy_files(path_for_simulations)
    
    create_hard_coded_python_run(path_for_simulations, net_path +'/' + attack)
    #h5_file = h5py.File(net_path +'/' + attack)
    #gids_to_simulate = list(set(Circ.targets.targets[circuit_target].resolve_contents_gids()) - set(list(h5_file['nodes'])))
    #add_to_user_target(gids_to_simulate, circuit_target + '_' + clean_attack, path_for_simulations)
    circuit_target = 'mc2_Column'

    for seed in seeds:
        BS = seed*100000
        run_name = clean_attack +'_s' + str(BS)
        
        
        f = open(path_for_simulations +'/BlueConfig_template','r')
        blue_out = crate_blueconfig(BlueConfig_file=f, CurrentDir = path_for_simulations, BS = BS, simulation_duration = simulation_duration,
                                                                run_name=run_name, ca=ca, k=k, Mg=Mg, circuit_target = circuit_target, decouple=decouple,
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
            print("sim exist!")
        
        
        paths_for_simulations.append(path_for_simulations)
    submit_jobs(run_names, paths_for_simulations, MaxJobs = 8,  all_after_one=all_after_one, ssh_path=ssh_path, force_all_after_one=force_all_after_one)
    #dasdasd
