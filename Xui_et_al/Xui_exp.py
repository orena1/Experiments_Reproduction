#Xui_et al experment recreations
#Created by Oren Amsalem oren.a4@gmail.com
import os
import shutil
import sys
sys.path.append('../general_scripts/')
from HelpFuncs import SetCaKThresh, SetCaK, SetFacDep
from Cheetah.Template import Template
import subprocess

execfile('../general_scripts/jobs_creation.py')
execfile('../general_scripts/opto_gen_protocols.py')

#for ca in [0.5,1.0,1.25,1.5,2.0,2.5]:
ca = 1.25 #CAline
k = 2.5
Mg = 1.0

var = 0.000001 # 0.000001 | 0.3 | 0.8

RunModeToNeurodamusPath = {'RunMode LoadBalance':['/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/hoclib','/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/powerpc64/special'], 
                        '#RunMode': ['/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/hoclib', '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/powerpc64/special']
                        }

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
    account  = 'proj2'
else:
## for bbpviz1
    hoc_lib = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/hoclib'
    init_name = 'init.hoc'
    special_path = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/neurodamus/lib/x86_64/special -mpi'
    nodes = 2
    ntask_per_node = 15
    partition = 'prod'
    bbpviz_txt = 'module load mvapich2/2.2b-slurm-nocuda-1 gcc/4.9.0 hdf5/1.8.16-1\n'\
                     'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/gpfs/bbp.cscs.ch/project/proj2/Programs/Master06_11_16/reportinglib/install/lib64\n\n'
    ssh_path = 'bbpviz1.cscs.ch'





remove_spon_minis = False
run = '1'
#other_circuit = '/gpfs/bbp.cscs.ch/project/proj2/circuits/SomatosensoryCxS1-v5.r0_postprocessing'
other_circuit = False
path_for_simulations = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Xue_Nature_2014/31_01_2017/Ca' + \
                            str(ca).replace('.','p') + '_K' + str(k).replace('.','p') +'/Run_' +str(run)  +  '/Remove_Minis_' +str(remove_spon_minis) +'/var_' + str(var).replace('.','p').replace('-','_')+'/'
if other_circuit is not False:
    path_for_simulations =path_for_simulations[:-1] + 'other_circuit/'

NMDA_GAMMA  = True
if NMDA_GAMMA==True:
    path_for_simulations  = path_for_simulations.replace('Xue_Nature_2014/','Xue_Nature_2014/Gamma_')
    special_path = '/gpfs/bbp.cscs.ch/project/proj2/Programs/Master07_07_17/neurodamus/lib_NMDA/powerpc64/special'



reports = {'soma_voltage':{
        'REPORT_TARGET':'mc2_Column',
        'START_TIME':str(1900),
        'END_TIME':str(9e9)}}

simulation_time = "03:00:00"
nice_level = 0


opto_gen_stimstart = 2000
simulation_duration = 2100

seeds = [3,4,5,6,7,8,9,10,11,12,13,14,15,16,17]
#seeds = [1,2]


#amplitudes = [60,100,140,160,180,200,210,220,245,265] #Ca1p5 or Ca1p25
#amplitudes = [40,80,100,120,140,160,170,175,180,200] #Ca2p5
amplitudes = [450,700] #Ca2p5



# seeds = [2]

# #amplitudes = [60,100,140,160,180,200,210,220,245,265] #Ca1p5 or Ca1p25
# #amplitudes = [40,80,100,120,140,160,170,175,180,200] #Ca2p5
# amplitudes = [450] #Ca2p5

amplitudes = map(float,amplitudes)
stim_durations = [5] #Don't use 0.5 ms


model_folders = '../O1_v5/'
FilesToCopy = ['launchScript_bg_template.sh', 'inputs.dat', 'user.target', 'BlueConfig_template']
if not os.path.exists(path_for_simulations):
    os.makedirs(path_for_simulations)
    
for FtC in FilesToCopy:
    shutil.copyfile(model_folders + FtC, path_for_simulations + '/' + FtC )

shutil.copyfile(os.path.basename(__file__), path_for_simulations + '/' + os.path.basename(__file__) )
print path_for_simulations
run_names = []
for seed in seeds:
    for amp in amplitudes:
        for dur in stim_durations:
            BS = seed*100000 + int(amp*10) + int(dur*1000)
            run_name = 'amp' + `float(amp)`.replace('.','p') + '_dur' + `float(dur)`.replace('.','p') + '_BS' + `BS`
            stim_vars = {'Layer4Excitatory':[{'amp':amp,'start':opto_gen_stimstart,'dur':dur, 'var':amp*var}]}
            morphs = ['Layer4Excitatory']
            
            f = open(path_for_simulations +'/BlueConfig_template','r')
            blue_out = crate_blueconfig(BlueConfig_file=f, CurrentDir = path_for_simulations, BS = BS, simulation_duration = simulation_duration,
                                                                    run_name=run_name, ca=ca, k=k, Mg=Mg, optogenetic_vars=['current_injections', morphs, stim_vars],reports=reports,
                                                                    remove_spon_minis=remove_spon_minis, other_circuit=other_circuit)
            f = open(path_for_simulations + 'BlueConfig_' + run_name, 'w')
            f.write(blue_out)
            f.close()
            
            
            f = open(path_for_simulations +'/launchScript_bg_template.sh','r')
            launch_out = create_launch_script(launchScript_file=f, hoc_lib=hoc_lib, init_name=init_name, special_path=special_path, simulation_time=simulation_time,
                                                                                run_name=run_name, nice_level=nice_level, nodes=nodes, ntask_per_node=ntask_per_node, 
                                                                                    bbpviz_txt = bbpviz_txt, partition=partition, account=account)
            f = open(path_for_simulations + 'launchScript_bg_' + run_name +'.sh', 'w')
            f.write(launch_out)
            f.close()
            if not os.path.exists(path_for_simulations + '/' + run_name): #If folder already exist do not send it.
                run_names.append('sbatch launchScript_bg_' + run_name +'.sh')

submit_jobs(run_names, path_for_simulations, MaxJobs = 2,  all_after_one=True)
                    
                











