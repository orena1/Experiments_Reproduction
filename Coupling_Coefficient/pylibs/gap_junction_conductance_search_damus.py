from neuron import h
import pickle
import numpy as np
import time
import sys
import os
import logging
#from mpi4py import MPI
#comm = MPI.COMM_WORLD
from neurodamus.core import MPI
import sys
from neurodamus.core import NeurodamusCore as Nd
from numbers import Number
from collections.abc import Set, Mapping
from collections import deque



from tqdm import tqdm

# if MPI.rank==0:
#     ll = list(h.Gap)
#     print(f'Number of GJs in node 0 = {ll}')
#     print(ll[0].get_segment())
# if MPI.rank==1:
#     ll = list(h.Gap)
#     print(f'Number of GJs in node 1 = {ll}')
#     print(ll[0].get_segment())

assert nd._run_conf["RunMode"] in ['WholeCell','RR'], 'for conductance search WholeCell/RR is required (althought might work with LoadBalance)'
# make sure that there are no synapses!
syn_models = ['DetAMPANMDA', 'DetGABAAB', 'ProbAMPANMDA_EMS', 'ProbGABAAB_EMS']
for syn in syn_models:
    if hasattr(h,syn):
        assert len(getattr(h,syn))==0, f'There are {len(getattr(h,syn))} {syn}, gpas compenstation should have zero synapses!'
        

if MPI.rank==0:  
    print(f"GJs per rank = {len(list(h.Gap))}")
    
sys.stdout.flush()
MPI._pc.barrier()






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

def save_data(gjc):
    # gjc set the conductance for which to save data for.       
        
    logging.info('Saving Data')
    data_to_save = {}
    data_to_save['Rins'] = Rins[gjc]
    data_to_save['CCs'] = CCs[gjc]
    data_to_save['g_pas_per_gjc_per_gid_per_seg'] = g_pas_per_gjc_per_gid_per_seg[gjc]

    save_path = f'{nd._run_conf["OutputRoot"]}/{gjc}'
    if MPI.rank==0:
        os.makedirs(save_path,exist_ok=True)
    MPI._pc.barrier() 
    pickle.dump(data_to_save, open(f'{save_path}/data_for_host_{MPI.rank}.p','wb'))
    
    # h.node0.pnm.pc.barrier()
    # MERGE CODE is avalilable in gap_junction_conductance_search.py
    ####
    
    MPI._pc.barrier()
    if MPI.rank==0:
        with open(f'{save_path}/completed.txt','w') as f:
            f.write('Done - ') #add datetime
            
    logging.info('*END* Saving Data')


#Broadcast input resistance 
# so that each node will know what is the input resistance in split cell that it have

#Rins = dict((gc,{gid:[] for gid in all_gids}) for gc in [0] + GJcs)


def broadcast_Rins_old(gc, Rins):
    logging.info('\nbroadcast Rins start , gc=' + str(gc)); st = time.time()
    #data = [Rins for i in range(int(h.node0.pnm.pc.nhost()))]
    data = MPI._pc.py_allgather(Rins[gc])
    
    #data = h.node0.pnm.pc.py_alltoall(data)
    for i in data:
        for gid in i:
            if len(i[gid]) > len(Rins[gc][gid]):
                Rins[gc][gid] = i[gid]

    logging.info('broadcast Rins finish , gc=' + str(gc) +'  took ' + str(time.time()-st) + '\n')
    MPI._pc.barrier()
    return(Rins)


def broadcast_Rins(gc, Rins):
    logging.info(f'\nbroadcast Rins start , gc={gc}'); st = time.time()
    to_send = {}
    for gid in gids_per_node:
        to_send[gid] = Rins[gc][gid][-1]
        
    data = MPI._pc.py_allgather(to_send)
    
    for i in data:
        for gid in i:
            if gid not in gids_per_node:
                Rins[gc][gid].append(i[gid])

    logging.info(f'broadcast Rins finish , gc={gc}  took ' + str(time.time()-st) + '\n')
    MPI._pc.barrier()
    return(Rins)


def node0_tqdm(close=0,pbar=None):
    if MPI.rank==0:
        if close==1:
            if pbar is not None:
                pbar.refresh()
                pbar.close()
                pbar.refresh()
                sys.stdout.flush()
                del pbar
            return
        if pbar is None:
            pbar = tqdm(total=len(all_gids), leave=False, file=sys.__stderr__)
            pbar.update(1)
            return pbar
        else:
            pbar.update(1)
            return pbar
    else:
        return None




def measure_Rin_impedance(all_gids, CCs, Rins, gc = None):
    pbar = None
    #globals - imp, h, 
    if gc != None:
        update_conductance(gc,nd)
    MPI._pc.barrier() 
    MPI._pc.setup_transfer()
      
    #h.dt = 5000
    #for i in range(5):
        #h.node0.log( str(i))
        #h.fadvance()
    nd._finalize_model()
    h.dt = 5000
    [h.fadvance() for i in range(5)]
    h.dt = 0.025
    [h.fadvance() for i in range(50)]
    
    # With impedance tool
    for jj,pre_gid in enumerate(all_gids):
        if pre_gid in gids_per_node:
            imp.loc(.5, sec = nd._circuits.global_manager.getCell(pre_gid).soma[0])

        steps = imp.compute(0, 1, 15000)
        
        if pre_gid in gids_per_node:
            Rins[gc][pre_gid].append(imp.transfer(.5, sec = nd._circuits.global_manager.getCell(pre_gid).soma[0]))
            #Rins[gc][pre_gid].append(np.random.uniform(41,100))
        
        if pre_gid in CCs[gc]:#for CC subsampeling
            for post_gid in all_gids:
                if post_gid in CCs[gc][pre_gid]:#for CC subsampeling
                    if post_gid in gids_per_node:
                        CCs[gc][pre_gid][post_gid].append(imp.transfer(.5, sec = nd._circuits.global_manager.getCell(post_gid).soma[0]))
                        #CCs[gc][pre_gid][post_gid].append(np.random.uniform(41,100))
        
        imp.loc(-1)
        pbar = node0_tqdm(close=0,pbar=pbar)
        ### debug print ram every 2% 
        # if jj%int(len(all_gids)/50)==0:
        #     Nd.MemUsage().print_mem_usage()
        #     if MPI.rank==0:
        #         print('\n')
                
    node0_tqdm(close=1, pbar=pbar)
    return(CCs, Rins) # no need to return them.. but still.




        
# Need more work!
#def measure_Rin_current_injection(all_gids, CCs, Rins, gc = None):
    ##globals - imp, h, 
    #if gc is not None:
        #h.node0.updateGJcon(gc)
    #h.node0.pnm.pc.barrier() 
    #h.node0.pnm.pc.setup_transfer()
      
    ##h.dt = 5000
    ##for i in range(5):
        ##h.node0.log( str(i))
        ##h.fadvance()
    #h.node0.finalizeModel()
    #h.dt = 5000
    #[h.fadvance() for i in range(5)]
    #h.dt = 0.025
    #[h.fadvance() for i in range(50)]
    
    ## With impedance tool
    #for pre_gid in all_gids:
        #h.finitialize(h.v_init)
        #if h.node0.pnm.gid_exists(pre_gid):
            #current_clamp[pre_gid].amp   = 
            #current_clamp[pre_gid].dur   =
            #current_clamp[pre_gid].delay =
        
        #value = -1
        #if h.node0.pnm.gid_exists(pre_gid):
            #Rins[gc][pre_gid].append( (v_per_gid[pre_gid][-1] - v_per_gid[pre_gid][x] ) / c_amp)
            #dV = (v_per_gid[pre_gid][-1] - v_per_gid[pre_gid][x] )
        #h.node0.pnm.pc.allgather(dV, result_vector)
        #dV = max(result_vector)
        #for post_gid in all_gids:
            #if h.node0.pnm.gid_exists(post_gid):
                #CCs[gc][pre_gid][post_gid].append( (v_per_gid[pre_gid][-1] - v_per_gid[pre_gid][x] ) / dV)

        #node0_tqdm()
    #node0_tqdm(close=1)
    #return(CCs, Rins) # no need to return them.. but still.







if settings['rm_correction_type']=='impedance_tool':
    measure_Rin = measure_Rin_impedance
elif settings['rm_correction_type']=='current_injection':
    raise Exception("Not implemented yet")
    

# set variables
GJcs = settings['rm_correction_gjcs'] # a list of Gap Junction conductances, for each value in the list a g_pas value that results in the original input resistance will be searched
GJcs = [gjc for gjc in GJcs if not os.path.exists(f'{nd._run_conf["OutputRoot"]}/{gjc}/completed.txt')]
number_of_iterations = settings['rm_correction_number_of_iterations'] # Number of iteration for g_pas search
cm = settings['rm_correction_cm']




logging.info( "--------------------------- starting python script  ---------------------------" )
nd._finalize_model()
logging.info( "----")

#I have a lot of these test, might make it faster

all_gids = nd._target_manager._targets[nd._base_circuit.CircuitTarget].get_gids()
all_gids = list(set(all_gids)) #? Maybe I need the set() for multisplit.. probably not 

gids_per_node = set(list(nd._circuits.node_managers[''].getGidListForProcessor()))
logging.info(f'len all_gids = {len(all_gids)} len gid_in_node {len(gids_per_node)}')



v_per_cell = {} # dictionary to record the voltage of the cell
IClamps = {}  # dictionary to keep track for the IClamps
logging.info('I measure CC only in a few neurons!!')
CCs = dict((gc,{pre_gid:{post_gid:[] for post_gid in list(gids_per_node)[:2]} for pre_gid in all_gids[:60]}) for gc in [0] + GJcs)
Rins = dict((gc,{gid:[] for gid in all_gids}) for gc in [0] + GJcs)
logging.info(f'CCs size = {getsize(CCs)/1000.0/1000} Rins size = {getsize(Rins)/1000.0/1000}')

#exit()
g_pas_per_seg_per_gid = {}


# get g_pas per seg per gid:
for gid in all_gids:
    if gid in gids_per_node:
        g_pas_per_seg_per_gid[gid] = {}
        cell = nd._circuits.global_manager.getCell(gid)
        for sec in cell.all:
            for seg in sec:
                g_pas_per_seg_per_gid[gid][str(seg)] = seg.g_pas


g_pas_per_gjc_per_gid_per_seg = {gc:{gid:{seg:[g_pas_per_seg_per_gid[gid][seg]] for seg in g_pas_per_seg_per_gid[gid]} for gid in g_pas_per_seg_per_gid} for gc in [0] + GJcs}

# remove active channels 
non_sotchastic_mechs = ['NaTs2_t', 'SKv3_1', 'Nap_Et2', 'Ih', 'Im', 'KdShu2007',
                 'K_Pst', 'K_Tst', 'Ca', 'SK_E2', 'Ca_LVAst', 'CaDynamics_E2'
                 ,'NaTa_t', 'CaDynamics_DC0','Ca_HVA2', 'NaTg']  \
                + ['TC_cad', 'TC_ih_Bud97', 'TC_Nap_Et2', 'TC_iA', 'TC_iL', 'TC_HH', 'TC_iT_Des98'] \
                + ['kdrb', 'na3', 'kap', 'hd', 'can', 'cal', 'cat', 'cagk', 'kca', 'cacum' ,'kdb', 'kmb', 'kad', 'nax', 'cacumb']




sotchastic_mechs = ['StochKv', 'StochKv2', 'StochKv3']


remove_channels = settings['remove_channels']
Mechanisims =[] 
if remove_channels=='all':              Mechanisims=non_sotchastic_mechs + sotchastic_mechs
if remove_channels=='only_stoch':       Mechanisims=sotchastic_mechs
if remove_channels=='only_non_stoch':   Mechanisims=non_sotchastic_mechs 


logging.info('Remove channels opt = ' + remove_channels)


MPI._pc.barrier()
for sec in h.allsec():
    for mec in Mechanisims:
        if mec in dir(sec(.5)): 
            sec.uninsert(mec)
            #h("uninsert " + mec)#
    
if MPI.rank==0:
    logging.info(str(sec.psection()))

#setup 
imp = h.Impedance()
h("forall {cm=0.0001}")

h.finitialize(h.v_init)
MPI._pc.setup_transfer()

logging.info( "--------------------------- Measure Rin without GJs ---------------------------\n" )
measure_Rin(all_gids, CCs, Rins, gc = 0)
broadcast_Rins(gc=0, Rins=Rins)
logging.info(f'CCs size = {getsize(CCs)/1000.0/1000} Rins size = {getsize(Rins)/1000.0/1000}')
save_data(gjc=0) 

# logging.info( "\n----------------Measure Rin with GJs for different conductance ----------------\n" )
# for gc in GJcs:
#     logging.info(f"\n gjc = {gc} {GJcs.index(gc)} / {len(GJcs)}")
#     measure_Rin(all_gids, CCs, Rins, gc = gc);
#     broadcast_Rins(gc, Rins)
#     logging.info(f'CCs size = {getsize(CCs)/1000.0/1000} Rins size = {getsize(Rins)/1000.0/1000}')


logging.info( "\n--------------------------- Attempt to fix Rin by Changing g_pas " + str(number_of_iterations)  + " Iterations--------------------------- " )

for gc in GJcs:
    num_cells_skiped = 0
    logging.info( f"GJc {gc} ** start ** ") 
    #reset g_pas of segments
    for gid in all_gids:
        if gid in gids_per_node:
            cell = nd._circuits.global_manager.getCell(gid)
            for sec in cell.all:
                for seg in sec:
                    seg.g_pas = g_pas_per_gjc_per_gid_per_seg[0][gid][str(seg)][0]


    # mesure Rin & CC for that GJc without gpas change
    logging.info('\n----------------Measure Rin with GJs no gpas change ----------------\n')
    logging.info(f"\n gjc = {gc} {GJcs.index(gc)} / {len(GJcs)}")
    measure_Rin(all_gids, CCs, Rins, gc = gc);
    broadcast_Rins(gc, Rins)
    logging.info(f'CCs size = {getsize(CCs)/1000.0/1000} Rins size = {getsize(Rins)/1000.0/1000}')

    
    last_effective_ind = {gid:0 for gid in all_gids}
    for iteration in range(number_of_iterations):
        
        logging.info( f'\nGJc {gc} iteration {iteration}/{number_of_iterations} | num_cells_skiped = ' + str(num_cells_skiped) +\
            ' | mean norm Rin = ' + str(np.mean([Rins[gc][gid][-1]/Rins[0][gid][-1] for gid in all_gids])))
        

        # change g_pas
        for gid in all_gids:
            if gid in gids_per_node: # if the node has a part of the cell
                cell = nd._circuits.global_manager.getCell(gid)
                for sec in cell.all:
                    for seg in sec:  # Change the g_pas with respect to the ration between the target Rin and the last changed Rin
                        last_effective_g_pas = g_pas_per_gjc_per_gid_per_seg[gc][gid][str(seg)][last_effective_ind[gid]]
                        seg.g_pas  = last_effective_g_pas * Rins[gc][gid][last_effective_ind[gid]]/Rins[0][gid][0]
                        
                        g_pas_per_gjc_per_gid_per_seg[gc][gid][str(seg)].append(seg.g_pas) # save this g_pas value
                            

        #change Rin
        measure_Rin(all_gids, CCs, Rins, gc = gc);
        
        #check in which neuron there was a meaningful Rin change
        broadcast_Rins(gc, Rins)
        logging.info(f'CCs size = {getsize(CCs)/1000.0/1000} Rins size = {getsize(Rins)/1000.0/1000}')
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
            logging.info( "\n Skipped all cells ")
            break
    
    logging.info(f"\n GJc {gc} ** Done ** ")
    save_data(gjc=gc)

#if h.node0.pnm.myid==0:
    #print(CCs[0.25])

#if h.node0.pnm.myid==1:
    #print(CCs[0.25])
sys.stdout.flush()
MPI._pc.barrier()




#s

def save_data():
    logging.info('Saving Data')
    data_to_save = {}
    data_to_save['Rins'] = Rins
    data_to_save['CCs'] = CCs
    data_to_save['g_pas_per_gjc_per_gid_per_seg'] = g_pas_per_gjc_per_gid_per_seg


    pickle.dump(data_to_save, open(f'{nd._run_conf["OutputRoot"]}/data_for_host_{MPI.rank}.p','wb'))
    
    MPI._pc.barrier() 
    logging.info('merging pickles')
    if MPI.rank==0:
        data_for_host = {}
        nhost = MPI._pc.nhost()
        for hn in range(nhost):
            data_for_host[hn] = pickle.load(open(f'{nd._run_conf["OutputRoot"]}/data_for_host_{hn}.p','rb'))
        
        
        all_values = data_for_host.values()
        
        # merge CCs
        for i in all_values:
            for gc in i['CCs']:
                for pre_gid in i['CCs'][gc]:
                    
                    if pre_gid not in CCs[gc]: CCs[gc][pre_gid] = {}
                    
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
        pickle.dump(data_to_save, open(f'{nd._run_conf["OutputRoot"]}/merged_data.p','wb'))
        
        pickle.dump(data_for_host, open(f'{nd._run_conf["OutputRoot"]}/data_for_host_merged.p','wb'))
            
    logging.info('*END* Saving Data')


#save_data()



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

### merge files manually
'''
import os
from tqdm import tqdm
import pickle
import numpy as np
files = [f for f in  os.listdir('.') if 'host_' in f and 'merged' not in f]
data_for_host = {}
for f in tqdm(files):
    nm = int(f.split('_')[-1].split('.')[0])
    data_for_host[nm] = pickle.load(open('data_for_host_' + str(nm) + '.p','rb'))
    
all_values = data_for_host.values()

all_values = [data_for_host[i] for i in data_for_host if i!=0]

CCs = data_for_host[0]['CCs']
# merge CCs
for i in tqdm(all_values):
    for gc in i['CCs']:
        for pre_gid in CCs[gc]:
            for post_gid in i['CCs'][gc][pre_gid]:
                CCs[gc][pre_gid][post_gid] = np.array(i['CCs'][gc][pre_gid][post_gid])


Rins = data_for_host[0]['Rins']
# merge Rins
for i in tqdm(all_values):
    for gc in i['Rins']:
        for gid in Rins[gc]:
            if i['Rins'][gc][gid]:
                Rins[gc][gid] = np.array(i['Rins'][gc][gid])


g_pas_per_gjc_per_gid_per_seg = data_for_host[0]['g_pas_per_gjc_per_gid_per_seg']
# merge g_pas_per_gjc_per_gid_per_seg
for i in tqdm(all_values):
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
pickle.dump(data_to_save, open('merged_data.p','wb'),2)
print("Finish saving 1")

pickle.dump(data_for_host, open('data_for_host_merged.p','wb'),2)
print("Finish saving 2")
'''


