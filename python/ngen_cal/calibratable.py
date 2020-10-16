from abc import ABC, abstractmethod
from pandas import Series, read_parquet # type: ignore
from typing import Optional, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from pandas import DataFrame, Series
    from pathlib import Path


class Calibratable(ABC):
    """
        A Calibratable interface defining required properties for a calibratable object
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
            An identifier for this calibratable unit, used to save unique checkpoint information.
        """
        pass

    @property
    def variables(self) -> 'Series':
        """
            Index series of variables
        """
        return Series(self.df.index.values)

    @abstractmethod
    def update(self, iteration: int) -> None:
        """
            Update the models information to prepare for the next model run

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
        return Path('{}_calibration_df_state.parquet'.format(self.id))

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

    @abstractmethod
    def save_output(self, i: int) -> None:
        """
            Save the last output of the runtime for iteration i
        """
        pass
