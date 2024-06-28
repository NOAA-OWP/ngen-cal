"""
This module includes several classes to hold algorithm, objective functions and strategy.

@author: Nels Frazer, Xia Feng
"""

from enum import Enum
from pydantic import BaseModel, PyObject, validator
from typing import Optional, Mapping, Any
try: #to get literal in python 3.7, it was added to typing in 3.8
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

from . import metric_functions
#from . import objectives


class Algorithm(str, Enum):
    """Enumeration of supported search algorithms."""
    dds = "dds"
    pso = "pso"
    gwo = "gwo"

class Objective(str, Enum):
    """Enumeration of supported objective functions."""
    __func_map__ = {
                    "kge": metric_functions.KGE,
                    "nse": metric_functions.NSE,
                    "rmse": metric_functions.root_mean_squared_error,
                    "rsr": metric_functions.rmse_std_ratio,
                    "nnse": metric_functions. Weighted_NSE,
                }

    kge = "kge"
    nse = "nse"
    nnse = "nnse"
    rmse = "rmse"
    rsr = "rsr"

    def __call__(self, *args, **kwargs):
        return self.__func_map__[self.value](*args, **kwargs)

class Estimation(BaseModel):
    """Estimation strategy for defining parameter estimation."""
    type: Literal['estimation']

    algorithm: Algorithm
    parameters: Optional[Mapping[str, Any]] = {}

class Sensitivity(BaseModel):
    """Sensitivity strategy for defining a sensitivity analysis"""
    type: Literal['sensitivity']
    pass #Not Implemented
