
def create_sync_thalamic_spikes(pulses_fr, fr_per_axon, stim_start_time, stim_end_time, seed):
    print('creating spike times - START')
    gaussian_std = 2 #ms
    interv = 1.0/pulses_fr*1000
    thalamic_rnd = np.random.RandomState(seed)
    to_add = [stim_start_time]
    while 1:
        rnd = -math.log(1.0 - thalamic_rnd.uniform(0,1)) / (1.0/interv)
        if rnd + to_add[-1] > stim_end_time:
            break
        else:
            to_add.append(rnd + to_add[-1])
    main_pulses = to_add[1:]
    fr_per_bin, bin_times = np.histogram(main_pulses,bins=np.arange(0,stim_end_time+100,0.025))
    fr_per_bin = fr_per_bin.astype(float)
    filtered_fr = scipy.ndimage.filters.gaussian_filter(fr_per_bin, gaussian_std/0.025)


    axons_fr_relative_to_bursts = fr_per_axon/pulses_fr
    sp_per_axon_gid = {}
    for axon_gid in AxoGidToXY.keys():
        sp_per_axon_gid[axon_gid] = np.nonzero(thalamic_rnd.binomial(1, p=filtered_fr*axons_fr_relative_to_bursts))[0]*0.025
    print('creating spike times - END')
    return(sp_per_axon_gid)

def create_sync_thalamic_spikes_bundles(pulses_fr, fr_per_axon, stim_start_time, stim_end_time, bundle_size, seed):
    if bundle_size == 9e9: # not bundles all working at once.
        return(create_sync_thalamic_spikes(pulses_fr, fr_per_axon, stim_start_time, stim_end_time, seed))
    
    print('creating spike times - START')
    gaussian_std = 2 #ms
    interv = 1.0/pulses_fr*1000
    axons_gids = AxoGidToXY.keys()
    sp_per_axon_gid = {}
    while len(axons_gids)>0:
        
        thalamic_rnd = np.random.RandomState(seed + len(axons_gids))
        to_add = [stim_start_time]
        while 1:
            rnd = -math.log(1.0 - thalamic_rnd.uniform(0,1)) / (1.0/interv)
            if rnd + to_add[-1] > stim_end_time:
                break
            else:
                to_add.append(rnd + to_add[-1])
        main_pulses = to_add[1:]
        fr_per_bin, bin_times = np.histogram(main_pulses,bins=np.arange(0,stim_end_time+100,0.025))
        fr_per_bin = fr_per_bin.astype(float)
        filtered_fr = scipy.ndimage.filters.gaussian_filter(fr_per_bin, gaussian_std/0.025)
        axons_fr_relative_to_bursts = fr_per_axon/pulses_fr
        
        if bundle_size<len(axons_gids):
            axons_gids_selected  =  thalamic_rnd.choice(axons_gids,bundle_size,replace=False)
        else:
            axons_gids_selected = axons_gids
        axons_gids = list(set(axons_gids) - set(axons_gids_selected))


        for axon_gid in axons_gids_selected:
            if axon_gid in sp_per_axon_gid: raise Exception('Debug!!!')
            sp_per_axon_gid[axon_gid] = np.nonzero(thalamic_rnd.binomial(1, p=filtered_fr*axons_fr_relative_to_bursts))[0]*0.025
    print('creating spike times - END')
    return(sp_per_axon_gid)



pulses_fr = 5 #hz, the firing rate of each each bundle
fr = 5 # hz, the firing rate of each axon, this does not have to be the same as pulses_fr
stim_start_time = 1000
bundle_size = 10 # how many axons in one bundle?
BS = 10 #seed
simulation_duration = ?


####
##AxoGidToXY is the dic with key = gid and value is x and y location, but the functions only needs the gid list
###




# I scaned those values, and found that I get the highest fano factor for those values. 

create_sync_thalamic_spikes_bundles(pulses_fr,  fr, stim_start_time, simulation_duration-250, bundle_size = bundle_size, seed=BS )



