from __future__ import annotations

import pandas as pd
from pandas import DataFrame# type: ignore
from typing import TYPE_CHECKING, Sequence
if TYPE_CHECKING:
    from pandas import DataFrame
    from pathlib import Path
    from datetime import datetime
    from ngen.cal._hookspec import ModelHooks
    from ngen.cal.model import EvaluationOptions
    from ngen.cal.meta import JobMeta

from pathlib import Path
from hypy.nexus import Nexus
from .calibratable import Adjustable, Evaluatable


class CalibrationSet(Evaluatable):
    """
        A HY_Features based catchment with additional calibration information/functionality
    """

    def __init__(self, adjustables: Sequence[Adjustable], eval_nexus: Nexus, hooks: ModelHooks, start_time: datetime, end_time: datetime, eval_params: EvaluationOptions):
        super().__init__(eval_params)
        self._eval_nexus = eval_nexus
        self._adjustables = adjustables
        # record the hooks needed for output and checkpointing
        self._hooks = hooks

        # TODO: derive this from realization config
        simulation_interval: pd.Timedelta = pd.Timedelta(3600, unit="s")
        obs = self._hooks.ngen_cal_model_observations(
            nexus=self._eval_nexus,
            start_time=start_time,
            end_time=end_time,
            simulation_interval=simulation_interval,
        )
        obs.rename("obs_flow", inplace=True)
        self._observed = obs

        self._output = None
        self._eval_range = self.eval_params._eval_range
    
    @property
    def evaluation_range(self) -> tuple[datetime, datetime] | None:
        return self._eval_range

    @property
    def adjustables(self):
        return self._adjustables

    @property
    def output(self) -> DataFrame:
        """
            The model output hydrograph for this catchment
            This re-reads the output file each call, as the output for given calibration catchment changes
            for each calibration iteration. If it doesn't exist, should return None
        """
        # TODO should contributing_catchments be singular??? assuming it is for now...
        # Call output hooks, take first non-none result provided from hooks (called in LIFO order of registration)
        cat_id = self._eval_nexus.contributing_catchments[0].id
        assert cat_id.startswith("cat"), f"expected catchment id to start with 'cat': {cat_id}"
        cat_id = cat_id.replace("cat", "wb")
        df = self._hooks.ngen_cal_model_output(id=cat_id)
        if df is None:
            # list of results is empty
            print("No suitable output found from output hooks...")
        return df

    # TODO should we still allow a setter here given the output hook used for this property?
    @output.setter
    def output(self, df):
        self._output = df

    @property
    def observed(self) -> DataFrame:
        """
            The observed hydrograph for this catchment FIXME move output/observed to calibratable?
        """
        hydrograph = self._observed
        if hydrograph is None:
            raise(RuntimeError(f"Error reading observation for {self._id}"))
        return hydrograph

    @observed.setter
    def observed(self, df):
        self._observed = df

    def check_point(self, iteration: int, info: JobMeta) -> None:
        """
            Save calibration information
        """
        for adjustable in self.adjustables:
            adjustable.df.to_parquet(info.workdir/adjustable.check_point_file)
        # call any model post hooks
        self._hooks.ngen_cal_model_iteration_finish(iteration = iteration, info = info)

    def restart(self) -> int:
        try:
            for adjustable in self.adjustables:
                adjustable.restart()
        except FileNotFoundError:
            return 0
        return super().restart()

class UniformCalibrationSet(CalibrationSet, Adjustable):
    """
        A HY_Features based catchment with additional calibration information/functionality
    """

    def __init__(self, eval_nexus: Nexus, hooks: ModelHooks, start_time: str, end_time: str, eval_params: EvaluationOptions, params: dict = {}):
        """

        """
        super().__init__(adjustables=[self], eval_nexus=eval_nexus, hooks=hooks, start_time=start_time, end_time=end_time, eval_params=eval_params)
        Adjustable.__init__(self=self, df=DataFrame(params).rename(columns={'init': '0'}))

        #For now, set this to None so meta update does the right thing
        #at some point, may want to refactor model update to handle this better
        self._id = None 

    #Required Adjustable properties
    @property
    def id(self) -> str:
        """
            An identifier for this unit, used to save unique checkpoint information.
        """
        return self._id

    #update handled in meta, TODO remove this method???
    def update_params(self, iteration: int) -> None:
        pass

    #Override this file name
    @property
    def check_point_file(self) -> Path:
        return Path(f'{self._eval_nexus.id}_parameter_df_state.parquet')

    def restart(self):
        try:
            #reload the param space for the adjustable
            Adjustable.restart(self)
        except FileNotFoundError:
            return 0
        #Reload the evaluation information
        return Evaluatable.restart(self)
