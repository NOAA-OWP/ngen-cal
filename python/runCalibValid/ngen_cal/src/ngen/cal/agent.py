"""
This module creates working directory and subdirectories, and stores  
properties related to configurations for executing calibration and validation runs.

@author: Nels Frazer, Xia Feng
"""

from abc import ABC, abstractmethod
import os
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from .strategy import Algorithm
from ngen.cal.meta import JobMeta
from .configuration import Model
from .utils import pushd

if TYPE_CHECKING:
    from typing import Sequence, Mapping, Any
    from pandas import DataFrame
    from ngen.cal.calibratable import Adjustable


class BaseAgent(ABC):
    """Abstract interface for Agent class."""
    @property
    def adjustables(self) -> 'Sequence[Adjustable]':
        return self.model.adjustables

    def restart(self) -> int:
        with pushd(self.job.workdir):
            starts = []
            for adjustable in self.adjustables:
                starts.append(adjustable.restart())
        if all( x == starts[0] for x in starts):
            #if everyone agrees on the iteration...
            print('restart iteration from ', starts[0])
            return starts[0]
        else:
            return 0
    
    @property
    @abstractmethod
    def model(self) -> 'Model':
        pass

    @property
    @abstractmethod
    def job(self) -> 'JobMeta':
        pass
    
    def update_config(self, i: int, params: 'DataFrame', id: str):
        """Update realization configuration file to execute BMI run at given iteration.

        parameters
        ---------
        i : Current iteration of calibration 
        params : DataFrame containing the parameter name in `param` and value in `i` columns 
        id : catchment id 

        """
        return self.model.update_config(i, params, id, path=self.job.workdir)
    
    @property
    def best_params(self) -> str:
        return self.model.best_params


class Agent(BaseAgent):
    """This is class for agent."""
    def __init__(self, model_conf: dict, workdir: 'Path', general: 'General', log: bool=False, restart: bool=False, agent_counter=0):
        """Construct attributes for the Agent class."""
        self._workdir = workdir
        self._job = None
        self._run_name = general.name 
        self._params = general.strategy.parameters
        self._algorithm = general.strategy.algorithm.value
        self._yaml_file = general.yaml_file
        self._calib_path = general.calib_path
        self._valid_path = general.valid_path
        self._general = general
        if restart and 'calib' in self._run_name:
            # find prior ngen workdirs
            # FIXME if a user starts with an independent calibration strategy
            # then restarts with a uniform strategy, this will "work" but probably shouldn't.
            # it works cause the independent writes a param df for the nexus that uniform also uses,
            # so data "exists" and it doesn't know its not conistent...
            # Conversely, if you start with uniform then try independent, it will start back at
            # 0 correctly since not all basin params can be loaded.
            # There are probably some similar issues with explicit and independent, since they have
            # similar data semantics
            workdirs = list(Path(workdir).rglob(model_conf['type']+"_*_worker"))
            if( len(workdirs) > 1 and self._algorithm=="pso") :
                print("More than one existing {} workdir, cannot restart")
            else:
                self._job = JobMeta(model_conf['type'], workdir, workdirs[agent_counter], log=log)

        if(self._job is None):
            self._job = JobMeta(model_conf['type'], workdir, log=log)

        if 'calib' in self._run_name:
            self._calib_path_output = os.path.join(self._job.workdir, 'Output_Calib')
            self._output_iter_path = os.path.join(self._job.workdir, 'Output_Iteration')
            self._plot_iter_path = os.path.join(self._job.workdir, 'Plot_Iteration')
            os.makedirs(self._calib_path_output, exist_ok=True)
            os.makedirs(self._output_iter_path, exist_ok=True)
            os.makedirs(self._plot_iter_path, exist_ok=True)

        if log and 'valid' in self._run_name:
            self._valid_path_output = os.path.join(self._job.workdir, 'Output_Valid') 
            self._valid_path_plot = os.path.join(self._workdir, 'Plot_Valid') 
            os.makedirs(self._valid_path_output, exist_ok=True)
            os.makedirs(self._valid_path_plot, exist_ok=True)
            self._calib_path_output = None
            self._output_iter_path = None 
            self._plot_iter_path = None 

        model_conf['workdir'] = self.job.workdir
        self._model = Model(model=model_conf)
        self._model.model.resolve_paths()

    @property
    def parameters(self) -> 'Mapping[str, Any]':
        return self._params

    @property
    def workdir(self) -> 'Path':
        return self._workdir

    @property
    def job(self) -> 'JobMeta':
        return self._job
    
    @property
    def model(self) -> 'Model':
        return self._model.model

    @property
    def cmd(self) -> str:
        """Proxy method to build command from contained model binary and args."""
        return "{} {}".format(self.model.get_binary(), self.model.get_args())

    def create_valid_cmd(self, valid_config_file) -> str:
        """Build command for validation run."""
        arg1 = self.model.__root__.catchments.resolve()
        arg2 = self.model.__root__.nexus.resolve()
        valid_args = '{} "all" {} "all" {}'.format(arg1, arg2, valid_config_file)

        return "{} {}".format(self.model.get_binary(), valid_args) 

    @property
    def calib_path(self) -> 'Path':
        """Directory for calibration run."""
        return self._calib_path

    @property
    def calib_path_output(self) -> 'Path':
        """Directory for calibration output."""
        return self._calib_path_output

    @property
    def output_iter_path(self) -> 'Path':
        """Directory for output at each calibration iteartion."""
        return self._output_iter_path

    @property
    def plot_iter_path(self) -> 'Path':
        """Directory for plots at each calibration iteartion"""
        return self._plot_iter_path

    @property
    def valid_path(self) -> 'Path':
        """Directory for output files of validation run."""
        return self._valid_path

    @property
    def valid_path_output(self) -> 'Path':
        """Directory for output files of validation run."""
        return self._valid_path_output

    @property
    def valid_path_plot(self) -> 'Path':
        """Directory for plots of validation run."""
        return self._valid_path_plot

    @property
    def algorithm(self) -> str:
        """Optimization algorithm."""
        return self._algorithm

    @property
    def run_name(self) -> 'Path':
        """Calibration or validation run."""
        return self._run_name

    @property
    def yaml_file(self) -> 'Path':
        """Calibration yaml file."""
        return self._yaml_file

    @property
    def df_precip(self) -> float:
        """Precipitation time series."""
        return self.model.df_precip

    @property
    def model_params(self) -> dict:
        """Model calibration parameters."""
        return self.model.model_params

    @property
    def realization_file(self) -> 'Path':
        """Model realization file."""
        return self.model.realization_file

    def duplicate(self, restart_flag=False, agent_counter=0) -> 'Agent':
        #serialize a copy of the model
        #FIXME ??? if you do self.model.resolve_paths() here, the duplicated agent
        #doesn't have fully qualified paths...but if you do it in constructor, it works fine...
        data = self.model.__root__.copy(deep=True)
        #return a new agent, which has a unique Model instance
        #and its own Job/workspace
        return Agent(data.dict(by_alias=True), self._workdir, self._general, log=False, restart=restart_flag, agent_counter=agent_counter)
