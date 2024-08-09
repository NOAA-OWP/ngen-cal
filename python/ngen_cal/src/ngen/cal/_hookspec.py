from __future__ import annotations

from typing import TYPE_CHECKING

import pluggy

from ngen.cal import PROJECT_SLUG

if TYPE_CHECKING:
    from datetime import datetime

    import pandas as pd
    from hypy.nexus import Nexus

    from ngen.cal.configuration import General
    from ngen.cal.model import ModelExec
    from ngen.cal.meta import JobMeta

hookspec = pluggy.HookspecMarker(PROJECT_SLUG)


@hookspec
def ngen_cal_configure(config: General) -> None:
    """
    Called before calibration begins.
    This allow plugins to perform initial configuration.

    Plugins' configuration data should be provided using the
    `plugins_settings` field in the `ngen.cal` configuration file.
    By convention, the name of the plugin should be used as top level key in
    the `plugin_settings` dictionary.
    """
    # NOTE: not sure if we should just provide `General.plugin_settings`?
    #       likewise, not sure if we should also pass the `model_conf`?
    #       i am not inclined to just add things to add things.
    #       for now, lets stick with `General` config until we _need_ more.


@hookspec
def ngen_cal_start() -> None:
    """Called when first entering the calibration loop."""


@hookspec
def ngen_cal_finish(exception: Exception | None) -> None:
    """
    Called after exiting the calibration loop.
    Plugin implementations are guaranteed to be called even if an exception is
    raised during the calibration loop.
    `exception` will be non-none if an exception was raised during calibration.
    """


class ModelHooks:
    @hookspec
    def ngen_cal_model_configure(self, config: ModelExec) -> None:
        """
        Called before calibration begins.
        This allow plugins to perform initial configuration.

        Plugins' configuration data should be provided using the
        `plugins_settings` field in the `model` section of an `ngen.cal`
        configuration file.
        By convention, the name of the plugin should be used as top level key in
        the `plugin_settings` dictionary.
        """

    @hookspec(firstresult=True)
    def ngen_cal_model_observations(
        self,
        nexus: Nexus,
        start_time: datetime,
        end_time: datetime,
        simulation_interval: pd.Timedelta,
    ) -> pd.Series:
        """
        Called during each calibration iteration to provide truth / observation
        values in the form of a pandas Series, indexed by time with a record
        every `simulation_interval`.
        The returned pandas Series should be in units of cubic meters per
        second.

        `nexus`: HY_Features Nexus
        `start_time`, `end_time`: inclusive simulation time range
        `simulation_interval`: time (distance) between simulation values
        """

    @hookspec(firstresult=True)
    def ngen_cal_model_output(self, id: str | None) -> pd.Series:
        """
        Called during each calibration iteration to provide the model output in
        the form of a pandas Series, indexed by time.
        Output series should be in units of cubic meters per second.
        """

    @hookspec
    def ngen_cal_model_iteration_finish(self, iteration: int, info: JobMeta) -> None:
        """
        Called after each model iteration is completed and evaluated.
        And before the next iteration is configured and started.
        Currently called at the end of an Adjustable's check_point function
        which writes out calibration/parameter state data each iteration.
        """
