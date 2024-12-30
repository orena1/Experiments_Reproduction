from neuron import h
import pickle
import numpy as np
import time
import sys
import os
#from mpi4py import MPI
#comm = MPI.COMM_WORLD

import sys
from numbers import Number
from collections import Set, Mapping, deque

#from tqdm import tqdm






#Broadcast input resistance 
# so that each node will know what is the input resistance in split cell that it have

#Rins = dict((gc,{gid:[] for gid in all_gids}) for gc in [0] + GJcs)


def broadcast_Rins(gc, Rins):
    h.node0.log('\nbroadcast Rins start , gc=' + str(gc)); st = time.time()
    #data = [Rins for i in range(int(h.node0.pnm.pc.nhost()))]
    data = h.node0.pnm.pc.py_allgather(Rins[gc])
    
    #data = h.node0.pnm.pc.py_alltoall(data)
    for i in data:
        for gid in i:
            if len(i[gid]) > len(Rins[gc][gid]):
                Rins[gc][gid] = i[gid]

    h.node0.log('broadcast Rins finish , gc=' + str(gc) +'  took ' + str(time.time()-st) + '\n')
    h.node0.pnm.pc.barrier()
    return(Rins)
    



def measure_Rin(all_gids, CCs, Rins, gc = None):
    #globals - imp, h, 
    if gc is not None:
        h.node0.updateGJcon(gc)
    h.node0.pnm.pc.barrier() 
    h.node0.pnm.pc.setup_transfer()
      

    h.node0.finalizeModel()
    h.dt = 5000
    [h.fadvance() for i in range(5)]
    h.dt = 0.025
    [h.fadvance() for i in range(50)]
    

    for pre_gid in all_gids:
        h.node0.pnm.pc.barrier()
        h.finitialize(h.v_init)
        if h.node0.pnm.gid_exists(pre_gid):
            imp.loc(.5, sec = h.node0.pnm.pc.gid2cell(pre_gid).soma[0])

        h.node0.pnm.pc.barrier()
        steps = imp.compute(0, 1, 15000)
        h.node0.pnm.pc.barrier()

        if h.node0.pnm.gid_exists(pre_gid):
            val = imp.transfer(.5, sec = h.node0.pnm.pc.gid2cell(pre_gid).soma[0])
            print(pre_gid,val)
            Rins[gc][pre_gid].append(val)
            
        #for post_gid in all_gids:
            #if h.node0.pnm.gid_exists(post_gid):
                #CCs[gc][pre_gid][post_gid].append(imp.transfer(.5, sec = h.node0.pnm.pc.gid2cell(post_gid).soma[0]))
        h.node0.pnm.pc.barrier()
        imp.loc(-1)

    return(CCs, Rins) # no need to return them.. but still.
    



# set variables
GJcs = list(np.arange(0,1,0.05))





h.node0.log( "--------------------------- starting python script  ---------------------------" )
h.node0.finalizeModel()
h.node0.log( "----")

circuitTarget = h.node0.targetParser.getTarget( h.node0.configParser.parsedRun.get("CircuitTarget").s ) 
all_gids = circuitTarget.completegids() # Get all the gids in the network
all_gids = list(set(all_gids)) #? Maybe I need the set() for multisplit.. probably not 

gid_in_node = list(h.node0.cellDistributor.getGidListForProcessor())
h.node0.log('len all_gids = ' + str(len(all_gids)) + ' len gid_in_node ' + str(len(gid_in_node)))



CCs = dict((gc,{pre_gid:{post_gid:[] for post_gid in gid_in_node} for pre_gid in all_gids}) for gc in [0] + GJcs)
Rins = dict((gc,{gid:[] for gid in all_gids}) for gc in [0] + GJcs)

#exit()


Mechanisims = ['kdrb', 'na3', 'kap', 'hd', 'can', 'cal', 'cat', 'cagk', 'kca', 'cacum' ,'kdb', 'kmb', 'kad', 'nax', 'cacumb']
h.node0.pnm.pc.barrier()
for sec in list(h.allsec()):
    for mec in Mechanisims:
        if mec in dir(sec(.5)): 
            sec.uninsert(mec)
            #h("uninsert " + mec)#
    #h.pop_section()


#setup 
imp = h.Impedance()
h("forall {cm=0.0001}")
h.finitialize(h.v_init)
h.node0.pnm.pc.setup_transfer()





h.node0.log( "--------------------------- Measure Rin without GJs ---------------------------\n" )
measure_Rin(all_gids, CCs, Rins, gc = 0);
#broadcast_Rins(gc=0, Rins=Rins)
#sys.stdout.flush()


h.node0.log( "\n----------------Measure Rin with GJs for different conductance ----------------\n" )
for gc in GJcs:

    measure_Rin(all_gids, CCs, Rins, gc = gc);

    broadcast_Rins(gc, Rins)
    for i in Rins[gc].values():
        if len(i)>0:
            if np.isnan(i[-1]):
                raise Exception("We have a nan gjc = " +  str(gc))

    
quit()    


