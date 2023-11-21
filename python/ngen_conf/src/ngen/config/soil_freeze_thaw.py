from typing import Literal, Optional, Mapping
from pydantic import Field

from .bmi_formulation import BMICxx


class SoilFreezeThaw(BMICxx):
    """A BMICXX implementation for the Soil Freeze Thaw ngen module"""

    model_params: Optional[Mapping[str, str]]
    # FIXME this isn't required for CXX bmi in ngen?
    registration_function: str = "none"
    # NOTE aliases don't propagate to subclasses, so we have to repeat the alias
    model_name: Literal["SoilFreezeThaw"] = Field(
        "SoilFreezeThaw", const=True, alias="model_type_name"
    )
