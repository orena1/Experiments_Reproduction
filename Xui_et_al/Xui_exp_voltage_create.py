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


OriginalPath = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Xue_Nature_2014/31_01_2017/Ca1p25_K2p5/Run_1/Remove_Minis_False/var_1e_06other_circuit/'
NewPath = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Xue_Nature_2014/31_01_2017/Ca1p25_K2p5/Run_1/Remove_Minis_False/var_1e_06other_circuit_SEClmaps/'

FilesToCopy = ['user.target','inputs.dat']

## Select Cells
generalConfigPath = '/gpfs/bbp.cscs.ch/project/proj2/simulations/ThlInput/AudInput12_4_16/SSA/Ca1p23/EE0_EI0_IE0_II0_TM_0/Freq_Tono_4to16_FR_S100_W_S0p2_TwoStimsExp/BlueConfig6666_106686'
Circ = bluepy.Circuit(generalConfigPath)
Lgids = np.sort(Circ.mvddb.select_gids(Neuron.layer==3,Neuron.hyperColumn==2, MType.synapse_class=='EXC'))
seed = 15
rand = np.random.RandomState(seed)
net_size = 132
Gids = np.sort(rand.choice(Lgids,size=net_size,replace=False))
Gids = {'L3_N' + str(net_size) + '_S' + str(seed):Gids}


#seeds = [1,2,3,4,5,6]
seeds = [2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17]

amplitudes = [450,700] 
amplitudes = map(float,amplitudes)
stim_durations = [5]

for voltage_clamp_at in [0,-80]:
    NewPath_v = NewPath + '/Vclamp_at_' + str(voltage_clamp_at).replace('-','neg') +'/'
    for seed in seeds:
        for amp in amplitudes:
            for dur in stim_durations:
                BS = seed*100000 + int(amp*10) + int(dur*1000)
                run_name = 'amp' + str(float(amp)).replace('.','p') + '_dur' + str(float(dur)).replace('.','p') + '_BS' + str(BS)
                print run_name
                spike_replay_path = OriginalPath +'/' + run_name + '/'
                blue_config_name = 'BlueConfig_' + run_name
                RunSingleGid(Gids, original_path=OriginalPath, blue_config_name=blue_config_name,  spike_replay_path=spike_replay_path, voltage_clamp_at=voltage_clamp_at,
                                        new_path = NewPath_v, FilesToCopy=FilesToCopy,ntasks=16,report_format='Bin')





























