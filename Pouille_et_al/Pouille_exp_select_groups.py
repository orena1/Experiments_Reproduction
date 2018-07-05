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
var = 0.000001 # 0.000001 |0.3


core_neuron = False
cluster = 'bbpv1' # bbpv1 # bbpviz1 # bbpv1core_neuron

if cluster == 'bbpviz1':
    ## for bbpbg1
    raise Exception('not_working_yet')
elif cluster == 'bbpv1':
    ## for bbpv1
    hoc_lib = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master07_04_18/neurodamus/lib/hoclib'
    init_name = 'init.hoc'
    special_path = '--mpi=pmi2 /gpfs/bbp.cscs.ch/project/proj2/Programs/Master07_04_18/neurodamus/lib/x86_64/special -mpi'
    nodes = 16
    ntask_per_node = 36
    partition = 'prod'
    bbpviz_txt = 'module load nix/hdf5/1.10.1 intel-parallel-studio/cluster.2018.1\n'\
                     'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/gpfs/bbp.cscs.ch/project/proj2/Programs/Master07_04_18/bbpviz1NeuRep/reportinglib/install/lib64\n\n'
    ssh_path = 'bbpv1.epfl.ch'
elif cluster == 'bbpv1core_neuron':
    hoc_lib = '/gpfs/bbp.cscs.ch/project/proj2/Programs/CoreNeuron_12_4_18/bbp5/sources/neurodamus/lib_gamma/hoclib'
    init_name = 'init.hoc'
    special_path = '''--mpi=pmi2 $NEURON_EXE -mpi -c 'strdef simulator' -c simulator='"CORENEURON"' '''
    nodes = 16
    ntask_per_node = 36
    partition = 'prod'
    bbpviz_txt = 'module intel-parallel-studio/cluster.2018.1\n\n'\
                  'export NEURON_EXE=/gpfs/bbp.cscs.ch/project/proj2/Programs/CoreNeuron_12_4_18/bbp5/sources/neurodamus/lib_gamma/x86_64/special\n'\
                  'export CORENEURON_EXE=/gpfs/bbp.cscs.ch/project/proj2/Programs/CoreNeuron_12_4_18/bbp5/install/bin/coreneuron_exec\n' \
                  'export HOC_LIBRARY_PATH=/gpfs/bbp.cscs.ch/project/proj2/Programs/CoreNeuron_12_4_18/bbp5/sources/neurodamus/lib/hoclib\n' \
                  'export LD_LIBRARY_PATH=/gpfs/bbp.cscs.ch/project/proj2/Programs/CoreNeuron_12_4_18/bbp5/install/lib64:$LD_LIBRARY_PATH\n'

    ssh_path = 'bbpv1.epfl.ch'
    core_neuron = True




NMDA_GAMMA = True
if NMDA_GAMMA==True:
    special_path = special_path.replace('lib','lib_gamma')



simulation_time = "09:25:00"
nice_level = 1200
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
amplitudes = [410,450,500,550,600,700,800,900,1500,2500,3500,4500]  # Ca1p5 # Ca2p0

run = 'Groups_stims_1'

amplitudes = map(float,amplitudes)




path_for_simulations = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Pouille_2009/09_05_2018/Ca' + str(ca).replace('.','p') + '_K' + str(k).replace('.','p') +'/Run_' +str(run)  +  '_step/Remove_Minis_' +str(remove_spon_minis) +'/var_' + str(var).replace('.','p').replace('-','_')+'/'
print(path_for_simulations)
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

base_target = 'mc2_L23_PC'
targets = []
for i in range(num_gorups):
    targets.append(create_partial_target(base_target = base_target ,percent = 0.05,seed = 5*i))
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



stim_durations = [5]
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

submit_jobs(run_names, path_for_simulations, MaxJobs = 18,  all_after_one=True, ssh_path=ssh_path)
                    
print('dfsdfdsf')



#### Ramp
amplitudes = [300,340,450,200,250,280,310,340,370,410,450,500,550,700,900,1200,1300,1500,1600,1650,1700,1750,1800,1900,2000,2100,2300,2500,3500] # Ca1p5 # Ca2p0

if var!=0.000001:
    raise Exception("No var is not 0.00001 no need to run ramp, as ramp does not have var!")

path_for_simulations = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Pouille_2009/09_05_2018/Ca'  \
                           + str(ca).replace('.','p') + '_K' + str(k).replace('.','p') +'/Run_' +str(run)  +  '_ramp/Remove_Minis_' +str(remove_spon_minis) +'/var_' + str(var).replace('.','p').replace('-','_')+'/'
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

stim_durations = [10]
run_names = []
for seed in seeds:
    for amp in amplitudes:
        for dur in stim_durations:
            BS = seed*100000 + int(amp*10) + int(dur*1000)
            run_name = 'amp' + `float(amp)`.replace('.','p') + '_dur' + `float(dur)`.replace('.','p') + '_BS' + `BS`
            stim_vars = {'L23_PC':[{'amp_start':0,'amp_end':amp,'start':opto_gen_stimstart,'dur':dur}]}
            morphs = ['L23_PC']
            
            f = open(path_for_simulations +'/BlueConfig_template','r')
            blue_out = crate_blueconfig(BlueConfig_file=f, CurrentDir = path_for_simulations, BS = BS, simulation_duration = simulation_duration,
                                                                    run_name=run_name, ca=ca, k=k, Mg=Mg, circuit_target=circuit_target, decouple=decouple,
                                                                    optogenetic_vars=['ramp_current_injections', morphs, stim_vars],reports=reports, remove_spon_minis=remove_spon_minis)
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
            if not os.path.exists(path_for_simulations + '/' + run_name):
                run_names.append('sbatch launchScript_bg_' + run_name +'.sh')

submit_jobs(run_names, path_for_simulations, MaxJobs = 5,  all_after_one=True, ssh_path=ssh_path)
                    

  
