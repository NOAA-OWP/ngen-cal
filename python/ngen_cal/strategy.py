from pydantic import BaseModel
from typing import Optional
try: #to get literal in python 3.7, it was added to typing in 3.8
    from typing import Literal
except ImportError:
    from typing_extensions import Literal
from enum import Enum

class Algorithm(str, Enum):
    """Enumeration of supported search algorithms

    """
    """Dynamic Dimensioned Search Algorithm
    """
    dds = "dds"

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

        TODO make this an enum
    """
    objective: Optional[str]

class Sensitivity(BaseModel):
    """
        Sensitivity strategy for defining a sensitivity analysis

        NOT IMPLEMENTED
    """
    type: Literal['sensitivity']
    pass #Not Implemented