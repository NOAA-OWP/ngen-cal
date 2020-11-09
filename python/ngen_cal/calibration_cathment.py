from pandas import DataFrame, read_csv # type: ignore
import shutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pandas import DataFrame, Series
    from pathlib import Path

from hypy.catchment import FormulatableCatchment # type: ignore

from .calibratable import Calibratable


class CalibrationCatchment(FormulatableCatchment, Calibratable):
    """
        A HY_Features based catchment with additional calibration information/functionality
    """

    def __init__(self,  workdir: 'Path', id: str, nexus, start_time: str, end_time: str, params: dict = {}):
        """

        """
        calibration_params = params.pop('calibration')
        FormulatableCatchment.__init__(self=self, catchment_id=id, params=params, outflow=nexus)
        Calibratable.__init__(self=self, df=DataFrame(calibration_params).rename(columns={'init': '0'}))
        #FIXME paramterize
        self._output_file = workdir/'{}_output.csv'.format(self.id)
        #use the nwis location to get observation data
        obs = self.outflow._hydro_location.get_data(start_time, end_time)
        #make sure data is hourly
        self._observed = obs.set_index('value_date')['value'].resample('1H').nearest()
        self._observed.rename('obs_flow', inplace=True)
        self._output = None

    @property
    def df(self) -> 'DataFrame':
        """

        """
        return self._df

    def check_point(self, path: 'Path') -> None:
        """

        """
        super().check_point(path)

    def load_df(self, path: 'Path') -> None:
        """

        """
        super().load_df(path)

    def update(self, iteration: int) -> None:
        """
            update configuration based on latest params
            This functionality currently exists in the meta class
        """
        pass

    @property
    def output(self) -> 'DataFrame':
        """
            The model output hydrograph for this catchment
            This re-reads the output file each call, as the output for given calibration catchment changes
            for each calibration iteration.  If it doesn't exist, should return None
        """
        try:
            self._output = read_csv(self._output_file, usecols=["Time", "Flow"], parse_dates=['Time'], index_col='Time')
            self._output.rename(columns={'Flow':'sim_flow'}, inplace=True)
            hydrograph = self._output
        except FileNotFoundError:
            hydrograph = None
        except Exception as e:
            raise(e)
        #if hydrograph is None:
        #    raise(RuntimeError("Error reading output: {}".format(self._output_file)))
        return hydrograph

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
