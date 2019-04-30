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
from scipy.spatial.distance import cdist
import bluepy
import pickle
import math
import scipy.ndimage

execfile('../general_scripts/jobs_creation.py')
execfile('../general_scripts/opto_gen_protocols.py')

#for ca in [0.5,1.0,1.25,1.5,2.0,2.5]:
ca = 1.23 #CAline
k = 5.0
Mg = 1.0

var = 0.000001 # 0.000001 | 0.3 | 0.8

generalConfigPath = '/gpfs/bbp.cscs.ch/project/proj2/simulations/ThlInput/AudInput12_4_16/SSA/Ca1p23/EE0_EI0_IE0_II0_TM_0/Freq_Tono_4to16_FR_S100_W_S0p2_TwoStimsExp/BlueConfig6666_106686'

change_gamma = True
core_neuron = False
knl = False
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
            base_dir.replace('soft','soft_knl')
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



def create_groups(spatial_data, dist_function, neuron_type, center_point = [344.766, 1038.23, 602.03], select_seed = 4): #move to helper functions
    #dist_function = 'xz_radius_y_step'
    '''
    This function should get:

    for case inwhich dist_function == 'r3'
    spatial_data  = {'group_name':{'distance_start':x ,'distance_end':x1 }}

    for case inwhich dist_function == 'x_radius_y_step'
    '''

    Circ  = bluepy.Circuit(generalConfigPath)
    gids_in_target = list(Circ.targets.targets[neuron_type].resolve_contents_gids())

    gids_per_group = {}
    cells_locations = pickle.load(open('/gpfs/bbp.cscs.ch/project/proj2/simulations/mc2_Col_v5_gid_to_xyz.p','r'))
    cells_gids = [gid for gid in cells_locations.keys() if gid in gids_in_target]
    cells_locations = np.array([cells_locations[gid] for gid in cells_gids])

    selsect_rnd = np.random.RandomState(select_seed)

    #     if dist_function == 'r3':
    #         r3_distances = scipy.spatial.distance.euclidean(center_point, cells_locations)
    #         last_r3_distance = 0
    #         for group_name in spatial_data:
    #             gids_per_group[group_name] =  cells_gids[np.argwhere(spatial_data[group_name]['distance_end']  - r3_distances>=spatial_data[group_name]['distance_start'])]

    if dist_function == 'xz_radius_y_step':

        xz_distances = cdist([[center_point[0],center_point[2]]]  , zip(cells_locations[:,0],cells_locations[:,2]))[0]
        y_distances =  cells_locations[:,1]
        for group_name in spatial_data:

            data = spatial_data[group_name]
            y_distances_in_xz_rad =  np.array([y_distances[i[0]] for i in np.argwhere((data['xz_radius_end']> xz_distances) &  (xz_distances >= data['xz_radius_start']))])
            cells_gids_in_xz_rad = np.array([cells_gids[i[0]] for i in np.argwhere((data['xz_radius_end']> xz_distances) &  (xz_distances >= data['xz_radius_start']))])


            gids_per_group[group_name] = [cells_gids_in_xz_rad[i[0]] for i in np.argwhere((data['y_step_end'] > y_distances_in_xz_rad) & (y_distances_in_xz_rad >= data['y_step_start']))]
            gids_per_group[group_name] = selsect_rnd.choice(gids_per_group[group_name], int(round(len(gids_per_group[group_name])*spatial_data[group_name]['cell_percent'] )), replace=False)
            add_to_user_target(gids_per_group[group_name], group_name, path_for_simulations)

    return(gids_per_group)





remove_spon_minis = False
groups = False


groups = '' if  groups == False else '_groups'


groups = 'loc_based'
run = 'lfp_with_thalamic_input_poisson_over_poisson_pulse_bundle_fr5_fr5_bund_10'



##################


# Set Gap Junctions
gap_junction_conductance = 0# 0 | 0.2 |0.5
gj_paths = {0.2:'/gpfs/bbp.cscs.ch/project/proj2/circuits/SomatosensoryCxS1-v5.r0/O1/0p0um/ncsStructural_gjdevel_withsoma2/pathways/Cond0_2/AlltoAll' ,
            0.5: '/gpfs/bbp.cscs.ch/project/proj2/circuits/SomatosensoryCxS1-v5.r0/O1/0p0um/ncsStructural_gjdevel_withsoma2/pathways/Cond0_5/AlltoAll'}
gap_junction_path = None
if gap_junction_conductance!=0:
    gap_junction_path = gj_paths[gap_junction_conductance]
    run += '_gj' + str(gap_junction_conductance).replace('.','p')
###################    
AxoGidToXY = pickle.load(open(os.environ['HOME'] + '/AxoGidToXY.p','r'))

def create_thalamic_spikes(fr_per_axon, stim_start_time, stim_end_time, seed):
    print('creating spike times - START')
    interv = 1.0/fr_per_axon*1000
    thalamic_rnd = np.random.RandomState(seed)
    sp_per_axon_gid = {}
    for axon_gid in AxoGidToXY.keys():
        to_add = [stim_start_time]
        while 1:
            rnd = -math.log(1.0 - thalamic_rnd.uniform(0,1)) / (1.0/interv)
            if rnd + to_add[-1] > stim_end_time:
                break
            else:
                to_add.append(rnd + to_add[-1])
        sp_per_axon_gid[axon_gid] = to_add[1:]
    print('creating spike times - END')
    return(sp_per_axon_gid)


def create_sync_thalamic_spikes(pulses_fr, fr_per_axon, stim_start_time, stim_end_time, seed):
    print('creating spike times - START')
    gaussian_std = 2 #ms
    interv = 1.0/pulses_fr*1000
    thalamic_rnd = np.random.RandomState(seed)
    to_add = [stim_start_time]
    while 1:
        rnd = -math.log(1.0 - thalamic_rnd.uniform(0,1)) / (1.0/interv)
        if rnd + to_add[-1] > stim_end_time:
            break
        else:
            to_add.append(rnd + to_add[-1])
    main_pulses = to_add[1:]
    fr_per_bin, bin_times = np.histogram(main_pulses,bins=np.arange(0,stim_end_time+100,0.025))
    fr_per_bin = fr_per_bin.astype(float)
    filtered_fr = scipy.ndimage.filters.gaussian_filter(fr_per_bin, gaussian_std/0.025)


    axons_fr_relative_to_bursts = fr_per_axon/pulses_fr
    sp_per_axon_gid = {}
    for axon_gid in AxoGidToXY.keys():
        sp_per_axon_gid[axon_gid] = np.nonzero(thalamic_rnd.binomial(1, p=filtered_fr*axons_fr_relative_to_bursts))[0]*0.025
    print('creating spike times - END')
    return(sp_per_axon_gid)

def create_sync_thalamic_spikes_bundles(pulses_fr, fr_per_axon, stim_start_time, stim_end_time, bundle_size, seed):
    if bundle_size == 9e9: # not bundles all working at once.
        return(create_sync_thalamic_spikes(pulses_fr, fr_per_axon, stim_start_time, stim_end_time, seed))
    
    print('creating spike times - START')
    gaussian_std = 2 #ms
    interv = 1.0/pulses_fr*1000
    axons_gids = AxoGidToXY.keys()
    sp_per_axon_gid = {}
    while len(axons_gids)>0:
        
        thalamic_rnd = np.random.RandomState(seed + len(axons_gids))
        to_add = [stim_start_time]
        while 1:
            rnd = -math.log(1.0 - thalamic_rnd.uniform(0,1)) / (1.0/interv)
            if rnd + to_add[-1] > stim_end_time:
                break
            else:
                to_add.append(rnd + to_add[-1])
        main_pulses = to_add[1:]
        fr_per_bin, bin_times = np.histogram(main_pulses,bins=np.arange(0,stim_end_time+100,0.025))
        fr_per_bin = fr_per_bin.astype(float)
        filtered_fr = scipy.ndimage.filters.gaussian_filter(fr_per_bin, gaussian_std/0.025)
        axons_fr_relative_to_bursts = fr_per_axon/pulses_fr
        
        if bundle_size<len(axons_gids):
            axons_gids_selected  =  thalamic_rnd.choice(axons_gids,bundle_size,replace=False)
        else:
            axons_gids_selected = axons_gids
        axons_gids = list(set(axons_gids) - set(axons_gids_selected))


        for axon_gid in axons_gids_selected:
            if axon_gid in sp_per_axon_gid: raise Exception('Debug!!!')
            sp_per_axon_gid[axon_gid] = np.nonzero(thalamic_rnd.binomial(1, p=filtered_fr*axons_fr_relative_to_bursts))[0]*0.025
    print('creating spike times - END')
    return(sp_per_axon_gid)


path_for_simulations = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Cardin_Nature_2009/24_09_2018/Ca' + \
                            str(ca).replace('.','p') + '_K' + str(k).replace('.','p') +'/Run_' +str(run)  +  '/Remove_Minis_' +str(remove_spon_minis) +'/var_' + str(var).replace('.','p').replace('-','_')+'/'

#hoc_lib = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/hoclib'
#init_name = 'init.hoc'
#special_path = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/powerpc64/special'



    
reports = {}

reports = {'soma_voltage':{
        'REPORT_TARGET':'mc2_Column',
        'START_TIME':str(1900),
        'END_TIME':str(2500)}}

RunMode = 'RunMode LoadBalance'
record_lfp = True
if record_lfp: 
    reports['LFP'] = {'START_TIME':str(0), 'END_TIME':str(9e9),'DT':str(0.1)}
    RunMode = 'RunMode WholeCell'


circuit_target = "mc2_Column"

simulation_time = "24:00:00" #It has to be 03 or 05 etc..
nice_level = 2000

opto_gen_stimstart = 2000
stim_durations = 3000 + 1#Don't use 0.5 ms
simulation_duration = 5200

seeds = [2]



pulse_widths = [2.5]
amplitudes = [100]
amplitudes = map(float,amplitudes)
freqs = [0,2,4,8,16,32,40,48,60,70,80,100,200]

### This is for groups
ind = 0
base_activation = 400
ba  = base_activation
activations = [[0.7,ba * 1], [0.65,ba*0.90], [0.60,ba*0.80], [0.12,ba*0.70], [0.02,ba*0.20],
              [0.20,ba*0.50],  [0.15,ba*0.40], [0.08,ba*0.30], [0.02,ba*0.20]  , [0.01,ba*0.5]]
              
path_for_simulations = path_for_simulations + 'BA_' + str(base_activation) +'/'

model_folders = '../O1_v5/'
FilesToCopy = ['launchScript_bg_template.sh', 'inputs.dat', 'user.target', 'BlueConfig_template']
if not os.path.exists(path_for_simulations):
    os.makedirs(path_for_simulations)
    
for FtC in FilesToCopy:
    shutil.copyfile(model_folders + FtC, path_for_simulations + '/' + FtC )

shutil.copyfile(os.path.basename(__file__), path_for_simulations + '/' + os.path.basename(__file__) )
print path_for_simulations
run_names = []



#freqs = [0,25,40]
#activations = [[1,100], [1,90], [1,80], [1,70], [1,20],
               #[1,50],  [1,40], [1,30], [1,20]  , [1,5]]


spatial_data = {}
for i in [[0,200],[200,9e9]]:
    for layer in [[1767.937, 1916.8004], [1415, 1767.92], [1225.438, 1414.999], [700.38, 1225.4], [ 0.0, 700.365]]:
        spatial_data['group' + str(ind)] = {'xz_radius_start':i[0],'xz_radius_end':i[1],'y_step_start':layer[0],'y_step_end':layer[1] \
                                    ,'cell_percent':activations[ind][0],'power':activations[ind][1]}
        ind+=1

create_groups(spatial_data, 'xz_radius_y_step', neuron_type = 'PV_FS')


### test
#seeds = [1]
#freqs = [40]
###

def save_spikes(sp_per_axon_gid, save_path):
    if not os.path.exists(save_path[:save_path.rindex('/')]):
        os.makedirs(save_path[:save_path.rindex('/')])
    f = open(save_path,'w')
    f.write('/scatter\n')
    sps = [zip(*[sp_per_axon_gid[axon_gid],[axon_gid]*len(sp_per_axon_gid[axon_gid])]) for axon_gid in sp_per_axon_gid]
    sps = sorted([i for j in sps for i in j])
    [f.write('{:} \t {:} \n'.format(spike_time,axon_gid)) for spike_time,axon_gid in sps]
    f.close()

amplitudes = [0]
for seed in seeds:
    for amp in amplitudes:
        for pulse_width in pulse_widths:
            for freq in freqs:
                for pulses_fr in [5]:
                    for fr in [5]:
                        dur = stim_durations
                        BS = seed*1000000 + int(pulses_fr*1214) +  int(amp*10) + int(pulse_width*10000) + int(freq*1000) + int(fr*800)

                        sp_per_axon_gid = create_sync_thalamic_spikes_bundles(pulses_fr,  fr, 1000, simulation_duration-250, bundle_size = 10, seed=BS )
                        spike_replay_path = path_for_simulations + '/SpikeFiles/input' + str(float(fr)).replace('.','p') + '_' +str(float(pulses_fr)).replace('.','p') + '_BS' + `BS`
                        save_spikes(sp_per_axon_gid, spike_replay_path)


                        run_name = 'pulse_fr_' + str(float(pulses_fr)).replace('.','p') + 'fr_' + `float(fr)`.replace('.','p') + 'freq' + `float(freq)`.replace('.','p') +  '_amp' + `float(amp)`.replace('.','p') + '_pulse_width' + `float(pulse_width)`.replace('.','p') + '_BS' + `BS`
                        stim_vars = {'PV_FS':[{'amp':amp,'start':opto_gen_stimstart,'dur':dur, 'var':amp*var, 'pulse_width': pulse_width , 'freq': freq}]}
                        morphs = ['PV_FS']
                        if groups=='_groups':
                            stim_vars = {'L23_PV':[{'amp':amp,'start':opto_gen_stimstart,'dur':dur, 'var':amp*var, 'pulse_width': pulse_width , 'freq': freq}],
                                        'L4_PV':[{'amp':amp*0.5,'start':opto_gen_stimstart,'dur':dur, 'var':amp*var, 'pulse_width': pulse_width , 'freq': freq}],
                                        'L5_PV':[{'amp':amp*0.3,'start':opto_gen_stimstart,'dur':dur, 'var':amp*var, 'pulse_width': pulse_width , 'freq': freq}],
                                        'L6_PV':[{'amp':amp*0.15,'start':opto_gen_stimstart,'dur':dur, 'var':amp*var, 'pulse_width': pulse_width , 'freq': freq}],}
                            morphs = ['L23_PV', 'L4_PV', 'L5_PV', 'L6_PV']
                        
                        if groups == 'loc_based':
                            stim_vars = {group_name:[{'amp':spatial_data[group_name]['power'],'start':opto_gen_stimstart,'dur':dur, 'var':amp*var, 'pulse_width': pulse_width , 'freq': freq}] for group_name in spatial_data}
                            morphs = spatial_data.keys()
                        
                        
                        f = open(path_for_simulations +'/BlueConfig_template','r')
                        blue_out = crate_blueconfig(BlueConfig_file=f, CurrentDir = path_for_simulations, BS = BS, simulation_duration = simulation_duration, spike_replay=spike_replay_path,
                                                                                run_name=run_name, ca=ca, k=k, Mg=Mg,circuit_target = circuit_target, optogenetic_vars=['pulse_train', morphs, stim_vars],reports=reports,
                                                                                RunMode = RunMode, remove_spon_minis=remove_spon_minis, gap_junction_path=gap_junction_path, core_neuron=core_neuron)
                        f = open(path_for_simulations + 'BlueConfig_' + run_name, 'w')
                        f.write(blue_out)
                        f.close()
                        
                        
                        f = open(path_for_simulations +'/launchScript_bg_template.sh','r')
                        launch_out = create_launch_script(launchScript_file=f, hoc_lib=hoc_lib, init_name=init_name, special_path=special_path, simulation_time=simulation_time,
                                                                                            run_name=run_name, nice_level=nice_level, nodes=nodes, ntask_per_node=ntask_per_node, 
                                                                                            bbpviz_txt = bbpviz_txt, partition=partition, core_neuron=core_neuron)
                        f = open(path_for_simulations + 'launchScript_bg_' + run_name +'.sh', 'w')
                        f.write(launch_out)
                        #os.chdir(path_for_simulations)
                        #os.system("sed -i -e 's/%s.mg/mg_ProbAMPANMDA_EMS/g' BlueConfig_" + run_name)
                        if record_lfp==True:
                           f.write("\nssh bbpviz1.bbp.epfl.ch <<'ENDSSH' \n")
                           f.write('PATH="/gpfs/bbp.cscs.ch/home/amsalem/anaconda2/bin:$PATH"\n')
                           f.write('python /gpfs/bbp.cscs.ch/home/amsalem/Dropbox/Blue_Brain/Experiments_Reproduction/general_scripts/LFP_calculator.py ' + path_for_simulations + 'BlueConfig_' + run_name + "\nENDSSH")
                           
                        f.close()
                        if not os.path.exists(path_for_simulations + '/' + run_name): #If folder already exist do not send it.
                            run_names.append('sbatch launchScript_bg_' + run_name +'.sh')

submit_jobs(run_names, path_for_simulations, MaxJobs = 8,  all_after_one=True, ssh_path=ssh_path)
                    


