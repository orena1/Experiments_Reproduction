from __future__ import division
import SimpleITK as sitk
import numpy as np
from numpy import *
import os
import sys

'''
This funciton reads a '.mhd' file using SimpleITK and return the image array, origin and spacing of the image.
'''

def load_itk(filename):
    # Reads the image using SimpleITK
    itkimage = sitk.ReadImage(filename)

    # Convert the image to a  numpy array first and then shuffle the dimensions to get axis in the order z,y,x
    ct_scan = sitk.GetArrayFromImage(itkimage)

    # Read the origin of the ct_scan, will be used to convert the coordinates from world to voxel and vice versa.
    origin = np.array(list(reversed(itkimage.GetOrigin())))

    # Read the spacing along each dimension
    spacing = np.array(list(reversed(itkimage.GetSpacing())))

    return ct_scan, origin, spacing

## The path of the output files from voxelize should be an input to the script
path = sys.argv[1]
#path = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Cardin_Nature_2009/31_07_2017/Ca1p23_K5p0/Run_2_LFP/Remove_Minis_False/var_1e_06//freq40p0_amp3000p0_pulse_width2p5_BS1095000/'
os.chdir(path)


files = [f for f in os.listdir('.') if 'mhd' in f]
sorted_files = [files[i] for i in argsort([float(f.split('volume')[1].split('.')[0]) for f in files])]



vv = load_itk(sorted_files[0])
xs = []
ys = []
zs = []
val = []
ct_scan = vv[0]
origin = vv[1]
spacing = vv[2]
LFP = {}

ijij_to_xyz = {}

for i in range(len(ct_scan)):
    for j in range(len(ct_scan[i])):
        for ij in range(len(ct_scan[i][j])):
            xs.append(origin[0]+spacing[0]*i)
            ys.append(origin[1]+spacing[1]*j)
            zs.append(origin[2]+spacing[2]*ij)
            ijij_to_xyz[(i,j,ij)] = [xs[-1],ys[-1],zs[-1]]
            val.append(ct_scan[i][j][ij])
            LFP[(xs[-1],ys[-1],zs[-1])] = zeros(len(files))
xd = range(len(ct_scan))
yd = range(len(ct_scan[i]))
zd = range(len(ct_scan[i][j]))
            
print('finish_run')
vv = load_itk(sorted_files[0])
n_files = len(sorted_files)
for nn,f in enumerate(sorted_files):
    itkimage = sitk.ReadImage(f)
    ct_scan = sitk.GetArrayFromImage(itkimage)
    for i in xd:
        for j in yd:
            for ij in zd:
                x,y,z = ijij_to_xyz[(i,j,ij)]
                LFP[(x,y,z)][nn]= ct_scan[i][j][ij]
    if nn%250==0:
        print(nn/n_files),

print('\n finish creation of LFP dic')
import cPickle as pickle
pickle.dump(LFP,open('LFP.p','w'),protocol=2)
print('finish LFP save')
#delete volume files.
for f in sorted_files:
    os.remove(f)
    os.remove(f[0:-4] + '.raw')
print("Done deleting files")
#delete_current_file.

#os.remove("AllCompartmentsMembrane.bbp")
