#!/usr/bin/env python
#from utils.objectives import custom
import glob
import subprocess
import shutil
import os
import pandas as pd
#import geopandas as gpd
#import netCDF4 as nc
from math import log

from configuration import Configuration
from meta import CalibrationMeta

def objective_func(simulated_hydrograph_file, observed_hydrograph, eval_range=None):
    simulated_hydrograph = pd.read_csv(simulated_hydrograph_file, header=None, usecols=[1,2], names=['time', 'flow'])
    simulated_hydrograph['time'] /= 86400 #partial day
    simulated_hydrograph['time'] += hydrograph_reference_date #Julian date from reference
    simulated_hydrograph['time'] = pd.to_datetime(simulated_hydrograph['time'], utc=True, unit='D', origin='julian').dt.round('1s')
    simulated_hydrograph.drop_duplicates('time', keep='last', inplace=True)
    simulated_hydrograph.set_index('time', inplace=True)
    #Join the data where the indicies overlap
    #print( simulated_hydrograph )
    #print( observed_hydrograph )
    df = pd.merge(simulated_hydrograph, observed_hydrograph, left_index=True, right_index=True)
    #print( df)
    if eval_range:
        df = df.loc[eval_range[0]:eval_range[1]]
    #print( df )
    #Evaluate custom objective function providing simulated, observed series
    return custom(df['flow'], df['Discharge_cms'])



def main(config_file):
    """
        We need to 'read' the configuration of the model we want to calibrate
    """

    config = Configuration(config_file)

    """
        It might make the most sense to link static/parameter info independently from model runtime such as start/end times
    """
    #This is the range of the hydrograph dates to run the objective function over
    evaluation_range = ('2011-08-05 12:00:00', '2011-08-08 00:00:00')

    """
    This was initially designed for a single basin calibration, should generalize for multiple
    """
    #gage id correspoinding to outlet_element_id
    usgs =  '02146300' #FIXME read from xwalk

    """
        Need to connect the calibrator to the output data from the binary, done here via files
    """
    #This is catchment specific (The nexus output of the catchment is what is required here)
    hydrograph_output_file = os.path.join(config.workdir, 'state.nc.{}.txt'.format(outlet_element_id) )
    #hydrograph_output_file = '/gscratch/rsteinke/runs/sugar_creek/2011-07-30-limited-regions/state.nc.7462.txt'
    """
        Need to get observed hydrograph to evaluate against
    """


    print("Starting calib")

    """
    Should input a set of catchments we want to calibrate???
    #FIXME use json input file defining these catchments
    """

    calibration_catchments = []

    """
    Build a dataframe of calibration parameters
    """
    #FIXME, NGen Calibration not implemented, this construct based on other code, may or may not be useful to implement
    data = NGenCalibration(config, calibration_catchments)

    """
    At this point the NGenCalibration object contains the catchments and all their properties that are going to be calibrated,
    grouped by the respective calibration parameters defined in ???hypy/formulation.py???
    The next steps require the initial DDS vector, which is each parameter, and its initial value.
    We build this vector from the identified classes then read the min/max from the user provided tables for these classes,
    and set the initial value to be in the middle.
    """

    """
    TODO calibrate each "catcment" independely, but there may be something interesting in grouping various formulation params
    into a single variable vector and calibrating a set of heterogenous formultions...
    """

    #TODO move most of this to utils module
    ngen_bin = "ngen"
    ngen_args = "{FIXME}".format(confif_file)

    meta = CalibraitonMeta(config, workdir, ngen_bin, ngen_args)
    print("Running initial simulation")
    print(ngen_cmd)

    start_iteration = 0
    #run NGEN here on initial parameters if needed
    ngen_log = open(os.path.join(config.workdir, 'ngen_calibration_log'), 'a')
    if config.args.restart:
        """
        FIXME there are some non-ngen specific details here that need to align to NGEN, such as states (ngen output)
        """
        #Restarting means we don't have to do this...find a clean way to convey this as long as an output file
        #exists for a previous time.  This script renames state.nc.*.txt to state.nc.*.txt_<i>
        #where i is the iteration, so if an _i exists, and a state.nc.*.txt exists, this file is the i+1 state
        #and we can restart from there.
        states = glob.glob(os.path.join(config.workdir, 'state.nc.{}.txt_*'.format(outlet_element_id)))
        if states:
            #FIXME just read from log and maybe verify...
            start_iteration = sorted( [ int(name.split('_')[-1]) for name in states ] )[-1]
            #last_evaluated = os.path.join(config.workdir, 'state.nc.{}.txt_{}'.format(outlet_element_id, start_iteration))
            #I don't think we can use next_eval, becuase we can't gaurantee the run is complete...will have to restart it to be ensure
            #next_eval = os.path.join(config.workdir, 'state.nc.{}.txt'.format(outlet_element_id))
            #FIXME file should always exist in this case, but what happens if it doesnt???
            last_iteration, best_params, best_score = read_param_log_file()
            """
            with open(os.path.join(config.workdir, 'best_params.log'), 'r') as param_log:
                best_params = int(param_log.readline())
                best_score = float(param_log.readline())
            """
            if last_iteration != start_iteration:
                print("ERROR: best_params.log iteration doesn't match output file iteration number for restart")
                os._exit(1)
            #We will start at the next iteration that hasn't been completed
            start_iteration += 1
            #It is possible another run has finished but hasn't been evaluated.
            #If the generated state file exists, and was created/modified after the last evaluated,
            #then its safe to assume  we can start from there
            #TODO read superfile, calculate how many entrys should be in state and verify that run completed.
            """
            next_eval = os.path.join(config.workdir, 'state.nc.{}.txt'.format(outlet_element_id))
            if os.path.isfile( next_eval ):
                if os.path.getmtime(next_eval) > os.path.getmtime(last_evaluated):
                    start_iteration += 1 #TODO this tells us that we have a new output file, is it guaranteed complete?
                else:
                    #Just continue with the next iteration of the DDS search...
                    #need to compute next_eval
                    #subprocess.check_call(ngen_cmd, stdout=adhydr_log, shell=True) #FIXME clean up this logic
                    #best_score = objective_func(hydrograph_output_file, observed_df, evaluation_range)
                    #best_params = 0
                    #write_param_log_file(best_params, best_score)
                    pass
            else:
                #We have a prior state, but not the next one.  Recompute the score/evalute from this last one and continue
                #Evaluate initial score....FIXME Reading from the log should be enough...just need to verify log iteration is same as start_iteration
                #best_score = objective_func(last_evaluated, observed_df, evaluation_range)
                #best_params = start_iteration - 1
                #FIXME file should always exist in this case, but what happens if it doesnt???
                with open(os.path.join(config.workdir, 'best_params.log'), 'r') as param_log:
                    best_params = int(param_log.readline())
                    best_score = float(param_log.readline())
            """
            """ FIXME can use this in an emergency if you know that the last run completed successfully
            next_eval = os.path.join(config.workdir, 'state.nc.{}.txt'.format(outlet_element_id))
            if os.path.isfile( next_eval ):
                #Evaluate score, run finished but wasn't evaluated
                score =  objective_func(hydrograph_output_file, observed_df, evaluation_range)
                shutil.move(hydrograph_output_file, '{}_{}'.format(hydrograph_output_file, start_iteration))
                if score <= best_score:
                    best_params = start_iteration
                    best_score = score
                    #Score has improved, run next simulation with
                print("Current score {}\nBest score {}".format(score, best_score))
                write_param_log_file(start_iteration, best_params, best_score)
                write_objective_log_file(start_iteration, score)
                start_iteration += 1
            """
        elif os.path.isfile( hydrograph_output_file ): #Iteration 0 complete
            #Evaluate initial score
            best_score = objective_func(hydrograph_output_file, observed_df, evaluation_range)
            best_params = 0
            write_param_log_file(0, best_params, best_score)
            write_objective_log_file(0, best_score)
            shutil.move(hydrograph_output_file, '{}_{}'.format(hydrograph_output_file, start_iteration))
            start_iteration = 1
        else:
            #No prior states written, start from the beginning
            subprocess.check_call(ngen_cmd, stdout=ngen_log, shell=True)
            #Evaluate initial score
            best_score = objective_func(hydrograph_output_file, observed_df, evaluation_range)
            best_params = 0
            write_param_log_file(0, best_params, best_score)
            write_objective_log_file(0, best_score)
            shutil.move(hydrograph_output_file, '{}_{}'.format(hydrograph_output_file, start_iteration))
            start_iteration = 1

        if os.path.isfile( os.path.join(config.workdir, 'calibration_df_state.msg') ):
            data.calibration_df = pd.read_msgpack( os.path.join(config.workdir, 'calibration_df_state.msg') )
    else:
        subprocess.check_call(ngen_cmd, stdout=ngen_log, shell=True)
        #Evaluate initial score
        best_score = objective_func(hydrograph_output_file, observed_df, evaluation_range)
        best_params = 0
        write_param_log_file(0, best_params, best_score)
        write_objective_log_file(0, best_score)
        shutil.move(hydrograph_output_file, '{}_{}'.format(hydrograph_output_file, start_iteration))
        start_iteration = 1

    #best_params = start_iteration #TODO this isn't really needed since best is always copied to next

    print("Starting Iteration: {}".format(start_iteration))
    print("Starting Best param: {}".format(best_params))
    print("Starting Best score: {}".format(best_score))
    print("Starting DDS loop")

    for catchment in catchments:
        dds(start_iteration, iterations, catchment, ngen_cmd, ngen_log)

if __name__ == "__main__":

    import argparse

    # get the command line parser
    parser = argparse.ArgumentParser(
        description='Calibrate catchments in NGEN NWM architecture.')
    parser.add_argument('-c', '--config-file', required=True, type=str,
                        help='The configuration json file for catchments to be operated on')
    args = parser.parse_args()

    main(args.config_file)
