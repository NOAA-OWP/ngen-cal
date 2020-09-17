from pandas import DataFrame
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pandas import DataFrame, Series

from hypy.catchment import Catchment
from ngen_cal.calibratable import Calibratable


class CalibrationCatchment(Catchment, Calibratable):
    """
        A HY_Features based catchment with additional calibration information/functionality
    """

    def __init__(self, id: str):
        """

        """
        super().__init__(id, {})
        self._df = p

    @property
    def df(self) -> 'DataFrame':
        """

        """
        pass

    def check_point(self) -> None:
        """

        """
        super().check_point(self)

    def update(self) -> None:
        """
            update configuration based on latest params
        """
        pass
