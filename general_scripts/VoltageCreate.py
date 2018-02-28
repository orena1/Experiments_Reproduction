from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
import os
import numpy as np
import bluepy
import shutil

import os
import numpy as np
import bluepy
import shutil
from bluepy.targets.mvddb import Neuron, MType, EType
import progressbar
import time
from bluepy.targets.mvddb import Neuron, MType, EType
import bluepy

Tmp = 'Stimulus spikeReplayCortex\n ' \
'{\n' \
'        Mode Current\n' \
'        Delay 0\n' \
'        Duration 100000000\n' \
'        Pattern SynapseReplay\n' \
'        SpikeFile ReplayPath\n'\
'}\n'\
'\n'\
'\n'\
'StimulusInject spikeReplayIntoUniverseCortex\n'\
'{\n'\
'        Stimulus spikeReplayCortex\n'\
'        Target Mosaic\n'\
'}\n\n'


ReportTxt = 'Report voltage\n'\
'{\n'\
'        Target GID\n'\
'          Type compartment\n'\
'      ReportOn v\n'\
'          Unit mV\n'\
'        Format ASCII\n'\
'            Dt 0.1\n'\
'     StartTime 0\n'\
'       EndTime 250000\n'\
'}\n\n'



SEClamptxt = 'Stimulus voltage_clamp\n ' \
'{\n' \
'        Mode Current\n' \
'        Pattern SEClamp\n' \
'        Delay 0\n' \
'        Duration 100000000\n' \
'        Voltage VOLTAGE\n' \
'}\n'\
'\n'\
'\n'\
'StimulusInject voltage_clamps\n'\
'{\n'\
'        Stimulus voltage_clamp\n'\
'        Target GID\n'\
'}\n\n'



ReportSEClampTxt = 'Report SEClamp_i\n'\
'{\n'\
'        Target GID\n'\
'          Type Summation\n'\
'      ReportOn SEClamp.i\n'\
'          Unit nA\n'\
'        Format ASCII\n'\
'            Dt 0.1\n'\
'     StartTime 0\n'\
'       EndTime 250000\n'\
'}\n\n'


TTXblock = 'Modification applyTTX\n'\
'{\n'\
'     Type TTX\n'\
'   Target TTARGET\n'\
'}\n\n'


cell_check = 1
def RunSingleGid(Gid, original_path, blue_config_name, spike_replay_path, new_path, FilesToCopy,
                 voltage_clamp_at, ttx = False, extra_string = '', ntasks=1, report_format='ASCII'):
    '''Gid can be a dic when the key is the name of the grop, or just a gid'''
    
    global cell_check
    Gid_is_group = [] # [] mean not
    if type(Gid)==dict:
        Gid_is_group = Gid[Gid.keys()[0]]
        Gid = Gid.keys()[0]
    print("Sending Neuron " + str(Gid))
    #if (type(Gid)==dict and len(Gid)>ntasks) or (type(Gid)!=dict and ntasks>1):
        #raise Exception("Number of nodes is higer than number of cells!")
        
    NeedToRun =0
    if not os.path.exists(new_path):
        os.makedirs(new_path)
        os.makedirs(new_path + 'SpikeFiles')
        NeedToRun = 1
    if NeedToRun==1:
        for FtC in FilesToCopy:
            shutil.copyfile(original_path + FtC, new_path + FtC )
        os.chdir(new_path)
    
    if extra_string=='':
        extra_string = blue_config_name.replace('BlueConfig','')
    
    if not os.path.isfile(new_path + 'SpikeFiles/' + extra_string  +  'out.dat'):
        shutil.copyfile(spike_replay_path + '/out.dat', new_path + 'SpikeFiles/' + extra_string  +  'out.dat') #copy out file
    else:
        print('Spike file already exist in the directory and it will not be copied')

    if not os.path.isfile(spike_replay_path+ '/out.dat'):
        raise Exception('replay file does not exists!')
    
    ##########################
    #### Create BlueConfig ###
    ##########################
    if cell_check==1 and os.path.exists(new_path + blue_config_name + '_' +  str(Gid)):
        ttm = raw_input('Cell was already submited, are you sure you want to resnd it? (y)/n/noAll')
        if ttm=='n':
            return()
        if ttm=='noAll':
            cell_check=0
    txt = ''
    f = open(original_path + blue_config_name , 'r' )
    for l in f:
        if 'RunMode' in l:
            txt+= '        #RunMode\n'
        elif 'CircuitTarget' in l and '#' not in l:
            txt+='  CircuitTarget a' +str(Gid) + '\n'
        elif 'Stimulus spikeReplay\n' == l:
            txt+= Tmp.replace('ReplayPath', new_path + 'SpikeFiles/' + extra_string  +  'out.dat') 
            txt+= ReportTxt.replace('GID','a'+str(Gid)).replace('ASCII',report_format).replace('voltage','voltage_' + str(Gid))
            if voltage_clamp_at != None:
                txt+= SEClamptxt.replace('GID','a'+str(Gid)).replace('VOLTAGE',str(voltage_clamp_at))
                txt+= ReportSEClampTxt.replace('GID','a'+str(Gid)).replace('ASCII',report_format).replace('SEClamp_i','SEClamp_i_' + str(Gid))
            if ttx == True:
                txt+= TTXblock.replace('TTARGET','a'+str(Gid))
            txt+=l
        elif 'Report' in l:
            txt += '#' + l
        elif original_path in l:
            txt+= l.replace(original_path,new_path)
        else:
            txt+=l

    
    f.close()
    f = open(new_path + blue_config_name + '_' +  str(Gid), 'w' )
    f.write(txt)
    f.close()
    
    #############################
    #### Create launchScript ####
    #############################
    txt = ''
    launch_script_name =  'launchScript_bg'+blue_config_name.replace('BlueConfig','')
    f = open(original_path + launch_script_name + '.sh', 'r' )
    for l in f:
        if 'job--name' in l:
            txt+=str(Gid) +'_'+l
        elif 'partition' in l:
            txt+=l.replace('prod','test')
        elif '--node' in l:
            pass
        elif '--ntasks-per-node' in l or '#SBATCH --ntasks=' in l:
            txt+= '#SBATCH --ntasks=' + str(ntasks) +'\n'
        elif '--overcommit' in l:
            pass
        elif '--time' in l:
            txt+='#SBATCH --time=5:00:00\n'
        elif '--output' in l or '--error' in l:
            txt+=l.replace('.log',blue_config_name.replace('BlueConfig','') + '_'+str(Gid) + '.log')
        elif 'HOC_LIBRARY_PATH=' in l:
            txt+='module load BBP/hpc/2017.06\n' # BBP/hpc/latest
        elif 'srun' in l and 'powerpc64' in l:
            if 'Master06_11_16' not in l and 'Master07_07_17' not in l:
                raise Exception('You need to fix the neurodamus paths,  also up!!!!!')
            txt+='srun special  -c '\
                '"{strdef configFile configFile=\\"' +blue_config_name + '_' +  str(Gid) +  '\\"}" -NFRAME 256 $BBP_HOME/hoclib/init.hoc -mpi \n'
        else:
            txt+=l
    f.close()
    f = open(new_path +  launch_script_name + '_' + str(Gid) + '.sh', 'w' )
    f.write(txt)
    f.close()

    #############################
    #### Create user.target #####
    #############################
    lines = list(open(new_path +  'user.target','r'))
    if 'Target Cell a' + str(Gid) +'\n' not in lines:
        print('Adding Neuron Target')
        f = open(new_path +  'user.target','a')
        f.write('Target Cell a' + str(Gid) +'\n')
        if Gid_is_group==[]:
            f.write('{\n  a' +str(Gid) + '\n}\n\n')
        else:
            f.write('{\n')
            for gid in Gid_is_group:
                f.write('a' +str(gid) + ' ')
            f.write('\n}\n\n')
        f.close()
    os.chdir(new_path)
    print('sbatch ' + launch_script_name + '_' + str(Gid) + '.sh')
    os.system('sbatch ' + launch_script_name + '_' + str(Gid) + '.sh')
    
###










    
