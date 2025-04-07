"""
This is a class to hold the name, initial, minimum and maximum values of calibration parameters.

@author: Nels Frazer
"""

from ast import Param
from typing import Sequence

from pydantic import BaseModel, Field


class Parameter(BaseModel, allow_population_by_field_name = True):
    """
        The data class for a given parameter
    """
    name: str = Field(alias='param')
    min: float
    max: float
    init: float

Parameters = Sequence[Parameter]
