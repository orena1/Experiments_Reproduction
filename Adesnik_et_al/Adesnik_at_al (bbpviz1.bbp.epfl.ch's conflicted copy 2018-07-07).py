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
from bluepy.v2 import Cell

execfile('../general_scripts/jobs_creation.py')
execfile('../general_scripts/opto_gen_protocols.py')

#for ca in [0.5,1.0,1.25,1.5,2.0,2.5]:
ca = 1.23 #CAline
k = 5.0
Mg = 1.0

var = 0.000001 # 0.000001 | 0.3 | 0.8

generalConfigPath = '/gpfs/bbp.cscs.ch/project/proj2/simulations/ThlInput/AudInput12_4_16/SSA/Ca1p23/EE0_EI0_IE0_II0_TM_0/Freq_Tono_4to16_FR_S100_W_S0p2_TwoStimsExp/BlueConfig6666_106686'

bbpviz1 = True

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
    hoc_lib = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master07_04_18/neurodamus/lib/hoclib'
    init_name = 'init.hoc'
    special_path = '--mpi=pmi2 /gpfs/bbp.cscs.ch/project/proj2/Programs/Master07_04_18/neurodamus/lib/x86_64/special -mpi'
    nodes = 16
    ntask_per_node = 36
    partition = 'prod'
    bbpviz_txt = 'module load nix/hdf5/1.10.1 intel-parallel-studio/cluster.2018.1\n'\
                     'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/gpfs/bbp.cscs.ch/project/proj2/Programs/Master07_04_18/bbpviz1NeuRep/reportinglib/install/lib64\n\n'
    ssh_path = 'bbpv1.epfl.ch'

    
    



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


#groups = 'loc_based'
groups = 'L23_PC@0.23'
run = '1_full_comp'


path_for_simulations = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Adesnik_Nature_2010/5_08_2018/Ca' + \
                            str(ca).replace('.','p') + '_K' + str(k).replace('.','p') +'/Run_' +str(run)  +  '/Remove_Minis_' +str(remove_spon_minis) +'/var_' + str(var).replace('.','p').replace('-','_')+'/'

#hoc_lib = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/hoclib'
#init_name = 'init.hoc'
#special_path = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/powerpc64/special'



reports = {'soma_voltage':{
        'REPORT_TARGET':'mc2_Column',
        'START_TIME':str(1900),
        'END_TIME':str(4200)}}

RunMode = 'RunMode LoadBalance'
record_lfp = True
if record_lfp: 
    reports['LFP'] = {'START_TIME':str(0), 'END_TIME':str(9e9),'DT':str(0.1)}
    RunMode = 'RunMode WholeCell'


circuit_target = "mc2_Column"

simulation_time = "24:00:00"
nice_level = 1000

opto_gen_stimstart = 2000
simulation_duration = 4200

seeds = [1]



pulse_widths = [2.5]
amplitudes = [100]
amplitudes = map(float,amplitudes)


### This is for groups
ind = 0
#base_activation = 400
#ba  = base_activation
#activations = [[0.7,ba * 1], [0.65,ba*0.90], [0.60,ba*0.80], [0.12,ba*0.70], [0.02,ba*0.20],
              #[0.20,ba*0.50],  [0.15,ba*0.40], [0.08,ba*0.30], [0.02,ba*0.20]  , [0.01,ba*0.5]]
              
#path_for_simulations = path_for_simulations + 'BA_' + str(base_activation) +'/'
gamma_val =0.062 # only two option available 0.062 or 0.08
if gamma_val=!0.062:
    if gamma_val!=0.08: raise Exception('Does not work!')
    path_for_simulations + '/gamma_0p08/'
    


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

if groups=='loc_based':
    spatial_data = {}
    for i in [[0,200],[200,9e9]]:
        for layer in [[1767.937, 1916.8004], [1415, 1767.92], [1225.438, 1414.999], [700.38, 1225.4], [ 0.0, 700.365]]:
            spatial_data['group' + str(ind)] = {'xz_radius_start':i[0],'xz_radius_end':i[1],'y_step_start':layer[0],'y_step_end':layer[1] \
                                        ,'cell_percent':activations[ind][0],'power':activations[ind][1]}
            ind+=1
    
    create_groups(spatial_data, 'xz_radius_y_step', neuron_type = 'PV_FS')

cells_group = 'PV_FS'

if '@' in groups:
    selsect_rnd = np.random.RandomState(6)
    cell_type, percent = groups.split('@')
    Circ  = bluepy.Circuit(generalConfigPath)
    cells = Circ.v2.cells.get({'$target': 'mc2_Column', Cell.MTYPE: cell_type})
    gids_per_group = np.sort(selsect_rnd.choice(list(cells.index), size=int(len(list(cells.index))*float(percent)), replace=False))
    groups = groups.replace('@','at').replace('.','p')
    add_to_user_target(gids_per_group,  path_for_simulations)
    cells_group = groups
### test
#seeds = [1]
#freqs = [40]
###


amplitudes_start_nd_end = np.array([[0,50], [0,100], [0,200], [0,400], [0,800]])
amplitudes_start_nd_end = amplitudes_start_nd_end.astype('float')
for seed in seeds:
    for amp_start, amp_end in amplitudes_start_nd_end:
        dur = 2000
        BS = seed*1000000 + int(amp_start*10) + int(dur*10000) + int(amp_end*1000)
        run_name = 'dur' + `float(dur)`.replace('.','p') +  '_amps' + `float(amp_start)`.replace('.','p') +  '_ampse' + `float(amp_end)`.replace('.','p')  + '_BS' + `BS`
        stim_vars = {cells_group:[{'amp_start':amp_start,'amp_end':amp_end, 'start':opto_gen_stimstart, 'dur':dur}]}
        morphs = [cells_group]
        
        
        #if groups=='_groups':
            #stim_vars = {'L23_PV':[{'amp':amp,'start':opto_gen_stimstart,'dur':dur, 'var':amp*var, 'pulse_width': pulse_width , 'freq': freq}],
                        #'L4_PV':[{'amp':amp*0.5,'start':opto_gen_stimstart,'dur':dur, 'var':amp*var, 'pulse_width': pulse_width , 'freq': freq}],
                        #'L5_PV':[{'amp':amp*0.3,'start':opto_gen_stimstart,'dur':dur, 'var':amp*var, 'pulse_width': pulse_width , 'freq': freq}],
                        #'L6_PV':[{'amp':amp*0.15,'start':opto_gen_stimstart,'dur':dur, 'var':amp*var, 'pulse_width': pulse_width , 'freq': freq}],}
            #morphs = ['L23_PV', 'L4_PV', 'L5_PV', 'L6_PV']
        
        #if groups == 'loc_based':
            #stim_vars = {group_name:[{'amp':spatial_data[group_name]['power'],'start':opto_gen_stimstart,'dur':dur, 'var':amp*var, 'pulse_width': pulse_width , 'freq': freq}] for group_name in spatial_data}
            #morphs = spatial_data.keys()
        
        
        f = open(path_for_simulations +'/BlueConfig_template','r')
        blue_out = crate_blueconfig(BlueConfig_file=f, CurrentDir = path_for_simulations, BS = BS, simulation_duration = simulation_duration,
                                                                run_name=run_name, ca=ca, k=k, Mg=Mg,circuit_target = circuit_target, optogenetic_vars=['ramp_current_injections', morphs, stim_vars],reports=reports,
                                                                RunMode = RunMode, remove_spon_minis=remove_spon_minis)
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
            f.write("\nssh bbpviz1.bbp.epfl.ch <<'ENDSSH' \n")
            f.write('PATH="/gpfs/bbp.cscs.ch/home/amsalem/anaconda2/bin:$PATH"\n')
            f.write('python /gpfs/bbp.cscs.ch/home/amsalem/Dropbox/Blue_Brain/Experiments_Reproduction/general_scripts/LFP_calculator.py ' + path_for_simulations + 'BlueConfig_' + run_name + "\nENDSSH")
            
        f.close()
        if not os.path.exists(path_for_simulations + '/' + run_name): #If folder already exist do not send it.
            run_names.append('sbatch launchScript_bg_' + run_name +'.sh')

submit_jobs(run_names, path_for_simulations, MaxJobs = 1,  all_after_one=True, ssh_path=ssh_path)
                    
                

#BlueConfig = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Cardin_Nature_2009/31_07_2017/Ca1p23_K5p0/Run_2_LFP/Remove_Minis_False/var_1e_06/BlueConfig_freq40p0_amp3000p0_pulse_width2p5_BS1095000'





