from pydantic import BaseModel, DirectoryPath, conint, PyObject, validator
from typing import Optional, Tuple, Union, Literal
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod
from .strategy import Objective
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
    #TODO make this optional, but co-dependent???
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
        use_enum_values = True

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
        with open(self._objective_log_file, 'a+') as log_file:
            log_file.write('{}, '.format(i))
            log_file.write('{}\n'.format(score))
    
    def write_param_log_file(self, i):
        with open(self._param_log_file, 'w+') as log_file:
            log_file.write('{}\n'.format(i))
            log_file.write('{}\n'.format(self.best_params))
            log_file.write('{}\n'.format(self.best_score))

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
        if id is not None:
            prefix = ""
        else:
            prefix = f"{self.id}_"
        return Path(self._param_log_file.parent, prefix + self._param_log_file.stem + self._param_log_file.suffix)

    @property
    def objective_log_file(self) -> Path:
        """
            The path to the best parameter log file
        """
        if id is not None:
            prefix = ""
        else:
            prefix = f"{self.id}_"
        return Path(self._objective_log_file.parent, prefix + self._objective_log_file.stem + self._objective_log_file.suffix)

    @validator("objective")
    def validate_objective(cls, value):
        if value is None:
            raise ValueError("Objective function must not be None")
        
        return value

class ModelExec(BaseModel, Configurable):
    """
        The data class for a given model, which must also be Configurable
    """
    binary: str
    args: Optional[str]
    workdir: DirectoryPath = Path("./")
    eval_params: EvaluationOptions

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
