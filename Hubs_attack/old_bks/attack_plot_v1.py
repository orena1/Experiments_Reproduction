from __future__ import division
from mayavi import mlab
import pandas as pnd
import cPickle as pickle
import numpy as np
import collections
cnt=  collections.Counter
#mc0_data = pnd.read_pickle('Dropbox/mc0_data.p')
# attackhub    = pickle.load(open('Dropbox/v2/test_sccs.L5_TTPC1.hub-attack.2122.(180729.160908).pickle','r'))
# attackrandom = pickle.load(open('Dropbox/v2/test_sccs.L5_TTPC1.random-attack.2122.(180729.161039).pickle','r'))

# attackhub    = pickle.load(open('Dropbox/v2/test_sccs.NMC.hub-attack.2122.(180729.210353).pickle','r'))
# attackrandom = pickle.load(open('Dropbox/v2/test_sccs.NMC.random-attack.2122.(180729.210747).pickle','r'))


#attackhub    = pickle.load(open('/Users/orenamsalem/Dropbox/v3/test_sccs.L5_TTPC1.hub-attack.2121.(180911.090045).pickle','r'))
#attackrandom = pickle.load(open('/Users/orenamsalem/Dropbox/v3/test_sccs.L5_TTPC1.random-attack.2122.(180911.085943).pickle','r'))

#attackhub    = pickle.load(open('/Users/orenamsalem/Dropbox/v3/test_sccs.NMC.hub-attack.2122.(180911.144001).pickle','r'))
#attackrandom = pickle.load(open('/Users/orenamsalem/Dropbox/v3/test_sccs.NMC.random-attack.2122.(180911.144356).pickle','r'))




#generalConfigPath = '/gpfs/bbp.cscs.ch/project/proj2/simulations/ThlInput/AudInput12_4_16/SSA/Ca1p23/EE0_EI0_IE0_II0_TM_0/Freq_Tono_4to16_FR_S100_W_S0p2_TwoStimsExp/BlueConfig6666_106686'
#print  'Loading all  took ' +  `time.time() - STloadTM` + ' secs'
#Circ = bluepy.Circuit(generalConfigPath)

data = pickle.load(open('/Users/orenamsalem/Downloads/data.p','r'))
gid_to_loc = data['neurons_position']

#array([   0,  100,  200,  300,  400,  500,  600,  700,  800,  900, 1000,
#       1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100,
#       2200, 2300, 2400])
#22000 - 

import glob
import seaborn as sns
filenames = glob.glob('/Users/orenamsalem/Dropbox/v3/*test_sccs*.pickle')
%gui qt
attack_sizes = [22000, 22100, 22200, 22300, 22400,
       22500, 22600, 22700, 22800, 22900, 23000, 23100, 23200, 23300,
       23400, 23500, 23600, 23700, 23800, 23900, 24000, 24100, 24200,
       24300, 24400, 24500, 24600, 24700, 24800, 24900, 25000, 25100,
       25200, 25300, 25400, 25500, 25600, 25700, 25800, 25900, 26000,
       26100, 26200, 26300, 26400, 26500, 26600, 26700, 26800, 26900,
       27000, 27100, 27200, 27300, 27400, 27500, 27600, 27700, 27800,
       27900, 28000, 28100, 28200, 28300, 28400, 28500, 28600, 28700,
       28800, 28900, 29000, 29100, 29200, 29300, 29400, 29500, 29600,
       29700, 29800, 29900, 30000, 30100, 30200, 30300, 30400, 30500,
       30600, 30700, 30800, 30900, 31000, 31100, 31200, 31300]

for fname in filenames:
    attack = pickle.load(open('/Users/orenamsalem/Dropbox/v3/' + fname ,'r'))



    for attack_size in attack_sizes[::3]:


        clusters_ids_to_show  = np.argsort(map(len,attack['attacks'][attack_size]['sccs']))[::-1]
        mlab.figure(1, fgcolor=(0, 0, 0), bgcolor=(1, 1, 1))
        colors = [(1,0,0), (0,1,0), (0,0,1)]
        alls = []

        X = np.array([ 115.46,  230.92,  461.84,  577.3 ,  461.84,  230.92,  115.46])
        Z = np.array([ 599.94,  399.96,  399.96,  599.94,  799.92,  799.92,  599.94])

        for i in range(len(X)-1):
            x = np.array([[X[i],X[i]],[X[i+1],X[i+1]]])
            z = np.array([[Z[i],Z[i]],[Z[i+1],Z[i+1]]])
            y = np.array([[    -100.,  2100.],
               [    -100.,  2100.]])
            mlab.mesh(x,y,z,color=(235/255.0,255/255.0,255/255.0),opacity=0.8)



        cyan_color= (0.12156862745098039, 0.4666666666666667, 0.7058823529411765)
        dark_cyan_color= (0, 0.5450980392156862, 0.5450980392156862)
        for ii,i in enumerate(clusters_ids_to_show):
            gids = attack['attacks'][attack_size]['sccs'][i]
            x=[]
            y=[]
            z=[]
            for gid in gids:
                if gid!=0:
                    x.append(gid_to_loc[gid][0])
                    y.append(gid_to_loc[gid][1])
                    z.append(gid_to_loc[gid][2])

            if len(x)>3:
                print('print_cluster')
                # Visualize the points
                print(len(x),ii)
                pts = mlab.points3d(x, y, z, scale_mode='none', scale_factor=0,color=cyan_color)

                # Create and visualize the mesh
                mesh = mlab.pipeline.delaunay3d(pts)
                surf_v = mlab.pipeline.surface(mesh, opacity=0.5,color=cyan_color)
                
                #surf_v = mlab.pipeline.volume(mlab.pipeline.gaussian_splatter(pts))
                #surf_v = mlab.pipeline.volume(mesh)
                alls.append([pts, mesh, surf_v])
            elif len(x)==2:
                pass
                l = mlab.plot3d(x, y, z,tube_radius=10,color=dark_cyan_color,opacity=0.8)
                alls.append([l])
            elif len(x) ==3:
                ###delaunay2d.Delaunay3D
                #tr = mlab.triangular_mesh(x, y, z, [(0,1,2)],color=sns.color_palette(n_colors=9)[0],opacity=0.5, tube_radius = 15)
                l = mlab.plot3d(x + [x[0]], y + [y[0]], z + [z[0]],tube_radius=10,color=cyan_color,opacity=0.8)
                alls.append([l])
            elif len(x) ==1:
                pts = mlab.points3d(x, y, z, scale_mode='none', opacity=0.4,scale_factor=15,color=(0.99, 0.99, 0.99))
                alls.append([pts])
        mlab.view(0,53,4500, roll=180)
        save_name  = filenames[0].split('/')[-1].split('.pickle')[0].replace('.','_')
        mlab.savefig('/Users/orenamsalem/Dropbox/v3/' + save_name  + 'ats_' + str(attack_size) + '.tiff',magnification=2)
        mlab.close(all=True)
