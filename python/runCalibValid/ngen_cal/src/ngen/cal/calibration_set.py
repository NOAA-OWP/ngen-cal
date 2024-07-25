"""
This module creates interface to adjust parameters, store
observation, and save streamflow from calibration and validation
runs and perform evaluation for a set of calibration catchments. 

@author: Nels Frazer, Xia Feng
"""

import glob
import os
from pathlib import Path
import shutil
import time
from typing import TYPE_CHECKING, Sequence

import netCDF4
import pandas as pd
from pandas import DataFrame# type: ignore

from hypy.nexus import Nexus
from .calibratable import Adjustable, Evaluatable

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path
    from typing import Tuple
    from pandas import DataFrame
    from .model import EvaluationOptions


class CalibrationSet(Evaluatable):
    """A HY_Features based catchment with additional calibration information/functionality."""
    def __init__(self, 
        adjustables: Sequence[Adjustable], 
        eval_nexus: Nexus,
        routing_output: 'Path', 
        start_time: str, 
        end_time: str, 
        eval_params: 'EvaluationOptions', 
        obsflow_file: 'Path',
        wb_lst: list,
) -> None:
        """Construct attributes for the CalibrationSet object.

        Parameters
        ----------
        adjustables: Adjustable object 
        eval_nexus : Obesrvable nexus ID 
        routing_output : Routing output file
        start_time : Starting simulation time 
        end_time : Endig simulation time 
        eval_params : EvaluationOptions object 
        obsflow_file : Streamflow observation file

        """
        super().__init__(eval_params)
        self._eval_nexus = eval_nexus
        self._adjustables = adjustables
        self._output_file = routing_output

        # Read observation data if observation file is provided
        if os.path.exists(obsflow_file):
            obs = pd.read_csv(obsflow_file)
            obs['value_date'] = pd.DatetimeIndex(obs['value_date'])
            self._observed = obs.set_index('value_date')
        else:
            # Otherwise pull observation from NWIS portal on-the-fly 
            obs =self._eval_nexus._hydro_location.get_data(start_time, end_time)
            self._observed = obs.set_index('value_time')['value'].resample('1H').nearest()
            self._observed.rename('obs_flow', inplace=True)
            self._observed = self._observed * 0.028316847 # Convert observation from ft^3/s to m^3/s

        self._output = None
        self._eval_range = self.eval_params._eval_range
        self._valid_eval_range = self.eval_params._valid_eval_range
        self._full_eval_range = self.eval_params._full_eval_range
        self._wb_lst = wb_lst
    
    @property
    def evaluation_range(self) -> 'Tuple[datetime, datetime]':
        return self._eval_range

    @property
    def valid_evaluation_range(self) -> 'Tuple[datetime, datetime]':
        return self._valid_eval_range

    @property
    def full_evaluation_range(self) -> 'Tuple[datetime, datetime]':
        return self._full_eval_range

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
            # Read the routed flow at the eval_nexus
            ncvar=netCDF4.Dataset(self._output_file, "r")
            fid_index = [list(ncvar['feature_id'][0:]).index(int(fid)) for fid in self._wb_lst]
            self._output = pd.DataFrame(data={'sim_flow': pd.DataFrame(ncvar['flow'][fid_index], index=fid_index).T.sum(axis=1)})

            # Get date 
            tnx_file = list(Path(self._output_file).parent.glob("nex*.csv"))[0]
            tnx_df = pd.read_csv(tnx_file, index_col=0, parse_dates=[1], names=['ts', 'time', 'Q']).set_index('time')
            dt_range = pd.date_range(tnx_df.index[1], tnx_df.index[-1], len(self._output.index)).round('min')
            self._output.index = dt_range
            self._output.index.name='Time'
            self._output = self._output.resample('1H').first()
            hydrograph = self._output

        except FileNotFoundError:
            print("{} not found. Current working directory is {}".format(self._output_file, os.getcwd()))
            print("Setting output to None")
            hydrograph = None
        except Exception as e:
            raise(e)

        return hydrograph

    @output.setter
    def output(self, df):
        self._output = df

    @property
    def observed(self) -> 'DataFrame':
        """Observed hydrograph for this catchment."""
        hydrograph = self._observed
        if hydrograph is None:
            raise(RuntimeError("Error reading observation for {}".format(self._id)))
        return hydrograph

    @observed.setter
    def observed(self, df):
        self._observed = df

    def save_output(self, i) -> None:
        """Save the last output to output for iteration i."""
        if os.path.exists(elf._output_file):
            shutil.move(self._output_file, '{}_last'.format(self._output_file))
    
    def check_point(self, path: 'Path') -> None:
        """Save calibration information."""
        for adjustable in self.adjustables:
            adjustable.df.to_parquet(path/adjustable.check_point_file)

    def restart(self) -> int:
        try:
            for adjustable in self.adjustables:
                adjustable.restart()
        except FileNotFoundError:
            return 0
        return super().restart()


class UniformCalibrationSet(CalibrationSet, Adjustable):
    """A HY_Features based catchment with additional calibration information/functionality"""
    def __init__(self, 
        eval_nexus: Nexus,
        routing_output: 'Path', 
        start_time: str, 
        end_time: str, 
        eval_params: 'EvaluationOptions', 
        obsflow_file: 'Path', 
        wb_lst: list,
        params: dict = {},
) -> None:
        """Constructor for the UniformCalibrationSet object."""
        super().__init__(adjustables=[self], eval_nexus=eval_nexus, routing_output=routing_output, start_time=start_time, end_time=end_time, eval_params=eval_params, obsflow_file=obsflow_file, wb_lst=wb_lst)
        Adjustable.__init__(self=self, df=DataFrame(params).rename(columns={'init': '0'}))

        #For now, set this to None so meta update does the right thing
        #at some point, may want to refactor model update to handle this better
        self._id = None 

    # Required Adjustable properties
    @property
    def id(self) -> str:
        """An identifier for this unit, used to save unique checkpoint information."""
        return self._id

    def save_output(self, i) -> None:
        """
            Save the last output to output for iteration i
        """
        #FIXME ensure _output_file exists
        #FIXME re-enable this once more complete
        shutil.move(self._output_file, '{}_last'.format(self._output_file))

    def save_calib_output(self, i, output_iter_file: 'Path', last_output_file: 'Path', calib_path1: 'Path', 
                         calib_path2: 'Path', calib_path3: Path = None, save_output_iter_flag=False) -> None:
        """Save model output from calibration run.

        Parameters:
        ----------
        i : iteration
        output_iter_file : output file at each iteration
        last_output_file : last output file
        calib_path1 : directory to store streamflow file at each iteration
        calib_path2 : current agent job directory 
        calib_path3 : directory to store catchment and nexsus output plus other output files, default None
        save_output_iter_flag : whether to save output at each iteration

        """
        if os.path.exists(self._output_file):
            flow_output = self._output.reset_index()
            flow_output = flow_output.rename(columns={'index': 'Time'})
            if i ==0 or save_output_iter_flag:
                filename_iter = os.path.join(calib_path1, output_iter_file + str('{:04d}').format(i) +'.csv')
                flow_output.to_csv(filename_iter, index=False)
            flow_output.to_csv(last_output_file, index=False)
            shutil.move(self._output_file, os.path.join(os.path.dirname(last_output_file), '{}_last'.format(self._output_file)))
        if calib_path3 is None:
           calib_path3 = calib_path2
        for csvfl in glob.glob(os.path.join(calib_path2, 'nex*.csv')):
            shutil.move(csvfl, calib_path3 + '/' + os.path.basename(csvfl))
        for csvfl in glob.glob(os.path.join(calib_path2, 'cat*.csv')):
            shutil.move(csvfl, calib_path3 + '/' + os.path.basename(csvfl))
        if len(glob.glob(os.path.join(calib_path2, '*.out')))>0:
            for outfl in glob.glob(os.path.join(calib_path2, '*.out')):
                shutil.move(outfl, calib_path3 + '/' + os.path.basename(outfl))

    def save_best_output(self, best_output_file: 'Path', best_save_flag = False) -> None:
        """Save the output at the best iteration

        Parameters:
        ----------
        best_output_file : Best output file name
        best_save_flag : Whether save output as best output

        """
        if self._output is not None and best_save_flag:
            flow_output = self._output.reset_index()
            flow_output = flow_output.rename(columns={'index': 'Time'})
            flow_output.to_csv(best_output_file, index=False)

    def save_valid_output(self, basinid: str, run_name: str, valid_path1: 'Path', valid_path2: 'Path', valid_path3: 'Path') -> None:
        """Save model output from validation run.

        Parameters:
        ----------
        run_name : Control or best run
        valid_path1 : Validation run main directory 
        valid_path2 : Validation run job work directory
        valid_path3 : Subdrirectory under valid_path2 to store output files 

        """
        if os.path.exists(self._output_file):
            flow_output = self._output.reset_index()
            flow_output = flow_output.rename(columns={'index': 'Time'})
            filename_valid = os.path.join(valid_path1, basinid + '_output_' + run_name + '.csv')
            flow_output.to_csv(filename_valid, index=False)
            shutil.move(self._output_file, os.path.join(valid_path2, '{}_'.format(self._output_file) + run_name))
        for csvfl in glob.glob(os.path.join(valid_path2, 'nex*.csv')):
           shutil.move(csvfl, valid_path3 + '/' + os.path.basename(csvfl).split('.')[0] + '_{}'.format(run_name) +'.csv')
        for csvfl in glob.glob(os.path.join(valid_path2, 'cat*.csv')):
           shutil.move(csvfl, valid_path3 + '/' + os.path.basename(csvfl).split('.')[0] + '_{}'.format(run_name) +'.csv')
        if len(glob.glob(os.path.join(valid_path2, '*.out')))>0:
            for outfl in glob.glob(os.path.join(valid_path2, '*.out')):
                shutil.move(outfl, valid_path3 + '/' + os.path.basename(outfl).split('.')[0] + '_{}'.format(run_name) +'.out')

    # Update handled in meta, TODO remove this method???
    def update_params(self, iteration: int) -> None:
        pass

    # Override this file name
    @property
    def check_point_file(self) -> 'Path':
        return Path('parameter_df_state_{}.parquet'.format(self._eval_nexus.id))

    def restart(self):
        """Prepare for calibration restart run."""
        # Reload the evaluation information
        start_iteration = Evaluatable.restart(self)
        try:
            # Reload the param space for the adjustable
            Adjustable.restart(self)
            shutil.copy(str(self.check_point_file), str(self.check_point_file) + '_before_restart_' + time.strftime('%Y%m%d_%H%M%S'))
            try:
                self.df.pop(str(start_iteration))
                self.check_point('./')
            except KeyError:
                pass
        except FileNotFoundError:
            return 0

        return start_iteration 
