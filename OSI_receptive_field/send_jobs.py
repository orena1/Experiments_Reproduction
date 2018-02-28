### orientation selectivty simulations.
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

    
nice_level = 100    
circuit_target = "mc2_Column"
remove_spon_minis = False
reports = {}


RunMode = 'RunMode LoadBalance'
record_lfp = False
if record_lfp: 
    reports['LFP'] = {'START_TIME':str(0), 'END_TIME':str(9e9),'DT':str(0.1)}
    RunMode = 'RunMode WholeCell'


## get which gid is on and which off

def set_main_path(BasePath, ca, k):
    txt = BasePath + '/Ca' + str(ca).replace('.','p') + '_K' + str(k).replace('.','p') + '/'
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



def load_file_and_create_fr_list(path_for_fr_files, min_fr  , max_fr, spon_fr ,spon_len):
    on_off_dic = pickle.load(open(path_for_fr_files + '/onoff.p','r'))
    gids = on_off_dic.keys()
    frs_per_orientation = {}
    for stim_orient in [0,20,40,60,80,100,120,140,160,180]:
        frs_per_orientation[stim_orient] = pickle.load(open(path_for_fr_files + '/frac_new' + str(stim_orient) + '.p','r'))



    mul_1 = array([[-1 if on_off_dic[gid] == 0 else 0] for gid in gids])
    mul_2 = array([[-1 if on_off_dic[gid] == 0 else 1] for gid in gids])
    minimal_firing_rate =  min_fr
    max_firing_rate =  max_fr
    spon_firing_rate = spon_fr

    orientation_matrix = {}
    for orientation in frs_per_orientation:
        orientation_matrix[orientation] = []
        for gid in gids:
            orientation_matrix[orientation].append(frs_per_orientation[orientation][gid])
        orientation_matrix[orientation] = (array(orientation_matrix[orientation])+mul_1)*mul_2*(max_firing_rate-minimal_firing_rate)+1

    first_orientation = 0
    long_matrix_code = orientation_matrix[first_orientation].copy()
    rnd_ors = np.random.RandomState(12)
    ors = frs_per_orientation.keys()*5
    rnd_ors.shuffle(ors)

    spontaneous_matrix =  ones_like(orientation_matrix[orientation])[:,:spon_len]
    for orientation in tqdm(ors):
        long_matrix_code =  np.concatenate((long_matrix_code,    spontaneous_matrix*spon_firing_rate),1)
        long_matrix_code = np.concatenate((long_matrix_code,orientation_matrix[orientation]),1)

    gid_to_fr_list = {}
    for i, gid in enumerate(gids):
        gid_to_fr_list[gid] = long_matrix_code[i]
    return(gid_to_fr_list, [first_orientation] + list(ors))


BasePath = '/gpfs/bbp.cscs.ch/project/proj2/simulations/ThlInput/OSI_receptive_field/'
experiment = {}
experiment['stim_type'] = 'file'
experiment['stim_dt'] = 1.0
experiment['name'] = 'exp_1'


AxoGidToXY = pickle.load(open(os.environ['HOME'] + '/AxoGidToXY.p','r'))
experiment['axons_settings']  = [AxoGidToXY]



experiment['minimal_firing_rate'] = 1.0
experiment['max_firing_rate'] = 7.0
experiment['spon_firing_rate'] = 1.5
experiment['seed'] = 12


gid_to_fr_list, orientations = load_file_and_create_fr_list(path_for_fr_files = BasePath +'Data/OSI_ors_27_12_17/', min_fr= experiment['minimal_firing_rate'], 
                                                            max_fr = experiment['max_firing_rate'], spon_fr = experiment['spon_firing_rate'], spon_len=2000)
experiment['orientations'] = orientations
experiment['gid_to_fr_list'] = gid_to_fr_list
experiment['simulation_end_time'] = len(gid_to_fr_list[gid_to_fr_list.keys()[0]])*experiment['stim_dt']
print(experiment['simulation_end_time'])
#experiment['simulation_end_time'] = 130000 # I run only 130 seconds to see what I get.
simulation_duration = experiment['simulation_end_time'] 
BS = experiment['seed']
run_name = 'OSI' + '_' + `BS` 
simulation_time = "168:00:00" # real run time













run_num = 'run_30_1_18'
run_names = []

path_for_simulations = set_main_path(BasePath, ca, k)
path_for_simulations += '/' + run_num + '/'
create_path_and_copy_file(path_for_simulations)


sp_times = create_axons_spikes(experiment['seed'], experiment)
spike_replay = path_for_simulations + 'SpikeFiles/input' + str(BS) + '.dat'
save_spike_file(sp_times[1],spike_replay)


f = open(path_for_simulations +'/BlueConfig_template','r')
blue_out = crate_blueconfig(BlueConfig_file=f, CurrentDir = path_for_simulations, BS = BS, simulation_duration = simulation_duration,
                                                        run_name=run_name, ca=ca, k=k, Mg=Mg,circuit_target = circuit_target, 
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

experiment['gid_to_fr_list']  = 'Removed_to_save_data'
pickle.dump(experiment,open(path_for_simulations+ '/experiment_' + run_name + '.p','w'),protocol=2)

if not os.path.exists(path_for_simulations + '/' + run_name): #If folder already exist do not send it.
    run_names.append('sbatch launchScript_bg_' + run_name +'.sh')

#submit_jobs(run_names, path_for_simulations, MaxJobs = 2,  all_after_one=True, ssh_path=ssh_path)
                    
