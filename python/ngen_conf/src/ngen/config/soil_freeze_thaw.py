from typing import Optional

from pydantic import BaseModel, Field

from .bmi_formulation import BMICxx


class SoilFreezeThawParams(BaseModel):
    """Class for validating Soil Freeze Thaw Parameters"""

    smcmax: Optional[float]
    b: Optional[float]
    satpsi: Optional[float]


class SoilFreezeThaw(BMICxx):
    """A BMIC++ implementation for Soil Freeze Thaw module"""

    model_params: Optional[SoilFreezeThawParams]
    registration_function: str = "none"
    main_output_variable: str = "num_cells"
    model_name: str = Field("SoilFreezeThaw", const=True, alias="model_type_name")

    _variable_names_map = {
        # TG from noah owp modular
        "ground_temperature": "TG"
    }
