# Function related to job creation

import os
import shutil
from HelpFuncs import SetCaKThresh, SetCaK, SetFacDep
from Cheetah.Template import Template
import subprocess




def crate_blueconfig(BlueConfig_file, CurrentDir, BS, simulation_duration, run_name, ca, k, Mg,
                    optogenetic_vars = [], RunMode = 'RunMode LoadBalance', DisableUseDep = [], report=None, remove_spon_minis=False ):

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
        elif '#RunMode' in line:
            newF += '        ' + RunMode + '\n'
        elif 'SpikeFile' in line:
            newF += '        SpikeFile ' + CurrentDir + '/inputs.dat\n'
        elif 'Duration' in line and RunBlock:
            newF += '         Duration ' + `simulation_duration`+'\n'
        elif 'Reports' in line:
            if report==None:
                newF +='\n'
            else:
                newF += ReportTxt.replace('REPORT_TARGET',report['REPORT_TARGET']).replace('START_TIME',report['START_TIME']).replace('END_TIME',report['END_TIME'])
        elif 'SponMinis' in line:
            if remove_spon_minis == False:
                newF += str(sponMinisTemplate)
        elif 'OptStim' in line and optogenetic_vars!=[]:
            newF += add_optogen(*optogenetic_vars) +'\n'
        elif 'ThreshInput' in line:
            newF += SetCaKThresh(ca, k, Mg)
        elif 'CaKa'in line:
            newF += SetCaK(ca, k, Mg)
        elif 'FacDep' in line:
            newF += SetFacDep(DisableUseDep)
        else:
            newF += line
        if '}' in line:
            RunBlock = 0 #End of RunBlock
                
    return(newF)
    
    
    
    
def create_launch_script(launchScript_file, hoc_lib, init_name, special_path, simulation_time, run_name, nice_level=0):

    newF = ''
    for line in launchScript_file:
        if "--output=" in line:
                newF += '#SBATCH --output=neurodamus-stdout_bg_' + run_name + '.log\n'
        elif "--job-name" in line:
                newF +='#SBATCH --job-name='+ run_name +'\n'
        elif "#SBATCH --time=" in line:
                newF += "#SBATCH --time=" + simulation_time + '\n'
        elif "--nice" in line and nice_level!=0:
                newF +='#SBATCH --nice=' + `nice_level`+'\n'
        elif "--error" in line:
                newF += '#SBATCH --error=neurodamus-stderr_bg_' + run_name + '.log\n'
        elif 'export HOC_LIB' in line:
                newF += 'export HOC_LIBRARY_PATH=' + hoc_lib + '\n'
        elif 'srun' in line:
                newF += line.replace('BlueConfig','BlueConfig_' + run_name).replace('init.hoc',init_name).replace('binPath',special_path) + '\n'
        else:
                newF += line
    return(newF)


def submit_jobs(run_names, path_for_simulations, MaxJobs, all_after_one=False):
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
    if os.path.exists('cx_16384.dat')==False and all_after_one==False:
        raise Exception("Not multisplit data and all_after_one is set to False")
    NumOfJobs = 0
    lastDep = 0
    JobsList = []
    for l in run_names:
        if NumOfJobs<MaxJobs:
            if all_after_one==True and NumOfJobs>0:
                SendTxt = l.split(' ')[0] + ' --dependency=afterany:' + JobsList[0] + ' ' +l.split(' ')[1]
                print 'ssh bbpbg1.cscs.ch ' + SendTxt
                ssh = subprocess.Popen(['ssh', 'bbpbg1.cscs.ch','cd ' + path_for_simulations +';', SendTxt],shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

            else:
                print 'ssh bbpbg1.cscs.ch ' + l
                ssh = subprocess.Popen(['ssh', 'bbpbg1.cscs.ch','cd ' + path_for_simulations +';', l],shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

        else:
            SendTxt = l.split(' ')[0] + ' --dependency=afterany:' + JobsList[lastDep] + ' ' +l.split(' ')[1]
            print 'ssh bbpbg1.cscs.ch' + SendTxt
            
            ssh = subprocess.Popen(['ssh', 'bbpbg1.cscs.ch','cd ' + path_for_simulations +';', SendTxt],shell=False,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            
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



ReportTxt = 'Report soma\n'\
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
