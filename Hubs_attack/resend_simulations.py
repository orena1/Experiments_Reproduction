import os
base_dir = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Reproducing_Experiments/29_7_19/Ca1p4_K5p0/Run_0'
folders = os.listdir(base_dir +'/.')
for fold in folders:
    files = os.listdir(base_dir + '/' + fold)
    l_files = [f for f in files if 'launchScript' in f and 'template' not in f]
    for l in l_files:
        if not os.path.exists(base_dir +'/' + fold + '/' + l.split('bg_')[1][:-3] + '/out.dat'):
            
            #pass#sdfsdf
            os.chdir(base_dir +'/' + fold + '/')
            os.system('sbatch ' + l)
            print(base_dir +'/' + fold + '/','sbatch ' + l)
            print('---------------------------------------')
