#Xui_et al experment recreations
#Created by Oren Amsalem oren.a4@gmail.com


import os
import shutil
import sys
sys.path.append('../general_scripts/')
from HelpFuncs import SetCaKThresh, SetCaK, SetFacDep
from Cheetah.Template import Template
import subprocess

execfile('../general_scripts/VoltageCreate.py')


exp_num = 0


### Step

OriginalPath = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Pouille_2009/02_03_2017/Ca1p5_K2p5/Run_0_step/'
NewPath = OriginalPath[:-1]+'_SEClmap/'

FilesToCopy = ['user.target','inputs.dat']

## Select Cells
generalConfigPath = '/gpfs/bbp.cscs.ch/project/proj2/simulations/ThlInput/AudInput12_4_16/SSA/Ca1p23/EE0_EI0_IE0_II0_TM_0/Freq_Tono_4to16_FR_S100_W_S0p2_TwoStimsExp/BlueConfig6666_106686'
Circ = bluepy.Circuit(generalConfigPath)
#Lgids = Circ.mvddb.select_gids(Neuron.layer==5,Neuron.hyperColumn==2, MType.synapse_class=='EXC')
#seed = 15
#rand = np.random.RandomState(seed)
#Gids_g = np.random.choice(Lgids,size=32,replace=False)

Gids_g = [77119,77171,75890,75551,81277]
Gids_g = {'L5_NChoose_1':Gids_g}
Gids = Gids_g
#seeds = [1,2,3,4]
seeds = [1,2,3,4,5,6]
amplitudes = [330,340.0,342,344,345,346,348]
amplitudes = map(float,amplitudes)

### Step
#stim_durations = [5]

#for voltage_clamp_at in [None,0,-80]:
    #NewPath_v = NewPath + '/Vclamp_at_' + str(voltage_clamp_at).replace('-','neg') +'/'
    #for seed in seeds:
        #for amp in amplitudes:
            #for dur in stim_durations:
                #BS = seed*100000 + int(amp*10) + int(dur*1000)
                #run_name = 'amp' + str(float(amp)).replace('.','p') + '_dur' + str(float(dur)).replace('.','p') + '_BS' + str(BS)
                #spike_replay_path = OriginalPath +'/' + run_name + '/'
                #blue_config_name = 'BlueConfig_' + run_name
                #RunSingleGid(Gids, original_path=OriginalPath, blue_config_name=blue_config_name,  spike_replay_path=spike_replay_path, voltage_clamp_at=voltage_clamp_at,
                                        #new_path = NewPath_v, FilesToCopy=FilesToCopy,ntasks=5,report_format='Bin')





seeds = [1,2,3,4,5,6]
amplitudes = [330,340.0,342,344,345,346,348]
amplitudes = map(float,amplitudes)

## Ramp
OriginalPath = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Pouille_2009/02_03_2017/Ca1p5_K2p5/Run_0_ramp/'
NewPath = OriginalPath[:-1]+'SEClmap_ttx/'

stim_durations = [10]
for voltage_clamp_at in [None,0,-80]:
    NewPath_v = NewPath + '/Vclamp_at_' + str(voltage_clamp_at).replace('-','neg') +'/'
    for seed in seeds:
        for amp in amplitudes:
            for dur in stim_durations:
                BS = seed*100000 + int(amp*10) + int(dur*1000)
                run_name = 'amp' + str(float(amp)).replace('.','p') + '_dur' + str(float(dur)).replace('.','p') + '_BS' + str(BS)
                spike_replay_path = OriginalPath +'/' + run_name + '/'
                blue_config_name = 'BlueConfig_' + run_name
                RunSingleGid(Gids, original_path=OriginalPath, blue_config_name=blue_config_name,  spike_replay_path=spike_replay_path, voltage_clamp_at=voltage_clamp_at,
                                        new_path = NewPath_v, ttx=True,FilesToCopy=FilesToCopy,ntasks=5,report_format='Bin')















