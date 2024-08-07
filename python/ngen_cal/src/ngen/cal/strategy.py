from __future__ import annotations

from pydantic import BaseModel
from typing import Optional, Mapping, Any
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
    pso = "pso"

class Objective(str, Enum):
    """Enumeration of supported search algorithms

    """
    """Dynamic Dimensioned Search Algorithm
    """
    __func_map__ = {"custom": objectives.custom,
                    "kling_gupta": objectives.kge,
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
    parameters: Optional[Mapping[str, Any]] = {}

class Sensitivity(BaseModel):
    """
        Sensitivity strategy for defining a sensitivity analysis

        NOT IMPLEMENTED
    """
    type: Literal['sensitivity']
    pass #Not Implemented
