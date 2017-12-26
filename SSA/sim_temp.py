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


execfile('../../OSI_files/CreateSimFiles_GitHub/CreateAxonalSpikeFilePossionGenerator_clean_auditory.py')
execfile('../general_scripts/jobs_creation.py')
execfile('../general_scripts/opto_gen_protocols.py')

#for ca in [0.5,1.0,1.25,1.5,2.0,2.5]:
ca = 1.25 #CAline
k = 5.0
Mg = 1.0


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

    
nice_level = 1000    
circuit_target = "mc2_Column"
remove_spon_minis = False
reports = {}


RunMode = 'RunMode LoadBalance'
record_lfp = False
if record_lfp: 
    reports['LFP'] = {'START_TIME':str(0), 'END_TIME':str(9e9),'DT':str(0.1)}
    RunMode = 'RunMode WholeCell'

def set_main_path(BasePath, ca, k, DisableUseDep, Disable_CortoCortical, remove_SK_E2, SSA):
    txt = BasePath + '/Ca' + str(ca).replace('.','p') + '_K' + str(k).replace('.','p') + '/'
    if Disable_CortoCortical==False:
        txt += 'EE0_' if ('Excitatory', 'Excitatory') in DisableUseDep else 'EE1_'
        txt += 'EI0_' if ('Excitatory', 'Inhibitory') in DisableUseDep else 'EI1_'
        txt += 'IE0_' if ('Inhibitory', 'Excitatory') in DisableUseDep else 'IE1_'
        txt += 'II0_' if ('Inhibitory', 'Inhibitory') in DisableUseDep else 'II1_'
    else:
        txt +='disableCorticalCons_'
    txt += 'TM0' if ('proj_Thalamocortical_VPM_Source', 'Mosaic') in DisableUseDep else 'TM1'
    
    if remove_SK_E2==True:
        txt = txt.replace('SSA','SSA_No_SK_E2')
    if SSA==0:
        txt = txt.replace('SSA','FRA')
    return(txt)


def create_path_and_copy_file(path_for_simulations):
    model_folders = '../O1_v5/'
    FilesToCopy = ['launchScript_bg_template.sh', 'inputs.dat', 'user.target', 'BlueConfig_template']
    if not os.path.exists(path_for_simulations):
        os.makedirs(path_for_simulations)
        
    for FtC in FilesToCopy:
        if not os.path.exists(path_for_simulations + '/' + FtC):
            shutil.copyfile(model_folders + FtC, path_for_simulations + '/' + FtC )

    shutil.copyfile(os.path.basename(__file__), path_for_simulations + '/' + os.path.basename(__file__) )




BasePath = '/gpfs/bbp.cscs.ch/project/proj2/simulations/ThlInput/AudInput15_12_17_new_architecture/SSA/'



experiment = {}

experiment['prefered_frequency_distribution'] = 'tonotopic'
experiment['width_value']       = 1.0


experiment['duration_of_stim']        = 30 
experiment['duration_between_stims']  = 270  #End to start
experiment['first_stimulus_time']     = 2000

experiment['ssa_presentations']     = 100
experiment['ssa_standard_probability'] = 0.9
experiment['ssa_presentations_seed'] = 1 

experiment['spontaneous_firing_rate_type'] = 'constant' #When I have sontaneuos firing rate, it will be added to the osi firing rate, which means that the firing rate will be higher than the one which was set in the 
experiment['spontaneous_firing_rate_value'] = 0 

experiment['simulation_end_time']     = (experiment['duration_between_stims'] + experiment['duration_of_stim'])*experiment['ssa_presentations'] + experiment['first_stimulus_time']  

AxoGidToXY = pickle.load(open(os.environ['HOME'] + '/AxoGidToXY.p','r'))
experiment['axons_settings']  = [AxoGidToXY]
experiment['prefered_frequency_boundaries'] = [4000, 16000]
experiment['tunnig_curve_type'] = 'triangle'

simulation_time = "36:00:00" # real run time
simulation_duration = experiment['simulation_end_time']   # bilogical time

experiment['stim_type'] = 'alpha_func'
experiment['alpha_func_delay'] = 15
experiment['alpha_func_tau']   = 2.65
experiment['axon_stim_firing_rate']  = 370





SSA = 1
seed = 1

def set_directory(experiment):
    if round(experiment['prefered_frequency_boundaries'][0]/1000.0,1) != round(experiment['prefered_frequency_boundaries'][0]/1000.0,2) or round(experiment['prefered_frequency_boundaries'][1]/1000.0,1) != round(experiment['prefered_frequency_boundaries'][1]/1000.0,2):
        raise Exception('We do not save a frequency with 2 numbers after the rounding point')
    Directory = 'Freq_Tono_' + str(round(experiment['prefered_frequency_boundaries'][0]/1000.0,1)).replace('.','p') + 'to' + str(round(experiment['prefered_frequency_boundaries'][1]/1000.0,1)).replace('.','p')  + \
                '_FR_S' + str(experiment['axon_stim_firing_rate']) + '_W_S' + str(experiment['width_value']).replace('.','p') + \
                '_TC_' + experiment['tunnig_curve_type'][:3] + '_ST_' + experiment['stim_type'] + '_Pres' + str(experiment['ssa_presentations'])
    if SSA==1: Directory+= '_SSA_p' +  str(1-experiment['ssa_standard_probability']).replace('.','p') +  '_' + experiment['SSAType']
    return(Directory)


SSATypes = ['TwoStimsPeriodic','TwoStims']
DisableUseDeps = [[], [('Excitatory', 'Inhibitory'), ('Excitatory', 'Excitatory'), ('Inhibitory', 'Excitatory'), ('Inhibitory','Inhibitory'), ('proj_Thalamocortical_VPM_Source', 'Mosaic')]]
Disable_CortoCorticals = [True,False]
remove_SK_E2s = [True,False]
#for SSA simulations
run_names = []

for SSAType in SSATypes:
    for DisableUseDep in DisableUseDeps:
        for remove_SK_E2 in remove_SK_E2s:
            for Disable_CortoCortical in Disable_CortoCorticals:
                for Standard,Deviant in [[6666,9600],[9600,6666]]:
                    init_name = 'init_NoSK_E2.hoc' if remove_SK_E2 else 'init.hoc'
                    experiment['SSAType'] = SSAType
                    experiment['stand_dev_couple'] = [Standard,Deviant]

                    BS = seed*(int(experiment['width_value']*100)+100000)+Standard
                    path_for_simulations = set_main_path(BasePath, ca, k, DisableUseDep, Disable_CortoCortical, remove_SK_E2, SSA) + '/' + set_directory(experiment) +'/'
                    create_path_and_copy_file(path_for_simulations)
                    print path_for_simulations
                    spike_replay = path_for_simulations + '/SpikeFiles/input' + str(Standard) + '_' + `BS` + '.dat'
                    print(spike_replay)
                    run_name = str(Standard) + '_' + `BS` 
                    
                    ## need to use this one.
                    job_name =  'Stand' + `float(Standard)` +  '_Dev' + `float(Deviant)` + '_Ca' + `float(ca)`.replace('.','p') + '_BS' + `BS` + '_DisUse' + `DisableUseDep`


                    #
                    # Chr options can be added here
                    #
                    

                    experiment['frequencies']     = SSA_protocol_stimulations(experiment)
                    create_axons_spikes(BS, experiment, save_path=spike_replay );

                    f = open(path_for_simulations +'/BlueConfig_template','r')
                    blue_out = crate_blueconfig(BlueConfig_file=f, CurrentDir = path_for_simulations, BS = BS, simulation_duration = simulation_duration,
                                                                            run_name=run_name, ca=ca, k=k, Mg=Mg,circuit_target = circuit_target, decouple=Disable_CortoCortical, optogenetic_vars=[],
                                                                            DisableUseDep = DisableUseDep,reports=reports,
                                                                            RunMode = RunMode, remove_spon_minis=remove_spon_minis, spike_replay=spike_replay)
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

#submit_jobs(run_names, path_for_simulations, MaxJobs = 2,  all_after_one=True, ssh_path=ssh_path)
                    
                

BlueConfig = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Cardin_Nature_2009/31_07_2017/Ca1p23_K5p0/Run_2_LFP/Remove_Minis_False/var_1e_06/BlueConfig_freq40p0_amp3000p0_pulse_width2p5_BS1095000'





