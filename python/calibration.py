#!/usr/bin/env python
import yaml
from os import chdir
from pathlib import Path
from ngen_cal.configuration import General, Model
from ngen_cal.meta import CalibrationMeta
from ngen_cal.search import dds

def main(general, model):

    print("Starting calib")

    """
    TODO calibrate each "catcment" independely, but there may be something interesting in grouping various formulation params
    into a single variable vector and calibrating a set of heterogenous formultions...
    """

    meta = CalibrationMeta(model, general)
    start_iteration = general.start_iteration
    if general.restart:
        start_iteration = meta.restart()


    print("Starting Iteration: {}".format(start_iteration))
    print("Starting Best param: {}".format(meta.best_params))
    print("Starting Best score: {}".format(meta.best_score))
    print("Starting DDS loop")

    #NOTE this assumes we calibrate each catchment independently, it may be possible to design an "aggregate" calibration
    #that works in a more sophisticated manner.
    for catchment in model.hy_catchments:
        dds(start_iteration, general.iterations, catchment, meta)

if __name__ == "__main__":


    import argparse

    # get the command line parser
    parser = argparse.ArgumentParser(
        description='Calibrate catchments in NGEN NWM architecture.')
    parser.add_argument('config_file', type=Path,
                        help='The configuration yaml file for catchments to be operated on')

    args = parser.parse_args()
    
    with open(args.config_file) as file:
        conf = yaml.safe_load(file)
    
    general = General(**conf['general'])
    # change directory to workdir
    chdir(general.workdir)
    model = Model.parse_obj(conf['model']).get_model()
    main(general, model)
