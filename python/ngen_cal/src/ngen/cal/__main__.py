#!/usr/bin/env python
from __future__ import annotations

import yaml
from os import chdir
from pathlib import Path
from ngen.cal.configuration import General
from ngen.cal.search import dds, dds_set, pso_search
from ngen.cal.strategy import Algorithm
from ngen.cal.agent import Agent
from ngen.cal._plugin_system import setup_plugin_manager

from typing import cast, Callable, List, Union, TYPE_CHECKING
from types import ModuleType

if TYPE_CHECKING:
    from typing import Mapping, Any
    from pluggy import PluginManager

def _loaded_plugins(pm: PluginManager) -> str:
    from .utils import type_as_import_string

    plugins: List[str] = []
    for (name, plugin) in pm.list_name_plugin():
        if not name:
            continue
        # case for a class based plugin. name in this case is the python ref id.
        if name[0].isdigit():
            qualified_name = type_as_import_string(plugin.__class__)
            name = f"{qualified_name} ({name})"

        plugins.append(name)

    return f"Plugins Loaded: {', '.join(plugins)}"


def main(general: General, model_conf: "Mapping[str, Any]"):
    #seed the random number generators if requested
    if general.random_seed is not None:
        import random
        random.seed(general.random_seed)
        import numpy as np
        np.random.seed(general.random_seed)

    plugins = cast(List[Union[Callable, ModuleType]], general.plugins)
    plugin_manager = setup_plugin_manager(plugins)

    print(_loaded_plugins(plugin_manager))

    # setup plugins
    plugin_manager.hook.ngen_cal_configure(config=general)

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

    # call `ngen_cal_start` plugin hook functions
    plugin_manager.hook.ngen_cal_start()

    try:
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
    # call `ngen_cal_finish` plugin hook functions
    except Exception as e:
        plugin_manager.hook.ngen_cal_finish(exception=e)
        raise e
    else:
        plugin_manager.hook.ngen_cal_finish(exception=None)


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
