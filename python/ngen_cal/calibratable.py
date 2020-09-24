from abc import ABC, abstractmethod
from pandas import Series, read_parquet
from typing import Optional, TYPE_CHECKING

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
        return '{}_calibration_df_state.parquet'.format(self.id)

    @abstractmethod
    def check_point(self, path: 'Path') -> None:
        """
            Save calibration information
        """
        self.df.to_parquet(path/self.check_point_file)

    @abstractmethod
    def load_df(self, path: 'Path') -> None:
        """
            Load saved calibration information
        """
        self._df = read_parquet(path/self.check_point_file)
