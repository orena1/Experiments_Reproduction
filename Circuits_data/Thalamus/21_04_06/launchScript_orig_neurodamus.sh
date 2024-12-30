#!/bin/bash -l
#SBATCH --partition=prod
#SBATCH --exclusive
#SBATCH --nodes=15
#SBATCH --cpus-per-task=2
#SBATCH -C "cpu"
#SBATCH --time=2:00:00
#SBATCH --output=neurodamus-stdout.log
#SBATCH --error=neurodamus-stderr.log
#SBATCH --account=proj55



#### SLURM Information
echo "SLURM information...
      partition: $MPIRUN_PARTITION
      number of nodes: $SLURM_JOB_NUM_NODES
      node id allocated: $SLURM_JOB_NODELIST
      number tasks per node: $SLURM_TASKS_PER_NODE
      directory from which sbatch was invoked: $SLURM_SUBMIT_DIR
      slurm memory binding: $SLURM_MEM_BIND
      slurm cpu binding: $SLURM_CPU_BIND
      job dependency: $SLURM_JOB_DEPENDENCY"

#### MPI to physical mapping
echo "
Physical mapping information...
You have been allocated: $SLURM_JOB_NODELIST"


#======JOB EXECUTION=====

#module load archive/2021-05
#module load neurodamus-thalamus/1.4-3.2.2
#module load py-neurodamus


#module load unstable neurodamus-thalamus/1.4-3.3.3
#module load /gpfs/bbp.cscs.ch/project/proj82/home/weji/software/modules/tcl/linux-rhel7-x86_64/py-neurodamus/develop-wrfaz
#srun dplace special BlueConfig -mpi -python $NEURODAMUS_PYTHON/init.py

module load unstable neurodamus-thalamus/1.4-3.3.3
module use -a /gpfs/bbp.cscs.ch/project/proj82/home/weji/software/modules/tcl/linux-rhel7-x86_64
module load py-neurodamus/develop-wrfaz7
srun dplace special BlueConfig -mpi -python $NEURODAMUS_PYTHON/init.py
