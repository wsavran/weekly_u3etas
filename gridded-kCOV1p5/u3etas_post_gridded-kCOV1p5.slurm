#! /bin/bash

#SBATCH --time=2:00:00
#SBATCH --nodes=1
#SBATCH --ntasks-per-node=20

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

od=$1
sm="/project/scec_608/wsavran/git/weekly_u3etas_processing/gridded-kCOV1p5/2020_07_13-weekly-1986-present-gridded-kCOV1.5_manifest.txt"
n=$(cat $sm | wc -l)

# Process simulations
for (( i=0; i<$n; i++ ));
do
    srun --exclusive --cpus-per-task=1 --ntasks=1 /project/scec_608/wsavran/envs/csep-dev/bin/python /project/scec_608/wsavran/git/weekly_u3etas_processing/u3etas_post_processing.py $i $sm $od & 
done
wait
