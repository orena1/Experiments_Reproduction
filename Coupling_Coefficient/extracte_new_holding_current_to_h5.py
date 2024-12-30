import bluepy
import pickle
import h5py
import os
sim = bluepy.Simulation('BlueConfig_num_0')
settings = pickle.load(open('settings.p','rb'))
gjc = settings['gjc']
gjc = str(gjc).replace('p','.')
vol = sim.v2.report('soma')
vol_pnd = vol.get_gid(vol.gids)


#load vc_currents
vc_curr_folder = sim.v2.config.config['Run_Default']['OutputRoot']
vc_curr_per_gid = {}
for f1 in os.listdir(vc_curr_folder):
    if 'data_for_host' in f1:
        tm = pickle.load(open(vc_curr_folder+'/'+f1,'rb'))
        for gid in tm:
            vc_curr_per_gid[gid] = tm[gid]
            
            
            
f = h5py.File('num_0/holding_per_gid.hdf5','a')
if 'holding_per_gid' not in f: f.create_group('holding_per_gid')

f['holding_per_gid'].create_group(gjc)
for gid in vc_curr_per_gid:
    f['holding_per_gid'][gjc]['a' + str(int(gid))] = vc_curr_per_gid[gid][-1]
f.close()
