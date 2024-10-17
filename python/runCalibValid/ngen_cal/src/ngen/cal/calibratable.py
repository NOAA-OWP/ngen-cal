"""
This module contains classes and methods to adjust catchment states.

@author: Nels Frazer, Xia Feng
"""

from abc import ABC, abstractmethod
from pathlib import Path
import sys
from typing import List, Optional, TYPE_CHECKING

import pandas as pd
from pandas import Series, read_parquet # type: ignore

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path
    from typing import Tuple, Callable
    from pandas import DataFrame, Series
    from .model import EvaluationOptions


class Adjustable(ABC):
    """
        An Adjustable interface defning required properties for adjusting an object's state
    """

    def __init__(self, df: 'DataFrame'):
        self._df = df.copy()
        self._df.drop_duplicates(subset='param', inplace=True) 
        self._adf = df

    @property
    def df(self) -> 'DataFrame':
        """
            A dataframe of the objects parameter values to calculate indexed relative to the variables
            being calibrated.  The columns of the dataframe will be appended to with each search iterations
            parameter value for that iteration.

            Must have the following columns:
            param: str Name of the parameters to calibrate
            lower: float lower limit of the parameter value
            upper: upper limit of the parameter value
            0:     float initial value of the parameter
            #TODO do we need a group index???
        """
        return self._df

    def switch_param_name(self, mlst: List, snm: str, dnm: str) -> None:
        """Switch parameter name

        Parameters
        ----------
        mlst : list of model name
        snm : source parameter name
        dnm : destination parameter name

        Returns
        ----------
        None

        """
        if any([m in self._adf['model'].unique() for m in mlst]):
            for m in mlst:
                if ((self._adf['model']==m) & (self._adf['param']==snm)).any():
                    self._adf.loc[(self._adf['model']==m) & (self._adf['param']==snm), 'param'] = dnm 

    def df_fill(self, iteration: int) -> None:
        """Fill all parameter DataFrame with unique parameter DataFrame"""
        filter_condition = 'LASAM' not in self._adf['model'].unique() or 'CFE' in self._adf['model'].unique()
        if iteration>0:
            if filter_condition:
                self.switch_param_name(['SFT', 'SMP'], 'smcmax', 'maxsmc')
            mdf = pd.merge(self._adf, self._df[['param', str(iteration)]], on='param')
            mdf.sort_values(['model','fac'], inplace=True)
            self._adf = mdf
        if filter_condition:
            self.switch_param_name(['SFT', 'SMP'], 'maxsmc', 'smcmax')
        if iteration == 0:
            self._df.reset_index(drop=True, inplace=True)
            if not all(pd.Series(self._df.index.values)==self._df['fac']):
                sys.exit('please check parameter order')

    @property
    def adf(self) -> 'DataFrame':
        """Contains all calibration parameters"""
        return self._adf

    @property
    @abstractmethod
    def id(self) -> str:
        """
            An identifier for this unit, used to save unique checkpoint information.
        """
        pass

    @property
    def variables(self) -> 'Series':
        """
            Index series of variables
        """
        return Series(self.df.index.values)

    @property
    def bounds(self) -> 'Tuple[Series]':
        """The bounds of each parameter that is adjustable

        Returns:
            Tuple[Series]: returns the (min,max) boundaries of the adjustable parameters
        """
        return (self.df['min'], self.df['max'])

    @abstractmethod
    def update_params(self, iteration: int) -> None:
        """
            FIXME update of parameter dataframe is currently done "inplace" -- there is no interface function
            There likely *should* be one -- the big question is can it be "bundled" with the Evaluatable update function
            or should it be a unique update/name, e.g. update_params(...) that does this?  With the CalibrationMeta 
            refactored largely under the Evaluatable interface, there are a few options for this to consider.
            Need to decide if this needs to remain???
            Parameters
            ----------
            iteration:
                int which column of the internal dataframe to use to update the model parameters from
        """
        pass

    @property
    def check_point_file(self) -> 'Path':
        """
            Filename checkpoint files are saved to
        """
        return Path('parameter_df_state_{}.parquet'.format(self.id))

    def check_point(self, path: 'Path') -> None:
        """
            Save calibration information
        """
        self.df.to_parquet(path/self.check_point_file)

    def load_df(self, path: 'Path') -> None:
        """
            Load saved calibration information
        """
        self._df = read_parquet(path/self.check_point_file)

    @abstractmethod
    def save_output(self, i: int) -> None:
        """
            Save the last output of the runtime for iteration i
        """
        pass

    def restart(self) -> None:
            self.load_df('./')


class Evaluatable(ABC):
    """
        An Evaluatable interface defining required properties for a evaluating and object's state
    """

    eval_params: 'EvaluationOptions'

    def __init__(self, eval_params: 'EvaluationOptions', **kwargs):
        """
        Args:
            eval_params (EvaluationOptions): The options configuring this evaluatable
        """
        self.eval_params = eval_params

    @property
    @abstractmethod
    def output(self) -> 'DataFrame':
        """
            The output data for the calibrated object
            Calibration re-reads the output each call, as the output for given calibration is expected to change
            for each calibration iteration.  If the output doesn't exist, should raise RuntimeError
        """
        pass

    @property
    @abstractmethod
    def observed(self) -> 'DataFrame':
        """
            The observed data for this calibratable.
            This should be rather static, and can be set at initialization then accessed via the property
        """
        pass

    @property
    @abstractmethod
    def evaluation_range(self) -> 'Tuple[datetime, datetime]':
        """
            The datetime range to evaluate the model results at.
            This should be a tuple in the form of (start_time, end_time).
        """
        pass
    
    @property
    def objective(self, *args, **kwargs) -> 'Callable':
        """
            The objective function to compute cost values with.

        Returns:
            Callable: objective function which takes simulation and observation time series as args
        """
        return self.eval_params.objective

    @property
    def target(self, *args, **kwargs) -> str:
        """
            Minimize or maximize objective function 
        """
        return self.eval_params.target
 
    def update(self, i: int, score: float, log: bool, algorithm: str) -> None:
        """_summary_

        Args:
            i (int): _description_
            score (float): _description_
            log (bool): _description_

        Returns:
            _type_: _description_
        """
        self.eval_params.update(i, score, log, algorithm)
    
    @property
    def best_params(self) -> str:
        """_summary_

        Returns:
            str: _description_
        """
        return self.eval_params._best_params_iteration
    
    @property
    def best_score(self) -> float:
        """_summary_

        Returns:
            float: _description_
        """
        return self.eval_params.best_score

    @property
    def basinID(self) -> str:
        """Stream gage ID at the basin outlet"""
        return self.eval_params.basinID

    @property
    def threshold(self) -> str:
        """streamflow threshold for calculation of categorical scores"""
        return self.eval_params.threshold

    @property
    def user(self) -> str:
        """User's email address to receieve run complete message"""
        return self.eval_params.user

    @property
    def station_name(self) -> str:
        """gage station name"""
        return self.eval_params.site_name

    @property
    def streamflow_name(self) -> str:
        """Simulated streamflow variable name"""
        return self.eval_params.streamflow_name

    @property
    def output_iter_file(self) -> 'Path':
        """Output file at each iteration"""
        return self.eval_params.output_iter_file

    @property
    def last_output_file(self) -> 'Path':
        """Output file at last iteration"""
        return self.eval_params.last_output_file

    @property
    def best_output_file(self) -> bool:
        """Output file at best iteration"""
        return self.eval_params.best_output_file

    @property
    def metric_iter_file(self) -> Path:
        """file to store metrics at each iteration"""
        return self.eval_params.metric_iter_file
    
    @property
    def param_iter_file(self) -> Path:
        """file to store calibrated parameters at each iteration"""
        return self.eval_params.param_iter_file

    @property
    def cost_iter_file(self) -> Path:
        """file to store global and local best cost function at each iteration"""
        return self.eval_params.cost_iter_file

    @property
    def best_save_flag(self) -> bool:
        """Whether save output file at each iteration"""
        return self.eval_params.best_save_flag

    @property
    def save_output_iter_flag(self) -> bool:
        """Whether save output file at each iteration"""
        return self.eval_params.save_output_iter_flag

    @property
    def save_plot_iter_flag(self) -> bool:
        """Whether save plot file at each iteration"""
        return self.eval_params.save_plot_iter_flag

    @property
    def save_plot_iter_freq(self) -> bool:
        """Save plot file every specified iteration"""
        return self.eval_params.save_plot_iter_freq

    def write_metric_iter_file(self, i: int, score: float, metrics: float) -> None:
        """Write statistical metrics at each iteration into csv file"""
        return self.eval_params.write_metric_iter_file(i, score, metrics)

    def write_param_iter_file(self, i: int, params: 'DataFrame') -> None:
        """Write calibrated parameters at each iteration into csv file"""
        return self.eval_params.write_param_iter_file(i, params)

    def write_param_all_file(self, i: int, params: 'DataFrame') -> None:
        """Write calibrated parameters at each iteration into csv file"""
        return self.eval_params.write_param_all_file(i, params)

    def write_last_iteration(self, i: int) -> None:
        """Write completed iteration into csv file"""
        return self.eval_params.write_last_iteration(i)

    def write_cost_iter_file(self, i: int, calib_run_path: Path) -> None:
        """Write global and local best cost function at each iteration into csv file"""
        return self.eval_params.write_cost_iter_file(i, calib_run_path)

    def write_hist_file(self, optimizer_result: 'SwarmOptimizer', agent: 'Agent', params_lst: list) -> Path:
        """Write cost and position history plus gloal best position into csv files"""
        return self.eval_params.write_hist_file(optimizer_result, agent, params_lst)

    def create_valid_realization_file(self, agent: 'Agent', params: 'pd.DataFrame') -> None:
        """Create configuration files for validation run"""
        return self.eval_params.create_valid_realization_file(agent, params)

    def write_valid_metric_file(self, valid_run_path: Path, run_name: str, metrics: float) -> None:
        """Write statistical metrics files for validation run"""
        return self.eval_params.write_valid_metric_file(valid_run_path, run_name, metrics)

    def write_run_complete_file(self, run_name: str, path: Path) -> None:
        """Write empty file if calibration or validation run is completed"""
        return self.eval_params.write_run_complete_file(run_name, path)

    def restart(self) -> int:
        return self.eval_params.restart()


class Calibratable(Adjustable, Evaluatable):
    """
        A Calibratable interface defining required properties for a calibratable object
    """
    def __init__(self, df: Optional['DataFrame'] = None):
        Adjustable.__init__(self, df)
