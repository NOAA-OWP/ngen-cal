from __future__ import annotations

from abc import ABC, abstractmethod
from pandas import Series, read_parquet # type: ignore
from typing import Optional, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from pandas import DataFrame, Series
    from pathlib import Path
    from datetime import datetime
    from typing import Tuple, Callable, Optional
    from ngen.cal.model import EvaluationOptions
    from ngen.cal.meta import JobMeta

class Adjustable(ABC):
    """
        An Adjustable interface defning required properties for adjusting an object's state
    """

    def __init__(self, df: Optional['DataFrame'] = None):
        self._df = df

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
    def bounds(self) -> 'Tuple[Series, Series]':
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
        return Path(f'{self.id}_parameter_df_state.parquet')

    def check_point(self, iteration: int, info: JobMeta) -> None:
        """
            Save calibration information
        """
        path = info.workdir
        self.df.to_parquet(path/self.check_point_file)

    def load_df(self, path: 'Path') -> None:
        """
            Load saved calibration information
        """
        self._df = read_parquet(path/self.check_point_file)

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
    def evaluation_range(self) -> 'Optional[Tuple[datetime, datetime]]':
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
 
    def update(self, i: int, score: float, log: bool) -> None:
        """
           Update the meta state for iteration `i` having score `score`
           logs objective information if log=True

            Simply passes through to @EvaluationOptions.update
        Args:
            i (int): iteration index to set score at
            score (float): score value to save
            log (bool): writes objective information to log file if True
        """
        self.eval_params.update(i, score, log)
    
    @property
    def best_params(self) -> str:
        """
            The integer iteration that contains the best parameter values, as a string

        Returns:
            str: iteration number
        """
        return self.eval_params._best_params_iteration
    
    @property
    def best_score(self) -> float:
        """
            Best score known to the current calibration

        Returns:
            float: best score
        """
        return self.eval_params.best_score
    
    def restart(self) -> int:
        return self.eval_params.restart()

class Calibratable(Adjustable, Evaluatable):
    """
        A Calibratable interface defining required properties for a calibratable object
    """
    def __init__(self, df: Optional['DataFrame'] = None):
        Adjustable.__init__(self, df)
