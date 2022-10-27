from typing import Optional
from pydantic import BaseModel, Field

from .bmi_formulation import BMICxx

class SLOTHParams(BaseModel):
    """Class for validating SLOTH Parameters
    """
    pass

class SLOTH(BMICxx):
    """A BMICXX implementation for the SLOTH ngen module
    """
    model_params: Optional[SLOTHParams]
    registration_function: str = "none" #FIXME this isn't required for CXX bmi in ngen?
    #NOTE aliases don't propagate to subclasses, so we have to repeat the alias
    model_name: str = Field("SLOTH", const=True, alias="model_type_name")
