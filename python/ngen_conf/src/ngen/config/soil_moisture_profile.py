from typing import Optional

from pydantic import BaseModel, Field

from .bmi_formulation import BMICxx


class SoilMoistureProfileParams(BaseModel):
    """Class for validating Soil Moisture Profile Parameters"""

    smcmax: Optional[float]
    b: Optional[float]
    satpsi: Optional[float]


class SoilMoistureProfile(BMICxx):
    """A BMIC++ implementation for Soil Moisture Profile module"""

    model_params: Optional[SoilMoistureProfileParams]
    registration_function: str = "none"
    main_output_variable: str = "soil_water_table"
    model_name: str = Field("SoilMoistureProfile", const=True, alias="model_type_name")

    _variable_names_map = {
        # SOIL_STORAGE from cfe
        "soil_storage": "SOIL_STORAGE",
        # SOIL_STORAGE_CHANGE from cfe
        "soil_storage_change": "SOIL_STORAGE_CHANGE",
    }
