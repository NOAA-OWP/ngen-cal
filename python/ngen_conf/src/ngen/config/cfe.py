from __future__ import annotations

from typing import Optional, Literal
from pydantic import BaseModel, Field

from .bmi_formulation import BMIC


class CFEParams(BaseModel):
    """Class for validating CFE Parameters"""

    b: Optional[float]
    """Pore size distribution index"""
    satdk: Optional[float]
    """Saturated hydraulic conductivity"""
    satpsi: Optional[float]
    """saturated capillary head"""
    slope: Optional[float]
    """Linear scaling of "openness" of bottom drainage boundary"""
    maxsmc: Optional[float]
    """saturated soil moisture content"""
    wltsmc: Optional[float]
    """wilting point soil moisture content"""
    refkdt: Optional[float]
    """
    Surface runoff parameter; REFKDT is a tuneable parameter that significantly
    impacts surface infiltration and hence the partitioning of total runoff into
    surface and subsurface runoff. Increasing REFKDT decreases surface runoff.
    Only applicable when surface_water_partitioning_scheme is Schaake.
    """
    expon: Optional[float]
    """soil primary outlet coefficient"""
    max_gw_storage: Optional[float]
    """Maximum groundwater storage"""
    cgw: Optional[float]
    """Coefficent for the groundwater equation"""
    alpha_fc: Optional[float]
    """field_capacity_atm_press_fraction (alpha_fc)"""
    kn: Optional[float]
    """Nash coefficient for subsurface lateral flow through Nash cascade"""
    klf: Optional[float]
    """Nash coefficient that determines the volume of lateral flow"""
    kinf_nash_surface: Optional[float]
    """
    Storage fraction per hour that moves from Nash surface reservoirs to soil.
    Only applicable surface_runoff_scheme = NASH_CASCADE.
    """
    retention_depth_nash_surface: Optional[float]
    """
    Water retention depth threshold (only applied to the first reservoir)
    Only applicable surface_runoff_scheme = NASH_CASCADE.
    """
    a_xinanjiang_inflection_point_parameter: Optional[float]
    """Contributing area curve inflection point"""
    b_xinanjiang_shape_parameter: Optional[float]
    """Contributing area curve shape parameter"""
    x_xinanjiang_shape_parameter: Optional[float]
    """Contributing area curve shape parameter"""

    class Config(BaseModel.Config):
        allow_population_by_field_name = True
        fields = {
            "cgw": {"alias": "Cgw"},
            "kn": {"alias": "Kn"},
            "klf": {"alias": "Klf"},
            "kinf_nash_surface": {"alias": "Kinf_nash_surface"},
            "a_xinanjiang_inflection_point_parameter": {
                "alias": "a_Xinanjiang_inflection_point_parameter"
            },
            "b_xinanjiang_shape_parameter": {"alias": "b_Xinanjiang_shape_parameter"},
            "x_xinanjiang_shape_parameter": {"alias": "x_Xinanjiang_shape_parameter"},
        }


class CFE(BMIC):
    """A BMIC implementation for the CFE ngen module
    """
    model_params: Optional[CFEParams]
    main_output_variable: str = 'Q_OUT'
    registration_function: str = "register_bmi_cfe"
    #NOTE aliases don't propagate to subclasses, so we have to repeat the alias
    model_name: Literal["CFE"] = Field("CFE", const=True, alias="model_type_name")

    #can set some default name map entries...will be overridden at construction
    #if a name_map with the same key is passed in, otherwise the name_map
    #will also include these mappings
    _variable_names_map =  {
        #"water_potential_evaporation_flux": "EVAPOTRANS",
        #"atmosphere_water__liquid_equivalent_precipitation_rate": "QINSUR"
        }
