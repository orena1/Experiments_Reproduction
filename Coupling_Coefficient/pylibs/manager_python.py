# this script will either set the stage for current injection or load the g_pas_conduction_search.py

import pickle
from neuron import h
import h5py
import numpy as np
import sys
if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

non_sotchastic_mechs = ['NaTs2_t', 'SKv3_1', 'Nap_Et2', 'Ih', 'Im', 'KdShu2007',
                'K_Pst', 'K_Tst', 'Ca', 'SK_E2', 'Ca_LVAst', 'CaDynamics_E2'
                ,'NaTa_t', 'CaDynamics_DC0','Ca_HVA2', 'NaTg'] +
                ['TC_cad', 'TC_ih_Bud97', 'TC_Nap_Et2', 'TC_iA', 'TC_iL', 'SK_E2', 'TC_HH', 'TC_iT_Des98']

sotchastic_mechs = ['StochKv', 'StochKv2', 'StochKv3']



    
if sys.version_info[0] < 3:
    settings = pickle.load(open(h.node0.configParser.parsedRun.get("CurrentDir").s  + "/settings.p",'r'))
else:
    settings = pickle.load(open(h.node0.configParser.parsedRun.get("CurrentDir").s  + "/settings.p",'rb'), encoding = 'latin1')


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
    h.node0.updateGJcon(gjc)
   
    # remove active channels 
    remove_channels = settings['remove_channels']
    Mechanisims =[]
    if remove_channels=='all':              Mechanisims=non_sotchastic_mechs + sotchastic_mechs
    if remove_channels=='only_stoch':       Mechanisims=sotchastic_mechs
    if remove_channels=='only_non_stoch':   Mechanisims=non_sotchastic_mechs
    h.node0.log("Removing channels type = " + remove_channels)
    for i in h.allsec():
        for mec in Mechanisims:
            h('uninsert ' +mec)


    if 'special_tag' in settings:
        gjc=0.1
        h.node0.log("****\n**** special_tag ****\n****")


    # load g_pas
    if settings['load_g_pas'] != False:
        h.node0.log("Changing g_pas to fit " + str(gjc))
        g_pas_file = h5py.File(settings['load_g_pas'],'r')
        for agid in g_pas_file['g_pas/' +str(gjc) + '/']:
            gid = int(agid[1:])
            if gid in list(h.node0.cellDistributor.getGidListForProcessor()): # if the node has a part of the cell
                cell = h.node0.pnm.pc.gid2cell(h.node0.cellDistributor.getSpGid(gid))
                for sec in cell.all:
                    for seg in sec:
                        seg.g_pas = g_pas_file['g_pas/' +str(gjc) + '/' + agid][str(seg)[str(seg).index('.')+1:]][settings['currention_iteration_load']]
        g_pas_file.close()
        h.node0.log("Changing g_pas to fit " + str(gjc) + " Done")
   
    # load current clamps
    if 'manual_MEComboInfoFile' in settings and settings['manual_MEComboInfoFile']:   #If I manually injecting different holding current for each cell, I will inject the current - the holding the emMEComboInfoFile
        h.node0.log("manual_MEComboInfoFile  file: " + settings['manual_MEComboInfoFile'])
        holding_ic_per_gid = {}
        if settings['procedure_type'] == 'find_holding_current': raise Exception("not make any sense")
        holding_per_gid = h5py.File(settings['manual_MEComboInfoFile'],'r') # load holding_per_gid
        for gid in holding_per_gid['holding_per_gid'][str(gjc)]:
            if h.node0.pnm.gid_exists(int(gid[1:])):
                holding_ic_per_gid[int(gid[1:])] = h.IClamp(0.5, sec = h.node0.pnm.pc.gid2cell(int(gid[1:])).soma[0])
                holding_ic_per_gid[int(gid[1:])].dur = 9e9 # this will continue also after the BlueConfig holding stopes
                if settings['disable_holding'] == True:
                    holding_ic_per_gid[int(gid[1:])].amp = holding_per_gid['holding_per_gid'][str(gjc)][gid][()]
                else:
                    holding_ic_per_gid[int(gid[1:])].amp = holding_per_gid['holding_per_gid'][str(gjc)][gid][()] - h.node0.cellDistributor.getMEType(int(gid[1:])).getHypAmp()
        
                
    
if settings['procedure_type'] == 'find_holding_current' and type(settings['vc_amp'])==str:
    if settings['disable_holding'] == False: raise Exception("There is no rational in VClamp with holding!")
    gjc = settings['gjc']
    save_saclamps_voltages = 1
    
    circuitTarget = h.node0.targetParser.getTarget( h.node0.configParser.parsedRun.get("CircuitTarget").s ) 
    all_gids = circuitTarget.completegids() # Get all the gids in the network
    all_gids = list(set(all_gids)) #? Maybe I need the set() for multisplit.. probably not 
    SEClmap_per_gid = {}
    SEClamp_current_per_gid = {}
    v_per_gid = h5py.File(settings['vc_amp'],'r') # load v_per_gid
    for gid in all_gids:
        if h.node0.pnm.gid_exists(gid):
            SEClmap_per_gid[gid] = h.SEClamp(0.5, sec = h.node0.pnm.pc.gid2cell(gid).soma[0])
            SEClmap_per_gid[gid].dur1 = 9e9
            SEClmap_per_gid[gid].amp1 = v_per_gid['v_per_gid']['a'+str(int(gid))].value
            SEClmap_per_gid[gid].rs  = 0.0000001
            SEClamp_current_per_gid[gid] = h.Vector()
            SEClamp_current_per_gid[gid].record(SEClmap_per_gid[gid]._ref_i)
    v_per_gid.close()
    
def save_seclamps():
    if save_saclamps_voltages:
        h.node0.log('Saving Data')
        for gid in SEClamp_current_per_gid:
            SEClamp_current_per_gid[gid] = np.array(SEClamp_current_per_gid[gid])
        pickle.dump(SEClamp_current_per_gid, open(h.node0.configParser.parsedRun.get("OutputRoot").s  +'/data_for_host_' + str(int(h.node0.pnm.myid)) + '.p','wb'), 2)
