from __future__ import division
from numpy import *
import numpy as np
import time
import os
import subprocess
import sys
def find_points(spacing):
    X = np.array([ 115.46,  230.92,  461.84,  577.3 ,  461.84,  230.92,  115.46])
    Z = np.array([ 599.94,  399.96,  399.96,  599.94,  799.92,  799.92,  599.94])

    min_x= min(X); max_x = max(X)
    min_y = 0;  max_y = 2066
    min_z = min(X); max_z = max(Z)

    all = []
    for i in range(len(X)-1):
        x = np.array([[X[i],X[i]],[X[i+1],X[i+1]]])
        z = np.array([[Z[i],Z[i]],[Z[i+1],Z[i+1]]])
        y = np.array([[    min_y,  max_y],
        [    min_y,  max_y]])
        #mmlab.mesh(x,y,z,color=(0/256.0,0/256.0,0/256.0),opacity=0.1)
        for r in range(len(x)):
            for rr in range(len(x[r])):
                all.append([x[r][rr],y[r][rr],z[r][rr]])




    def in_hull(p, hull):
        """
        Test if points in `p` are in `hull`

        `p` should be a `NxK` coordinates of `N` points in `K` dimensions
        `hull` is either a scipy.spatial.Delaunay object or the `MxK` array of the 
        coordinates of `M` points in `K`dimensions for which Delaunay triangulation
        will be computed
        """
        from scipy.spatial import Delaunay
        if not isinstance(hull,Delaunay):
            hull = Delaunay(hull)

        return hull.find_simplex(p)>=0

    pps = []
    for x in arange(min_x,max_x+spacing,spacing):
        for y in arange(min_y,max_y+spacing,spacing):
            for z in arange(min_z,max_z+spacing,spacing):
                pps.append([x,y,z])

    vs = in_hull(pps, all)



    xs=[]; ys=[]; zs=[]
    for i in range(len(pps)):
        if vs[i]:
            xs.append(pps[i][0])
            ys.append(pps[i][1])
            zs.append(pps[i][2])

    return(xs,ys,zs)


def bin_search(item):

    first = 1
    last = 10000
    found = False

    while first<=last and not found:
        pos = 0
        midpoint = (first + last)/2
        if abs(len(find_points(midpoint)[0]) - item)<10:
            pos = midpoint
            found = True
        else:
            if item < len(find_points(midpoint)[0]):
                first = midpoint
            else:
                last = midpoint
        if abs(first-last)<0.1:
            found = True
            pos = [first,last][argmin([abs(item-len(find_points(first)[0])),abs(item-len(find_points(last)[0]))])]
        print(first,last),
    print('\n Number of points' + str(len(find_points(pos)[0])))
    return(pos)
    
num_measure_points = 400
spacing0 = bin_search(num_measure_points)

points = find_points(spacing0)
points = [[points[0][i],points[1][i], points[2][i]] for i in range(len(points[0]))]

if len(sys.argv)>1:
    BlueConfig = sys.argv[1]
    print('BlueConfig=' + BlueConfig)
else:
    BlueConfig = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Cardin_Nature_2009/31_07_2017/Ca1p23_K5p0/Run_2_LFP/Remove_Minis_False/var_1e_06/BlueConfig_freq40p0_amp3000p0_pulse_width2p5_BS1095000'
command = 'target=mc2_Column&report=AllCompartmentsMembrane&functor=lfp&cutoff=10000'


f = open(BlueConfig,'r')
for l in f: 
    if 'OutputRoot' in l: 
        out_dir = l.split()[1]
        os.chdir(out_dir)
    if 'Duration' in l: #get simulation time
        simulation_time = l.split()[1]
    if '}' in l:
        break
    




'''
voxelize --volume "fivoxsomas:///gpfs/bbp.cscs.ch/project
/proj2/simulations/Reproducing_Experiments/Cardin_Nature_2009/3
1_07_2017/Ca1p23_K5p0/Run_2_LFP/Remove_Minis_False/var_1e_06/BlueConfig_freq40p0_a
mp3000p0_pulse_width2p5_BS1095000?target=mc2_Column&report=AllCompartmentsMembrane&functor=lfp&cutoff=10000&resolution=0.0059" --times '2000 2010'
'''


##################
##### This is for running one work using CUDA
####################
def build_sbatch_script_CUDA(resolution):
    """
    Build sbatch script for a certain frame range
    """

    values = {}
    out_file = BlueConfig.split('/')[-1][11:]
    
    #ptxt = 'voxelize --volume "fivoxsomas:///' + BlueConfig + '?' + command + '&resolution=' + str(resolution) +  '" --times "0 12"'
    ptxt = 'voxelize --volume "fivoxcompartments:///' + BlueConfig + '?' + command + '&resolution=' + str(resolution) +  '" --times "0 ' + simulation_time + '"'
    values['ptxt'] = ptxt
    
    values['job_name'] = out_file
    values['job_time'] = '24:00:00'
    values['queue'] = 'prod'
    values['account'] = 'proj2'
    values['nodes'] = 1
    values['tasks_per_node'] = 3
    values['output_dir'] = out_dir



    sbatch_script = '\n'.join((
        '#!/bin/bash',
        '#SBATCH --job-name="{job_name}"',
        '#SBATCH --time="{job_time}"',
        '#SBATCH --partition="{queue}"',
        '#SBATCH --account="{account}"',
        '#SBATCH --nodes="{nodes}"',
        '#SBATCH --ntasks-per-node="{tasks_per_node}"',
        '#SBATCH --output="{output_dir}/{job_name}_out.txt"',
        '#SBATCH --error="{output_dir}/{job_name}_err.txt"',
        '#SBATCH --gres=gpu:1',
        'cd {output_dir}',
        'srun --pty --preserve-env -n1 --mpi=none $SHELL',
        'module load BBP/viz/latest',
        '',
        '{ptxt}',
        'PATH="/gpfs/bbp.cscs.ch/home/amsalem/anaconda2/bin:$PATH"\n',
        'python /gpfs/bbp.cscs.ch/home/amsalem/Dropbox/Blue_Brain/Experiments_Reproduction/general_scripts/mhd_to_pickler.py ' + out_dir +'',
        
    )).format(**values)

    return sbatch_script

resolution = 1/spacing0
if os.path.exists('out.dat'):
    sbatch_script = build_sbatch_script_CUDA(resolution)
    sbatch = subprocess.Popen(['sbatch'], stdin=subprocess.PIPE)
    print(sbatch_script)
    sbatch.communicate(input=sbatch_script)
else:
    print("Out file does not exist, LFP will not be calcualted.") 



##################
##### This is for for running one work on each node
####################


def build_sbatch_script(point):
    """
    Build sbatch script for a certain frame range
    """

    values = {}
    point_str = '{:} {:} {:}'.format(point[0],point[1],point[2])
    out_file = 'LFP_p_{:}_{:}_{:}'.format(point[0],point[1],point[2]).replace('.','p')
    ptxt = 'sample-point --volume "fivoxsomas:///' + BlueConfig + '?' + command + '" --point "' + point_str + '" --times "0 200" --output ' + out_file + '.txt'
    values['ptxt'] = ptxt
    
    values['job_name'] = out_file
    values['job_time'] = '06:00:00'
    values['queue'] = 'prod'
    values['account'] = 'proj2'
    values['nodes'] = 1
    values['tasks_per_node'] = 16
    values['output_dir'] = out_dir



    sbatch_script = '\n'.join((
        '#!/bin/bash',
        '#SBATCH --job-name="{job_name}"',
        '#SBATCH --time="{job_time}"',
        '#SBATCH --partition="{queue}"',
        '#SBATCH --account="{account}"',
        '#SBATCH --nodes="{nodes}"',
        '#SBATCH --ntasks-per-node="{tasks_per_node}"',
        '#SBATCH --output="{output_dir}/{job_name}_out.txt"',
        '#SBATCH --error="{output_dir}/{job_name}_err.txt"',
        'cd {output_dir}',
        'module load BBP/viz/latest',
        '{ptxt}'
    )).format(**values)

    return sbatch_script



# print("Submit job {0} for frames {1} to {2}...".format(idx, start,
                                                        # end))
# for ind,point in enumerate([points[0]]):
    # sbatch_script = build_sbatch_script(point)
    # sbatch = subprocess.Popen(['sbatch'], stdin=subprocess.PIPE)
    # sbatch.communicate(input=sbatch_script)





##################
##### This is for for running many works on one node
####################




# max_sub_pro = 16
# num_runnig = 0
# Ps = []
# for ind,point in enumerate(points):
    # num_runnig = sum([1 for p in Ps if p.poll()==None])
    # while num_runnig>=max_sub_pro:
        # time.sleep(10)
        # num_runnig = sum([1 for p in Ps if p.poll()==None])
        # print('sleep'),
    
    
    
    # print('Starting point ' + str(ind) + ' out of ' + str(len(points)) + '  ' + str(ind/len(points)*100))
    
    
    # point_str = '{:} {:} {:}'.format(point[0],point[1],point[2])
    # out_file = 'LFP_p_{:}_{:}_{:}'.format(point[0],point[1],point[2]).replace('.','p')
    # args = ['sample-point', '--volume', 'fivoxsomas://' + BlueConfig + '?' + command, '--point', point_str , '--times', "0 200", '--output',  out_file + '.txt']
    # p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Ps.append(p)

# while sum([1 for p in Ps if p.poll()==None])>0:
    # time.sleep(10)
    # print('Waiting for last jobs to finish'),



#
# End!
#




# files = os.path.listdir()
# for i in os.path.listdir()





# point = points[0]

# ptxt = 'sample-point --volume "fivoxsomas:///' + BlueConfig + '?' + command + '" --point "' + point_str + '" --times "0 200" --output ' + out_file + '.txt'
# args = ['sample-point', '--volume', 'fivoxsomas:///' + BlueConfig + '?' + command, '--point', point_str , '--times', "0 200", '--output',  out_file + '.txt']
# p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


# import subprocess
# p = subprocess.Popen(ptxt.split())


# ptxt = 'sample-point --volume "fivoxsomas:///gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/Cardin_Nature_2009/31_07_2017/Ca1p23_K5p0/Run_2_LFP/Remove_Minis_False/var_1e_06/BlueConfig_freq40p0_amp3500p0_pulse_width2p5_BS1100000?target=mc2_Column&report=AllCompartmentsMembrane&functor=lfp&cutoff=10000" --point "182.3021875 182.3021875 182.3021875" --times "0 200" --output LFP_p_182p3021875_182p3021875_182p3021875.txt'



