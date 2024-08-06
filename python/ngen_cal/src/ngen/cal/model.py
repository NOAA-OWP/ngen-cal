from __future__ import annotations

from pydantic import BaseModel, DirectoryPath, conint, PyObject, validator, Field, root_validator
from typing import Any, cast, Callable, Dict, List, Optional, Tuple, Union
from types import ModuleType, FunctionType
try: #to get literal in python 3.7, it was added to typing in 3.8
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod
from .strategy import Objective
from ngen.cal._plugin_system import setup_scoped_plugin_manager
from .utils import PyObjectOrModule, type_as_import_string
from pluggy import PluginManager
from ngen.cal._hookspec import ModelHooks
# additional constrained types
PosInt = conint(gt=-1)

class Configurable(ABC):
    """
        Abastract interface for wrapping configurable external models
        for use in the ngen-cal package
    """

    @abstractmethod
    def get_binary() -> str:
        """Get the binary string to execute

        Returns:
            str: The binary name or path used to execute the Configurable model
        """
    
    @abstractmethod
    def get_args() -> str:
        """Get the args to pass to the binary

        Returns:
            str: Preconfigured arg string to pass to the binary upon execution
        """

    @abstractmethod
    def update_config(*args, **kwargs):
        pass

class EvaluationOptions(BaseModel):
    """
        A data class holding evaluation parameters
    """
    #Optional, but co-dependent, see @_validate_start_stop_both_or_neither_exist for validation logic
    evaluation_start: Optional[datetime]
    evaluation_stop: Optional[datetime]
    _eval_range: Tuple[datetime, datetime] = None
    """
        Optional objective function selector
        TODO allow for additional kwargs to be supplied to these functions?
        Document that all functions must take obs, sim args
    """
    objective: Optional[Union[Objective, PyObject]] = Objective.custom
    target: Union[Literal['min'], Literal['max'], float] = 'min'
    _best_score: float
    _best_params_iteration: str = '0'
    id: Optional[str]
    _param_log_file: Path
    _objective_log_file: Path

    class Config:
        """Override configuration for pydantic BaseModel
        """
        underscore_attrs_are_private = True
        use_enum_values = False #if true, then objective turns into a str, and things blow up

    def __init__(self, **kwargs):
        """
        
        """
        self._param_log_file = kwargs.pop('param_log_file', Path('best_params.txt'))
        self._objective_log_file = kwargs.pop('objective_log_file', Path('objective_log.txt'))
        super().__init__(**kwargs)
        if self.evaluation_start and self.evaluation_stop:
            self._eval_range = (self.evaluation_start, self.evaluation_stop)
        else: #TODO figure out open/close range???
            self._eval_range=None
        if self.target == 'max':
            self._best_score = float('-inf')
        else: #must be min or value, either way this works
            self._best_score = float('inf')
        self._best_params_iteration = '0' #String representation of interger iteration

    def update(self, i: int, score: float, log: bool) -> None:
        """Update the meta state for iteration `i` having score `score`
           logs objective information if log=True

        Args:
            i (int): iteration index to set score at
            score (float): score value to save
            log (bool): writes objective information to log file if True
        """
        #TODO store current_score and current_iteration?
        if self.target == 'min':
            if score <= self._best_score:
                self._best_params_iteration = str(i)
                self._best_score = score
        elif self.target == 'max':
            if score >= self._best_score:
                self._best_params_iteration = str(i)
                self._best_score = score
        else: #target is a specific value
            if abs( score - self.target ) <= abs(self._best_score - self.target):
                self._best_params_iteration = str(i)
                self._best_score = score
        if log:
            self.write_param_log_file(i)
            self.write_objective_log_file(i, score)

    def write_objective_log_file(self, i, score):
        with open(self.objective_log_file, 'a+') as log_file:
            log_file.write(f'{i}, ')
            log_file.write(f'{score}\n')
    
    def write_param_log_file(self, i):
        with open(self.param_log_file, 'w+') as log_file:
            log_file.write(f'{i}\n')
            log_file.write(f'{self.best_params}\n')
            log_file.write(f'{self.best_score}\n')

    @property
    def best_score(self) -> float:
        """
            Best score known to the current calibration
        """
        return self._best_score

    @property
    def best_params(self) -> str:
        """
            The integer iteration that contains the best parameter values, as a string
        """
        return self._best_params_iteration

    @property
    def param_log_file(self) -> Path:
        """
            The path to the best parameter log file
        """
        if self.id is None:
            prefix = ""
        else:
            prefix = f"{self.id}_"
        return Path(self._param_log_file.parent, prefix + self._param_log_file.stem + self._param_log_file.suffix)

    @property
    def objective_log_file(self) -> Path:
        """
            The path to the best parameter log file
        """
        if self.id is None:
            prefix = ""
        else:
            prefix = f"{self.id}_"
        return Path(self._objective_log_file.parent, prefix + self._objective_log_file.stem + self._objective_log_file.suffix)

    @root_validator()
    def _validate_start_stop_both_or_neither_exist(cls, values):
        """
            Evaluation range is optional, so both have to None, or both have to be set
        """
        start = values["evaluation_start"]
        stop = values["evaluation_stop"]
        if start is None and stop is None:
            return values
        elif start is not None and stop is not None:
            return values
        raise ValueError("Both 'evaluation_start' and 'evaluation_stop' must be set or neither be set.")

    @validator("objective")
    def validate_objective(cls, value):
        if value is None:
            #raise ValueError("Objective function must not be None")
            print("Objective cannot be none -- setting default objective")
            value = Objective.custom
        return value

    def read_param_log_file(self):
        with open(self.param_log_file) as log_file:
            iteration = int(log_file.readline())
            best_params = int(log_file.readline())
            best_score = float(log_file.readline())
        return iteration, best_params, best_score

    def restart(self) -> int:
        """
            Attempt to restart a calibration from a previous state.
            If no previous state is available, start from 0

            Returns
            -------
            int iteration to start calibration at
        """
        try:
            last_iteration, best_params, best_score = self.read_param_log_file()
            self._best_params_iteration = str(best_params)
            self._best_score = best_score
            start_iteration = last_iteration + 1

            #TODO verify that loaded calibration info aligns with iteration?  Anther reason to consider making this meta
            #per catchment???

        except FileNotFoundError:
            start_iteration = 0

        return start_iteration

class ModelExec(BaseModel, Configurable):
    """
        The data class for a given model, which must also be Configurable
    """
    binary: str
    args: Optional[str]
    workdir: DirectoryPath = Path("./") #FIXME test the various workdirs
    eval_params: Optional[EvaluationOptions] = Field(default_factory=EvaluationOptions)
    plugins: List[PyObjectOrModule] = Field(default_factory=list)
    plugin_settings: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    _plugin_manager: PluginManager
    class Config(BaseModel.Config):
        # properly serialize plugins
        json_encoders = {
            type: type_as_import_string,
            ModuleType: lambda mod: mod.__name__,
            FunctionType: type_as_import_string,
        }
        underscore_attrs_are_private = True

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        model_plugins = cast(List[Union[Callable, ModuleType]], self.plugins)
        self._plugin_manager = setup_scoped_plugin_manager(ModelHooks, model_plugins)

    #FIXME formalize type: str = "ModelName"
    def get_binary(self)->str:
        """Get the binary string to execute

        Returns:
            str: The binary name or path used to execute the Configurable model
        """
        return self.binary

    def get_args(self)->str:
        """Get the args to pass to the binary

        Returns:
            str: Preconfigured arg string to pass to the binary upon execution
        """
        return self.args
