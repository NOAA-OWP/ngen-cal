#!/usr/bin/env python
from pathlib import Path
from ngen_cal.configuration import Configuration
from ngen_cal.meta import CalibrationMeta
from ngen_cal.search import dds

def main(config_file, catchment_data, nexus_data, crosswalk, restart):
    """
        We need to 'read' the configuration of the model we want to calibrate
    """
    workdir = Path.cwd()
    config = Configuration(config_file, catchment_data, nexus_data, crosswalk, workdir)

    """
        It might make the most sense to link static/parameter info independently from model runtime such as start/end times
    """
    #This is the range of the hydrograph dates to run the objective function over
    evaluation_range = ('2011-08-05 12:00:00', '2011-08-08 00:00:00')

    print("Starting calib")

    """
    TODO calibrate each "catcment" independely, but there may be something interesting in grouping various formulation params
    into a single variable vector and calibrating a set of heterogenous formultions...
    """

    #TODO move most of this to utils module
    ngen_bin = "ngen"
    ngen_args = '{} "" {} "" {}'.format(catchment_data, nexus_data, config_file)

    meta = CalibrationMeta(config, workdir, ngen_bin, ngen_args, "ngen-calibration")
    meta.log_file = None
    start_iteration = 0
    iterations = 100
    #run NGEN here on initial parameters if needed
    if restart:
        start_iteration = meta.restart()

    print("Starting Iteration: {}".format(start_iteration))
    print("Starting Best param: {}".format(meta.best_params))
    print("Starting Best score: {}".format(meta.best_score))
    print("Starting DDS loop")

    #NOTE this assumes we calibrate each catchment independently, it may be possible to design an "aggregate" calibration
    #that works in a more sophisticated manner.
    for catchment in config.catchments:
        dds(start_iteration, iterations, catchment, meta)

if __name__ == "__main__":

    import argparse

    # get the command line parser
    parser = argparse.ArgumentParser(
        description='Calibrate catchments in NGEN NWM architecture.')
    parser.add_argument('-c', '--config-file', required=True, type=str,
                        help='The configuration json file for catchments to be operated on')
    parser.add_argument('-d', '--catchment-data', required=True, type=str,
                        help='The catchment hydrofabric data file')
    parser.add_argument('-n', '--nexus-data', required=True, type=str,
                        help='The nexus hydrofabric datafile')
    parser.add_argument('-x', '--crosswalk', required=True, type=str,
                        help='The crossswalk data file linking nexus identities')
    parser.add_argument('-r', '--restart', action='store_true',
                        help='Attempt to restart from a previous calibration')
    args = parser.parse_args()

    main(args.config_file, args.catchment_data, args.nexus_data, args.crosswalk, args.restart)
