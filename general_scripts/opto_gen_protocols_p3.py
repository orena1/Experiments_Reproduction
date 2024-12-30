#Optogenetic like function, to insert ChR like input to cells
#Created by Oren Amsalem oren.a4@gmail.com

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
