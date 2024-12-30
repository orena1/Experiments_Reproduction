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
execfile('../../OSI_files/CreateSimFiles_GitHub/CreateAxonalSpikeFilePossionGenerator_clean_visual.py')
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


def set_main_path(BasePath, ca, k, DisableUseDep, Disable_CortoCortical, remove_SK_E2):
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
        txt = txt.replace('OSI','OSI_No_SK_E2')
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

#for ca in [0.5,1.0,1.25,1.5,2.0,2.5]:
ca = float(1.23) #CAline
k = float(5.0)
Mg = float(1.0)
seed = 1


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
    partition = 'prod'
    if change_gamma:
        base_dir = base_dir.replace('soft', 'soft_gamma')
    if knl == True:
        partition = 'prod_knl'
        base_dir = base_dir.replace('soft_gamma','soft_gamma_knl')
        if change_gamma==False: 
            base_dir.replace('soft','soft_knl')
    hoc_lib = base_dir + '/sources/neurodamus/lib/hoclib'
    init_name = 'init.hoc'
    special_path = ''' special -mpi '''
    
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




def create_path_and_copy_file(path_for_simulations):
    model_folders = '../O1_v5/'
    FilesToCopy = ['launchScript_bg_template.sh', 'inputs.dat', 'user.target', 'BlueConfig_template']
    if not os.path.exists(path_for_simulations):
        os.makedirs(path_for_simulations)
        
    for FtC in FilesToCopy:
        if not os.path.exists(path_for_simulations + '/' + FtC):
            shutil.copyfile(model_folders + FtC, path_for_simulations + '/' + FtC )

    shutil.copyfile(os.path.basename(__file__), path_for_simulations + '/' + os.path.basename(__file__) )



BasePath = '/gpfs/bbp.cscs.ch/project/proj2/simulations/ThlInput/Visual_input23_10_18/OSI_knl/0to330_long'

experiment = {}
#AxoGidToXY = pickle.load(open(os.environ['HOME'] + '/positions.pkl','r'))

AxoGidToXY = pickle.load(open(os.environ['HOME'] + '/AxoGidToXY.p','r'))

AxoGidToXY = pickle.load(open(os.environ['HOME'] + '/AxoGidToXY_O1.pkl','r'))
experiment['axons_settings']  = [AxoGidToXY]
experiment['stim_type'] = 'oscillatory'
experiment['vari']     = 1.5
experiment['mod_freq']     = 2


experiment['prefered_angle_distribution'] = 'Choice'
experiment['prefered_angle_distribution_choice_values'] =[[5.0001,15,25,35,45,55,65,75,85,95,105,115,125,135,145,155,165,175],[0.03,0.0362,0.0362,0.047,0.0824,0.1141,0.2372,0.162,0.08,0.0343,0.016,0.0175,0.0131,0.0116,0.0107,0.018,0.0243,0.0294],5]
experiment['prefered_angle_seed'] = 1
experiment['osi_values_distribution']       = 'Choice'
experiment['osi_values_distribution_choice_values']  = [[0.1,0.3,0.5,0.7,0.9],[0.600,0.2,0.12,0.05,0.03],0.1]
experiment['osi_values_seed'] = 1
experiment['mean_firing_rate_distribution']  = 'Identical'
experiment['identical_fr_value']          = 7.3 # Note that the 'constant' spontaneous firing rate it added to this value
experiment['duration_of_stim']        = 2000 
experiment['duration_between_stims']  = 2000
experiment['first_stimulus_time']     = 4000
experiment['orientations']     = [0,20,40,60,80,100,120,140,160]#,180,200,220,240,260,280,300,320,340,340]
experiment['orientations']     = [0,30,60,90,120,150,180,210,240,270,300,330]#,180,200,220,240,260,280,300,320,340,340]

random.RandomState(10).shuffle(experiment['orientations'])
experiment['spontaneous_firing_rate_type'] = 'linear_spon_fr' #When I have sontaneuos firing rate, it will be added to the osi firing rate, which means that the firing rate will be higher than the one which was set in the 
experiment['spontaneous_firing_rate_value'] = 2.75 #firing rate for constant and ratio for linear_spon_fr

experiment['simulation_end_time']     = experiment['first_stimulus_time'] + (experiment['duration_between_stims'] + experiment['duration_of_stim'])*len(experiment['orientations'])
# we assume that the full 1250um is 30 degree, and we want 0.07 cycles per degree, so the width is 15
# so the width will be 625
simulation_time = "24:00:00" # real run time
simulation_duration = experiment['simulation_end_time']   # biological time

experiment['cycle_size'] = 625 

experiment['name'] = 'exp_1'


experiment['circuit_target'] = circuit_target




ca = 1.25
k = float(5)
DisableUseDep = []
Disable_CortoCortical = False
remove_SK_E2 = False

init_name = 'init_NoSK_E2.hoc' if remove_SK_E2 else 'init.hoc'


reports = {'soma_voltage':{
        'REPORT_TARGET':'mc2_Column',
        'START_TIME':str(1900),
        'END_TIME':str(9e9)}}
        
        
projection_path = '/gpfs/bbp.cscs.ch/project/proj32/BlobStim/proj_test_O1/s2f'


run_names = []
for seed in [1]:#,2,3]:
    BS = seed*(int(0.8*100)+100000)



    path_for_simulations = set_main_path(BasePath, ca, k, DisableUseDep, Disable_CortoCortical, remove_SK_E2) + '/'# + set_directory(experiment) +'/'
    print path_for_simulations
    if tm_text!='stop_asking': tm_text = raw_input('Is this path ok? ("stop_asking" will stop asking)')


    create_path_and_copy_file(path_for_simulations)
    circuit_target_name =  set_circuit_target_by_axes_limit(blue_config_circ, path_for_simulations, circuit_target)
    spike_replay = path_for_simulations + '/SpikeFiles/inputOSI_exp' + `BS` + '.dat'
    print(spike_replay)
    run_name = 'OSI_exp' + `BS`



    ## need to use this one.
    job_name =   path_for_simulations[path_for_simulations.index('/Ca')-5:]


    #
    # Chr options can be added here
    #



    _,axon_activity_vars = create_axons_spikes(BS, experiment, save_path=spike_replay );


    f = open(path_for_simulations +'/BlueConfig_template','r')
    blue_out = crate_blueconfig(BlueConfig_file=f, CurrentDir = path_for_simulations, BS = BS, simulation_duration = simulation_duration,
                                                            run_name=run_name, ca=ca, k=k, Mg=Mg,circuit_target = circuit_target_name, decouple=Disable_CortoCortical, optogenetic_vars=[],
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
    if record_lfp==True:
        f.write("\nssh bbpviz1.cscs.ch <<'ENDSSH' \n")
        f.write('PATH="/gpfs/bbp.cscs.ch/home/amsalem/anaconda2/bin:$PATH"\n')
        f.write('python /gpfs/bbp.cscs.ch/home/amsalem/Dropbox/Blue_Brain/Experiments_Reproduction/general_scripts/LFP_calculator.py ' + path_for_simulations + 'BlueConfig_' + run_name + "\nENDSSH")
        
    f.close()
    [axon_activity_vars[axon_gid].pop('time_to_firing_rate_frequency') for axon_gid in axon_activity_vars]

    experiment['axon_activity_vars'] = axon_activity_vars
    pickle.dump(experiment,open(path_for_simulations+ '/experiment_' + run_name + '.p','w'))
    if not os.path.exists(path_for_simulations + '/' + run_name): #If folder already exist do not send it.
        run_names.append('sbatch launchScript_bg_' + run_name +'.sh')
    else:
        print('************ Job already submitted, not sure if completed **************')
    #as it is per directory I need to submit the jobs here!

submit_jobs(run_names, path_for_simulations, MaxJobs = 1,  all_after_one=True, ssh_path=ssh_path)
run_names = []


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

