from __future__ import annotations

from typing import Literal
from pydantic import BaseModel, Field

from .bmi_formulation import BMIFortran


class NoahOWPParams(BaseModel):
    """Class for validating NoahOWP Parameters
    """
    #define params which can be adjusted here
    #see cfe.py for example
    pass

class NoahOWP(BMIFortran):
    """A BMIFortran implementation for a noahowp module
    """
    #NGEN complains about 'model_params' = {} in input...use none to remove it for now
    model_params: NoahOWPParams = None
    main_output_variable: str = 'QINSUR'
    #NOTE aliases don't propagate to subclasses, so we have to repeat the alias
    model_name: Literal["NoahOWP"] = Field("NoahOWP", const=True, alias="model_type_name")

    _variable_names_map =  {
            "PRCPNONC": "atmosphere_water__liquid_equivalent_precipitation_rate",
            "Q2": "atmosphere_air_water~vapor__relative_saturation",
            "SFCTMP": "land_surface_air__temperature",
            "UU": "land_surface_wind__x_component_of_velocity",
            "VV": "land_surface_wind__y_component_of_velocity",
            "LWDN": "land_surface_radiation~incoming~longwave__energy_flux",
            "SOLDN": "land_surface_radiation~incoming~shortwave__energy_flux",
            "SFCPRS": "land_surface_air__pressure"
        }
