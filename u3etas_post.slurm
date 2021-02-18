#! /bin/bash

#SBATCH -t 0:30:00
#SBATCH -N 1
#SBATCH --mem 0
#SBATCH --ntasks-per-node=10
#SBATCH --ntasks=10
#SBATCH --mail-type=ALL
#SBATCH --mail-user=wsavran@usc.edu

######################
## INPUT PARAMETERS ##
######################

# the above '#SBATCH' lines are requred, and are supposed to start with a '#'. They must be at the beginning of the file
# the '-t hh:mm:ss' argument is the wall clock time of the job
# the '-N 7' argument specifies the number of nodes required, in this case 7
# the 'p scec' argument specifies the queue, this line can be removed if you want the default queue
# the '--mem 0' argument fixes some USC HPC weirdness and shouldn't be removed
# the '--ntasks specifies the number of tasks to be run
# the '--tasks_per_node should be set based on the memory usage of the jobs being run. the scec nodes have 64 Gb of memory'
# the last two options send email notifications to the user

#############################
## POST PROCESSING SCRIPT
#############################
# absolute paths to the pyton interpreter insure that we are using the correct distributiuon
# 

module load gcc
module load anaconda3

srun -E -l --multi-prog /project/scec_608/wsavran/git/weekly_u3etas_processing/u3_jobs.conf
