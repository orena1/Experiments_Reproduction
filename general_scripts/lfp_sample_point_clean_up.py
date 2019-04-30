from __future__ import division
import SimpleITK as sitk
import numpy as np
from numpy import *
import os
import sys
import re, pickle


## The path of the output files from voxelize should be an input to the script
path = sys.argv[1]
number_of_files = int(sys.argv[2])
#path = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Cardin_Nature_2009/31_07_2017/Ca1p23_K5p0/Run_2_LFP/Remove_Minis_False/var_1e_06//freq40p0_amp3000p0_pulse_width2p5_BS1095000/'
os.chdir(path)



def parse_LFP_file_to_pickle(f_name):
    f = open(f_name,'r')
    dic_loc_to_xyz = {}
    for line in f:
        if '#' in line and 'SamplePoint' in line and 'position' in line:
            m = re.search('# - SamplePoint_(.*) position: (.*),(.*),(.*)', line)
            sp_num = m.group(1)
            sp_x = m.group(2)
            sp_y = m.group(3)
            sp_z = m.group(4)
            dic_loc_to_xyz[int(sp_num)] = (float(sp_x),float(sp_y),float(sp_z))
    f.close()
    xyz_to_lfp = {}
    lfp_data = np.loadtxt(f_name)
    time = lfp_data[:,0]
    for i in range(1,lfp_data.shape[1]):
        xyz_to_lfp[dic_loc_to_xyz[i-1]] = lfp_data[:,i]
    return(xyz_to_lfp)

files = [f for f in os.listdir('.') if 'LFP_' in f]
completed_files = 0
for f in files:
    if '_out' in f:
        f1 = open(f,'r')
        for l in f1:
            if '100%' in l:
                completed_files+=1
                break
        f1.close()

if completed_files == number_of_files: # all runs finished the LFP calculation.
    #To do 
    # merge LFP to a dictonary.
    print("merge LFP to a dictonary and save file")
    xyz_to_lfp = {}
    for i in range(1,number_of_files+1):
        xyz_to_lfp.update(parse_LFP_file_to_pickle(path + '/LFP_' + str(i)  +'_sample_points'))

    print("finish merge LFP to a dictonary")
    pickle.dump(xyz_to_lfp,open(path +'/emsim_LFP.p','w'))
    
    print("delete AllCompartmentsMembrane deleting files")
    os.remove("AllCompartmentsMembrane.bbp")
    print("finish AllCompartmentsMembrane deleting files, should delete the AllCompartmentsMembrane")
else:
    print('Completed jobs {} and number of files {}, not equal, doing nothing'.format(completed_files, number_of_files))
    
