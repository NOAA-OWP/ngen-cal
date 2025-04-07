#!/bin/bash
# ------------------------------------------------
# This script automates the entire calibration process
# from generating input to executing calibration and validation runs.
# User needs to specify basin, workdir and scriptdir.

# workdir is the concatenation of entries for options main_dir, objective_function,  
# optimization_algorithm, and model specified in input.config:
# workdir=main_dir/objective_function_optimization_algorithm/model  

# Author: Xia Feng
# ------------------------------------------------

# Activate virtual environment
source venv-cal/bin/activate 
python=`which python3`

# Working Directory 
basin='01010101'
workdir='working_dir' 

# Create input data and files 
pyscript1='scriptdir/createInput/src/create_input.py'
config_file_input='scriptdir/python/createInput/configs/input.config'
echo 'Creating Input Data and Files'
$python $pyscript1 $config_file_input 
echo 'Input Data and Files are Generated'

# Execute calibration run
pyscript2='scriptdir/runCalibValid/calibration.py'
config_file_calib=$workdir$basin'/Input/'$basin'_config_calib.yaml'
echo 'Running Calibration Simulation'
$python $pyscript2 $config_file_calib >>'calib_run_out'
echo 'Calibration Run Is Completed'

# Execute validation run
pyscript3='scriptdir/runCalibValid/validation.py'
config_file_control=$workdir$basin'/Output/Validation_Run/'$basin'_config_valid_control.yaml'
config_file_best=$workdir$basin'/Output/Validation_Run/'$basin'_config_valid_best.yaml'
config_file_valid_run=( $config_file_control $config_file_best )
run_type=( 'control' 'best' )
i=0
while [ $i -le 1 ]
do
    echo 'Running Validation' ${run_type[$i]^} 'Simulation'
    $python $pyscript3 ${config_file_valid_run[$i]} >>'valid_run_out'
    i=$(($i+1))
done
echo 'Validation Run Is Completed'
