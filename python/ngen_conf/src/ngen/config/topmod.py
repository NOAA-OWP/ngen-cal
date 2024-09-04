from __future__ import annotations

from typing import Optional, Literal
from pydantic import BaseModel, Field

from .bmi_formulation import BMIC


class TopmodParams(BaseModel):
    """Class for validating Topmod Parameters"""
    szm: Optional[float]
    """
    Exponential scaling parameter for decline of transmissivity with increase in storage deficit
    Unit: meters (m)
    """
    sr0: Optional[float]
    """
    initial root zone storage deficit
    Unit: meters (m)
    """
    srmax: Optional[float]
    """
    Maximum capacity of the root zone  (Available water capacity to plants)
    Unit: meters (m)
    """
    td: Optional[float]
    """
    Time delay for recharge to the saturated zone per unit of deficit
    Unit: hours (h)
    """
    t0: Optional[float]
    """
    natural log of downslope transmissivity when the soil is just saturated to the surface (corresponds to transmissivities of 0.000335 and 2980.96 m/h)
    Unit: meters per hour (m/h)
    """
    chv: Optional[float]
    """
    Average channel flow velocity
    Unit: meters per hour (m/h)
    """
    rv: Optional[float]
    """
    Internal overland flow routing velocity
    Unit: meters per hour (m/h)
    """

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
