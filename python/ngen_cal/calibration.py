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

def main(config_file, restart):
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
    if restart:
        start_iteration = meta.restart()

    print("Starting Iteration: {}".format(start_iteration))
    print("Starting Best param: {}".format(meta.best_params))
    print("Starting Best score: {}".format(meta.best_score))
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
    parser.add_argement('-r', '--restart', action='store_true',
                        help='Attempt to restart from a previous calibration')
    args = parser.parse_args()

    main(args.config_file, args.restart)
