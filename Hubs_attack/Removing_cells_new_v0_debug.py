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
from tqdm import tqdm

execfile('../../Experiments_Reproduction/general_scripts/jobs_creation.py')
execfile('../../Experiments_Reproduction/general_scripts/opto_gen_protocols.py')
generalConfigPath = '/gpfs/bbp.cscs.ch/project/proj2/simulations/ThlInput/AudInput12_4_16/SSA/Ca1p23/EE0_EI0_IE0_II0_TM_0/Freq_Tono_4to16_FR_S100_W_S0p2_TwoStimsExp/BlueConfig6666_106686'

#for ca in [0.5,1.0,1.25,1.5,2.0,2.5]:
ca = float(1.25) # float(1.25)#CAline| float(1.4)
k = float(5.0)
Mg = float(1.0)
RunMode = 'RunMode LoadBalance'


change_gamma = True
core_neuron = True
knl = True
cluster = 'neuron_coreneuron' # bbpv1 # bbpviz1 # bbpv1core_neuron

if cluster == 'neuron_coreneuron':
    base_dir = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master_Core_22_9_18/soft'  # 'Master_Core_22_9_18' # use this Master_Core_28_12_18 to record voltage
    partition = 'prod'
    bbpviz_txt =  'module load archive/2020-03; module load neurodamus-neocortex/0.3 \n'
    
    if knl == True:
        partition = 'prod_knl'
        bbpviz_txt =  'module load archive/2020-03; module load neurodamus-neocortex/0.3-knl \n'
    hoc_lib = ''
    init_name = 'init.hoc'
    special_path = ''' special -mpi '''
    ssh_path = 'bbpv1.epfl.ch'
    if knl == True:
        nodes = 30#55
        ntask_per_node = 64
    else:
        nodes = 16
        ntask_per_node = 36
        

AxoGidToXY = pickle.load(open(os.environ['HOME'] + '/AxoGidToXY.p','rb'))
def create_normalization_factor(vari):# { LOCAL temps,temps1, precision : I need to think how can I change this code so that changing the vari.
    temps  = 0
    temps1 = 0
    precision =10000
    for i in range(0,precision):
        temps  = temps +  (np.sin( (1.5+(i/precision)*2)  * np.pi)+1)*(1/precision)
        temps1 = temps1 + (( (np.sin((1.5+(i/precision)*2)* np.pi)+1))**vari)*(1/precision)

    factor = temps/temps1   
    return(factor)

def fr_function(t):
    return (axon_spontanues_firing_rate + factor*axon_stim_firing_rate*((np.sin((t+phase)*mod_freq1-0.5*np.pi)+1)**vari))/1000.0

def create_thalamic_spikes(fr_function, stim_end_time, seed):
    print('creating spike times - START')
    thalamic_rnd = np.random.RandomState(seed)
    max_firing_rate = (factor*axon_stim_firing_rate*(2**vari) + axon_spontanues_firing_rate)/1000.0
    
    sp_per_axon_gid = {}
    
    for axon_gid in tqdm(AxoGidToXY.keys()):
        spike_times = []
        t = 250 
        lamd = max_firing_rate #Do I need to multiply in 2?? I can multiply just to make sure, but it will make everything slow
        while (t<=stim_end_time):#{ :this Algorithm is from http://freakonometrics.hypotheses.org/724  from this paper. http://filebox.vt.edu/users/pasupath/papers/nonhompoisson_streams.pdf
            u = thalamic_rnd.uniform()
            t = t - np.log(u)/lamd
            if t<=stim_end_time:
                if thalamic_rnd.uniform() <= fr_function(t)/lamd:
                    invl=t
                    spike_times.append(invl)
        sp_per_axon_gid[axon_gid] = spike_times
    print('creating spike times - END')
    return(sp_per_axon_gid)


def save_spikes(sp_per_axon_gid, save_path):
    if not os.path.exists(save_path[:save_path.rindex('/')]):
        os.makedirs(save_path[:save_path.rindex('/')])
    f = open(save_path,'w')
    f.write('/scatter\n')
    sps = [zip(*[sp_per_axon_gid[axon_gid],[axon_gid]*len(sp_per_axon_gid[axon_gid])]) for axon_gid in sp_per_axon_gid]
    sps = sorted([i for j in sps for i in j])
    [f.write('{:} \t {:} \n'.format(spike_time,axon_gid)) for spike_time,axon_gid in sps]
    f.close()


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



simulation_time = "04:00:00"
nice_level = 0
simulation_duration = 500
circuit_target = 'mc2_Column'
RNGMode = 'Random123'
decouple = False
remove_spon_minis = False


reports = {}

def copy_files(path_for_simulations):
    print(path_for_simulations)
    model_folders = '../../Experiments_Reproduction/O1_v5/'
    FilesToCopy = ['launchScript_bg_template.sh', 'inputs.dat', 'user.target', 'BlueConfig_template']
    if not os.path.exists(path_for_simulations):
        os.makedirs(path_for_simulations)

    for FtC in FilesToCopy:
        shutil.copyfile(model_folders + FtC, path_for_simulations + '/' + FtC )

    shutil.copyfile(os.path.basename(__file__), path_for_simulations + '/' + os.path.basename(__file__) )



axon_spontanues_firing_rate = 14
axon_stim_firing_rate = 0.0001
vari = 6
factor = create_normalization_factor(vari)
phase = 0
freq = 2
mod_freq1 = freq * 2  * np.pi/1000.0

thalmaic_input = True
thalamic_path = ''
if thalmaic_input:
    thalamic_path = 'thalamic_inp/spon_fr' + str(axon_spontanues_firing_rate) +'_stim_fr' + str(axon_stim_firing_rate) +'_vari' + str(vari) +'_freq' + str(freq) +'/'


input_path = None
Circ = bluepy.Circuit(generalConfigPath)

run = '0'

seeds = [1]#,2]#,3]

force_all_after_one=False
all_after_one=True
attack_source = 'hubs' #hubs, in-hubs, out-hubs, katz, pagerank
net_path = '/gpfs/bbp.cscs.ch/data/project/proj5/hub_attacks/networks/' + attack_source + '/'
files = os.listdir(net_path)
## #humbs attack
files = [i for i in files if 'random' not in i and 'txt' not in i]
hubs_attacked  = np.sort([int(i.split('_')[1].split('.')[0]) for i in files])

attack_to_simulate = hubs_attacked

files_to_simulate = [i for i in files if len([1 for j in attack_to_simulate if '{:05d}'.format(j)+'.(' in i])>0]
#sdfd

### random sample
# rnd = np.random.RandomState(253) #112;70, 170;70, 70;45, 150;15 10,20 , 50, 35,120
# files = [i for i in files if 'nodes' in i and 'txt' not in i and ('ihub' in i or 'ehub' in i)]
# files_to_simulate = rnd.choice(files, size=70, replace =False)


#debug - attack of zero / 1
files_to_simulate = ['hubs_00001.(200526.230858).h5']


for attack in files_to_simulate:
    clean_attack = attack.replace('(','_').replace(')','_')[:-3]
    run_names = []
    paths_for_simulations = []
    path_for_simulations = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/hub_debug/29_7_19/' + thalamic_path + 'Ca' + str(ca).replace('.','p') + '_K' + \
                             str(k).replace('.','p') +'/Run_' +str(run)  +  '/' + clean_attack +'/'
    #if os.path.exists(path_for_simulations):#if base_folder exist, skip
    #   print("simulation exist!")
    #   continue
    copy_files(path_for_simulations)
    
    h5_file = h5py.File(net_path +'/' + attack)
    gids_to_simulate = list(set(Circ.targets.targets[circuit_target].resolve_contents_gids()) - set(list(h5_file['nodes'])))

    add_to_user_target(gids_to_simulate, circuit_target + '_' + clean_attack, path_for_simulations)
    

    for seed in seeds:
        BS = seed*100000
        run_name = clean_attack +'_s' + str(BS)
        if thalmaic_input:
            sp_per_axon_gid = create_thalamic_spikes(fr_function, stim_end_time=simulation_duration, seed=seed)
            input_path = path_for_simulations +'/SpikeFiles/' + run_name
            save_spikes(sp_per_axon_gid, save_path=input_path)
            
            
        f = open(path_for_simulations +'/BlueConfig_template','r')
        blue_out = crate_blueconfig(BlueConfig_file=f, CurrentDir = path_for_simulations, BS = BS, simulation_duration = simulation_duration,
                                                                run_name=run_name, ca=ca, k=k, Mg=Mg, circuit_target = circuit_target + '_' + clean_attack, decouple=decouple,
                                                                optogenetic_vars=[],reports=reports,RunMode=RunMode, remove_spon_minis=remove_spon_minis,RNGMode=RNGMode, core_neuron=core_neuron,
                                                                spike_replay=input_path)
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
        
        #if not os.path.exists(path_for_simulations + '/' + run_name): #If folder already exist do not send it.
        run_names.append('sbatch launchScript_bg_' + run_name +'.sh')
        #else:
        print("simulation out directory already exist!")
        
        
        paths_for_simulations.append(path_for_simulations)
    submit_jobs(run_names, paths_for_simulations, MaxJobs = 8,  all_after_one=all_after_one, ssh_path=ssh_path, force_all_after_one=force_all_after_one)
