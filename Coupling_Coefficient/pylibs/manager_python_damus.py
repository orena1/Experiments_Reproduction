# this script will either set the stage for current injection or load the g_pas_conduction_search.py

import logging
import pickle
import sys
import logging
import h5py
import numpy as np
from neurodamus.core import MPI
from neurodamus.core import NeurodamusCore as Nd
from neurodamus import Neurodamus
from neurodamus.utils.logging import log_stage, log_verbose
from neuron import h


##Qs 
#nd._circuits.node_managers[''].getGidListForProcessor() # should I iterate over all node_managers?



def update_conductance(gjc,nd):
    # Maybe Fernando can suggest something more stable?
    # I can aslo use the direct access to gap, but I would prefer to use neurosamus
    
    # This does not work when I remove synapses, not sure what is going on...
    ####$$$$$
    # for _,conns in nd._circuits.edge_managers[('','')][0]._populations[(0,0)]._connections_map.items():
    #     for con in conns:
    #         con.update_conductance(gjc)
    #####$$$$$$
    
    for gap in list(h.Gap):
        gap.g  = gjc
    
    ## For now I'll just verify directly from neuron that the conductance is correct
    for gap in list(h.Gap):
        assert gap.g == gjc

non_sotchastic_mechs = ['NaTs2_t', 'SKv3_1', 'Nap_Et2', 'Ih', 'Im', 'KdShu2007',
                'K_Pst', 'K_Tst', 'Ca', 'SK_E2', 'Ca_LVAst', 'CaDynamics_E2'
                ,'NaTa_t', 'CaDynamics_DC0','Ca_HVA2', 'NaTg']  \
                + ['TC_cad', 'TC_ih_Bud97', 'TC_Nap_Et2', 'TC_iA', 'TC_iL', 'TC_HH', 'TC_iT_Des98'] \
                + ['kdrb', 'na3', 'kap', 'hd', 'can', 'cal', 'cat', 'cagk', 'kca', 'cacum' ,'kdb', 'kmb', 'kad', 'nax', 'cacumb']

sotchastic_mechs = ['StochKv', 'StochKv2', 'StochKv3']


nd = Neurodamus('BlueConfig_num_0', auto_init=False)


settings = pickle.load(open(nd._run_conf["CurrentDir"]+ "/settings.p",'rb'))
logging.info("Finish loading settings")

# delete all the synapses / This assume that the synapses are first in the list..., also sometime I don't need
# to delete all syanpese!!!!
if 'remove_synapses' in settings:
    if settings['remove_synapses']:
        nd._circuits.edge_managers[('','')].pop(0)
        logging.info("remove all synapses")
else: # if there is no remove_synapses key, it means that it is an old setting file, which means we need to remove synapses
    nd._circuits.edge_managers[('','')].pop(0)
    logging.info("remove all synapses")

logging.info("Run init")
nd.init()




#deterministic_StochKv
if settings['determanisitc_stoch']:
    for sec in h.allsec():
        if 'StochKv3' in dir(sec(.5)): sec.deterministic_StochKv3=1
        if 'StochKv2' in dir(sec(.5)): sec.deterministic_StochKv2=1
        if 'StochKv1' in dir(sec(.5)): sec.deterministic_StochKv1=1
   

load_g_pas_correction_file = 0
save_saclamps_voltages = 0
if settings['procedure_type'] == 'rm_correction':
    load_g_pas_correction_file = 1
elif settings['procedure_type'] in ['validation_sim', 'find_holding_current']:
    gjc = settings['gjc']
    logging.info("set GJc = " + str(gjc))
    update_conductance(gjc, nd)
   
    # remove active channels 
    remove_channels = settings['remove_channels']
    Mechanisims =[]
    if remove_channels=='all':              Mechanisims=non_sotchastic_mechs + sotchastic_mechs
    if remove_channels=='only_stoch':       Mechanisims=sotchastic_mechs
    if remove_channels=='only_non_stoch':   Mechanisims=non_sotchastic_mechs
    logging.info("Removing channels type = " + remove_channels)
    

    for sec in h.allsec():
        for mec in Mechanisims:
            if mec in dir(sec(.5)): sec.uninsert(mec)


    if 'special_tag' in settings:
        gjc=0.1
        logging.info("****\n**** special_tag ****\n****")


    # load g_pas
    if settings['load_g_pas'] != False:
        logging.info(f"Changing g_pas to fit {gjc} - file {settings['load_g_pas']} - start!")
        g_pas_file = h5py.File(settings['load_g_pas'],'r')
        for agid in g_pas_file[f'g_pas/{gjc}/']:
            gid = int(agid[1:])
            if gid in list(nd._circuits.node_managers[''].getGidListForProcessor()): # if the node has a part of the cell
                cell = nd._circuits.global_manager.getCell(gid)
                for sec in cell.all:
                    for seg in sec:
                        seg.g_pas = g_pas_file[f'g_pas/{gjc}/{agid}'][str(seg)[str(seg).index('.')+1:]][settings['correction_iteration_load']]
        g_pas_file.close()
        logging.info("Changing g_pas to fit " + str(gjc) + " Done")
    MPI._pc.barrier()
    # load current clamps
    if 'manual_MEComboInfoFile' in settings and settings['manual_MEComboInfoFile']:   #If I manually injecting different holding current for each cell, I will inject the current - the holding the emMEComboInfoFile
        logging.info("manual_MEComboInfoFile  file: " + settings['manual_MEComboInfoFile'])
        MPI._pc.barrier()
        holding_ic_per_gid = {}
        if settings['procedure_type'] == 'find_holding_current': raise Exception("not make any sense")
        holding_per_gid = h5py.File(settings['manual_MEComboInfoFile'],'r') # load holding_per_gid
        for agid in holding_per_gid['holding_per_gid'][str(gjc)]:
            gid = int(agid[1:])
            if gid in list(nd._circuits.node_managers[''].getGidListForProcessor()):
                holding_ic_per_gid[gid] = h.IClamp(0.5, sec = nd._circuits.global_manager.getCell(gid).soma[0])
                holding_ic_per_gid[gid].dur = 9e9 # this will continue also after the BlueConfig holding stopes
                
                
                holding_ic_per_gid[gid].amp = holding_per_gid['holding_per_gid'][str(gjc)][agid][()]
        
        logging.info(str(["Need to think better about holding, look at manager_python.py below this comment!"]*5))
                
                #if settings['disable_holding'] == True:
                    #holding_ic_per_gid[int(gid[1:])].amp = holding_per_gid['holding_per_gid'][str(gjc)][gid][()]
                #else:
                    #holding_ic_per_gid[int(gid[1:])].amp = holding_per_gid['holding_per_gid'][str(gjc)][gid][()] - h.node0.cellDistributor.getMEType(int(gid[1:])).getHypAmp()
        logging.info("Finish manual_MEComboInfoFile")
        
                
    
if settings['procedure_type'] == 'find_holding_current' and type(settings['vc_amp'])==str:
    logging.info("Start find_holding_current")
    logging.info(f"-voltage file - {settings['vc_amp']}")
    
    if settings['disable_holding'] == False: logging.info(str(["I am doing V_clamp and not disable holding! - it is a bit strange, think about it\n"]*3))
    gjc = settings['gjc']
    save_saclamps_voltages = 1
    

    all_gids = nd._target_manager._targets[nd._base_circuit.CircuitTarget].get_gids()
    all_gids = list(set(all_gids)) #? Maybe I need the set() for multisplit.. probably not 
    
    
    SEClmap_per_gid = {}
    SEClamp_current_per_gid = {}
    v_per_gid = h5py.File(settings['vc_amp'],'r') # load v_per_gid
    for gid in all_gids:
        if gid in list(nd._circuits.node_managers[''].getGidListForProcessor()):
            SEClmap_per_gid[gid] = h.SEClamp(0.5, sec = nd._circuits.global_manager.getCell(gid).soma[0])
            SEClmap_per_gid[gid].dur1 = 9e9
            SEClmap_per_gid[gid].amp1 = float(v_per_gid['v_per_gid']['a'+str(int(gid))][()])
            SEClmap_per_gid[gid].rs  = 0.0000001
            SEClamp_current_per_gid[gid] = h.Vector()
            SEClamp_current_per_gid[gid].record(SEClmap_per_gid[gid]._ref_i)
    v_per_gid.close()
    logging.info("Finish find_holding_current")

def save_seclamps():
    if save_saclamps_voltages:
        logging.info('Saving SEClamp Data')
        #logging.info(SEClamp_current_per_gid)
        SEClamp_current_per_gid_a = {}
        for gid in SEClamp_current_per_gid:
            SEClamp_current_per_gid_a[gid] = np.array(SEClamp_current_per_gid[gid])
        logging.info('to array finished')
        #logging.info(SEClamp_current_per_gid)
        pickle.dump(SEClamp_current_per_gid_a, open(f'{nd._run_conf["OutputRoot"]}/data_for_host_{MPI.rank}.p','wb'))
        logging.info('Finish Saving Data')



if load_g_pas_correction_file:
    logging.info("Loading g_pas_correction_file")
    exec(open('/gpfs/bbp.cscs.ch/home/amsalem/Dropbox/Blue_Brain/Experiments_Reproduction/Coupling_Coefficient/pylibs/gap_junction_conductance_search_damus.py').read())
else:
    MPI._pc.barrier()
    nd._finalize_model() # sometime need another stdinit so to implement the changes that I did
    nd.run()    
    if settings['procedure_type'] == 'find_holding_current' and type(settings['vc_amp'])==str:
        save_seclamps()
        logging.info('Done ? #Finish Saving Data')