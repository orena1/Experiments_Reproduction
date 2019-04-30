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

from tqdm import tqdm


try: # Python 2
    zero_depth_bases = (basestring, Number, xrange, bytearray)
    iteritems = 'iteritems'
except NameError: # Python 3
    zero_depth_bases = (str, bytes, Number, range, bytearray)
    iteritems = 'items'

def getsize(obj_0):
    """Recursively iterate to sum size of object & members."""
    _seen_ids = set()
    def inner(obj):
        obj_id = id(obj)
        if obj_id in _seen_ids:
            return 0
        _seen_ids.add(obj_id)
        size = sys.getsizeof(obj)
        if isinstance(obj, zero_depth_bases):
            pass # bypass remaining control flow and return
        elif isinstance(obj, (tuple, list, Set, deque)):
            size += sum(inner(i) for i in obj)
        elif isinstance(obj, Mapping) or hasattr(obj, iteritems):
            size += sum(inner(k) + inner(v) for k, v in getattr(obj, iteritems)())
        # Check for custom object instances - may subclass above too
        if hasattr(obj, '__dict__'):
            size += inner(vars(obj))
        if hasattr(obj, '__slots__'): # can have __slots__ with __dict__
            size += sum(inner(getattr(obj, s)) for s in obj.__slots__ if hasattr(obj, s))
        return size
    return inner(obj_0)




#Broadcast input resistance 
# so that each node will know what is the input resistance in split cell that it have

def broadcast_Rins(gc, Rins):
    h.node0.log('\nbroadcast Rins start , gc=' + str(gc)); st = time.time()
    #data = [Rins for i in range(int(h.node0.pnm.pc.nhost()))]
    data = h.node0.pnm.pc.py_allgather(Rins)
    
    #data = h.node0.pnm.pc.py_alltoall(data)
    for i in data:
        for gid in i[gc]:
            if len(i[gc][gid]) > len(Rins[gc][gid]):
                Rins[gc][gid] = i[gc][gid]

    h.node0.log('broadcast Rins finish , gc=' + str(gc) +'  took ' + str(time.time()-st) + '\n')
    
    return(Rins)
    
pbar = 0 
def node0_tqdm(close=0):
    global pbar
    if h.node0.pnm.myid==0:
        if close==1:
            pbar.refresh()
            pbar.close()
            pbar.refresh()
            sys.stdout.flush()
            pbar = 0
            return()
        if pbar is 0:
            pbar = tqdm(total=len(all_gids), leave=False, file=sys.__stdout__)
            pbar.update(1)
        else:
            pbar.update(1)


def measure_Rin_impedance(all_gids, CCs, Rins, gc = None):
    #globals - imp, h, 
    if gc is not None:
        h.node0.updateGJcon(gc)
    h.node0.pnm.pc.setup_transfer()
      
    #h.dt = 5000
    #for i in range(5):
        #h.node0.log( str(i))
        #h.fadvance()
    
    #h.dt = 5000
    #[h.fadvance() for i in range(50)]
    h.dt = 0.025
    [h.fadvance() for i in range(50)]
    
    # With impedance tool
    for pre_gid in all_gids:
        if h.node0.pnm.gid_exists(pre_gid):
            imp.loc(.5, sec = h.node0.pnm.pc.gid2cell(pre_gid).soma[0])
        steps = imp.compute(0, 1, 15000)
        
        if h.node0.pnm.gid_exists(pre_gid):
            Rins[gc][pre_gid].append(imp.transfer(.5, sec = h.node0.pnm.pc.gid2cell(pre_gid).soma[0]))
            
        for post_gid in all_gids:
            if h.node0.pnm.gid_exists(post_gid):
                CCs[gc][pre_gid][post_gid].append(imp.transfer(.5, sec = h.node0.pnm.pc.gid2cell(post_gid).soma[0]))
        h.node0.pnm.pc.barrier()
        imp.loc(-1)
        node0_tqdm()
    node0_tqdm(close=1)
    return(CCs, Rins) # no need to return them.. but still.

if settings['rm_correction_type']=='impedance_tool':
    measure_Rin = measure_Rin_impedance
elif settings['rm_correction_type']=='current_injection':
    raise Exception("Not implemented yet")
    

# set variables
GJcs = settings['rm_correction_gjcs'] # a list of Gap Junction conductances, for each value in the list a g_pas value that results in the original input resistance will be searched
number_of_iterations = settings['rm_correction_number_of_iterations'] # Number of iteration for g_pas search
cm = settings['rm_correction_cm']




h.node0.log( "--------------------------- starting python script  ---------------------------" )
h.node0.finalizeModel()
h.node0.log( "SET cvode to 0" )
cvode=h.CVode()
h.node0.log( str(cvode.active()))
x = cvode.active(False)
h.node0.log(str(x))
h.node0.log( "----")
#asdas
circuitTarget = h.node0.targetParser.getTarget( h.node0.configParser.parsedRun.get("CircuitTarget").s ) 
all_gids = circuitTarget.completegids() # Get all the gids in the network
all_gids = list(set(all_gids)) #? Maybe I need the set() for multisplit.. probably not 

gid_in_node = list(h.node0.cellDistributor.getGidListForProcessor())
h.node0.log('len all_gids = ' + str(len(all_gids)) + ' len gid_in_node ' + str(len(gid_in_node)))


v_per_cell = {} # dictionary to record the voltage of the cell
IClamps = {}  # dictionary to keep track for the IClamps
CCs = dict((gc,{pre_gid:{post_gid:[] for post_gid in gid_in_node} for pre_gid in all_gids}) for gc in [0] + GJcs)
Rins = dict((gc,{gid:[] for gid in all_gids}) for gc in [0] + GJcs)
h.node0.log('CCs size = ' + str(getsize(CCs)/1000.0/1000) + ' Rins size = ' + str(getsize(Rins)/1000.0/1000))

#exit()
g_pas_per_seg_per_gid = {}


# get g_pas per seg per gid:
for gid in all_gids:
    if gid in list(h.node0.cellDistributor.getGidListForProcessor()):
        g_pas_per_seg_per_gid[gid] = {}
        cell = h.node0.pnm.pc.gid2cell(h.node0.cellDistributor.getSpGid(gid))
        for sec in cell.all:
            for seg in sec:
                g_pas_per_seg_per_gid[gid][str(seg)] = seg.g_pas


g_pas_per_gjc_per_gid_per_seg = {gc:{gid:{seg:[g_pas_per_seg_per_gid[gid][seg]] for seg in g_pas_per_seg_per_gid[gid]} for gid in g_pas_per_seg_per_gid} for gc in [0] + GJcs}

# remove active channels 
non_sotchastic_mechs = ['NaTs2_t', 'SKv3_1', 'Nap_Et2', 'Ih', 'Im', 'KdShu2007',
                 'K_Pst', 'K_Tst', 'Ca', 'SK_E2', 'Ca_LVAst', 'CaDynamics_E2'
                 ,'NaTa_t', 'CaDynamics_DC0','Ca_HVA2', 'NaTg'] +
                ['TC_cad', 'TC_ih_Bud97', 'TC_Nap_Et2', 'TC_iA', 'TC_iL', 'SK_E2', 'TC_HH', 'TC_iT_Des98']

sotchastic_mechs = ['StochKv', 'StochKv2', 'StochKv3']


remove_channels = settings['remove_channels']
Mechanisims =[]
if remove_channels=='all':              Mechanisims=non_sotchastic_mechs + sotchastic_mechs
if remove_channels=='only_stoch':       Mechanisims=sotchastic_mechs
if remove_channels=='only_non_stoch':   Mechanisims=non_sotchastic_mechs 

h.node0.log('Remove channels opt = ' + remove_channels)


for i in h.allsec():
    for mec in Mechanisims:
        h('uninsert ' +mec)
        
#setup 
imp = h.Impedance()
#h("forall {cm=0.0001}")

h.finitialize(h.v_init)
h.node0.pnm.pc.setup_transfer()

h.node0.log( "--------------------------- Measure Rin without GJs ---------------------------\n" )
measure_Rin(all_gids, CCs, Rins, gc = 0);
broadcast_Rins(gc=0, Rins=Rins)


h.node0.log( "\n----------------Measure Rin with GJs for different conductance ----------------\n" )
for gc in GJcs:
    h.node0.log( "\n gjc = " + str(gc) + ' ' + str(GJcs.index(gc)) + '/' + str(len(GJcs)))
    measure_Rin(all_gids, CCs, Rins, gc = gc);
    broadcast_Rins(gc, Rins)

h.node0.log( "\n--------------------------- Attempt to fix Rin by Changing g_pas " + str(number_of_iterations)  + " Iterations--------------------------- " )
num_cells_skiped = 0
for gc in GJcs:
    h.node0.log( "GJc " + str(gc) + " ** start ** ")
    last_effective_ind = {gid:0 for gid in all_gids}
    
    
    #reset g_pas of segments
    for gid in all_gids:
        if gid in list(h.node0.cellDistributor.getGidListForProcessor()):
            cell = h.node0.pnm.pc.gid2cell(h.node0.cellDistributor.getSpGid(gid))
            for sec in cell.all:
                for seg in sec:
                    seg.g_pas = g_pas_per_gjc_per_gid_per_seg[0][gid][str(seg)][0]


    
    for iteration in range(number_of_iterations):
        
        h.node0.log( "\nGJc " + str(gc) + " iteration " + str(iteration) + '/' + str(number_of_iterations) + ' | num_cells_skiped = ' + str(num_cells_skiped) +\
            ' | mean norm Rin = ' + str(np.mean([Rins[gc][gid][-1]/Rins[0][gid][-1] for gid in all_gids])))
        

        # change g_pas
        for gid in all_gids:
            if gid in list(h.node0.cellDistributor.getGidListForProcessor()): # if the node has a part of the cell
                cell = h.node0.pnm.pc.gid2cell(h.node0.cellDistributor.getSpGid(gid))
                for sec in cell.all:
                    for seg in sec:  # Change the g_pas with respect to the ration between the target Rin and the last changed Rin
                        last_effective_g_pas = g_pas_per_gjc_per_gid_per_seg[gc][gid][str(seg)][last_effective_ind[gid]]
                        seg.g_pas  = last_effective_g_pas * Rins[gc][gid][last_effective_ind[gid]]/Rins[0][gid][0]
                        
                        g_pas_per_gjc_per_gid_per_seg[gc][gid][str(seg)].append(seg.g_pas) # save this g_pas value
                            

        #change Rin
        measure_Rin(all_gids, CCs, Rins, gc = gc);
        
        #check in which neuron there was a meaningful Rin change
        broadcast_Rins(gc, Rins)
        h.node0.log( '\n- mem of CCs ' + str(getsize(CCs)/1000.0) )
        num_cells_skiped = 0
        for gid in all_gids:
            skip_cell = 0
            if abs((Rins[0][gid][-1] - Rins[gc][gid][-1]))/Rins[0][gid][-1] < 0.01: #if the difference is lower than 1%
                skip_cell = 1
            if abs(Rins[gc][gid][last_effective_ind[gid]] - Rins[gc][gid][-1])<1 : # if last change was smaller than 1 Mohm
                skip_cell = 1
            
            
            if skip_cell == 0:
                last_effective_ind[gid]+=1
            else:
                num_cells_skiped+=1
            
        if num_cells_skiped == len(all_gids):
            h.node0.log( "\n Skipped all cells ")
            break
        
    h.node0.log( "\n GJc " + str(gc) + " ** Done ** ")
            





#s

def save_data():
    h.node0.log('Saving Data')
    data_to_save = {}
    data_to_save['Rins'] = Rins
    data_to_save['CCs'] = CCs
    data_to_save['g_pas_per_gjc_per_gid_per_seg'] = g_pas_per_gjc_per_gid_per_seg


    pickle.dump(data_to_save, open(h.node0.configParser.parsedRun.get("OutputRoot").s  +'/data_for_host_' + str(int(h.node0.pnm.myid)) + '.p','wb'),2)
    
    h.node0.pnm.pc.barrier() 
    h.node0.log('merging pickles')
    if h.node0.pnm.myid==0:
        data_for_host = {}
        nhost = h.node0.pnm.pc.nhost()
        for hn in range(nhost):
            data_for_host[hn] = pickle.load(open(h.node0.configParser.parsedRun.get("OutputRoot").s  +'/data_for_host_' + str(hn) + '.p','rb'))
        
        
        all_values = data_for_host.values()
        
        # merge CCs
        for i in all_values:
            for gc in i['CCs']:
                for pre_gid in CCs[gc]:
                    for post_gid in i['CCs'][gc][pre_gid]:
                        CCs[gc][pre_gid][post_gid] = np.array(i['CCs'][gc][pre_gid][post_gid])

        # merge Rins
        for i in all_values:
            for gc in i['Rins']:
                for gid in Rins[gc]:
                    if i['Rins'][gc][gid]:
                        Rins[gc][gid] = np.array(i['Rins'][gc][gid])
                        
                        
        # merge g_pas_per_gjc_per_gid_per_seg
        for i in all_values:
            for gc in i['g_pas_per_gjc_per_gid_per_seg']:
                for gid in i['g_pas_per_gjc_per_gid_per_seg'][gc]:
                    for segname in i['g_pas_per_gjc_per_gid_per_seg'][gc][gid]:
                        i['g_pas_per_gjc_per_gid_per_seg'][gc][gid][segname] = np.array(i['g_pas_per_gjc_per_gid_per_seg'][gc][gid][segname])
                    g_pas_per_gjc_per_gid_per_seg[gc][gid] = i['g_pas_per_gjc_per_gid_per_seg'][gc][gid]
        
        # save merged data
        data_to_save = {}
        data_to_save['Rins'] = Rins
        data_to_save['CCs'] = CCs
        data_to_save['g_pas_per_gjc_per_gid_per_seg'] = g_pas_per_gjc_per_gid_per_seg
        pickle.dump(data_to_save, open(h.node0.configParser.parsedRun.get("OutputRoot").s  +'/merged_data.p','wb'),2)
        
        pickle.dump(data_for_host, open(h.node0.configParser.parsedRun.get("OutputRoot").s  +'/data_for_host_merged.p','wb'),2)
            
    h.node0.log('*END* Saving Data')


save_data()



#GJcs = [0.1,1]  # a list of Gap Junction conductances, for each value in the list a g_pas value that results in the original input resistance will be searched

#aa = pickle.load(open('data_for_host_merged.p','rb'))
#all_values = aa.values()
#all_gids = all_values[0]['CCs'][0].keys()


#CCs = dict((gc,{gid:{gid:[] for gid in all_gids} for gid in all_gids}) for gc in [0] + GJcs)
#Rins = dict((gc,{gid:[] for gid in all_gids}) for gc in [0] + GJcs)


## merge CCs
#for i in all_values:
    #for gc in i['CCs']:
        #for pre_gid in CCs[gc]:
            #for post_gid in CCs[gc][pre_gid]:
                #if i['CCs'][gc][pre_gid][post_gid]:
                    #CCs[gc][pre_gid][post_gid] = i['CCs'][gc][pre_gid][post_gid]

## merge Rins
#for i in all_values:
    #for gc in i['Rins']:
        #for gid in Rins[gc]:
            #if i['Rins'][gc][gid]:
                #Rins[gc][gid] = i['Rins'][gc][gid]



