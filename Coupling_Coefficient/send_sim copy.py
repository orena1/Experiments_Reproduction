#create current injection and mesure CC
from __future__ import division
import os
import shutil
import sys
sys.path.append('../general_scripts/')

from Cheetah.Template import Template
import subprocess
import numpy as np
import bluepy
import pickle

execfile('../general_scripts/jobs_creation.py')
execfile('../general_scripts/opto_gen_protocols.py')




#for ca in [0.5,1.0,1.25,1.5,2.0,2.5]:
ca = float(1.23) #CAline
k = float(5.0)
Mg = float(1.0)



change_gamma = True
core_neuron = False
knl = False
cluster = 'neuron_coreneuron' # bbpv1 # bbpviz1 # bbpv1core_neuron
#if core_neuron==True or knl:
    #raise Exception("Does not work")
if cluster == 'neuron_coreneuron':
    
    partition = 'prod'
    hoc_lib = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Gap_Junctions/hoclib/'
    init_name = 'init_remove_active.hoc'
    special_path = ''' special -mpi '''
    
    bbpviz_txt =  'export MODULEPATH=/gpfs/bbp.cscs.ch/project/proj64/home/kumbhar/softwares/modules/tcl/linux-rhel7-x86_64:$MODULEPATH\n'\
                    + 'module load neurodamus/plasticity-knl\n'\
                    + 'module load synapsetool/0.3.2\n'\
                    + 'module load reportinglib/develop\n'\
                    + 'export HOC_LIBRARY_PATH=/gpfs/bbp.cscs.ch/project/proj2/simulations/Gap_Junctions/hoclib/'
    ssh_path = 'bbpv1.epfl.ch'
    if knl == True:
        nodes = 25
        ntask_per_node = 64
    else:
        nodes = 30
        ntask_per_node = 36
        

def create_path_and_copy_file(path_for_simulations):
    model_folders = '../O1_v6_20171212/'
    FilesToCopy = ['launchScript_bg_template.sh', 'inputs.dat', 'user.target', 'BlueConfig_template']
    if not os.path.exists(path_for_simulations):
        os.makedirs(path_for_simulations)
        
    for FtC in FilesToCopy:
        if not os.path.exists(path_for_simulations + '/' + FtC):
            shutil.copyfile(model_folders + FtC, path_for_simulations + '/' + FtC )

    shutil.copyfile(os.path.basename(__file__), path_for_simulations + '/' + os.path.basename(__file__) )
    
    

nice_level = 0    
circuit_target = "PV_mc2"
remove_spon_minis = False
reports = {}
RNGMode = 'Random123'

RunMode = 'RunMode LoadBalance'


reports['soma_voltage'] = {'REPORT_TARGET':'PV_mc2','START_TIME':str(0), 'END_TIME':str(9e9),'DT':str(0.1)}
    



BS = 0 # seed
simulation_time = "12:00:00" # real run time


ca = -1
k = -1
Mg = -1
circuit_target_name = circuit_target
Disable_CortoCortical = False
DisableUseDep = False
spike_replay = None
projection_path = None


path_for_simulations = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Gap_Junctions/current_injections_v3_remove_active/'
create_path_and_copy_file(path_for_simulations)
print(path_for_simulations)
gids_to_test = [2011, 2391, 2500, 3121, 4782, 8077, 157388, 136577, 14559, 6150]

for gid in gids_to_test:
    f = open(path_for_simulations + 'user.target','a')
    f.write('Target Cell a' + str(gid) + '\n{\n')
    f.write('   a' + str(gid))
    f.write('\n}\n\n')
    f.close()


run_name = 'num_0'
run_names = []
## need to use this one.
job_name =  'Current_injections'


#
# Chr options 
#
stim_num = 3
stim_dur = 400
stim_isi = 400

stim_vars = {'a' + str(gid):[{'amp':-70,'start':1000 + (stim_dur+stim_isi)*stim_num*j,'dur':(stim_dur+stim_isi)*stim_num, 'var':0, 'pulse_width': stim_dur , 'freq': 1000/(stim_dur+stim_isi)}] 
                for j,gid in enumerate(gids_to_test)}
 
optogenetic_vars=['pulse_train', ['a' + str(gid) for gid in gids_to_test], stim_vars]
pickle.dump(stim_vars,open(path_for_simulations +'/stim_var.p','w'),2)

simulation_duration = len(gids_to_test)*((stim_dur+stim_isi)*stim_num) + 1000


#for ssrun_time in range(0,simulation_duration + 60000,60000):
f = open(path_for_simulations +'/BlueConfig_template','r')
blue_out = crate_blueconfig(BlueConfig_file=f, CurrentDir = path_for_simulations, BS = BS, simulation_duration = simulation_duration,
                                                        run_name=run_name, ca=ca, k=k, Mg=Mg,circuit_target = circuit_target_name, decouple=Disable_CortoCortical, optogenetic_vars=optogenetic_vars,
                                                        DisableUseDep = DisableUseDep,reports=reports,
                                                        RunMode = RunMode, remove_spon_minis=remove_spon_minis, spike_replay=spike_replay, RNGMode=RNGMode, core_neuron=core_neuron, projection_path=projection_path)
f = open(path_for_simulations + 'BlueConfig_' + run_name, 'w')
f.write(blue_out)
f.close()


f = open(path_for_simulations +'/launchScript_bg_template.sh','r')
launch_out = create_launch_script(launchScript_file=f, hoc_lib=hoc_lib, init_name=init_name, special_path=special_path, simulation_time=simulation_time,
                                                                    run_name=run_name, nice_level=nice_level, nodes=nodes, ntask_per_node=ntask_per_node, 
                                                                    bbpviz_txt = bbpviz_txt, partition=partition, job_name=job_name, core_neuron=core_neuron)
f = open(path_for_simulations + 'launchScript_bg_' + run_name +'.sh', 'w')
f.write(launch_out)
f.close()

if not os.path.exists(path_for_simulations + '/' + run_name): #If folder already exist do not send it.
    run_names.append('sbatch launchScript_bg_' + run_name +'.sh')
else:
    print('************ Job already submitted, not sure if completed **************')
#as it is per directory I need to submit the jobs here!

submit_jobs(run_names, path_for_simulations, MaxJobs = 1,  all_after_one=True, ssh_path=ssh_path)

