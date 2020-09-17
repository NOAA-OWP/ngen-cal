from abc import ABC, abstractproperty, abstractmethod
from pandas import Series
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pandas import Dataframe, Series
    from pathlib import Path

class Calibratable(ABC):
    """
        A Calibratable interface defining required properties for a calibratable object
    """

    @abstractproperty
    def df(self) -> 'Dataframe':
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
        pass

    @abstractproperty
    def id(self) -> str:
        """
            An identifier for this calibratable unit, used to save unique checkpoint information.
        """
        pass

    def variables(self) -> 'Series':
        """
            Index series of variables
        """
        return pd.Series(self.df.index.values)

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

    @abstractmethod
    def check_point(self, path: 'Path') -> None:
        """
            Save calibration information
        """
        self.df.to_msgpack(path+'{}_calibration_df_state.msg'.format(self.id))
