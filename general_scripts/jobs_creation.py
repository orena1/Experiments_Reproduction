# Function related to job creation

import os
import shutil
from HelpFuncs import SetCaKThresh, SetCaK, SetFacDep
from Cheetah.Template import Template
import subprocess




def crate_blueconfig(BlueConfig_file, CurrentDir, BS, simulation_duration, run_name, ca, k, Mg,
                    circuit_target='mc2_Column', decouple=False, optogenetic_vars = [], RunMode = 'RunMode LoadBalance', DisableUseDep = [], reports={}, remove_spon_minis=False,
                    spike_replay=None, other_circuit=False, v_clamp = {}):

    '''
    v_clamp example - v_clamp[voltage][target] -- v_clamp[-80][L2_PC,L5_PC]
    '''

    newF = ''
    RunBlock = 1 #I assume the RunBlock is in the start
    for line in BlueConfig_file:
        if 'CurrentDir' in line:
            newF += '      CurrentDir ' + CurrentDir+'\n'
        elif 'OutputRoot' in line:
            newF += '      OutputRoot ' + CurrentDir + '/' + run_name + '\n'
        elif 'TargetFile' in line:
            newF += '      TargetFile ' + CurrentDir + '/user.target\n'
        elif 'BaseSeed' in line:
            newF += '        BaseSeed ' + `BS` + '\n'
            if 'LFP' in reports:
                newF += '        ElectrodesPath /gpfs/bbp.cscs.ch/project/proj1/circuits/SomatosensoryCxS1-v5.r0/O1/merged_circuit\n'
        elif '#RunMode' in line:
            newF += '        ' + RunMode + '\n'
        elif 'CircuitTarget' in line:
            newF +='  CircuitTarget ' + circuit_target +'\n'
        elif 'SpikeFile' in line:
            if spike_replay==None:
                newF += '        SpikeFile ' + CurrentDir + '/inputs.dat\n'
            else:
                newF += '        SpikeFile ' + spike_replay + '\n'
        elif 'Duration' in line and RunBlock:
            newF += '         Duration ' + `simulation_duration`+'\n'
        elif 'Reports' in line:
            for report_type in reports:
                if report_type=='soma_voltage':
                    newF += Voltage_Report.replace('REPORT_TARGET',reports['soma_voltage']['REPORT_TARGET']).replace('START_TIME',reports['soma_voltage']['START_TIME']).replace('END_TIME',reports['soma_voltage']['END_TIME'])
                if report_type=='LFP':
                    newF += LFP_Report.replace('START_TIME',reports['LFP']['START_TIME']).replace('END_TIME',reports['LFP']['END_TIME']).replace('DT',reports['LFP']['DT'])
            if v_clamp != {}:
                print(v_clamp)
                for v in v_clamp:
                    for v_clamp_target in v_clamp[v]:
                        newF += SEClamptxt.replace('GID',v_clamp_target).replace('VOLTAGE',str(v))
                        newF += ReportSEClampTxt.replace('GID',v_clamp_target).replace('ASCII','Bin').replace('SEClamp_i','SEClamp_i_' + v_clamp_target)
        elif 'SponMinis' in line:
            if remove_spon_minis == False:
                newF += str(sponMinisTemplate)
        elif 'OptStim' in line:
            if  optogenetic_vars!=[]:
                newF += add_optogen(*optogenetic_vars) +'\n'
        elif 'ThreshInput' in line:
            newF += SetCaKThresh(ca, k, Mg)
        elif 'CaKa'in line:
            newF += SetCaK(ca, k, Mg)
        elif 'FacDep' in line:
            newF += SetFacDep(DisableUseDep)
        elif 'nrnPath' in line and (decouple == True or other_circuit is not False):
            if decouple ==True and other_circuit is False:
                newF +='       nrnPath /gpfs/bbp.cscs.ch/project/proj2/simulations/ThlInput/VisuInput/emptyNRN \n'
            elif decouple ==False and other_circuit is  not False:
                newF +='       nrnPath ' + other_circuit + ' \n'
            else:
                raise Exception('decouple == True and other_circuit is not False')
        else:
            newF += line
        if '}' in line:
            RunBlock = 0 #End of RunBlock
                
    return(newF)
    
    
    
    [003-005,007,011]
def create_launch_script(launchScript_file, hoc_lib, init_name, special_path, simulation_time, run_name, nice_level=0,
                         nodes=512, ntask_per_node=32, bbpviz_txt = '', partition='prod',account='proj2', job_name=''):

    if job_name =='':
        job_name = run_name
    newF = ''
    for line in launchScript_file:
        if "--output=" in line:
            newF += '#SBATCH --output=neurodamus-stdout_bg_' + run_name + '.log\n'
        elif "--job-name" in line:
            newF +='#SBATCH --job-name='+ job_name +'\n'
        elif "--nodes" in line:
            if  bbpviz_txt=='':
                newF +='#SBATCH --nodes=' +str(nodes) +'\n'
        elif "--ntasks-per-node" in line:
            if  bbpviz_txt=='':
                newF +='#SBATCH --ntasks-per-node=' +str(ntask_per_node) +'\n'
            elif bbpviz_txt!='':
                #newF +='#SBATCH --ntasks-per-node=' +str(ntask_per_node) +'\n'
                #newF +='#SBATCH --nodes=' +str(nodes) +'\n'
                #newF +='#SBATCH --exclusive \n'
                newF +='#SBATCH -n ' + str(ntask_per_node*nodes) +'\n'
                #newF +='#SBATCH --cpus-per-task=1\n'
        elif "#SBATCH --time=" in line:
            newF += "#SBATCH --time=" + simulation_time + '\n'
        elif "#SBATCH --partition=" in line:
            newF += '#SBATCH --partition=' + str(partition) + '\n'
        elif "--nice" in line and nice_level!=0:
            newF +='#SBATCH --nice=' + `nice_level`+'\n'
        elif "--error" in line:
            newF += '#SBATCH --error=neurodamus-stderr_bg_' + run_name + '.log\n'
        elif "--account" in line:
            newF += '#SBATCH --account=' + account + '\n'
        elif "--overcommit" in line:
            if bbpviz_txt=='':
                newF += line
        elif 'export HOC_LIB' in line:
            newF += 'export HOC_LIBRARY_PATH=' + hoc_lib + '\n' + bbpviz_txt
        elif 'srun' in line:
            if bbpviz_txt!='':#X fix
                newF +=  'srun -n $SLURM_JOB_NUM_NODES --ntasks-per-node=1  sudo /usr/local/bin/restartX.sh \n'
            newF += line.replace('BlueConfig','BlueConfig_' + run_name).replace('init.hoc',init_name).replace('binPath',special_path) + '\n'
        else:
                newF += line
    return(newF)


def submit_jobs(run_names, path_for_simulations, MaxJobs, all_after_one=False, ssh_path ='bbpbg2.cscs.ch'):
    '''
    This function submit the jobs to the bbpbg1
    
    Parameters
    ----------
    run_names: list of strings
               Each string in the list will be executed on bbpbg1 e.g. ['sbatch l_1.sh', 'sbatch l_2.sh']
    path_for_simulations: string
                          The path to the lauchscripts
    
    MaxJobs: int
             Maximum number of concurrent jobs
    all_after_one: True or False
                   When this var is True all the works will be executed after the first job (if MaxJobs<inf the concurrent jobs will start after the first job)
    
    
    example: submit_jobs([..], [..], 5, all_after_one=Ture)   - the first job will run and after it will be finished the max concurrent jobs will be 5
             submit_jobs([..], [..], 5, all_after_one=False)  - max concurrent jobs will be 5
             submit_jobs([..], [..], 9e9, all_after_one=True) - the first job will run and after it will be finished all other jobs will run
            
    ___
    
    
    
    '''
    BaseDir = os.getcwd()
    os.chdir(path_for_simulations)
    if os.path.exists('mcomplex.dat')==False and all_after_one==False:
        raise Exception("Not multisplit data and all_after_one is set to False")
    NumOfJobs = 0
    lastDep = 0
    JobsList = []
    for l in run_names:
        if NumOfJobs<MaxJobs:
            if all_after_one==True and NumOfJobs>0:
                SendTxt = l.split(' ')[0] + ' --dependency=afterany:' + JobsList[0] + ' ' +l.split(' ')[1]
                print 'ssh ' + ssh_path + ' ' + SendTxt
                ssh = subprocess.Popen(['ssh', ssh_path,'cd ' + path_for_simulations +';', SendTxt],shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

            else:
                print 'ssh '+ssh_path + ' ' + l
                ssh = subprocess.Popen(['ssh', ssh_path,'cd ' + path_for_simulations +';', l],shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

        else:
            SendTxt = l.split(' ')[0] + ' --dependency=afterany:' + JobsList[lastDep] + ' ' +l.split(' ')[1]
            print 'ssh ' + ssh_path + ' ' + SendTxt
            
            ssh = subprocess.Popen(['ssh', ssh_path,'cd ' + path_for_simulations +';', SendTxt],shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            
            lastDep+=1
        result = ssh.stdout.readlines()
        erre = ssh.stderr.readlines()
        print '--'
        print result
        print erre
        JobsList.append(result[0].split()[-1])
        NumOfJobs+=1
    
    os.chdir(BaseDir)
    print path_for_simulations
    print '-------------'
    return(JobsList)



Voltage_Report = 'Report soma\n'\
'{\n'\
'        Target REPORT_TARGET\n'\
'          Type compartment\n'\
'      ReportOn v\n'\
'          Unit mV\n'\
'        Format Bin\n'\
'            Dt 0.1\n'\
'     StartTime START_TIME\n'\
'       EndTime END_TIME\n'\
'}\n\n'



LFP_Report = 'Report AllCompartmentsMembrane\n'\
'{\n'\
'        Target AllCompartments\n'\
'          Type Summation\n'\
'      ReportOn i_membrane\n'\
'          Unit nA\n'\
'        Format Bin\n'\
'            Dt DT\n'\
'     StartTime START_TIME\n'\
'       EndTime END_TIME\n'\
'}\n\n'



SponMinisTemplate = """
Connection ConL6Exc-Uni
{
        Source Excitatory
        Destination Layer6
        Weight 1.0
        SpontMinis 0.04
}

Connection ConL5Exc-Uni
{
        Source Excitatory
        Destination Layer5
        Weight 1.0
        SpontMinis 0.067
}

Connection ConL4Exc-Uni
{
        Source Excitatory
        Destination Layer4
        Weight 1.0
        SpontMinis 0.072
}

Connection ConL3Exc-Uni
{
        Source Excitatory
        Destination Layer3
        Weight 1.0
        SpontMinis 0.122
}

Connection ConL2Exc-Uni
{
        Source Excitatory
        Destination Layer2
        Weight 1.0
        SpontMinis 0.26
}

Connection ConL1Exc-Uni
{
        Source Excitatory
        Destination Layer1
        Weight 1.0
        SpontMinis 0.63
}



Connection ConInh-Uni
{
        Source Inhibitory
        Destination Mosaic
        Weight 1.0
  SpontMinis 0.012
}"""


sponMinisTemplate = Template(SponMinisTemplate)

SEClamptxt = 'Stimulus voltage_clamp\n ' \
'{\n' \
'        Mode Current\n' \
'        Pattern SEClamp\n' \
'        Delay 0\n' \
'        Duration 100000000\n' \
'        Voltage VOLTAGE\n' \
'}\n'\
'\n'\
'\n'\
'StimulusInject voltage_clamps\n'\
'{\n'\
'        Stimulus voltage_clamp\n'\
'        Target GID\n'\
'}\n\n'



ReportSEClampTxt = 'Report SEClamp_i\n'\
'{\n'\
'        Target GID\n'\
'          Type Summation\n'\
'      ReportOn SEClamp.i\n'\
'          Unit nA\n'\
'        Format ASCII\n'\
'            Dt 0.1\n'\
'     StartTime 0\n'\
'       EndTime 250000\n'\
'}\n\n'


