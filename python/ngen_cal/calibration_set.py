from pandas import DataFrame# type: ignore
import shutil
from typing import TYPE_CHECKING, Sequence
import pandas as pd
if TYPE_CHECKING:
    from pandas import DataFrame
    from pathlib import Path
from pathlib import Path
from hypy.nexus import Nexus
from .calibratable import Adjustable, Evaluatable


class CalibrationSet(Evaluatable):
    """
        A HY_Features based catchment with additional calibration information/functionality
    """

    def __init__(self, adjustables: Sequence[Adjustable], eval_nexus: Nexus, routing_output: 'Path', start_time: str, end_time: str):
        """

        """
        self._eval_nexus = eval_nexus
        self._adjustables = adjustables
        self._output_file = routing_output

        #use the nwis location to get observation data
        obs =self._eval_nexus._hydro_location.get_data(start_time, end_time)
        #make sure data is hourly
        self._observed = obs.set_index('value_time')['value'].resample('1H').nearest()
        self._observed.rename('obs_flow', inplace=True)
        #observations in ft^3/s convert to m^3/s
        self._observed = self._observed * 0.028316847
        self._output = None

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
        try:
            #in this case, look for routed data
            #this is really model specific, so not as generalizable the way this
            #is coded right now =(
            #would be better to hook this from the model object???
            #read the routed flow at the eval_nexus
            df = pd.read_hdf(self._output_file)
            df.index = df.index.map(lambda x: 'wb-'+str(x))
            df.columns = pd.MultiIndex.from_tuples(df.columns)

            # TODO should contributing_catchments be singular??? assuming it is for now...
            df = df.loc[self._eval_nexus.contributing_catchments[0].replace('cat', 'wb')]
            self._output = df.xs('q', level=1, drop_level=False)
            #This is a hacky way to get the time index...pass the time around???
            tnx_file = list(Path(self._output_file).parent.glob("tnx*"))[0]
            tnx_df = pd.read_csv(tnx_file, index_col=0, parse_dates=[1], names=['ts', 'time', 'Q']).set_index('time')
            dt_range = pd.date_range(tnx_df.index[0], tnx_df.index[-1], len(self._output.index)).round('min')
            self._output.index = dt_range
            #this may not be strictly nessicary...I think the _evalutate will align these...
            self._output = self._output.resample('1H').first()
            self._output.name="sim_flow"
            # self._output = read_csv(self._output_file, usecols=["Time", self._output_var], parse_dates=['Time'], index_col='Time', dtype={self._output_var: 'float64'})
            # self._output.rename(columns={self._output_var:'sim_flow'}, inplace=True)
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
    
    def check_point(self, path: 'Path') -> None:
        """
            Save calibration information
        """
        for adjustable in self.adjustables:
            adjustable.df.to_parquet(path/adjustable.check_point_file)

class UniformCalibrationSet(CalibrationSet, Adjustable):
    """
        A HY_Features based catchment with additional calibration information/functionality
    """

    def __init__(self, eval_nexus: Nexus, routing_output: 'Path', start_time: str, end_time: str,  params: dict = {}):
        """

        """
        super().__init__(adjustables=[self], eval_nexus=eval_nexus, routing_output=routing_output, start_time=start_time, end_time=end_time)
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

    def save_output(self, i) -> None:
        """
            Save the last output to output for iteration i
        """
        #FIXME ensure _output_file exists
        #FIXME re-enable this once more complete
        shutil.move(self._output_file, '{}_last'.format(self._output_file))
    
    #update handled in meta, TODO remove this method???
    def update(self, iteration: int) -> None:
        pass

    #Override this file name
    @property
    def check_point_file(self) -> 'Path':
        return Path('{}_parameter_df_state.parquet'.format(self._eval_nexus.id))
