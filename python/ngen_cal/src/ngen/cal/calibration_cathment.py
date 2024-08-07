from pandas import DataFrame, read_csv # type: ignore
import shutil
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pandas import DataFrame
    from pathlib import Path
    from geopandas import GeoSeries
    from datetime import datetime
    from typing import Tuple, Optional
    from .model import EvaluationOptions

from hypy.catchment import FormulatableCatchment # type: ignore
from hypy.nexus import Nexus

from .calibratable import Adjustable, Evaluatable

class AdjustableCatchment(FormulatableCatchment, Adjustable):
    """
        A Formulatable catchment that has an Adjustable interface to adjust
        parameteters used by the catchment.
    """

    def __init__(self,  workdir: 'Path', id: str, nexus, params: dict = {}):
        """Create an adjustable catchment and initialize its parameter space

        Args:
            workdir (Path): working directory of the calibration runs
            id (str): catchment id of this unit
            nexus (_type_): the downstream nexus associated with the catchment
            params (dict, optional): Mapping of parameter names and values. Defaults to {}.
        """

        FormulatableCatchment.__init__(self=self, catchment_id=id, params=params, outflow=nexus)
        Adjustable.__init__(self=self, df=DataFrame(params).rename(columns={'init': '0'}))
        #FIXME paramterize
        self._output_file = workdir/'{}.csv'.format(self.id)
        self._workdir = workdir

    def save_output(self, i) -> None:
        """
            Save the last output to output for iteration i
        """
        #FIXME ensure _output_file exists
        #FIXME re-enable this once more complete
        shutil.move(self._output_file, '{}_last'.format(self._output_file))

    #update handled in meta, TODO remove this method???
    def update_params(self, iteration: int) -> None:
        pass

class EvaluatableCatchment(Evaluatable):
    """
        A catchment which is "observable" which means model output can be evaluated against
        these observations for this catchment.
    """
    def __init__(self, nexus: Nexus, start_time: str, end_time: str, fabric: "GeoSeries", output_var: str, eval_params: 'EvaluationOptions'):
        """Initialize the evaluatable catchment

        Args:
            nexus (Nexus): An NWIS nexus to query stream flow data from
            start_time (str): starting datetime to request observations for
            end_time (str): ending datetime to request observations for
            fabric (GeoSeries): The catchment hydrofabric representation
            params (dict, optional): _description_. Defaults to {}.
        """
        super().__init__(eval_params)
        self._outflow = nexus
        #For BMI modules, look up name from realization config
        #If no `main_output_variable`, default to Q_OUT
        self._output_var = output_var
        #use the nwis location to get observation data
        obs = self._outflow._hydro_location.get_data(start_time, end_time)
        #make sure data is hourly
        self._observed = obs.set_index('value_time')['value'].resample('1H').nearest()
        self._observed.rename('obs_flow', inplace=True)
        #observations in ft^3/s convert to m^3/s
        self._observed = self._observed * 0.028316847
        self._output = None
        self._fabric = fabric
        self._eval_range = self.eval_params._eval_range

    @property
    def evaluation_range(self) -> 'Optional[Tuple[datetime, datetime]]':
        return self._eval_range

    @property
    def output(self) -> 'DataFrame':
        """
            The model output hydrograph for this catchment
            This re-reads the output file each call, as the output for given calibration catchment changes
            for each calibration iteration.  If it doesn't exist, should return None
        """
        try:
            #FIXME get the output variable from config
            self._output = read_csv(self._output_file, usecols=["Time", self._output_var], parse_dates=['Time'], index_col='Time', dtype={self._output_var: 'float64'})
            self._output.rename(columns={self._output_var:'sim_flow'}, inplace=True)
            #FIXME make sure units are correct here...
            #Assumes model catchment outputs are in m/hr, convert to m^3/s
            self._output = self._output * self._fabric['area_sqkm']*1000000/3600
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

class CalibrationCatchment(AdjustableCatchment, EvaluatableCatchment):
    """
        A Calibratable interface defining required properties for a calibratable object
    """
    def __init__(self, workdir: str, id: str, nexus: Nexus, start_time: str, end_time: str, fabric: "GeoSeries", output_var: str, eval_params: 'EvaluationOptions', params: dict = {}):
        EvaluatableCatchment.__init__(self, nexus, start_time, end_time, fabric, output_var, eval_params)
        AdjustableCatchment.__init__(self,  workdir, id, nexus, params)

    def restart(self) -> int:
        #TODO validate the dataframe
        restart_iteration = 0
        try:
            super(AdjustableCatchment, self).load_df(self._workdir)
            restart_iteration = super(EvaluatableCatchment, self).restart()
        except FileNotFoundError:
            pass
        return restart_iteration
