#!/bin/bash -l
#SBATCH --job-name="neurodamus-run"
#SBATCH --partition=prod
#SBATCH --nodes=512
#SBATCH --ntasks-per-node=32
#SBATCH --overcommit
#SBATCH --time=65:00:00
##SBATCH --mail-user=oren.amsalem@epfl.ch
#SBATCH --mail-type=ALL
#SBATCH --output=neurodamus-stdout_bg_200.log
#SBATCH --error=neurodamus-stderr_bg_200.log
#SBATCH --account=proj2
#SBATCH --nice=0

echo "StartTime" `date +"%d-%m-%y-%T"`

#### SLURM Information
echo "SLURM information...
      partition: $MPIRUN_PARTITION
      number of nodes: $SLURM_JOB_NUM_NODES
      node id allocated: $SLURM_JOB_NODELIST
      number tasks per node: $SLURM_TASKS_PER_NODE
      directory from which sbatch was invoked: $SLURM_SUBMIT_DIR
      slurm memory binding: $SLURM_MEM_BIND
      slurm cpu binding: $SLURM_CPU_BIND
      job dependency: $SLURM_JOB_DEPENDENCY
      job id: $SBATCH_JOBID"



#### MPI to physical mapping
echo "
Physical mapping information...
You have been allocated: $SLURM_JOB_NODELIST
Physical Mapping from slurm nodes to BG/Q compute (CNK) nodes, midplanes to BG/Q
I/O node racks and I/O nodes (8 I/O nodes per midplane):
 SLURM_NodeName=bgq0000 CNK_RackMidplane_ID=R00-M0 IORACK_ID=Q04-I0 IONODES=bbpio001-bbpio008
 SLURM_NodeName=bgq0001 CNK_RackMidplane_ID=R00-M1 IORACK_ID=Q04-I1 IONODES=bbpio009-bbpio016
 SLURM_NodeName=bgq0010 CNK_RackMidplane_ID=R01-M0 IORACK_ID=Q04-I2 IONODES=bbpio017-bbpio024
 SLURM_NodeName=bgq0011 CNK_RackMidplane_ID=R01-M1 IORACK_ID=Q04-I3 IONODES=bbpio025-bbpio032
 SLURM_NodeName=bgq1000 CNK_RackMidplane_ID=R02-M0 IORACK_ID=Q04-I4 IONODES=bbpio033-bbpio040
 SLURM_NodeName=bgq1001 CNK_RackMidplane_ID=R02-M1 IORACK_ID=Q04-I5 IONODES=bbpio041-bbpio048
 SLURM_NodeName=bgq1009 CNK_RackMidplane_ID=R03-M0 IORACK_ID=Q04-I6 IONODES=bbpio049-bbpio056
 SLURM_NodeName=bgq1011 CNK_RackMidplane_ID=R03-M1 IORACK_ID=Q04-I7 IONODES=bbpio057-bbpio064"

#======START=====
# Place where you load required modules

# workaround
sleep 5
module load slurm
module load numpy
#
echo "Print current shell limits :"
echo
ulimit -a
echo "===== Beginning job execution ======"
echo


#======JOB EXECUTION=====


module purge
module load neurodamus/hippocampus

srun  special -mpi  -c "{strdef configFile configFile=\"BlueConfig_num_0\"}" -NFRAME 256 $HOC_LIBRARY_PATH/init.hoc
