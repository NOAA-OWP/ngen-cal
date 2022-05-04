from pydantic import BaseModel, PyObject, validator
from typing import Optional, Union
try: #to get literal in python 3.7, it was added to typing in 3.8
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from enum import Enum

from . import objectives

class Algorithm(str, Enum):
    """Enumeration of supported search algorithms

    """
    """Dynamic Dimensioned Search Algorithm
    """
    dds = "dds"

class Objective(Enum):
    """Enumeration of supported search algorithms

    """
    """Dynamic Dimensioned Search Algorithm
    """
    __func_map__ = {"custom": objectives.custom, 
                    "kling_gupta": objectives.kling_gupta_efficiency,
                    "nnse": objectives.normalized_nash_sutcliffe,
                    "single_peak": objectives.peak_error_single,
                    "volume": objectives.volume_error
                }

    custom = "custom"
    kling_gupta = "kling_gupta"
    nnse = "nnse"
    single_peak = "single_peak"
    volume = "volume"

    def __call__(self, *args, **kwargs):
        return self.__func_map__[self.value](*args, **kwargs)

class Estimation(BaseModel):
    """
        Estimation strategy for defining parameter estimation
    """

    """
        Tag for discriminator overloading
    """
    type: Literal['estimation']

    """
        Algorithm enum value defining the desired search algorithm to use
    """
    algorithm: Algorithm

    """
        Optional objective function selector
        TODO allow for additional kwargs to be supplied to these functions?
        Document that all functions must take obs, sim args
    """
    objective: Optional[Union[Objective, PyObject]] = Objective.custom
    target: Union[Literal['min'], Literal['max'], float] = 'min'

    @validator("objective")
    def validate_objective(cls, value):
        if value is None:
            raise ValueError("Objective function must not be None")
        
        return value

class Sensitivity(BaseModel):
    """
        Sensitivity strategy for defining a sensitivity analysis

        NOT IMPLEMENTED
    """
    type: Literal['sensitivity']
    pass #Not Implemented