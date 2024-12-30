# create current injection and mesure CC
from __future__ import division
import typing
import pandas as pd
import scipy
import pickle
import bluepy
import numpy as np
import subprocess
from Cheetah.Template import Template
from sklearn.cluster import KMeans
import os
import shutil
import sys
sys.path.append('../general_scripts/')
exec(open('../general_scripts/jobs_creation_p3.py').read())
exec(open('../general_scripts/opto_gen_protocols_p3.py').read())

core_neuron = False


circuit_to_run = {'neocortex_v6': {},
                  'hippocampus_06_03_2019': {'gids_to_test': [17068, 16946, 17062, 17064, 17015],
                                             'base_path': '/gpfs/bbp.cscs.ch/project/proj2/simulations/Gap_Junctions_v1/hippocampus/circ03_06_2019_v2/',
                                             'circuit_target': 'SP_PVBC_gjs',
                                             'model_folders': '../Circuits_data/Hippocampus/20190306/',
                                             'hoc_lib': '/gpfs/bbp.cscs.ch/home/amsalem/rsync/Blue_Brain/Experiments_Reproduction/Coupling_Coefficient/hoclib_hippocampus/',
                                             'special_path': '$SPECIAL -mpi ',
                                             'bbpviz_txt': 'module load hpe-mpi\nmodule load python/3.6.5\nexport SPECIAL=/gpfs/bbp.cscs.ch/project/proj2/Programs/test/hippocampus/soft/sources/neurodamus/x86_64/special'



                                             },
                  'thalamus_19_04_2018': {'gids_to_test': [6, 7, 14, 21],
                                          'base_path': '/gpfs/bbp.cscs.ch/project/proj2/simulations/Gap_Junctions_v1/thalamus/circ19_04_2018_prune/',
                                          'circuit_target': 'Rt_RC_gjs',
                                          'model_folders': '../Circuits_data/Thalamus/19_04_2018/',
                                          'hoc_lib': '/gpfs/bbp.cscs.ch/home/amsalem/rsync/Blue_Brain/Experiments_Reproduction/Coupling_Coefficient/hoclib_thalamus/',
                                          'special_path': 'special -mpi ',
                                          'bbpviz_txt': 'module load neurodamus-thalamus/0.3/python3/parallel; export HOC_LIBRARY_PATH=/gpfs/bbp.cscs.ch/home/amsalem/rsync/Blue_Brain/Experiments_Reproduction/Coupling_Coefficient/hoclib_thalamus/'
                                          },

                  'thalamus_19_11_2019': {'gids_to_test': [33432, 29392, 30161, 32302, 29140],
                                          'base_path': '/gpfs/bbp.cscs.ch/project/proj55/amsalem/gap_junctions/circ19_11_19/',
                                          'circuit_target': 'mc2_Rt',
                                          'model_folders': '../Circuits_data/Thalamus/19_11_2019/',
                                          'hoc_lib': '',
                                          'special_path': 'special -mpi ',
                                          'bbpviz_txt': 'module load neurodamus-thalamus/0.3/python3/parallel/serial; export HOC_LIBRARY_PATH=/gpfs/bbp.cscs.ch/home/amsalem/rsync/Blue_Brain/Experiments_Reproduction/Coupling_Coefficient/hoclib_thalamus_0p3/'
                                          },
                  'thalamus_19_11_2019_gjs_19_20_20': {'gids_to_test': [33432, 29392, 30161, 32302, 29140, 33505, 29674, 29351, 30628],
                                                       'base_path': '/gpfs/bbp.cscs.ch/project/proj55/amsalem/gap_junctions/circ19_11_2019_gjs_19_20_20_new_holding/',
                                                       'circuit_target': 'mc2_Rt',
                                                       'model_folders': '../Circuits_data/Thalamus/19_11_2019_gjs_19_20_20/',
                                                       'hoc_lib': '',
                                                       'special_path': 'special -mpi ',
                                                       'bbpviz_txt': 'module load archive/2020-02\nmodule load neurodamus-thalamus/0.3-knl\nmodule load py-h5py/2.10.0\n export HOC_LIBRARY_PATH=/gpfs/bbp.cscs.ch/home/amsalem/rsync/Blue_Brain/Experiments_Reproduction/Coupling_Coefficient/hoclib_thalamus_0p3/'
                                                       },
                  'thalamus_19_11_2019_gjs_19_20_20_full': {'gids_to_test': [33432, 29392, 30161, 32302, 29140, 33505, 29674, 29351, 30628],
                                                            'base_path': '/gpfs/bbp.cscs.ch/project/proj55/amsalem/gap_junctions/circ19_11_2019_gjs_19_20_20_full/',
                                                            'circuit_target': 'Rt_RC',
                                                            'model_folders': '../Circuits_data/Thalamus/19_11_2019_gjs_19_20_20/',
                                                            'hoc_lib': '',
                                                            'special_path': 'special -mpi ',
                                                            'bbpviz_txt': 'module load archive/2020-02\nmodule load neurodamus-thalamus/0.3-knl\nmodule load py-h5py/2.10.0\n export HOC_LIBRARY_PATH=/gpfs/bbp.cscs.ch/home/amsalem/rsync/Blue_Brain/Experiments_Reproduction/Coupling_Coefficient/hoclib_thalamus_0p3/'
                                                            },
                  'thalamus_21_21_22': {'gids_to_test': [33505, 29674, 29351, 30628],
                                        'base_path': '/gpfs/bbp.cscs.ch/project/proj55/amsalem/gap_junctions/circ21_21_22/',
                                        'circuit_target': 'Rt_RC',
                                        'model_folders': '../Circuits_data/Thalamus/21_21_22/',
                                        'hoc_lib': '',
                                        'special_path': '/gpfs/bbp.cscs.ch/project/proj55/iavarone/releases/circuits/O1/2021-21-22/test-simulations/base-circuit/x86_64/special -mpi ',
                                        'bbpviz_txt': 'module load archive/2020-02\nmodule load neurodamus-thalamus/0.3-knl\nmodule load py-h5py/2.10.0\n export HOC_LIBRARY_PATH=/gpfs/bbp.cscs.ch/home/amsalem/rsync/Blue_Brain/Experiments_Reproduction/Coupling_Coefficient/hoclib_thalamus_1p4_3p3p2/'
                                        },
                  'thalamus_21_04_06': {'sim_account': 'proj55',
                                        'gids_to_test': [1188448, 1188554, 1188570, 1189197, 1189653],
                                        'base_path': '/gpfs/bbp.cscs.ch/project/proj55/amsalem/gap_junctions/circ21_04_06/',
                                        'circuit_target': 'Rt_RC',
                                        'model_folders': '../Circuits_data/Thalamus/21_04_06/',
                                        'hoc_lib': '',
                                        'special_path': 'special',
                                        'bbpviz_txt': 'module purge all\n'
                                        'module load archive/2022-06\n'
                                                     'module load neurodamus-thalamus/1.6-2.11.3\n'
                                                     'module load py-neurodamus/2.11.3\n'
                                                     'module load py-h5py/3.4.0\n'
                                                     'export MPI_COLL_OPT=false\n',
                                        'split_method': {'method': 'kmeans', 'n_clusters': 13, 'rm_dist': 390}
                                        },
                  }


# 'gids_to_test':[30521,30718, 31251, 32080] - old...

circ = 'thalamus_21_04_06'
exp_name = '5_validation_sim_with_gj_no_fix'
correction_iteration_load = 4 # -1 for last


# 0_rm_correction
# 1_extract_holding_voltage
# 2_find_correct_holding
# 3_validation_sim_with_gj
# 4_validation_sim_without_gj
# 5_validation_sim_with_gj_no_fix

# testts
# find_correct_holding_no_gpas_correction -
# validation_sim_with_gj_no_fix_with_currection_current


def get_split_cells(circuit_path, rm_dist, circuit_target, n_clusters, plot_debug=1):
    '''
    I need to split the cells twice, one time to get group of cells, and second time for the cells where were in the boundary
    of the gorups in the first group.
    '''
    circ = bluepy.Circuit(circuit_path)
    cells = circ.cells.get(circuit_target)

    kmeans0 = KMeans(n_clusters=n_clusters, random_state=0).fit(
        cells[['x', 'y', 'z']])

    cells['labels'] = [f'l{i}' for i in kmeans0.labels_]
    rm_per_center = []
    for center in kmeans0.cluster_centers_:
        rm_per_center.append(np.where(scipy.spatial.distance_matrix(
            [center], cells[['x', 'y', 'z']])[0] < rm_dist)[0])

    cells_i = cells.reset_index().copy()
    cells_d = cells_i.drop(
        list(set([i for j in rm_per_center for i in j])), axis=0)
    kmeans1 = KMeans(n_clusters=n_clusters, random_state=0).fit(
        cells_d[['x', 'y', 'z']])
    cells['labels_inv'] = [f'l_in{i}' for i in np.argmin(
        scipy.spatial.distance_matrix(cells[['x', 'y', 'z']], kmeans1.cluster_centers_), 1)]

    if plot_debug:
        import plotly.express as px
        fig0 = px.scatter_3d(cells, x='x', y='y', z='z', color='labels_inv')
        fig1 = px.scatter_3d(cells, x='x', y='y', z='z', color='labels')
    return cells, fig0, fig1, kmeans0.cluster_centers_, kmeans1.cluster_centers_


def create_path_and_copy_file(path_for_simulations, model_folders):
    #model_folders = '../O1_v6_20171212/'
    #model_folders = '../Circuits_data/Hippocampus/20190306/'
    #model_folders = '../Circuits_data/Thalamus/19_04_2018/'

    FilesToCopy = ['launchScript_bg_template.sh',
                   'inputs.dat', 'user.target', 'BlueConfig_template']
    if not os.path.exists(path_for_simulations):
        os.makedirs(path_for_simulations)

    for FtC in FilesToCopy:
        if FtC == 'user.target':
            shutil.copyfile(model_folders + FtC,
                            path_for_simulations + '/' + FtC)
        else:
            if not os.path.exists(path_for_simulations + '/' + FtC):
                shutil.copyfile(model_folders + FtC,
                                path_for_simulations + '/' + FtC)

    shutil.copyfile(os.path.basename(__file__),
                    path_for_simulations + '/' + os.path.basename(__file__))


def create_directory(base_path, settings):
    base_path += settings['procedure_type'] + '/' + 'Circ_' + settings['circuit_target'] + '_' + 'Remove_ch_' + settings['remove_channels']  \
        + '_Det_stoch_' + str(settings['determanisitc_stoch']) + \
        '_Dis_holding_' + str(settings['disable_holding'])
    if settings['procedure_type'] in ['validation_sim', 'find_holding_current']:
        base_path += '_gjc' + str(settings['gjc']).replace('.', 'p')
        if settings['change_MEComboInfoFile'] == None:
            base_path += '_Change_mecomb_False'
        else:
            base_path += '_Change_mecomb_True'
        if settings['manual_MEComboInfoFile'] != False:
            base_path += '_manual_MEComboInfoFile_True'
        else:
            base_path += '_manual_MEComboInfoFile_False'

        if settings['load_g_pas'] == False:
            base_path += '_Load_g_pas_False'
        else:
            base_path += '_Load_g_pas_True' + '_Correc_iter_load' + \
                str(settings['correction_iteration_load']
                    ).replace('-1', 'last')

        if settings['procedure_type'] == 'validation_sim':
            stim_string = 'stim_amp' + str(settings['stim_amp']).replace('-', 'm') + '_stim_num' + str(
                settings['stim_num']) + '_stim_dur' + str(settings['stim_dur']) + '_stim_isi' + str(settings['stim_isi'])
        if settings['procedure_type'] == 'find_holding_current':
            if type(settings['vc_amp']) == str:
                stim_string = 'vc_ampFile'
            else:
                stim_string = 'vc_amp' + \
                    str(settings['vc_amp']).replace('-', 'm')

        base_path = base_path.replace('/Circ', '/' + stim_string + '/Circ')
    else:
        base_path += '_Correc_type_' + settings['rm_correction_type'] + '_Cm' + str(settings['rm_correction_cm']).replace('.', 'p') \
            + '_Num_iter_' + \
            str(settings['rm_correction_number_of_iterations'])
    if 'special_tag' in settings:
        base_path += '_Special_' + settings['special_tag']+'/'
    base_path += '/'

    return(base_path)


def add_groups_to_user_target(path_for_simulations, group_to_gids: typing.Dict[str, list]):
    f = open(path_for_simulations + 'user.target', 'a')
    for group_name in group_to_gids:
        f.write(f'\nTarget Cell ' + group_name + '\n{\n')
        for gid in group_to_gids[group_name]:
            f.write(f'a{gid} ')
        f.write('\n}\n\n')
    f.close()


def create_current_injections(path_for_simulations, gids_to_test):
    stim_start = 2500
    for gid in gids_to_test:
        f = open(path_for_simulations + 'user.target', 'a')
        f.write('\nTarget Cell a' + str(gid) + '\n{\n')
        f.write(f'a{gid} ')
        f.write('\n}\n\n')
        f.close()

    # Chr options
    #
    stim_num = settings['stim_num']
    stim_dur = settings['stim_dur']
    stim_isi = settings['stim_isi']

    stim_vars = {'a' + str(gid): [{'amp': settings['stim_amp'], 'start':stim_start + (stim_dur+stim_isi)*stim_num*j, 'dur':(stim_dur+stim_isi)*stim_num, 'var':0, 'pulse_width': stim_dur, 'freq': 1000/(stim_dur+stim_isi)}]
                 for j, gid in enumerate(gids_to_test)}

    optogenetic_vars = ['pulse_train', [
        'a' + str(gid) for gid in gids_to_test], stim_vars]
    pickle.dump(stim_vars, open(path_for_simulations + '/stim_var.p', 'wb'), 2)
    simulation_duration = len(gids_to_test) * \
        ((stim_dur+stim_isi)*stim_num) + stim_start

    return(stim_vars, optogenetic_vars, simulation_duration)


def set_stages_settings():
    stages_settings = {'0_rm_correction': {'procedure_type': 'rm_correction',
                                           'remove_channels': 'all',
                                           'disable_holding': False},
        '1_extract_holding_voltage': {
            'procedure_type': 'validation_sim',
            'remove_channels': 'none',
            'stim_num': 1,
            'stim_dur': 1,
            'stim_isi': 3000,
            'stim_amp': 0.0000000001,
            'disable_holding': False,
            'gjc': 0.0,
            'manual_MEComboInfoFile': False,
            'load_g_pas': False},
                       
        '2_find_correct_holding': {
            'procedure_type': 'find_holding_current',
            'remove_channels': 'none',
            'vc_amp': circuit_to_run[circ]['base_path'] + '/validation_sim/stim_amp1em10_stim_num1_stim_dur1_stim_isi3000/Circ_' + circuit_to_run[circ]['circuit_target'] + '_Remove_ch_none_Det_stoch_True_Dis_holding_False_gjc0p0_Change_mecomb_False_manual_MEComboInfoFile_False_Load_g_pas_False/num_0/v_per_gid.hdf5',
            'load_g_pas': circuit_to_run[circ]['base_path'] + '/rm_correction/Circ_' + circuit_to_run[circ]['circuit_target'] + '_Remove_ch_all_Det_stoch_True_Dis_holding_False_Correc_type_impedance_tool_Cm0p01_Num_iter_10/num_0/g_pas_passive.hdf5',
            'stim_num': 1,
            'stim_dur': 1,
            'stim_isi': 3000,
            'stim_amp': 0.0000000001,
            'disable_holding': False,
            'gjc': gjc,
            'manual_MEComboInfoFile': False,
    },
        '3_validation_sim_with_gj': {
            'procedure_type': 'validation_sim',
            'load_g_pas': circuit_to_run[circ]['base_path'] + '/rm_correction/Circ_' + circuit_to_run[circ]['circuit_target'] + '_Remove_ch_all_Det_stoch_True_Dis_holding_False_Correc_type_impedance_tool_Cm0p01_Num_iter_10/num_0/g_pas_passive.hdf5',
            'manual_MEComboInfoFile': circuit_to_run[circ]['base_path'] + '/find_holding_current/vc_ampFile/Circ_' + circuit_to_run[circ]['circuit_target'] + '_Remove_ch_none_Det_stoch_True_Dis_holding_False_gjc' + str(gjc).replace('.', 'p') + f'_Change_mecomb_False_manual_MEComboInfoFile_False_Load_g_pas_True_Correc_iter_load{correction_iteration_load}/num_0/holding_per_gid.hdf5'.replace('load-1','loadlast'),
            'remove_channels': 'none',
            'stim_num': 1,
            'stim_dur': 800,
            'stim_isi': 800,
            'stim_amp': 180,
            'disable_holding': False,
            'gjc': gjc},
        '4_validation_sim_without_gj': {
            'procedure_type': 'validation_sim',
            'load_g_pas': False,
            'manual_MEComboInfoFile': False,
            'remove_channels': 'none',
            'stim_num': 1,
            'stim_dur': 800,
            'stim_isi': 800,
            'stim_amp': 180,
            'disable_holding': False,
            'gjc': 0.0},
    }

    stages_settings['5_validation_sim_with_gj_no_fix'] = stages_settings['3_validation_sim_with_gj'].copy()
    stages_settings['5_validation_sim_with_gj_no_fix']['load_g_pas'] = False
    stages_settings['5_validation_sim_with_gj_no_fix']['manual_MEComboInfoFile'] = False

    stages_settings['find_correct_holding_no_gpas_correction'] = stages_settings['2_find_correct_holding'].copy()
    stages_settings['find_correct_holding_no_gpas_correction']['load_g_pas'] = False

    stages_settings['validation_sim_with_gj_no_fix_with_currection_current'] = stages_settings['3_validation_sim_with_gj'].copy()
    stages_settings['validation_sim_with_gj_no_fix_with_currection_current']['load_g_pas'] = False
    stages_settings['validation_sim_with_gj_no_fix_with_currection_current']['manual_MEComboInfoFile'] = stages_settings[
        'validation_sim_with_gj_no_fix_with_currection_current']['manual_MEComboInfoFile'].replace('True_Correc_iter_loadlast', 'False')

    return(stages_settings)


knl = False
if knl == True:
    partition = 'prod_knl'
    nodes = 25
    ntask_per_node = None
else:
    partition = 'prod'
    nodes = 50
    ntask_per_node = None
    cpus_per_task = 2
    circuit_to_run[circ]['bbpviz_txt'] = circuit_to_run[circ]['bbpviz_txt'].replace(
        '-knl', '')

#init_name = 'init.hoc'
init_name = '/gpfs/bbp.cscs.ch/home/amsalem/Dropbox/Blue_Brain/Experiments_Reproduction/Coupling_Coefficient/pylibs/manager_python_damus.py'
ssh_path = 'bbpv1.epfl.ch'

nice_level = 0
remove_spon_minis = False
Disable_CortoCortical = False
DisableUseDep = False
spike_replay = None
projection_path = None
reports = {}
v_clamp = {}
optogenetic_vars = []
RNGMode = 'Random123'
BS = 0  # seed
ca = -1
k = -1
Mg = -1
simulation_time = "04:00:00"  # real run time
MEComboInfoFile = None
simulation_duration = 100


hoc_lib = circuit_to_run[circ]['hoc_lib']
special_path = circuit_to_run[circ]['special_path']
bbpviz_txt = circuit_to_run[circ]['bbpviz_txt']
account = circuit_to_run[circ]['sim_account'] if 'sim_account' in circuit_to_run[circ] else 'proj2'

gjc = 0.2
stages_settings = set_stages_settings()


gids_to_test = circuit_to_run[circ]['gids_to_test']
if exp_name in ['1_extract_holding_voltage', '2_find_correct_holding']:
    gids_to_test = [gids_to_test[0]]
print(exp_name)
settings = {}
# ['validation_sim' # 'validation_sim' | 'validation_sim' | 'find_holding_current'
settings['procedure_type'] = stages_settings[exp_name]['procedure_type']
# remove_channels#'all' #'only_stoch','only_non_stoch', 'none','all'
settings['remove_channels'] = stages_settings[exp_name]['remove_channels']
settings['determanisitc_stoch'] = True  # True|False
# SP_PVBC_gjs' # PV_mc2 | Rt_RC_gjs | SP_PVBC
settings['circuit_target'] = circuit_to_run[circ]['circuit_target']
# False # True|False
settings['disable_holding'] = stages_settings[exp_name]['disable_holding']

settings['split_method'] = circuit_to_run[circ]['split_method'] if 'split_method' in circuit_to_run[circ] else None
if settings['split_method'] == None and settings['procedure_type'] == 'rm_correction':
    group_name = settings['circuit_target']
#settings['special_tag'] = '0as0p1'


if settings['procedure_type'] == 'rm_correction':
    # 'impedance_tool', 'current_injections'
    settings['rm_correction_type'] = 'impedance_tool'
    settings['rm_correction_cm'] = 0.01
    settings['rm_correction_number_of_iterations'] = 10
    settings['rm_correction_gjcs'] = [0.1, 0.2, 0.25, 0.3, 0.35, 0.5]
    simulation_time = "24:00:00"  # real run time
    RunMode = 'RunMode WholeCell'
elif settings['procedure_type'] in ['validation_sim', 'find_holding_current']:
    # '/gpfs/bbp.cscs.ch/project/proj2/simulations/Gap_Junctions/test4.hdf5' # path to h5 file with g_pas values | False
    settings['load_g_pas'] = stages_settings[exp_name]['load_g_pas']
    settings['manual_MEComboInfoFile'] = stages_settings[exp_name]['manual_MEComboInfoFile']
    settings['correction_iteration_load'] = correction_iteration_load
    settings['gjc'] = stages_settings[exp_name]['gjc']
    reports['soma_voltage'] = {'REPORT_TARGET': settings['circuit_target'], 'START_TIME': str(
        0), 'END_TIME': str(9e9), 'DT': str(0.1)}
    settings['change_MEComboInfoFile'] = None
    MEComboInfoFile = settings['change_MEComboInfoFile']
    if type(settings['change_MEComboInfoFile']) == str and (settings['manual_MEComboInfoFile'] != None):
        raise Exception('Not really make any sense')
    if type(settings['change_MEComboInfoFile']) == str and type(settings['load_g_pas']) != str:
        raise Exception('Not really make any sense')

    if settings['procedure_type'] == 'validation_sim':
        #settings['stim_num'] = 1
        #settings['stim_dur'] = 2
        #settings['stim_isi'] = 3000
        #settings['stim_amp'] = 0.0000000001
        RunMode = 'RunMode LoadBalance'

        settings['stim_num'] = stages_settings[exp_name]['stim_num']
        settings['stim_dur'] = stages_settings[exp_name]['stim_dur']
        settings['stim_isi'] = stages_settings[exp_name]['stim_isi']
        settings['stim_amp'] = stages_settings[exp_name]['stim_amp']
    if settings['procedure_type'] == 'find_holding_current':
        settings['vc_amp'] = stages_settings[exp_name]['vc_amp']

        simulation_duration = 3000
        RunMode = 'RunMode WholeCell'
        if type(settings['vc_amp']) != str:
            v_clamp[settings['vc_amp']] = [
                circuit_to_run[circ]['circuit_target']]
        print([' I am runing hoding and VClamp in the same time - you need to think about it!\n']*5)


input("I am manually changing the g_pas value!!!")
# I diable it, but will need it for a different circuit
# if settings['load_g_pas']:
#     assert 'circ19_11_2019_gjs_19_20_20' in settings['load_g_pas']
#     settings['load_g_pas'] = settings['load_g_pas'].replace("circ19_11_2019_gjs_19_20_20_new_holding", "circ19_11_2019_gjs_19_20_20")


# debug
if 'vc_amp' in settings and not os.path.isfile(settings['vc_amp']):
    raise Exception("file vc_amp does not exist", settings['vc_amp'])
if 'load_g_pas' in settings and settings['load_g_pas'] and not os.path.isfile(settings['load_g_pas']):
    raise Exception("file load_g_pas does not exist", settings['load_g_pas'])
if 'manual_MEComboInfoFile' in settings and settings['manual_MEComboInfoFile'] and not os.path.isfile(settings['manual_MEComboInfoFile']):
    raise Exception("file manual_MEComboInfoFile does not exist",
                    settings['manual_MEComboInfoFile'])


base_path = circuit_to_run[circ]['base_path']
#base_path = '/gpfs/bbp.cscs.ch/project/proj2/simulations/Gap_Junctions_v1/thalamus/circ19_04_2018/'

base_path += '/'



def submit_job(simulation_duration, optogenetic_vars, group_name, repetitions=1):
    '''

    repetitions - for the case of rm_compensation I might want to run a few repeats as it has the ability to continue

    '''
    '''TODO stop using globals'''
    if repetitions > 1:
        assert settings['procedure_type'] == 'rm_correction'

    path_for_simulations = create_directory(base_path, settings)
    path_for_simulations += f'/{group_name}/'
    # input(path_for_simulations)
    create_path_and_copy_file(path_for_simulations,
                              circuit_to_run[circ]['model_folders'])
    
    pickle.dump(settings, open(path_for_simulations + '/settings.p', 'wb'))
    if settings['split_method'] != None and settings['procedure_type'] == 'rm_correction':
        add_groups_to_user_target(path_for_simulations, group_to_cells)
        circuit_target_name = group_name
    else:
        circuit_target_name = settings['circuit_target']
        

    run_name = 'num_0'
    run_names = []
    job_name = settings['procedure_type']

    if settings['procedure_type'] == 'validation_sim':
        stim_vars, optogenetic_vars, simulation_duration = create_current_injections(
            path_for_simulations, gids_to_test)

    # for ssrun_time in range(0,simulation_duration + 60000,60000):
    f = open(path_for_simulations + '/BlueConfig_template', 'r')
    blue_out = create_blueconfig(BlueConfig_file=f, CurrentDir=path_for_simulations, BS=BS, simulation_duration=simulation_duration,
                                 run_name=run_name, ca=ca, k=k, Mg=Mg, circuit_target=circuit_target_name, decouple=Disable_CortoCortical, optogenetic_vars=optogenetic_vars,
                                 DisableUseDep=DisableUseDep, reports=reports, v_clamp=v_clamp, MEComboInfoFile=MEComboInfoFile,
                                 RunMode=RunMode, remove_spon_minis=remove_spon_minis, spike_replay=spike_replay, RNGMode=RNGMode, core_neuron=core_neuron, projection_path=projection_path)
    f = open(path_for_simulations + 'BlueConfig_' + run_name, 'w')
    if settings['disable_holding']:
        blue_out = blue_out.replace(
            'StimulusInject hypamp_mosaic', '#StimulusInject hypamp_mosaic')
    f.write(blue_out)
    f.close()

    f = open(path_for_simulations + '/launchScript_bg_template.sh', 'r')
    launch_out = create_launch_script(launchScript_file=f, hoc_lib=hoc_lib, init_name=init_name, special_path=special_path, simulation_time=simulation_time,
                                      run_name=run_name, nice_level=nice_level, nodes=nodes, ntask_per_node=ntask_per_node,cpus_per_task=cpus_per_task,
                                      bbpviz_txt=bbpviz_txt, partition=partition, job_name=job_name, core_neuron=core_neuron, account=account)
    f = open(path_for_simulations + 'launchScript_bg_' + run_name + '.sh', 'w')
    f.write(launch_out)
    f.close()

    # If folder already exist do not send it.
    if not os.path.exists(path_for_simulations + '/' + run_name):
        run_names.append('sbatch launchScript_bg_' + run_name + '.sh')
        for i in range(1, repetitions):
            run_names.append(run_names[-1])

    else:
        print('************ Job already submitted, not sure if completed **************')
    # as it is per directory I need to submit the jobs here!

    submit_jobs(run_names, path_for_simulations, MaxJobs=1,
                all_after_one=True, ssh_path=ssh_path)


if settings['procedure_type'] == 'rm_correction' and settings['split_method']:
    cells, fig0, fig1, cluster_centers_0, cluster_centers_1 = get_split_cells(circuit_path=f"{circuit_to_run[circ]['model_folders']}/BlueConfig_template", circuit_target=settings['circuit_target'],
                                                                              rm_dist=settings['split_method']['rm_dist'], n_clusters=settings['split_method']['n_clusters'])
    k_labels, kinv_labels = cells.labels.unique(), cells.labels_inv.unique()
    cells_r = cells.reset_index()
    group_to_cells = {}
    for x, row in pd.DataFrame(cells_r[['index', 'labels']].groupby('labels')['index']).iterrows():  # ugly!
        group_to_cells[row[0]] = row[1].values
    for x, row in pd.DataFrame(cells_r[['index', 'labels_inv']].groupby('labels_inv')['index']).iterrows():  # ugly!
        group_to_cells[row[0]] = row[1].values
    
    min_per_group = min([cells for cells in group_to_cells.values()])
    assert min_per_group>nodes*40, f'min cells in group {min_per_group} smaller than number of nodes, either increase group size of decresee node count'
    cells_r.to_pickle(f'{create_directory(base_path, settings)}/cells_groups.pkl')
    pickle.dump({'cluster_centers_0': cluster_centers_0, 'cluster_centers_1': cluster_centers_1},
                open(f'{create_directory(base_path, settings)}/cluster_centers.pkl', 'wb'))
    tm = 0
    for group_name in list(k_labels) + list(kinv_labels):
        submit_job(simulation_duration, optogenetic_vars,
                   group_name, repetitions=4)


else:
    submit_job(simulation_duration, optogenetic_vars,
                   group_name = '', repetitions=1)
