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
import bluepy
tm_text = ''
tm_text1 = ''
execfile('../../OSI_files/CreateSimFiles_GitHub/CreateAxonalSpikeFilePossionGenerator_clean_auditory.py')
execfile('../general_scripts/jobs_creation.py')
execfile('../general_scripts/opto_gen_protocols.py')
generalConfigPath = '/gpfs/bbp.cscs.ch/project/proj2/simulations/ThlInput/AudInput12_4_16/SSA/Ca1p23/EE0_EI0_IE0_II0_TM_0/Freq_Tono_4to16_FR_S100_W_S0p2_TwoStimsExp/BlueConfig6666_106686'
#print  'Loading all  took ' +  `time.time() - STloadTM` + ' secs'
blue_config_circ = bluepy.Circuit(generalConfigPath)


def set_directory(experiment):
    if round(experiment['prefered_frequency_boundaries'][0]/1000.0,2) != round(experiment['prefered_frequency_boundaries'][0]/1000.0,3) or round(experiment['prefered_frequency_boundaries'][1]/1000.0,2) != round(experiment['prefered_frequency_boundaries'][1]/1000.0,3):
        raise Exception('We do not save a frequency with 2 numbers after the rounding point')
    Directory = 'Freq_Tono_' + str(round(experiment['prefered_frequency_boundaries'][0]/1000.0,2)).replace('.','p') + 'to' + str(round(experiment['prefered_frequency_boundaries'][1]/1000.0,2)).replace('.','p')  + \
                '_FR_m' + str(experiment['axon_stim_firing_rate_gaussian_mean']).replace('.','p') + '_std' + str(experiment['axon_stim_firing_rate_gaussian_std']).replace('.','p') +\
                '_W_T' + experiment['tunning_width_distribution'][:3]
    if experiment['tunning_width_distribution'] ==  'gaussian':  Directory+= '_m' + str(experiment['tunning_width_gaussian_mean']).replace('.','p') + '_std' + str(experiment['tunning_width_gaussian_std']).replace('.','p')
    if experiment['tunning_width_distribution'] ==  'exp'     :  Directory+= '_m' + str(experiment['tunning_width_exp_loc']).replace('.','p') + '_std' + str(experiment['tunning_width_exp_scale']).replace('.','p')
    Directory += '_TC_' + experiment['tunnig_curve_type'][:3] + '_ST_' + experiment['stim_type'] 
    if experiment['stim_type']=='alpha_func': 
        Directory+= '_DT_' + experiment['alpha_func_delay_distribution'][:3]
        if   experiment['alpha_func_delay_distribution'] == 'frequency_correlated':
            Directory+= '_del_b' + str(experiment['delays_gaus_base_line']).replace('.','p') + '_norm' + str(experiment['delays_gaus_norm_factor']).replace('.','p') + '_std' + str(experiment['delays_gaus_std']).replace('.','p')
        elif experiment['alpha_func_delay_distribution'] == 'gaussian':
            Directory+= '_del_m' + str(experiment['alpha_func_delay_gaussian_mean']).replace('.','p') + '_std' + str(experiment['alpha_func_delay_gaussian_std']).replace('.','p')
        Directory+= '_tau_m' + str(experiment['alpha_func_tau_gaussian_mean']).replace('.','p') + '_std' + str(experiment['alpha_func_tau_gaussian_std']).replace('.','p')

    Directory+= '_Pres' + str(experiment['ssa_presentations']) + '_resPro' + str(experiment['responsive_axons_probability']).replace('.','p')
    if SSA==1: Directory+= '_SSA_p' +  str(1-experiment['ssa_standard_probability']).replace('.','p') +  '_' + experiment['SSAType']
    if experiment['circuit_target']!="mc2_Column":
        Directory+= '/mc2_X' + `experiment['circuit_target']['x'][0]`.replace('-','m') + 'to'+ `experiment['circuit_target']['x'][1]`.replace('-','m') + \
                        '_Y' + `experiment['circuit_target']['y'][0]`.replace('-','m') + 'to'+ `experiment['circuit_target']['y'][1]`.replace('-','m') + \
                        '_Z' + `experiment['circuit_target']['z'][0]`.replace('-','m') + 'to'+ `experiment['circuit_target']['z'][1]`.replace('-','m') +'/'
    return(Directory)




#for ca in [0.5,1.0,1.25,1.5,2.0,2.5]:
ca = float(1.23) #CAline
k = float(5.0)
Mg = float(1.0)



change_gamma = True
core_neuron = True
knl = True
cluster = 'neuron_coreneuron' # bbpv1 # bbpviz1 # bbpv1core_neuron

if cluster == 'bbpviz1':
    ## for bbpbg1
    raise Exception('not_working_yet')
elif cluster == 'bbpv1':
    ## for bbpv1
    hoc_lib = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master07_04_18/neurodamus/lib/hoclib'
    init_name = 'init.hoc'
    special_path = '--mpi=pmi2 /gpfs/bbp.cscs.ch/project/proj2/Programs/Master07_04_18/neurodamus/lib/x86_64/special -mpi'
    nodes = 24
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
    bbpviz_txt = 'module load intel-parallel-studio/cluster.2018.1\n\n'\
                  'export NEURON_EXE=/gpfs/bbp.cscs.ch/project/proj2/Programs/CoreNeuron_12_4_18/bbp5/sources/neurodamus/lib_gamma/x86_64/special\n'\
                  'export CORENEURON_EXE=/gpfs/bbp.cscs.ch/project/proj2/Programs/CoreNeuron_12_4_18/bbp5/install/bin/coreneuron_exec\n' \
                  'export HOC_LIBRARY_PATH=/gpfs/bbp.cscs.ch/project/proj2/Programs/CoreNeuron_12_4_18/bbp5/sources/neurodamus/lib/hoclib\n' \
                  'export LD_LIBRARY_PATH=/gpfs/bbp.cscs.ch/project/proj2/Programs/CoreNeuron_12_4_18/bbp5/install/lib64:$LD_LIBRARY_PATH\n'

    ssh_path = 'bbpv1.epfl.ch'
    core_neuron = True
    
elif cluster == 'neuron_coreneuron':
    base_dir = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master_Core_22_9_18/soft'
    if change_gamma:
        base_dir = base_dir.replace('soft', 'soft_gamma')
    if knl == True:
        base_dir = base_dir.replace('soft_gamma','soft_gamma_knl')
        if change_gamma==False: 
            base_dir = base_dir.replace('soft','soft_knl')
    hoc_lib = base_dir + '/sources/neurodamus/lib/hoclib'
    init_name = 'init.hoc'
    special_path = ''' special -mpi '''
    partition = 'prod'
    bbpviz_txt =  'module load hpe-mpi nix/cmake\n\n'\
                  'export BASE_DIR=' + base_dir + '\n'\
                  'export LD_LIBRARY_PATH=$BASE_DIR/install/lib64:$BASE_DIR/install/lib:$LD_LIBRARY_PATH\n'\
                  'export PATH=$BASE_DIR/sources/neurodamus/lib/x86_64:$PATH\n'
    ssh_path = 'bbpv1.epfl.ch'
    if knl == True:
        nodes = 55
        ntask_per_node = 64
    else:
        nodes = 16
        ntask_per_node = 36


nice_level = 0    
circuit_target = "mc2_Column"
remove_spon_minis = False
reports = {}
RNGMode = 'Random123'

RunMode = 'RunMode LoadBalance'
record_lfp = False
if record_lfp: 
    reports['LFP'] = {'START_TIME':str(0), 'END_TIME':str(9e9),'DT':str(0.1)}
    RunMode = 'RunMode WholeCell'

def set_main_path(BasePath, ca, k, DisableUseDep, Disable_CortoCortical, remove_SK_E2, SSA):
    txt = BasePath + '/Ca' + str(ca).replace('.','p') + '_K' + str(k).replace('.','p') + '/'
    if Disable_CortoCortical==False:
        if ('Excitatory','mc2_depressive_target_of_exc') in DisableUseDep:
            txt += 'Edep0_'
        else:
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



BasePath = '/gpfs/bbp.cscs.ch/project/proj2/simulations/ThlInput/AudInput23_09_18/SSA/'


experiment = {}

experiment['prefered_frequency_distribution'] = 'tonotopic'



experiment['duration_of_stim']        = 30 
experiment['duration_between_stims']  = 270  #End to start
experiment['first_stimulus_time']     = 2000

experiment['ssa_presentations']     = 500
experiment['ssa_standard_probability'] = 0.95



experiment['ssa_presentations_seed'] = 1 

experiment['spontaneous_firing_rate_type'] = 'constant' #When I have sontaneuos firing rate, it will be added to the osi firing rate, which means that the firing rate will be higher than the one which was set in the 
experiment['spontaneous_firing_rate_value'] = 0 

experiment['simulation_end_time']     = (experiment['duration_between_stims'] + experiment['duration_of_stim'])*experiment['ssa_presentations'] + experiment['first_stimulus_time']  

AxoGidToXY = pickle.load(open(os.environ['HOME'] + '/AxoGidToXY.p','r'))
experiment['axons_settings']  = [AxoGidToXY]
#experiment['prefered_frequency_boundaries'] = [5660, 11310] # 1 octave
#experiment['prefered_frequency_boundaries'] = [4760, 13450] # 1.5 octaves
experiment['prefered_frequency_boundaries'] = [4000, 16000] # 2 octvaes


simulation_time = "24:00:00" # real run time
simulation_duration = experiment['simulation_end_time']   # bilogical time

#Tunning curve
experiment['tunnig_curve_type'] = 'triangle' #'exp', 'triangle'






#Read Data from fit!

amp_to_dist_vals = {}

amp_to_dist_vals[30] = {'tun_width_dist': 'exp', 'w_exp_scale':0.231, 'w_exp_loc': 0.64, 'fr_dist':'gaussian', 'fr_guas_mean': 88, 'fr_gaus_std':60, 'alph_func_dist':'gaussian', 'alph_tau_mean': 4.1, 'alph_tau_std':2.1,
'delay_gaus_norm_f': 2.53, 'delay_gaus_std':0.957}
amp_to_dist_vals[40] = {'tun_width_dist': 'exp', 'w_exp_scale':0.621, 'w_exp_loc': 0.2, 'fr_dist':'gaussian', 'fr_guas_mean': 338, 'fr_gaus_std':207, 'alph_func_dist':'gaussian', 'alph_tau_mean': 2.4, 'alph_tau_std':1.5,
'delay_gaus_norm_f': 2.62, 'delay_gaus_std':0.605}
amp_to_dist_vals[50] = {'tun_width_dist': 'exp', 'w_exp_scale':0.619, 'w_exp_loc': 0.36, 'fr_dist':'gaussian', 'fr_guas_mean': 437, 'fr_gaus_std':269, 'alph_func_dist':'gaussian', 'alph_tau_mean': 2.3, 'alph_tau_std':0.78,
'delay_gaus_norm_f': 4.68, 'delay_gaus_std':0.663}
amp_to_dist_vals[60] = {'tun_width_dist': 'exp', 'w_exp_scale':0.88, 'w_exp_loc': 0.24, 'fr_dist':'gaussian', 'fr_guas_mean': 448, 'fr_gaus_std':179, 'alph_func_dist':'gaussian', 'alph_tau_mean': 2.3, 'alph_tau_std':0.88,
'delay_gaus_norm_f': 6.53, 'delay_gaus_std':0.676}
amp_to_dist_vals[70] = {'tun_width_dist': 'exp', 'w_exp_scale':1.07, 'w_exp_loc': 0.36, 'fr_dist':'gaussian', 'fr_guas_mean': 466, 'fr_gaus_std':163, 'alph_func_dist':'gaussian', 'alph_tau_mean': 2.5, 'alph_tau_std':0.86,
'delay_gaus_norm_f': 2.85, 'delay_gaus_std':0.241}
amp_to_dist_vals[80] = {'tun_width_dist': 'exp', 'w_exp_scale':1.32, 'w_exp_loc': 0.67, 'fr_dist':'gaussian', 'fr_guas_mean': 459, 'fr_gaus_std':120, 'alph_func_dist':'gaussian', 'alph_tau_mean': 2.7, 'alph_tau_std':1.0,
'delay_gaus_norm_f': 4.89, 'delay_gaus_std':0.129}
amp_to_dist_vals[90] = {'tun_width_dist': 'exp', 'w_exp_scale':1.76, 'w_exp_loc': 0.86, 'fr_dist':'gaussian', 'fr_guas_mean': 497, 'fr_gaus_std':164, 'alph_func_dist':'gaussian', 'alph_tau_mean': 2.8, 'alph_tau_std':1.3,
'delay_gaus_norm_f': 3.8, 'delay_gaus_std':0.2}




##vvvvvvv new fit data:  19_8_18, only changes that I want:vvvv

#amp_to_dist_vals[30] = {'tun_width_dist': 'exp', 'w_exp_scale':0.231, 'w_exp_loc': 0.64, 'fr_dist':'gaussian', 'fr_guas_mean': 88, 'fr_gaus_std':60, 'alph_func_dist':'gaussian', 'alph_tau_mean': 4.1, 'alph_tau_std':2.1,
#'delay_gaus_norm_f': 2.53, 'delay_gaus_std':0.957, 'base_line': 21.5 }
amp_to_dist_vals[40] = {'tun_width_dist': 'exp', 'w_exp_scale':0.621, 'w_exp_loc': 0.2, 'fr_dist':'gaussian', 'fr_guas_mean': 338, 'fr_gaus_std':207, 'alph_func_dist':'gaussian', 'alph_tau_mean': 2.4, 'alph_tau_std':1.5,
'delay_gaus_norm_f': 2.62, 'delay_gaus_std':0.605, 'base_line': 21.4 }
amp_to_dist_vals[50] = {'tun_width_dist': 'exp', 'w_exp_scale':0.719, 'w_exp_loc': 0.19, 'fr_dist':'gaussian', 'fr_guas_mean': 421, 'fr_gaus_std':262, 'alph_func_dist':'gaussian', 'alph_tau_mean': 2.1, 'alph_tau_std':0.85,
'delay_gaus_norm_f': 4.68, 'delay_gaus_std':0.663, 'base_line': 24.1 }
amp_to_dist_vals[60] = {'tun_width_dist': 'exp', 'w_exp_scale':0.9, 'w_exp_loc': 0.24, 'fr_dist':'gaussian', 'fr_guas_mean': 440, 'fr_gaus_std':175, 'alph_func_dist':'gaussian', 'alph_tau_mean': 2.3, 'alph_tau_std':0.88,
'delay_gaus_norm_f': 6.53, 'delay_gaus_std':0.672, 'base_line': 20.8 }
#amp_to_dist_vals[70] = {'tun_width_dist': 'exp', 'w_exp_scale':1.06, 'w_exp_loc': 0.36, 'fr_dist':'gaussian', 'fr_guas_mean': 477, 'fr_gaus_std':167, 'alph_func_dist':'gaussian', 'alph_tau_mean': 2.4, 'alph_tau_std':0.94,
#'delay_gaus_norm_f': 2.85, 'delay_gaus_std':0.242, 'base_line': 19.9 }
amp_to_dist_vals[80] = {'tun_width_dist': 'exp', 'w_exp_scale':1.45, 'w_exp_loc': 0.67, 'fr_dist':'gaussian', 'fr_guas_mean': 453, 'fr_gaus_std':119, 'alph_func_dist':'gaussian', 'alph_tau_mean': 2.7, 'alph_tau_std':0.97,
'delay_gaus_norm_f': 4.89, 'delay_gaus_std':0.137, 'base_line': 15.0 }
#amp_to_dist_vals[90] = {'tun_width_dist': 'exp', 'w_exp_scale':1.76, 'w_exp_loc': 0.86, 'fr_dist':'gaussian', 'fr_guas_mean': 496, 'fr_gaus_std':165, 'alph_func_dist':'gaussian', 'alph_tau_mean': 2.8, 'alph_tau_std':1.3,
#'delay_gaus_norm_f': 3.74, 'delay_gaus_std':0.192, 'base_line': 17.6 }




def change_all_to_same_width(source_amp, amp_to_dist_vals):
    for amp in amp_to_dist_vals:
        for parm in amp_to_dist_vals[amp]:
            if parm in ['w_exp_scale','w_exp_loc']:
                amp_to_dist_vals[amp][parm]  = amp_to_dist_vals[source_amp][parm]
    return(amp_to_dist_vals)


def change_all_to_same_fr(source_amp, amp_to_dist_vals):
    for amp in amp_to_dist_vals:
        for parm in amp_to_dist_vals[amp]:
            if parm in ['fr_dist','fr_guas_mean', 'fr_gaus_std']:
                amp_to_dist_vals[amp][parm]  = amp_to_dist_vals[source_amp][parm]
    return(amp_to_dist_vals)

### #set values for amp
##--------
def set_exp_by_amp(amp):
    experiment['tunning_width_distribution']       = amp_to_dist_vals[amp]['tun_width_dist']
    experiment['tunning_width_exp_scale']          = amp_to_dist_vals[amp]['w_exp_scale']
    experiment['tunning_width_exp_loc']            = amp_to_dist_vals[amp]['w_exp_loc']

    experiment['axon_stim_firing_rate_distribution']       = amp_to_dist_vals[amp]['fr_dist']
    experiment['axon_stim_firing_rate_gaussian_mean']       = amp_to_dist_vals[amp]['fr_guas_mean']
    experiment['axon_stim_firing_rate_gaussian_std']       = amp_to_dist_vals[amp]['fr_gaus_std']

    experiment['alpha_func_tau_distribution'] = amp_to_dist_vals[amp]['alph_func_dist']
    experiment['alpha_func_tau_gaussian_mean'] = amp_to_dist_vals[amp]['alph_tau_mean']
    experiment['alpha_func_tau_gaussian_std']  = amp_to_dist_vals[amp]['alph_tau_std']

    experiment['alpha_func_delay_distribution'] = 'frequency_correlated'
    experiment['delays_gaus_norm_factor'] = amp_to_dist_vals[amp]['delay_gaus_norm_f']
    experiment['delays_gaus_std']         = amp_to_dist_vals[amp]['delay_gaus_std']
    experiment['delays_gaus_base_line'] = float(18) ## I remove 10 ms so I will not need to fix the concept that each presentation is 30 ms!

##--------

check_amp_on_csi_control = False
check_amp_on_csi_control_same_fr = False
if check_amp_on_csi_control and check_amp_on_csi_control_same_fr:
    raise Exception('You can not have both True')

source_amp = 80
if check_amp_on_csi_control:
    raw_input('You are now changing w_exp_scale w_exp_loc of all amps to the value of ' + str(source_amp))
    amp_to_dist_vals = change_all_to_same_width(80, amp_to_dist_vals)


if check_amp_on_csi_control_same_fr:
    raw_input('You are now changing fr_dist fr_guas_mean and fr_gaus_std of all amps to the value of ' + str(source_amp))
    amp_to_dist_vals = change_all_to_same_fr(80, amp_to_dist_vals)


### This is very IMPORTANT, do not delete it!
experiment['stim_type'] = 'alpha_func'
experiment['duration_of_stim']             = 300 
experiment['duration_between_stims']       = 0  #End to start
experiment['responsive_axons_probability'] = float(0.58)








pref_boundary_vals = [[4000, 16000]]
center_frequencies = [(6666, 9600)]
experiment['center_frequencies'] = center_frequencies

experiment['circuit_target'] = circuit_target
Ca_vals = [1.23]
k_vals = [float(4.15)]


for amp in [60]:#40,50,60,70,80]:
    set_exp_by_amp(amp)
    #for x_start in [50,240,260,280,300,320]:
        #circuit_target = {'x':[x_start,600], 'y':[-9000,9000], 'z':[-9000,9000]}
        #experiment['circuit_target'] = circuit_target
    
        #for w_exp_loc in [0.1,0.45,0.65,0.85]:
            #experiment['tunning_width_exp_loc'] = w_exp_loc
    for change_delay in [False]:#[False, True]:
        #Set all delays to the same value
        if change_delay == True:
            experiment['alpha_func_delay_distribution'] = 'gaussian'
            experiment['alpha_func_delay_gaussian_mean'] = float(5) ## I remove 10 ms so I will not need to fix the concept that each presentation is 30 ms!
            experiment['alpha_func_delay_gaussian_std'] = float(0)
            
        for ca in Ca_vals:
            for k in k_vals:

                SSA = 1
                seed = 1
                SSATypes = ['TwoStims']

                #SSATypes = ['DeviantAlone']
                #SSATypes = ['DiverseNarrowExp']
                SSATypes = ['Equal']; experiment['ssa_standard_probability'] = 0.5
                #DisableUseDeps = [[], [('Excitatory', 'Inhibitory'), ('Excitatory', 'Excitatory'), ('Inhibitory', 'Excitatory'), ('Inhibitory','Inhibitory'), ('proj_Thalamocortical_VPM_Source', 'Mosaic')]]
                #DisableUseDeps =[[('Excitatory', 'Inhibitory'), ('Excitatory', 'Excitatory'), ('Inhibitory', 'Excitatory'), ('Inhibitory','Inhibitory'), ('proj_Thalamocortical_VPM_Source', 'Mosaic')]]
                DisableUseDeps = [[]]#,[('Excitatory', 'Inhibitory'), ('Excitatory', 'Excitatory'), ('Inhibitory', 'Excitatory'), ('Inhibitory','Inhibitory'), ('proj_Thalamocortical_VPM_Source', 'Mosaic')]]
                #DisableUseDeps = [[],[('proj_Thalamocortical_VPM_Source', 'Mosaic'),('Excitatory','mc2_depressive_target_of_exc')]]
                
                
                
                Disable_CortoCorticals = [False]
                remove_SK_E2s = [False]
                #for SSA simulations
                run_names = []
                

                
                for SSAType in SSATypes:
                    if SSAType in ['TwoStims', 'TwoStimsPeriodic', 'TwoStimsPeriodicP9_29', 'DeviantAlone']:
                        center_frequencies = [center_frequencies[0], center_frequencies[0][::-1]]
                    for DisableUseDep in DisableUseDeps:
                        for remove_SK_E2 in remove_SK_E2s:
                            for Disable_CortoCortical in Disable_CortoCorticals:
                                for Standard,Deviant in center_frequencies:
                                    init_name = 'init_NoSK_E2.hoc' if remove_SK_E2 else 'init.hoc'
                                    experiment['SSAType'] = SSAType
                                    experiment['stand_dev_couple'] = [Standard,Deviant]

                                    BS = seed*(int(0.8*100)+100000)+Standard
                                    if SSA!=1:
                                        raise Exception('Look at the seed, I might need to change it')

                                    path_for_simulations = set_main_path(BasePath, ca, k, DisableUseDep, Disable_CortoCortical, remove_SK_E2, SSA) + '/' + set_directory(experiment) +'/'
                                    print path_for_simulations
                                    if tm_text!='stop_asking': tm_text = raw_input('Is this path ok? ("stop_asking" will stop asking)')
                                    if os.path.exists(path_for_simulations) and Standard == [6666,9600]:tm_text1 = raw_input('This path already exist (pass)'); 
                                    if tm_text1=='pass': continue
                                    
                                    create_path_and_copy_file(path_for_simulations)
                                    circuit_target_name =  set_circuit_target_by_axes_limit(blue_config_circ, path_for_simulations, circuit_target)
                                    spike_replay = path_for_simulations + '/SpikeFiles/input' + str(Standard) + '_' + `BS` + '.dat'
                                    print(spike_replay)

                                    run_name = str(Standard) + '_' + `BS` 
                                    
                                    ## need to use this one.
                                    job_name =  'S' + `int(Standard)` +  '_D' + `int(Deviant)` +  '_' + path_for_simulations[path_for_simulations.index('/Ca')-5:]


                                    #
                                    # Chr options can be added here
                                    #
                                    

                                    experiment['frequencies']     = SSA_protocol_stimulations(experiment, SSA)
                                    _,axon_activity_vars = create_axons_spikes(BS, experiment, save_path=spike_replay );
                                    #for ssrun_time in range(0,simulation_duration + 60000,60000):
                                    f = open(path_for_simulations +'/BlueConfig_template','r')
                                    blue_out = crate_blueconfig(BlueConfig_file=f, CurrentDir = path_for_simulations, BS = BS, simulation_duration = simulation_duration,
                                                                                            run_name=run_name, ca=ca, k=k, Mg=Mg,circuit_target = circuit_target_name, decouple=Disable_CortoCortical, optogenetic_vars=[],
                                                                                            DisableUseDep = DisableUseDep,reports=reports,
                                                                                            RunMode = RunMode, remove_spon_minis=remove_spon_minis, spike_replay=spike_replay, RNGMode=RNGMode, core_neuron=core_neuron)
                                    f = open(path_for_simulations + 'BlueConfig_' + run_name, 'w')
                                    f.write(blue_out)
                                    f.close()
                                    
                                    
                                    f = open(path_for_simulations +'/launchScript_bg_template.sh','r')
                                    launch_out = create_launch_script(launchScript_file=f, hoc_lib=hoc_lib, init_name=init_name, special_path=special_path, simulation_time=simulation_time,
                                                                                                        run_name=run_name, nice_level=nice_level, nodes=nodes, ntask_per_node=ntask_per_node, 
                                                                                                        bbpviz_txt = bbpviz_txt, partition=partition, job_name=job_name, core_neuron=core_neuron)
                                    f = open(path_for_simulations + 'launchScript_bg_' + run_name +'.sh', 'w')
                                    f.write(launch_out)
                                    if record_lfp==True:
                                        f.write("\nssh bbpviz1.cscs.ch <<'ENDSSH' \n")
                                        f.write('PATH="/gpfs/bbp.cscs.ch/home/amsalem/anaconda2/bin:$PATH"\n')
                                        f.write('python /gpfs/bbp.cscs.ch/home/amsalem/Dropbox/Blue_Brain/Experiments_Reproduction/general_scripts/LFP_calculator.py ' + path_for_simulations + 'BlueConfig_' + run_name + "\nENDSSH")
                                        
                                    f.close()
                                    [axon_activity_vars[axon_gid].pop('time_to_firing_rate_frequency') for axon_gid in axon_activity_vars]
                                    for axon_gid in axon_activity_vars:
                                        axon_activity_vars[axon_gid]['alpha_func_delay'] = axon_activity_vars[axon_gid]['alpha_func_delay']() if experiment['alpha_func_delay_distribution']  == 'gaussian' else None

                                    experiment['axon_activity_vars'] = axon_activity_vars
                                    pickle.dump(experiment,open(path_for_simulations+ '/experiment_' + run_name + '.p','w'))
                                    if not os.path.exists(path_for_simulations + '/' + run_name): #If folder already exist do not send it.
                                        run_names.append('sbatch launchScript_bg_' + run_name +'.sh')
                                    else:
                                        print('************ Job already submitted, not sure if completed **************')
                                #as it is per directory I need to submit the jobs here!

                                submit_jobs(run_names, path_for_simulations, MaxJobs = 1,  all_after_one=True, ssh_path=ssh_path)
                                run_names = []
#submit_jobs(run_names, path_for_simulations, MaxJobs = 2,  all_after_one=True, ssh_path=ssh_path)
                    
                

#BlueConfig = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Cardin_Nature_2009/31_07_2017/Ca1p23_K5p0/Run_2_LFP/Remove_Minis_False/var_1e_06/BlueConfig_freq40p0_amp3000p0_pulse_width2p5_BS1095000'



''' Send all options
SSATypes = ['TwoStimsPeriodic','TwoStims']
DisableUseDeps = [[], [('Excitatory', 'Inhibitory'), ('Excitatory', 'Excitatory'), ('Inhibitory', 'Excitatory'), ('Inhibitory','Inhibitory'), ('proj_Thalamocortical_VPM_Source', 'Mosaic')]]
Disable_CortoCorticals = [True,False]
remove_SK_E2s = [True,False]
for SSAType in SSATypes:
    for DisableUseDep in DisableUseDeps:
        for remove_SK_E2 in remove_SK_E2s:
            for Disable_CortoCortical in Disable_CortoCorticals:
                for Standard,Deviant in [[6666,9600],[9600,6666]]:
'''
