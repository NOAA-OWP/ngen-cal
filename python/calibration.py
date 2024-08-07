#!/usr/bin/env python
import yaml
from os import chdir
from pathlib import Path
from ngen.cal.configuration import General
from ngen.cal.search import dds, dds_set, pso_search
from ngen.cal.strategy import Algorithm
from ngen.cal.agent import Agent

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Mapping, Any

def main(general: General, model_conf: Mapping[str, Any]):
    #seed the random number generators if requested
    if general.random_seed is not None:
        import random
        random.seed(general.random_seed)
        import numpy as np
        np.random.seed(general.random_seed)

    print("Starting calib")

    """
    TODO calibrate each "catcment" independely, but there may be something interesting in grouping various formulation params
    into a single variable vector and calibrating a set of heterogenous formultions...
    """
    start_iteration = 0
    #Initialize the starting agent
    agent = Agent(model_conf, general.workdir, general.log, general.restart, general.strategy.parameters)
    if general.strategy.algorithm == Algorithm.dds:
        func = dds_set #FIXME what about explicit/dds
        start_iteration = general.start_iteration
        if general.restart:
            start_iteration = agent.restart()
    elif general.strategy.algorithm == Algorithm.pso: #TODO how to restart PSO?
        if agent.model.strategy != "uniform":
            print("Can only use PSO with the uniform model strategy")
            return
        if general.restart:
            print("Restart not supported for PSO search, starting at 0")
        func = pso_search

    print("Starting Iteration: {}".format(start_iteration))
    # print("Starting Best param: {}".format(meta.best_params))
    # print("Starting Best score: {}".format(meta.best_score))
    print("Starting calibration loop")


    #NOTE this assumes we calibrate each catchment independently, it may be possible to design an "aggregate" calibration
    #that works in a more sophisticated manner.
    if agent.model.strategy == 'explicit': #FIXME this needs a refactor...should be able to use a calibration_set with explicit loading
        for catchment in agent.model.adjustables:
            dds(start_iteration, general.iterations, catchment, agent)

    elif agent.model.strategy == 'independent':
        #for catchment_set in agent.model.adjustables:
        func(start_iteration, general.iterations, agent)

    elif agent.model.strategy == 'uniform':
        #for catchment_set in agent.model.adjustables:
        #    func(start_iteration, general.iterations, catchment_set, agent)
        func(start_iteration, general.iterations, agent)

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

    #model = Model(model=conf['model']).model
    main(general, conf['model'])
