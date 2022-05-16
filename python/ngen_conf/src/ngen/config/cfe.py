from typing import Optional
from pydantic import BaseModel, Field

from .bmi_formulation import BMIC

class CFEParams(BaseModel):
    """Class for validating CFE Parameters
    """
    maxsmc: Optional[float]
    satdk: Optional[float]
    slope: Optional[float]
    bb: Optional[float]
    multiplier: Optional[float]
    expon: Optional[float]

class CFE(BMIC):
    """A BMIC implementation for the CFE ngen module
    """
    model_params: CFEParams = {}
    main_output_variable: str = 'Q_OUT'
    registration_function: str = "register_bmi_cfe"
    #NOTE aliases don't propagate to subclasses, so we have to repeat the alias
    model_name: str = Field("CFE", const=True, alias="model_type_name")

    #can set some default name map entries...will be overridden at construction
    #if a name_map with the same key is passed in, otherwise the name_map
    #will also include these mappings
    _variable_names_map =  {
        #"water_potential_evaporation_flux": "EVAPOTRANS",
        "atmosphere_water__liquid_equivalent_precipitation_rate": "QINSUR"
        }
