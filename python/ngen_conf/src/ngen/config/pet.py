from pydantic import PyObject, Field
from typing import Literal, Union
from .bmi_formulation import BMIC

class PET(BMIC):
    """A C implementation of several ET calculation algorithms
    """
    #should all be reasonable defaults for pET
    main_output_variable: Literal["water_potential_evaporation_flux"] = "water_potential_evaporation_flux"
    #NOTE aliases don't propagate to subclasses, so we have to repeat the alias
    model_name: str = Field("PET", alias="model_type_name")
    # source: https://github.com/NOAA-OWP/evapotranspiration/blob/0a66999db9695bccf4c1e35d904aa86f04e6cacf/src/bmi_pet.c#L1215
    registration_function: str = "register_bmi_pet"

    _variable_names_map =  {
            "water_potential_evaporation_flux":"water_potential_evaporation_flux"
        }
