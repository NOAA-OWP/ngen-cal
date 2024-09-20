#!/usr/bin/env python
from __future__ import annotations

import yaml
from os import chdir
from pathlib import Path
from ngen.cal.configuration import General, Model
from ngen.cal.ngen import Ngen
from ngen.cal.search import dds, dds_set, pso_search
from ngen.cal.strategy import Algorithm
from ngen.cal.agent import Agent
from ngen.cal._plugin_system import setup_plugin_manager

from typing import cast, Callable, List, Union, TYPE_CHECKING
from types import ModuleType

if TYPE_CHECKING:
    from ngen.config.realization import NgenRealization
    from typing import Mapping, Any
    from pluggy import PluginManager

def _loaded_plugins(pm: PluginManager) -> str:
    from .utils import type_as_import_string

    plugins: list[str] = []
    for (name, plugin) in pm.list_name_plugin():
        if not name:
            continue
        # case for a class based plugin. name in this case is the python ref id.
        if name[0].isdigit():
            qualified_name = type_as_import_string(plugin.__class__)
            name = f"{qualified_name} ({name})"

        plugins.append(name)

    return f"Plugins Loaded: {', '.join(plugins)}"


def _update_troute_config(
    realization: NgenRealization,
    troute_config: dict[str, Any],
):
    start = realization.time.start_time
    end = realization.time.end_time
    duration = (end - start).total_seconds()

    troute_config["compute_parameters"]["restart_parameters"]["start_datetime"] = (
        start.strftime("%Y-%m-%d %H:%M:%S")
    )

    forcing_parameters = troute_config["compute_parameters"]["forcing_parameters"]
    dt = forcing_parameters["dt"]
    nts, r = divmod(duration, dt)
    assert r == 0, "routing timestep is not evenly divisible by ngen_timesteps"
    forcing_parameters["nts"] = nts


def main(general: General, model_conf: Mapping[str, Any]):
    #seed the random number generators if requested
    if general.random_seed is not None:
        import random
        random.seed(general.random_seed)
        import numpy as np
        np.random.seed(general.random_seed)

    # model scope plugins setup in constructor
    model = Model(model=model_conf)

    # NOTE: if support for new models is added, this will need to be modified
    assert isinstance(model.model, Ngen), f"ngen.cal.ngen.Ngen expected, got {type(model.model)}"
    model_inner = model.model.unwrap()

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

    # Initialize the starting agent
    agent = Agent(model, general.workdir, general.log, general.restart, general.strategy.parameters)

    # Agent mutates the model config, so `ngen_cal_model_configure` is called afterwards
    model_inner._plugin_manager.hook.ngen_cal_model_configure(config=model_inner)

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

    print(f"Starting Iteration: {start_iteration}")
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

        if (validation_parms := model.model.unwrap().val_params) is not None:
            print("configuring calibration")
            # NOTE: importing here so its easier to refactor in the future
            from ngen.cal.calibration_set import CalibrationSet
            import pandas as pd
            from typing import TYPE_CHECKING
            if TYPE_CHECKING:
                from typing import Sequence
                import pandas as pd
                from ngen.cal.calibration_cathment import CalibrationCatchment

            adjustables: Sequence[CalibrationCatchment] = agent.model.adjustables

            realization: NgenRealization = agent.model.unwrap().ngen_realization
            assert realization is not None

            sim_start, sim_end = validation_parms.sim_interval()
            eval_start, eval_end = validation_parms.evaluation_interval()
            print(f"validation {sim_start=} {sim_end=}")

            # NOTE: do this before `update_config` is called so the right path is written to disk
            realization.time.start_time = sim_start
            realization.time.end_time = sim_end

            assert realization.routing is not None

            troute_config_path = realization.routing.config

            with troute_config_path.open() as fp:
                troute_config = yaml.safe_load(fp)

            _update_troute_config(realization, troute_config)

            troute_config_path_validation = troute_config_path.with_name("troute_validation.yaml")
            with troute_config_path_validation.open("w") as fp:
                yaml.dump(troute_config, fp)

            # NOTE: do this before `update_config` is called so the right path is written to disk
            realization.routing.config = troute_config_path_validation

            for calibration_object in adjustables:
                best_df: pd.DataFrame = calibration_object.df[[str(agent.best_params), 'param', 'model']]

                agent.update_config(agent.best_params, best_df, calibration_object.id)

                # NOTE: importing here so its easier to refactor in the future
                from ngen.cal.search import _execute, _objective_func
                from ngen.cal.utils import pushd

                print("starting calibration")
                # TODO: validation_parms.objective and target are not being correctly configured
                _execute(agent)
                with pushd(agent.job.workdir):
                    sim = calibration_object.output

                    assert isinstance(calibration_object, CalibrationSet)
                    # TODO: get from realization config
                    simulation_interval = pd.Timedelta(3600, unit="s")
                    # TODO: need a way to get the nexus
                    nexus = calibration_object._eval_nexus
                    agent_pm = agent.model.unwrap()._plugin_manager
                    obs = agent_pm.hook.ngen_cal_model_observations(
                        nexus=nexus,
                        # NOTE: techinically start_time=`eval_start` + `simulation_interval`
                        start_time=eval_start,
                        end_time=eval_end,
                        simulation_interval=simulation_interval,
                    )
                    print(f"{sim=}")
                    print(f"{obs=}")
                    score = _objective_func(sim, obs, validation_parms.objective, (sim_start, sim_end))
                    print(f"validation run score: {score}")

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
