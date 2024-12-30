# helper function. create new usergroups in user.target
def add_to_user_target(gids, target_name, path_for_simulations):
    for l in open(path_for_simulations + 'user.target','r'):
        if 'Target Cell ' + target_name + '\n{\n' in l:
            _ = raw_input('Target already exist, will not readd it ok?')
            return()
    gids = np.sort(gids).astype(int)
    f = open(path_for_simulations + 'user.target','a')
    f.write('Target Cell ' + target_name + '\n{\n')
    [f.write('a' + str(gid) + ' ' ) for gid in gids];
    f.write('\n}\n\n')
    f.close()
    



####
### This function create cell groups, this is so that we can create a different ChR activation for each group
####
def create_groups(spatial_data, dist_function, neuron_type, center_point = [344.766, 1038.23, 602.03], select_seed = 4): #move to helper functions
    #dist_function = 'xz_radius_y_step'
    '''
    This function should get:

    for case inwhich dist_function == 'r3'
    spatial_data  = {'group_name':{'distance_start':x ,'distance_end':x1 }}

    for case inwhich dist_function == 'x_radius_y_step'
    '''

    Circ  = bluepy.Circuit(generalConfigPath)
    gids_in_target = list(Circ.targets.targets[neuron_type].resolve_contents_gids())

    gids_per_group = {}
    cells_locations = pickle.load(open('/gpfs/bbp.cscs.ch/project/proj2/simulations/mc2_Col_v5_gid_to_xyz.p','r'))
    cells_gids = [gid for gid in cells_locations.keys() if gid in gids_in_target]
    cells_locations = np.array([cells_locations[gid] for gid in cells_gids])

    selsect_rnd = np.random.RandomState(select_seed)

    #     if dist_function == 'r3':
    #         r3_distances = scipy.spatial.distance.euclidean(center_point, cells_locations)
    #         last_r3_distance = 0
    #         for group_name in spatial_data:
    #             gids_per_group[group_name] =  cells_gids[np.argwhere(spatial_data[group_name]['distance_end']  - r3_distances>=spatial_data[group_name]['distance_start'])]

    if dist_function == 'xz_radius_y_step':

        xz_distances = cdist([[center_point[0],center_point[2]]]  , zip(cells_locations[:,0],cells_locations[:,2]))[0]
        y_distances =  cells_locations[:,1]
        for group_name in spatial_data:

            data = spatial_data[group_name]
            y_distances_in_xz_rad =  np.array([y_distances[i[0]] for i in np.argwhere((data['xz_radius_end']> xz_distances) &  (xz_distances >= data['xz_radius_start']))])
            cells_gids_in_xz_rad = np.array([cells_gids[i[0]] for i in np.argwhere((data['xz_radius_end']> xz_distances) &  (xz_distances >= data['xz_radius_start']))])


            gids_per_group[group_name] = [cells_gids_in_xz_rad[i[0]] for i in np.argwhere((data['y_step_end'] > y_distances_in_xz_rad) & (y_distances_in_xz_rad >= data['y_step_start']))]
            gids_per_group[group_name] = selsect_rnd.choice(gids_per_group[group_name], int(round(len(gids_per_group[group_name])*spatial_data[group_name]['cell_percent'] )), replace=False)
            add_to_user_target(gids_per_group[group_name], group_name, path_for_simulations)

    return(gids_per_group)


## example use
## x,z is from 0-200 and 200-9e9
## y is in the groups [[1767.937, 1916.8004], [1415, 1767.92], [1225.438, 1414.999], [700.38, 1225.4], [ 0.0, 700.365]]
## Eventually we get this groups. 
## activation variable correspond to the amount of ChR activation in each group and probability of neurons that will have ChR
## for example -  [0.7,100] will mean that 70% of the neurons will be activated with 100 (this could be 100% relative to baseline of 100 nA... depending of the decision.



base_activation = 400
ba  = base_activation
activations = [[0.7,ba * 1], [0.65,ba*0.90], [0.60,ba*0.80], [0.12,ba*0.70], [0.02,ba*0.20],
              [0.20,ba*0.50],  [0.15,ba*0.40], [0.08,ba*0.30], [0.02,ba*0.20]  , [0.01,ba*0.5]]

spatial_data = {}
for i in [[0,200],[200,9e9]]:
    for layer in [[1767.937, 1916.8004], [1415, 1767.92], [1225.438, 1414.999], [700.38, 1225.4], [ 0.0, 700.365]]:
        spatial_data['group' + str(ind)] = {'xz_radius_start':i[0],'xz_radius_end':i[1],'y_step_start':layer[0],'y_step_end':layer[1] \
                                    ,'cell_percent':activations[ind][0],'power':activations[ind][1]}
        ind+=1

create_groups(spatial_data, 'xz_radius_y_step', neuron_type = 'PV_FS')



# now we create this variable 
var = 0.000001 #variability in the pulse.
pulse_width = 2.5 # pulse length
freq = 40 # number of pulses in a second
dur = 3000 # the duration of the stimuli (3000 will mean [when freq =40] that we will inject 40*3 pulses
opto_gen_stimstart = 1000 # the time to start in injecting the pulses


stim_vars = {group_name:[{'amp':spatial_data[group_name]['power'],'start':opto_gen_stimstart,'dur':dur, 'var':amp*var, 'pulse_width': pulse_width , 'freq': freq}] for group_name in spatial_data}
morphs = spatial_data.keys()
optogenetic_vars=['pulse_train', morphs, stim_vars]


# optogenetic_vars goes into this function
txt = add_optogen(*optogenetic_vars)
#add txt to blueconfig 




from __future__ import division
from Cheetah.Template import Template


template_Current = """
Stimulus ChR2_Current_$N
{

              Mode Current
           Pattern Noise
       MeanPercent $k_inj
          Variance $var
             Delay $delay
          Duration $dur
}

StimulusInject ChR2_Current_$N
{
        Stimulus ChR2_Current_$N
        Target $chr2_target
}"""
template_current = Template(template_Current)




template_RelativeLinear = """
Stimulus ChR2_RelativeLinear_$N
{

              Mode Current
           Pattern RelativeLinear
       PercentStart $perc_start
       PercentEnd   $perc_end
             Delay $delay
          Duration $dur
}

StimulusInject ChR2_RelativeLinear_$N
{
        Stimulus ChR2_RelativeLinear_$N
        Target $chr2_target
}"""
template_relativeLinear = Template(template_RelativeLinear)



''' This is what I can use for the pulse and it will not take much memory, as it is only a current injection!!!
templateDefSSA = """
Stimulus ChR2_ThresholdInh_$N
{

              Mode Current
           Pattern RelativeLinear
       PercentStart $k_inj
             Delay $delay
          Duration $dur
}

StimulusInject ChR2_ThresholdIntoInh_$N
{
        Stimulus ChR2_ThresholdInh_$N
        Target $chr2_target
}"""
templateSSA = Template(templateDefSSA)

'''



def add_optogen(stim_type, morph_list, stim_vars_dic):
    ''' The code will add a current injection to the cells which will imitate channel rodopshin injections
    Parameters
    ----------
    stim_type  :str
                The type of current injectio protocol
                current_injections - this will create current injections as set in the stim_vars

    morph_list :list of strings
                A list of morphological type (or cell groups) to which the stimuli will be injected.
                
    stim_vars_dic  :dictionary 
                    The vals of the stimuli for each morh type, per stim_type
                    for stim_type == 'current_injections'
                    stim_vars[cell_type] should be a list when each val in the list is a dic = {'amp': the amplitude (in percent of threshold), 
                                                                                                'start': the time of the start of the stimulus, 'dur': the duration of the stimulus}
                                                                                                
                    for stim_type == 'ramp_current_injections':
                    stim_vars[cell_type] = {'start_amp': the start amplitude (in percent of threshold), 'end_amp':the end amplitude (in percent of threshold)
                                            'start': the time of the start of the stimulus, 'dur': the duration of the stimulus}
                    for stim_type == 'pulse_train':
                        NEED to write.

    Returns
    -------
    str_chunk : string
                A string to be added to the BlueConfig which contains the stimulus

    Examples
    --------
    >>> morphs = ['L2_LBC','L4_NBC']
    >>> stim_vars = {'L2_LBC':[{'amp':0.5,'start':100,'dur':100},{'amp':0.5,'start':400,'dur':100},{'amp':0.5,'start':900,'dur':100}],
                        'L4_NBC':[{'amp':0.5,'start':100,'dur':100},{'amp':0.5,'start':400,'dur':100},{'amp':0.5,'start':900,'dur':100}]}
    >>> out = add_optogen('current_injections', morphs, stim_vars)

    '''

    str_chunk = ''
    if stim_type == 'current_injections':
        template = template_current
        for cell_number, cell_type in enumerate(morph_list):
            for stim_number, stim_vars in enumerate(stim_vars_dic[cell_type]):
                template.N           = cell_number*1000+stim_number
                template.chr2_target = cell_type
                template.k_inj       = stim_vars['amp']
                template.delay       = stim_vars['start']
                template.dur         = stim_vars['dur']
                template.var         = stim_vars['var']
                str_chunk           += str(template)

    if stim_type == 'ramp_current_injections':
        template = template_relativeLinear
        for cell_number, cell_type in enumerate(morph_list):
            for stim_number, stim_vars in enumerate(stim_vars_dic[cell_type]):
                template.N           = cell_number*1000+stim_number
                template.chr2_target = cell_type
                template.perc_start  = stim_vars['amp_start']
                template.perc_end    = stim_vars['amp_end']
                template.delay       = stim_vars['start']
                template.dur         = stim_vars['dur']
                str_chunk           += str(template) 
    
    if stim_type == 'pulse_train':
        template = template_current
        for cell_number, cell_type in enumerate(morph_list):
            for stim_number, stim_vars in enumerate(stim_vars_dic[cell_type]):
                if stim_vars['freq']==0: continue# do not add to str_chunk if freq==0
            
                next_stim = stim_vars['start']
                pulse_num = 0
                while next_stim < stim_vars['start'] + stim_vars['dur']:
                    template.N           = cell_number*100000+stim_number*1000 + pulse_num
                    template.chr2_target = cell_type
                    template.k_inj       = stim_vars['amp']
                    template.delay       = next_stim 
                    template.dur         = stim_vars['pulse_width']
                    template.var         = stim_vars['var']
                    str_chunk           += str(template)
                    
                    next_stim = next_stim + 1000/stim_vars['freq']
                    pulse_num+=1
    return(str_chunk)


