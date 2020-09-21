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

    def __init__(self, id: str, params: dict = {}):
        """

        """
        calibration_params = params[id].pop('calibration')
        super().__init__(id, params)
        self._df = DataFrame(calibration_params).rename(columns={'init':'0'})
        #FIXME paramterize
        self._output_file = 'test_file.out'

    @property
    def df(self) -> 'DataFrame':
        """

        """
        return self._df

    def check_point(self) -> None:
        """

        """
        super().check_point(self)

    def update(self) -> None:
        """
            update configuration based on latest params
        """
        pass
