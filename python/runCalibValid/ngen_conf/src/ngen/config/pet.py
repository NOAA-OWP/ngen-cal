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

    _variable_names_map =  {
            "water_potential_evaporation_flux":"water_potential_evaporation_flux"
        }
