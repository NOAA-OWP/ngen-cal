from __future__ import annotations

from typing import Optional, Literal
from pydantic import BaseModel, Field

from .bmi_formulation import BMIC

class TopmodParams(BaseModel):
    """Class for validating Topmod Parameters
    """
    sr0: Optional[float]
    srmax: Optional[float]
    szm: Optional[float]
    t0: Optional[float]
    td: Optional[float]

class Topmod(BMIC):
    """A BMIC implementation for the Topmod ngen module
    """
    model_params: Optional[TopmodParams]
    main_output_variable: str = 'Qout'
    registration_function: str = "register_bmi_topmodel"
    #NOTE aliases don't propagate to subclasses, so we have to repeat the alias
    model_name: Literal["TOPMODEL"] = Field("TOPMODEL", const=True, alias="model_type_name")

    #can set some default name map entries...will be overridden at construction
    #if a name_map with the same key is passed in, otherwise the name_map
    #will also include these mappings
    _variable_names_map =  {
        #"water_potential_evaporation_flux": "EVAPOTRANS",
        "atmosphere_water__liquid_equivalent_precipitation_rate": "QINSUR"
        }
