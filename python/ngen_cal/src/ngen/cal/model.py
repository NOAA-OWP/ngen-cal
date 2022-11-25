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

    class Config:
        """Override configuration for pydantic BaseModel
        """
        underscore_attrs_are_private = True
        use_enum_values = True

    def __init__(self, **kwargs):
        """
        
        """
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
