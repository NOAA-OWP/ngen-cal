from ast import Param
from pydantic import BaseModel
from typing import Sequence

class Parameter(BaseModel):
    """
        The data class for a given parameter
    """
    name: str
    min: float
    max: float
    init: float

Parameters = Sequence[Parameter]