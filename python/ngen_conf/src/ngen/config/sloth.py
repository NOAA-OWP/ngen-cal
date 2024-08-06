from __future__ import annotations

from typing import Literal, Optional, Mapping
from pydantic import Field

from .bmi_formulation import BMICxx

class SLOTH(BMICxx):
    """A BMICXX implementation for the SLOTH ngen module
    """
    model_params: Optional[Mapping[str, str]] #Is this a better represntation of SLOTH params??? just generic mappings?
    registration_function: str = "none" #FIXME this isn't required for CXX bmi in ngen?
    #NOTE aliases don't propagate to subclasses, so we have to repeat the alias
    model_name: Literal["SLOTH"] = Field("SLOTH", const=True, alias="model_type_name")
