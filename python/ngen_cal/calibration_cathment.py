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

    def __init__(self, id: str, params: dict = {}):
        """

        """
        calibration_params = params.pop('calibration')
        FormulatableCatchment.__init__(self=self, catchment_id=id, params=params, outflow=nexus)
        Calibratable.__init__(self=self, df=DataFrame(calibration_params).rename(columns={'init': '0'}))
        #FIXME paramterize
        self._output_file = 'test_file.out'

        self._observed = None
        self._output = None
        #TODO find nwis info from nexus hydro_location information

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
        #FIXME read the correct ngen output structure nex-X_output.csv
        #simulated_hydrograph_file = workdir+"{}_output.csv".format(self.id)
        #hydrograph = pd.read_csv(simulated_hydrograph_file, header=None, usecols=[0,1], names=['time', 'flow'])
        #hydrograph['time'] /= 86400 #partial day
        #hydrograph['time'] += hydrograph_reference_date #Julian date from reference
        #hydrograph['time'] = pd.to_datetime(simulated_hydrograph['time'], utc=True, unit='D', origin='julian').dt.round('1s')
        #hydrograph.drop_duplicates('time', keep='last', inplace=True)
        #hydrograph.set_index('time', inplace=True)
        hydrograph = self._output
        if hydrograph is None:
            raise(RuntimeError("Error reading output: {}".format(self._output_file)))
        return hydrograph

    @output.setter
    def output(self, df):
        self._output = df

    @property
    def observed(self) -> 'DataFrame':
        """
            The observed hydrograph for this catchment FIXME set up in __init__ move output/observed to calibratable

            This should be rather static, and can be set at initialization then accessed via the property
            TODO pull in simultion start/stop time so we know how much data to pull
        """
        #FIXME hook to NWIS
        #observed_file = os.path.join(config.workdir, 'usgs_{}_observed.csv'.format(usgs))
        #observed_df = pd.read_csv(observed_file, parse_dates=['Date_Time']).set_index('Date_Time')
        #observed_df = observed_df.tz_localize('UTC')
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
        #shutil.move(self._output_file, '{}_{}'.format(self._output_file, i))
        pass
