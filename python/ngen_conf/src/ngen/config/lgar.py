from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field

from .bmi_formulation import BMICxx


class LgarParams(BaseModel):
    smcmin: Optional[float]
    """
    residual volumetric water content
    Unit: cm3/cm3
    """
    smcmax: Optional[float]
    """
    water content of the soil at natural saturation;
    Unit: cm3/cm3
    """
    van_genuchten_alpha: Optional[float]
    """
    van Genuchten parameter related to inverse of air entry pressure
    Unit: 1/cm
    """
    van_genuchten_n: Optional[float]
    """
    van Genuchten parameter related to pore size distribution
    Unit: -
    """
    hydraulic_conductivity: Optional[float]
    """
    saturated hydraulic conductivity of the soil
    Unit: cm/h
    """
    soil_depth_layers: Optional[float]
    """
    soil layer thickness
    Unit: cm
    """
    ponded_depth_max: Optional[float]
    """
    maximum allowed ponded water depth
    Unit: cm
    """
    field_capacity: Optional[float]
    """
    negative capillary head representing field capacity, used in reduction of PET to AET
    Unit: cm
    """


class LGAR(BMICxx):
    """A BMIC++ implementation for LGAR module"""

    model_params: Optional[LgarParams]
    registration_function: str = "none"
    main_output_variable: str = "precipitation_rate"
    model_name: str = Field("LGAR", const=True, alias="model_type_name")

    _variable_names_map = {
        # QINSUR from noah owp modular
        "precipitation_rate": "QINSUR",
        # EVAPOTRANS from noah owp modular
        "potential_evapotranspiration_rate": "EVAPOTRANS",
    }
