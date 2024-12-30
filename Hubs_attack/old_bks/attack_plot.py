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

attackhub    = pickle.load(open('/Users/orenamsalem/Dropbox/v3/test_sccs.NMC.hub-attack.2122.(180911.144001).pickle','r'))
attackrandom = pickle.load(open('/Users/orenamsalem/Dropbox/v3/test_sccs.NMC.random-attack.2122.(180911.144356).pickle','r'))




#generalConfigPath = '/gpfs/bbp.cscs.ch/project/proj2/simulations/ThlInput/AudInput12_4_16/SSA/Ca1p23/EE0_EI0_IE0_II0_TM_0/Freq_Tono_4to16_FR_S100_W_S0p2_TwoStimsExp/BlueConfig6666_106686'
#print  'Loading all  took ' +  `time.time() - STloadTM` + ' secs'
#Circ = bluepy.Circuit(generalConfigPath)

data = pickle.load(open('/Users/orenamsalem/Downloads/data.p','r'))
gid_to_loc = data['neurons_position']

#array([   0,  100,  200,  300,  400,  500,  600,  700,  800,  900, 1000,
#       1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000, 2100,
#       2200, 2300, 2400])
#22000 - 




%gui qt

attack_size = 29700
import seaborn as sns
attack = attackhub
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
    mlab.mesh(x,y,z,color=(175/255.0,255/255.0,255/255.0),opacity=0.1)



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
mlab.view(0,90,4500, roll=180)




mlab.show()



attack = attackrandom
for attack_size in np.sort(attack['attacks'].keys()):
    print(attack_size,np.array(map(len,attack['attacks'][attack_size]['sccs']))[np.array(map(len,attack['attacks'][attack_size]['sccs']))>2] ),
    attack = attackhub
    print(np.array(map(len,attack['attacks'][attack_size]['sccs']))[np.array(map(len,attack['attacks'][attack_size]['sccs']))>2] )
    



for attack_size in np.sort(attack['attacks'].keys()):
    print(attack_size,cnt([len(rr) for rr in attack['attacks'][attack_size]['sccs']]))

 l = mlab.plot3d([10.0,10.0], [20.0,20.0], [5.0,6.0])


### Example:
attack_size = 31100

samples_sizes = [ 30000,

clusters_ids_to_show  = np.argsort(map(len,attack['attacks'][attack_size]['sccs']))[::-1]
mlab.figure(1, fgcolor=(0, 0, 0), bgcolor=(1, 1, 1))
colors = [(1,0,0), (0,1,0), (0,0,1)]

for ii,i in enumerate(clusters_ids_to_show[:3]):
    gids = attack['attacks'][attack_size]['sccs'][i]
    x=[]
    y=[]
    z=[]
    for gid in gids:
        x.append(mc0_data.loc[gid].x)
        y.append(mc0_data.loc[gid].y)
        z.append(mc0_data.loc[gid].z)


    # Visualize the points
    pts = mlab.points3d(x, y, z, scale_mode='none', scale_factor=0,color=colors[ii])

    # Create and visualize the mesh
    mesh = mlab.pipeline.delaunay3d(pts)
    surf = mlab.pipeline.surface(mesh, opacity=0.5,color=colors[ii])
mlab.show()





import glob
filenames = glob.glob('/Users/orenamsalem/Dropbox/v3/*NMC*.pickle')

for filename in filenames:
    print(filename)

    with open(filename) as f_handle:
        data = pickle.load(f_handle)

    attacks = data['attacks']
    attack_mode = data['attack_mode']

    ns = {f: [len(cc) for cc in v['sccs']] for f, v in attacks.items()}
    xy = {f: max(n)/sum(n) for f, n in ns.items()}
    plt.plot(xy.keys(), xy.values(), '.', label=attack_mode)
plt.legend()



n =2
t = np.linspace(-np.pi, np.pi, n)
z = np.exp(1j * t)
x = z.real.copy()
y = z.imag.copy()
z = np.zeros_like(x)

triangles = [(0, i, i + 1) for i in range(1, n)]
x = np.r_[0, x]
y = np.r_[0, y]
z = np.r_[1, z]
t = np.r_[0, t]
triangular_mesh(x, y, z, triangles, scalars=t)




gids = attack['attacks'][attack_size]['sccs'][i]
x=[]
y=[]
z=[]
for gid in gids:
    if gid!=0:
        x.append(gid_to_loc[gid][0])
        y.append(gid_to_loc[gid][1])
        z.append(gid_to_loc[gid][2])





triangles = [(0, i, i + 1) for i in range(1, n)]
x = np.r_[0, x]
y = np.r_[0, y]
z = np.r_[1, z]


