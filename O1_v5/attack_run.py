from neurodamus import Neurodamus
from neurodamus.utils.logging import log_stage, log_verbose
from tqdm import tqdm
import h5py
import sys
import logging


for arg in sys.argv:
    if 'configFile' in arg:
        blueconfig = arg.split('="')[1][:-2]

nd = Neurodamus(blueconfig, auto_init=False)

remove_edges = h5py.File(@attack_path,'r')['edges']

gid_in_node = set(nd._cell_distributor.getGidListForProcessor())

#print(gid_in_node, nd.MPI.rank)
### method 1 - use the method that is available already
#for post in tqdm(remove_edges):
    #post_gids = [int(post.split('_')[1])]
    #if post_gids[0] in gid_in_node:
        #print(post_gids, nd.MPI.rank)
        #pre_gids = set(list(remove_edges[post]))
        #nd._synapse_manager.delete_group(set(post_gids), pre_gids)



### method 2 - use new method
log_stage('Starting edge removal')

logging.info('Create post_pre_pairs')
post_pre_pairs = []
for post in remove_edges:
    post_gid = int(post.split('_')[1])
    if post_gid in gid_in_node:
        for pre in remove_edges[post]:
            post_pre_pairs.append((post_gid,pre))

logging.info('Delete pairs')
nd._synapse_manager.delete_pairs(post_pre_pairs)
log_stage("Run init")
nd.init()
log_stage('Run simulation!')
nd.run()
