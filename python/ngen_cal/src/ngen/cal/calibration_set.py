from pandas import DataFrame# type: ignore
import shutil
from typing import TYPE_CHECKING, Sequence
import pandas as pd
if TYPE_CHECKING:
    from pandas import DataFrame
    from pathlib import Path
    from pluggy import HookRelay
    from datetime import datetime
    from typing import Tuple, Optional
    from .model import EvaluationOptions
import os
from pathlib import Path
import warnings
from hypy.nexus import Nexus
from .calibratable import Adjustable, Evaluatable


class CalibrationSet(Evaluatable):
    """
        A HY_Features based catchment with additional calibration information/functionality
    """

    def __init__(self, adjustables: Sequence[Adjustable], eval_nexus: Nexus, hooks: 'HookRelay', start_time: str, end_time: str, eval_params: 'EvaluationOptions'):
        """

        """
        super().__init__(eval_params)
        self._eval_nexus = eval_nexus
        self._adjustables = adjustables
        # record the hooks needed for output
        self._output_hook = hooks.ngen_cal_model_output

        #use the nwis location to get observation data
        obs =self._eval_nexus._hydro_location.get_data(start_time, end_time)
        #make sure data is hourly
        self._observed = obs.set_index('value_time')['value'].resample('1H').nearest()
        self._observed.rename('obs_flow', inplace=True)
        #observations in ft^3/s convert to m^3/s
        self._observed = self._observed * 0.028316847
        self._output = None
        self._eval_range = self.eval_params._eval_range
    
    @property
    def evaluation_range(self) -> 'Optional[Tuple[datetime, datetime]]':
        return self._eval_range

    @property
    def adjustables(self):
        return self._adjustables

    @property
    def output(self) -> 'DataFrame':
        """
            The model output hydrograph for this catchment
            This re-reads the output file each call, as the output for given calibration catchment changes
            for each calibration iteration. If it doesn't exist, should return None
        """
        # TODO should contributing_catchments be singular??? assuming it is for now...
        # Call output hooks, take first non-none result provided from hooks (called in LIFO order of registration)
        df = self._output_hook(id=self._eval_nexus.contributing_catchments[0].replace('cat', 'wb'))
        if not df:
            # list of results is empty
            print("No suitable output found from output hooks...")
            df = None
        elif len(df) > 1:
            # TODO with the hook being firstresult=True, I don't think this is possible to hit...
            warnings.warn("Multiple output data found, using first registered")
            df = df[0]
        else:
            df = df[0]
        return df

    # TODO should we still allow a setter here given the output hook used for this property?
    @output.setter
    def output(self, df):
        self._output = df

    @property
    def observed(self) -> 'DataFrame':
        """
            The observed hydrograph for this catchment FIXME move output/observed to calibratable?
        """
        hydrograph = self._observed
        if hydrograph is None:
            raise(RuntimeError("Error reading observation for {}".format(self._id)))
        return hydrograph

    @observed.setter
    def observed(self, df):
        self._observed = df

    def save_output(self, i) -> None:
        """
            Save the last output to output for iteration i
        """
        #FIXME ensure _output_file exists
        #FIXME re-enable this once more complete
        shutil.move(self._output_file, '{}_last'.format(self._output_file))
    
    def check_point(self, path: 'Path') -> None:
        """
            Save calibration information
        """
        for adjustable in self.adjustables:
            adjustable.df.to_parquet(path/adjustable.check_point_file)

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

    def __init__(self, eval_nexus: Nexus, hooks: 'HookRelay', start_time: str, end_time: str, eval_params: 'EvaluationOptions', params: dict = {}):
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
    def check_point_file(self) -> 'Path':
        return Path('{}_parameter_df_state.parquet'.format(self._eval_nexus.id))

    def restart(self):
        try:
            #reload the param space for the adjustable
            Adjustable.restart(self)
        except FileNotFoundError:
            return 0
        #Reload the evaluation information
        return Evaluatable.restart(self)