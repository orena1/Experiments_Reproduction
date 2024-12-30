#create current injection and mesure CC
from __future__ import division
import os
import shutil
import sys
sys.path.append('../general_scripts/')

from Cheetah.Template import Template
import subprocess
import numpy as np
import bluepy
import pickle

execfile('../general_scripts/jobs_creation.py')
execfile('../general_scripts/opto_gen_protocols.py')




#for ca in [0.5,1.0,1.25,1.5,2.0,2.5]:
ca = float(1.23) #CAline
k = float(5.0)
Mg = float(1.0)



change_gamma = False
core_neuron = False
knl = False
cluster = 'neuron_coreneuron' # bbpv1 # bbpviz1 # bbpv1core_neuron
#if core_neuron==True or knl:
    #raise Exception("Does not work")
if cluster == 'neuron_coreneuron':
    
    partition = 'prod'
    hoc_lib = '/gpfs/bbp.cscs.ch/home/amsalem/rsync/Blue_Brain/Experiments_Reproduction/Coupling_Coefficient/hoclib/'
    init_name = 'init.hoc'
    special_path = ''' special -mpi '''
    
    bbpviz_txt =  'export MODULEPATH=/gpfs/bbp.cscs.ch/project/proj64/home/kumbhar/softwares/modules/tcl/linux-rhel7-x86_64:$MODULEPATH\n'\
                    + 'module load neurodamus/plasticity-knl\n'\
                    + 'module load synapsetool/0.3.2\n'\
                    + 'module load reportinglib/develop\n'\
                    + 'export HOC_LIBRARY_PATH=/gpfs/bbp.cscs.ch/home/amsalem/rsync/Blue_Brain/Experiments_Reproduction/Coupling_Coefficient/hoclib/'
    ssh_path = 'bbpv1.epfl.ch'
    if knl == True:
        nodes = 55
        ntask_per_node = 64
    else:
        nodes = 11
        ntask_per_node = 36




def create_path_and_copy_file(path_for_simulations, model_folders):
    #model_folders = '../O1_v6_20171212/'
    #model_folders = '../Circuits_data/Hippocampus/20190306/'
    #model_folders = '../Circuits_data/Thalamus/19_04_2018/'
    
    FilesToCopy = ['launchScript_bg_template.sh', 'inputs.dat', 'user.target', 'BlueConfig_template']
    if not os.path.exists(path_for_simulations):
        os.makedirs(path_for_simulations)
        
    for FtC in FilesToCopy:
        if FtC == 'user.target':
            shutil.copyfile(model_folders + FtC, path_for_simulations + '/' + FtC )
        else:
            if not os.path.exists(path_for_simulations + '/' + FtC):
                shutil.copyfile(model_folders + FtC, path_for_simulations + '/' + FtC )

    shutil.copyfile(os.path.basename(__file__), path_for_simulations + '/' + os.path.basename(__file__) )



def create_directory(base_path, settings):
    base_path += settings['procedure_type'] +'/' +'Circ_'+ settings['circuit_target'] + '_' +  'Remove_ch_' + settings['remove_channels']  \
                 + '_Det_stoch_' + str(settings['determanisitc_stoch']) + '_Dis_holding_' + str(settings['disable_holding']) 
    if settings['procedure_type'] in ['validation_sim', 'find_holding_current']:
        base_path += '_gjc' + str(settings['gjc']).replace('.','p')
        if settings['change_MEComboInfoFile'] ==None:
            base_path += '_Change_mecomb_False'
        else:
            base_path += '_Change_mecomb_True'
        if settings['manual_MEComboInfoFile'] !=False:
            base_path += '_manual_MEComboInfoFile_True'
        else:
            base_path += '_manual_MEComboInfoFile_False'
        
        
        if settings['load_g_pas']==False:
            base_path += '_Load_g_pas_False'
        else:
            base_path += '_Load_g_pas_True' + '_Correc_iter_load' + str(settings['correction_iteration_load']).replace('-1','last')
        
        
        
        if settings['procedure_type'] == 'validation_sim':
            stim_string = 'stim_amp' + str(settings['stim_amp']).replace('-','m') + '_stim_num' + str(settings['stim_num']) + '_stim_dur'+ str(settings['stim_dur']) + '_stim_isi'+ str(settings['stim_isi'])
        if settings['procedure_type'] == 'find_holding_current':
            if type(settings['vc_amp'])==str:
                stim_string = 'vc_ampFile'
            else:
                stim_string = 'vc_amp' + str(settings['vc_amp']).replace('-','m')
        
        base_path = base_path.replace('/Circ','/' + stim_string + '/Circ')
    else:
        base_path += '_Correc_type_' + settings['rm_correction_type'] + '_Cm' + str(settings['rm_correction_cm']).replace('.','p') \
            + '_Num_iter_' + str(settings['rm_correction_number_of_iterations'])
    if 'special_tag' in settings:
        base_path+= '_Special_' + settings['special_tag']+'/'
    base_path+='/'

    return(base_path)


def create_current_injections(path_for_simulations, gids_to_test):

    

    for gid in gids_to_test:
        f = open(path_for_simulations + 'user.target','a')
        f.write('\nTarget Cell a' + str(gid) + '\n{\n')
        f.write('   a' + str(gid))
        f.write('\n}\n\n')
        f.close()
    
    #
    # Chr options 
    #
    stim_num = settings['stim_num']
    stim_dur = settings['stim_dur']
    stim_isi = settings['stim_isi']

    stim_vars = {'a' + str(gid):[{'amp':settings['stim_amp'],'start':1000 + (stim_dur+stim_isi)*stim_num*j,'dur':(stim_dur+stim_isi)*stim_num, 'var':0, 'pulse_width': stim_dur , 'freq': 1000/(stim_dur+stim_isi)}] 
                    for j,gid in enumerate(gids_to_test)}
    
    optogenetic_vars=['pulse_train', ['a' + str(gid) for gid in gids_to_test], stim_vars]
    pickle.dump(stim_vars,open(path_for_simulations +'/stim_var.p','w'),2)
    simulation_duration = len(gids_to_test)*((stim_dur+stim_isi)*stim_num) + 1000

    return(stim_vars, optogenetic_vars,simulation_duration)


circuit_to_run = {'neocortex_v6':{},
                  'hippocampus_06_03_2019':{'gids_to_test':[17068,16946,17062,17064,17068],
                                             'base_path':'/gpfs/bbp.cscs.ch/project/proj2/simulations/Gap_Junctions_v1/hippocampus/circ03_06_2019_v2/',
                                             'circuit_target':'SP_PVBC_gjs',
                                             'model_folders':'../Circuits_data/Hippocampus/20190306/',
                                             'hoc_lib':'/gpfs/bbp.cscs.ch/home/amsalem/rsync/Blue_Brain/Experiments_Reproduction/Coupling_Coefficient/hoclib_hippocampus/',
                                             'special_path':'$SPECIAL -mpi ',
                                             'bbpviz_txt':'module load hpe-mpi\nmodule load python/3.6.5\nexport SPECIAL=/gpfs/bbp.cscs.ch/project/proj2/Programs/test/hippocampus/soft/sources/neurodamus/x86_64/special'
                                                 
                                             
                                             
                                                 }
                  }


def set_stages_settings():
    stages_settings  = {'1_extract_holding_voltage':{'remove_channels':False,
                                                    'procedure_type':'validation_sim',
                                                    'remove_channels':'none',
                                                    'stim_num':1,
                                                    'stim_dur':1,
                                                    'stim_isi':3000,
                                                    'stim_amp':0.0000000001,
                                                    'disable_holding',False,
                                                    'gjc':0.0,
                                                    'manual_MEComboInfoFile':False,
                                                    'load_g_pas':False },
                        '2_find_correct_holding':{'remove_channels':False,
                                                    'procedure_type':'find_holding_current',
                                                    'remove_channels':'none',
                                                    'vc_amp':circuit_to_run[circ]['base_path'] +'/validation_sim/stim_amp1em10_stim_num1_stim_dur1_stim_isi3000/Circ' +  circuit_to_run[circ]['circuit_target'] + '_Remove_ch_none_Det_stoch_True_Dis_holding_False_gjc0p0_Change_mecomb_False_manual_MEComboInfoFile_False_Load_g_pas_False/num_0/v_per_gid.hdf5',
                                                    'load_g_pas':circuit_to_run[circ]['base_path'] +'/rm_correction/Circ' +  circuit_to_run[circ]['circuit_target'] + '_Remove_ch_all_Det_stoch_True_Dis_holding_False_Correc_type_impedance_tool_Cm0p01_Num_iter_10/num_0/g_pas_passive.hdf5',
                                                    'stim_num':1,
                                                    'stim_dur':1,
                                                    'stim_isi':3000,
                                                    'stim_amp':0.0000000001,
                                                    'disable_holding',False,
                                                    'gjc':gjc,
                                                    'manual_MEComboInfoFile':False,
                                                    },
                        '3_validation_sim_with_gj':{'remove_channels':False,
                                                    'procedure_type':'validation_sim',
                                                    'load_g_pas':circuit_to_run[circ]['base_path'] +'/rm_correction/Circ' +  circuit_to_run[circ]['circuit_target'] + '_Remove_ch_all_Det_stoch_True_Dis_holding_False_Correc_type_impedance_tool_Cm0p01_Num_iter_10/num_0/g_pas_passive.hdf5',
                                                    'manual_MEComboInfoFile':circuit_to_run[circ]['base_path'] +'vc_ampFile/Circ_' + circuit_to_run[circ]['circuit_target'] + '_Remove_ch_none_Det_stoch_True_Dis_holding_False_gjc' + str(gjc) + ' _Change_mecomb_False_manual_MEComboInfoFile_False_Load_g_pas_True_Correc_iter_loadlast/num_0/holding_per_gid.hdf5'
                                                    'remove_channels':'none',
                                                    'stim_num':1,
                                                    'stim_dur':100,
                                                    'stim_isi':400,
                                                    'stim_amp':150,
                                                    'disable_holding',False,
                                                    'gjc':gjc},
                        '4_validation_sim_with_gj':{'remove_channels':False,
                                                    'procedure_type':'validation_sim',
                                                    'load_g_pas':False,
                                                    'manual_MEComboInfoFile':False,
                                                    'remove_channels':'none',
                                                    'stim_num':1,
                                                    'stim_dur':100,
                                                    'stim_isi':400,
                                                    'stim_amp':150,
                                                    'disable_holding',False}
                                                 
    return(stages_settings)


gjc = 0.2
circ = 'hippocampus_06_03_2019'
stages_settings = set_stages_settings()



hoc_lib = circuit_to_run[circ]['hoc_lib']
special_path = circuit_to_run[circ]['special_path']
bbpviz_txt =circuit_to_run[circ]['bbpviz_txt']



nice_level = 0    

remove_spon_minis = False
Disable_CortoCortical = False
DisableUseDep = False
spike_replay = None
projection_path = None
gids_to_test = [17068,16946,17062,17064,17015]

reports = {}
v_clamp = {}
optogenetic_vars =[]
RNGMode = 'Random123'
RunMode = 'RunMode LoadBalance'
BS = 0 # seed
ca = -1
k = -1
Mg = -1

simulation_duration = 100
simulation_time = "01:00:00" # real run time
MEComboInfoFile = None


for remove_channels in ['none']:
    for load_g_pas in ['/gpfs/bbp.cscs.ch/project/proj2/simulations/Gap_Junctions_v1/hippocampus/circ03_06_2019_v2/rm_correction/Circ_SP_PVBC_gjs_Remove_ch_all_Det_stoch_True_Dis_holding_False_Correc_type_impedance_tool_Cm0p01_Num_iter_10/num_0/g_pas_passive.hdf5']:#'/gpfs/bbp.cscs.ch/project/proj2/simulations/Gap_Junctions/test4.hdf5']:#,False]:
        for gjc in [0.2]:
            for MEComboInfoFile in [None]:#,'/gpfs/bbp.cscs.ch/home/amsalem/Dropbox/Blue_Brain/Experiments_Reproduction/Coupling_Coefficient/mecombo_emodel.tsv']:

                settings = {}
                settings['procedure_type'] = 'validation_sim' # 'validation_sim' | 'validation_sim' | 'find_holding_current'
                settings['remove_channels'] = remove_channels#'all' #'only_stoch','only_non_stoch', 'none','all'
                settings['determanisitc_stoch'] = True # True|False
                settings['circuit_target'] = circuit_to_run[circ]['circuit_target'] #SP_PVBC_gjs' # PV_mc2 | Rt_RC_gjs | SP_PVBC
                settings['disable_holding'] = False # True|False
                #settings['special_tag'] = '0as0p1'



                if settings['procedure_type'] =='rm_correction':
                    settings['rm_correction_type'] = 'impedance_tool' # 'impedance_tool', 'current_injections'
                    settings['rm_correction_cm'] = 0.01 
                    settings['rm_correction_number_of_iterations'] = 10
                    settings['rm_correction_gjcs'] = [0.1,0.2,0.25,0.3,0.35,0.5]
                    simulation_time = "08:00:00" # real run time
                    RunMode = 'RunMode WholeCell'
                elif settings['procedure_type'] in ['validation_sim', 'find_holding_current']:
                    settings['load_g_pas'] = load_g_pas#'/gpfs/bbp.cscs.ch/project/proj2/simulations/Gap_Junctions/test4.hdf5' # path to h5 file with g_pas values | False
                    settings['manual_MEComboInfoFile'] = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Gap_Junctions_v1/hippocampus/circ03_06_2019_v2/find_holding_current/vc_ampFile/'\
                         + 'Circ_SP_PVBC_gjs_Remove_ch_none_Det_stoch_True_Dis_holding_False_gjc0p2_Change_mecomb_False_manual_MEComboInfoFile_False_Load_g_pas_True_Correc_iter_loadlast/num_0/'\
                             +'holding_per_gid.hdf5'#False#'/gpfs/bbp.cscs.ch/home/amsalem/Dropbox/Blue_Brain/Experiments_Reproduction/Coupling_Coefficient/holding_per_gid.hdf5' #False, '/gpfs/bbp.cscs.ch/home/amsalem/Dropbox/Blue_Brain/Experiments_Reproduction/Coupling_Coefficient/holding_per_gid.hdf5'
                    settings['correction_iteration_load'] = -1
                    settings['gjc'] = gjc#0.1
                    reports['soma_voltage'] = {'REPORT_TARGET':settings['circuit_target'],'START_TIME':str(0), 'END_TIME':str(9e9),'DT':str(0.1)}
                    settings['change_MEComboInfoFile'] = None
                    MEComboInfoFile = settings['change_MEComboInfoFile']
                    if type(settings['change_MEComboInfoFile'])==str and (settings['manual_MEComboInfoFile']!=None): raise Exception('Not really make any sense')
                    if type(settings['change_MEComboInfoFile'])==str and type(settings['load_g_pas'])!=str: raise Exception('Not really make any sense')
                    
                    if settings['procedure_type'] == 'validation_sim':
                        #settings['stim_num'] = 1
                        #settings['stim_dur'] = 2
                        #settings['stim_isi'] = 3000
                        #settings['stim_amp'] = 0.0000000001
                        RunMode = 'RunMode LoadBalance'
                        
                        settings['stim_num'] = 1
                        settings['stim_dur'] = 1000
                        settings['stim_isi'] = 400
                        settings['stim_amp'] = 149
                    if settings['procedure_type'] == 'find_holding_current':
                        settings['vc_amp'] = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Gap_Junctions_v1/hippocampus/circ03_06_2019_v2/validation_sim/stim_amp1em10_stim_num1_stim_dur1_stim_isi3000/Circ_SP_PVBC_gjs_Remove_ch_none_Det_stoch_True_Dis_holding_False_gjc0p0_Change_mecomb_False_manual_MEComboInfoFile_False_Load_g_pas_False/num_0/v_per_gid.hdf5'  #''/gpfs/bbp.cscs.ch/home/amsalem/Dropbox/Blue_Brain/Experiments_Reproduction/Coupling_Coefficient/v_per_gid.hdf5' | -84
                        
                        simulation_duration = 3000
                        RunMode = 'RunMode WholeCell'
                        if type(settings['vc_amp'])!=str: v_clamp[settings['vc_amp']] = [circuit_to_run[circ]['circuit_target']]
                        print([' I am runing hoding and VClamp in the same time - you need to think about it!\n']*5) 
                    
        
                
                
                #debug
                if 'vc_amp' in settings and not os.path.isfile(settings['vc_amp']):raise Exception("file vc_amp does not exist")
                if settings['load_g_pas'] and not os.path.isfile(settings['load_g_pas']):raise Exception("file load_g_pas does not exist")
                if 'manual_MEComboInfoFile' in settings and settings['manual_MEComboInfoFile'] and not os.path.isfile(settings['manual_MEComboInfoFile']):raise Exception("file manual_MEComboInfoFile does not exist",settings['manual_MEComboInfoFile'])
                                
                
                base_path = circuit_to_run[circ]['base_path']
                #base_path = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Gap_Junctions_v1/thalamus/circ19_04_2018/'
                if knl:
                    base_path +='knl'
                if core_neuron:
                    base_path +='Core'
                base_path+='/'
                path_for_simulations = create_directory(base_path, settings)
                raw_input(path_for_simulations)
                create_path_and_copy_file(path_for_simulations, circuit_to_run[circ]['model_folders'])
                pickle.dump(settings, open(path_for_simulations +'/settings.p','w'))
                
                
                circuit_target = settings['circuit_target']
                circuit_target_name = circuit_target
                run_name = 'num_0'
                run_names = []
                job_name =  settings['procedure_type']


                if settings['procedure_type'] == 'validation_sim':
                    stim_vars, optogenetic_vars, simulation_duration = create_current_injections(path_for_simulations, gids_to_test)



                #for ssrun_time in range(0,simulation_duration + 60000,60000):
                f = open(path_for_simulations +'/BlueConfig_template','r')
                blue_out = crate_blueconfig(BlueConfig_file=f, CurrentDir = path_for_simulations, BS = BS, simulation_duration = simulation_duration,
                                                                        run_name=run_name, ca=ca, k=k, Mg=Mg,circuit_target = circuit_target_name, decouple=Disable_CortoCortical, optogenetic_vars=optogenetic_vars,
                                                                        DisableUseDep = DisableUseDep,reports=reports, v_clamp=v_clamp, MEComboInfoFile=MEComboInfoFile,
                                                                        RunMode = RunMode, remove_spon_minis=remove_spon_minis, spike_replay=spike_replay, RNGMode=RNGMode, core_neuron=core_neuron, projection_path=projection_path)
                f = open(path_for_simulations + 'BlueConfig_' + run_name, 'w')
                if settings['disable_holding']: blue_out=blue_out.replace('StimulusInject hypamp_mosaic','#StimulusInject hypamp_mosaic')
                f.write(blue_out)
                f.close()


                f = open(path_for_simulations +'/launchScript_bg_template.sh','r')
                launch_out = create_launch_script(launchScript_file=f, hoc_lib=hoc_lib, init_name=init_name, special_path=special_path, simulation_time=simulation_time,
                                                                                    run_name=run_name, nice_level=nice_level, nodes=nodes, ntask_per_node=ntask_per_node, 
                                                                                    bbpviz_txt = bbpviz_txt, partition=partition, job_name=job_name, core_neuron=core_neuron)
                f = open(path_for_simulations + 'launchScript_bg_' + run_name +'.sh', 'w')
                f.write(launch_out)
                f.close()

                if not os.path.exists(path_for_simulations + '/' + run_name): #If folder already exist do not send it.
                    run_names.append('sbatch launchScript_bg_' + run_name +'.sh')
                else:
                    print('************ Job already submitted, not sure if completed **************')
                #as it is per directory I need to submit the jobs here!

                submit_jobs(run_names, path_for_simulations, MaxJobs = 1,  all_after_one=True, ssh_path=ssh_path)

