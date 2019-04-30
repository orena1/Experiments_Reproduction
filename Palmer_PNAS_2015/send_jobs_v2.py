### Palmer et al 
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
from tqdm import tqdm

execfile('../../OSI_files/CreateSimFiles_GitHub/CreateAxonalSpikeFilePossionGenerator_clean_visual.py')
execfile('../general_scripts/jobs_creation.py')
execfile('../general_scripts/opto_gen_protocols.py')
generalConfigPath = '/gpfs/bbp.cscs.ch/project/proj2/simulations/ThlInput/AudInput12_4_16/SSA/Ca1p23/EE0_EI0_IE0_II0_TM_0/Freq_Tono_4to16_FR_S100_W_S0p2_TwoStimsExp/BlueConfig6666_106686'
#print  'Loading all  took ' +  `time.time() - STloadTM` + ' secs'
blue_config_circ = bluepy.Circuit(generalConfigPath)


#for ca in [0.5,1.0,1.25,1.5,2.0,2.5]:
ca = 1.25 #CAline
k = 5.0
Mg = 1.0



change_gamma = True
core_neuron = True
knl = False
cluster = 'neuron_coreneuron' # bbpv1 # bbpviz1 # bbpv1core_neuron

if cluster == 'neuron_coreneuron':
    base_dir = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master_Core_22_9_18/soft'
    partition = 'prod'
    if change_gamma:
        base_dir = base_dir.replace('soft', 'soft_gamma')
    if knl == True:
        partition = 'prod_knl'
        base_dir = base_dir.replace('soft_gamma','soft_gamma_knl')
        if change_gamma==False: 
            base_dir = sbase_dir.replace('soft','soft_knl')
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


    
nice_level = 3000    
remove_spon_minis = False
reports = {}


RunMode = 'RunMode LoadBalance'
record_lfp = False
if record_lfp: 
    reports['LFP'] = {'START_TIME':str(0), 'END_TIME':str(9e9),'DT':str(0.1)}
    RunMode = 'RunMode WholeCell'


## get which gid is on and which off

def set_main_path(BasePath, ca, k, experiment):
    Directory = BasePath + '/Ca' + str(ca).replace('.','p') + '_K' + str(k).replace('.','p') + '/'
    if experiment['circuit_target'] not in ["mc2_Column", 'O1_slice_mc2']:
        Directory+= '/X' + `experiment['circuit_target']['x'][0]`.replace('-','m') + 'to'+ `experiment['circuit_target']['x'][1]`.replace('-','m') + \
                        '_Y' + `experiment['circuit_target']['y'][0]`.replace('-','m') + 'to'+ `experiment['circuit_target']['y'][1]`.replace('-','m') + \
                        '_Z' + `experiment['circuit_target']['z'][0]`.replace('-','m') + 'to'+ `experiment['circuit_target']['z'][1]`.replace('-','m') +'/'
    return(Directory)



def create_path_and_copy_file(path_for_simulations):
    model_folders = '../O1_v5/'
    FilesToCopy = ['launchScript_bg_template.sh', 'inputs.dat', 'user.target', 'BlueConfig_template']
    if not os.path.exists(path_for_simulations):
        os.makedirs(path_for_simulations)
        
    for FtC in FilesToCopy:
        if not os.path.exists(path_for_simulations + '/' + FtC):
            shutil.copyfile(model_folders + FtC, path_for_simulations + '/' + FtC )

    shutil.copyfile(os.path.basename(__file__), path_for_simulations + '/' + os.path.basename(__file__) )


def save_spike_file(axon_activity_vars,save_path):
    print(save_path)

    if not os.path.exists(save_path[:save_path.rindex('/')]):
        os.makedirs(save_path[:save_path.rindex('/')])
    f = open(save_path,'w')
    f.write('/scatter\n')
    sps = [zip(*[axon_activity_vars[axon_gid]['spike_times'],[axon_gid]*len(axon_activity_vars[axon_gid]['spike_times'])]) for axon_gid in axon_activity_vars]
    sps = sorted([i for j in sps for i in j])
    [f.write('{:} \t {:} \n'.format(spike_time,axon_gid)) for spike_time,axon_gid in sps]
    f.close()



def load_file_and_create_fr_list(path_for_overlap_files, min_fr  , max_fr, spon_fr):
    on_off_dic = pickle.load(open(path_for_overlap_files + '/onoff.p','r'))
    gids = on_off_dic.keys()
    overlap_per_gid= pickle.load(open(path_for_overlap_files + '/overlap_dt3p1_stri_rad0.3025.p','r'))
    #overlap_per_gid= pickle.load(open(path_for_overlap_files + 'overlap_dt3p1_stri_rad2.5.p','r'))
    ### I assume that the baseline is 0.5, so I am adding a manual fix, I will need to change it , it I think this project is going
    #
    #  ## LOOK HERE !!!
    #  This code is not amazing, it give me 4 hz for gray, 7 for fullly activated and 1 for not activated
    #
    #### I assume that the baseline is 0.5, so I am adding a manual fix, I will need to change it , it I think this project is going
    # Jared stim it is white on black

    mul_1 = array([[-1 if on_off_dic[gid] == 0 else 0] for gid in gids])
    mul_2 = array([[-1 if on_off_dic[gid] == 0 else 1] for gid in gids])
    minimal_firing_rate =  min_fr
    max_firing_rate =  max_fr
    spon_firing_rate = spon_fr

    overlap_matrix = []
    for gid in gids:
        overlap_matrix.append(overlap_per_gid[gid])  # this means that the backgroud is black
    fr_matrix = (array(overlap_matrix)+mul_1)*mul_2*(max_firing_rate-minimal_firing_rate)

    gid_to_fr_list = {}
    for i, gid in enumerate(gids):
        gid_to_fr_list[gid] = fr_matrix[i]
    return(gid_to_fr_list,overlap_matrix)



BasePath = '/gpfs/bbp.cscs.ch/home/amsalem/proj2/simulations/ThlInput/Palmer_PNAS_2015/18_11_18/bar_radius_0p3025/'
#BasePath = '/gpfs/bbp.cscs.ch/home/amsalem/proj2/simulations/ThlInput/Palmer_PNAS_2015/18_11_18/bar_radius_2p5/'

experiment = {}
experiment['stim_type'] = 'file'
experiment['stim_dt'] = 3.1
experiment['name'] = 'exp_1'


AxoGidToXY = pickle.load(open(os.environ['HOME'] + '/axon_gid_to_location_O1_slice_mc2_np.pkl','r'))
experiment['axons_settings']  = [AxoGidToXY['neurons_position']]



experiment['minimal_firing_rate'] = 0
experiment['max_firing_rate'] = 7.0
experiment['spon_firing_rate'] = 0
experiment['seed'] = 12


gid_to_fr_list,overlap_matrix = load_file_and_create_fr_list(path_for_overlap_files = '/gpfs/bbp.cscs.ch/home/amsalem/proj2/simulations/ThlInput/Palmer_PNAS_2015/Data/Jared/', min_fr= experiment['minimal_firing_rate'], 
                                                            max_fr = experiment['max_firing_rate'], spon_fr = experiment['spon_firing_rate'])




experiment['gid_to_fr_list'] = gid_to_fr_list
experiment['simulation_end_time'] = len(gid_to_fr_list[gid_to_fr_list.keys()[0]])*experiment['stim_dt']
#experiment['simulation_end_time'] = 130000 # I run only 130 seconds to see what I get.
simulation_duration = experiment['simulation_end_time'] 
BS = experiment['seed']
run_name = 'test' + '_' + `BS` 
simulation_time = "24:00:00" # real run time






##full slice = 465 to 830

sp_times = create_axons_spikes(experiment['seed'], experiment)



for y_remove in [0,50,100,150]:
    if 830-y_remove<465+y_remove:
        raise Exception('too much')
    
    circuit_target = {'x':[-150,850], 'y':[465+y_remove,830-y_remove], 'z':[-9000,9000]}
    experiment['circuit_target'] = circuit_target
    run_names = []



    path_for_simulations = set_main_path(BasePath, ca, k,experiment)
    create_path_and_copy_file(path_for_simulations)
    circuit_target_name =  set_circuit_target_by_axes_limit(blue_config_circ, path_for_simulations, circuit_target, base_target = 'O1_Slice')
    

    
    
    spike_replay = path_for_simulations + 'SpikeFiles/input' + str(BS) + '.dat'
    sp_times_per_column = {gid:sp_times[1][gid] for gid in sp_times[1] if experiment['axons_settings'][0][gid][1]<830-y_remove and experiment['axons_settings'][0][gid][1]>465+y_remove}
    
    save_spike_file(sp_times_per_column,spike_replay)


    f = open(path_for_simulations +'/BlueConfig_template','r')
    blue_out = crate_blueconfig(BlueConfig_file=f, CurrentDir = path_for_simulations, BS = BS, simulation_duration = simulation_duration,
                                                            run_name=run_name, ca=ca, k=k, Mg=Mg,circuit_target = circuit_target_name, 
                                                            reports=reports,
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

    #experiment['gid_to_fr_list']  = 'Removed_to_save_data'
    pickle.dump(experiment,open(path_for_simulations+ '/experiment_' + run_name + '.p','w'),protocol=2)

    #if not os.path.exists(path_for_simulations + '/' + run_name): #If folder already exist do not send it.
        #run_names.append('sbatch launchScript_bg_' + run_name +'.sh')

#submit_jobs(run_names, path_for_simulations, MaxJobs = 2,  all_after_one=True, ssh_path=ssh_path)
                    
