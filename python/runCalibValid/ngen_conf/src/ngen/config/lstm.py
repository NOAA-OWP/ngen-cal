from pydantic import PyObject, Field
from typing import Literal, Union
from .bmi_formulation import BMIPython

class LSTM(BMIPython):
    """A BMIPython implementation for an ngen LSTM module
    """
    #should all be reasonable defaults for LSTM
    python_type: Union[PyObject, str] = "bmi_lstm.bmi_LSTM"
    main_output_variable: Literal["land_surface_water__runoff_depth"] = "land_surface_water__runoff_depth"
    #NOTE aliases don't propagate to subclasses, so we have to repeat the alias
    model_name: str = Field("LSTM", alias="model_type_name")

    _variable_names_map =  {
            "atmosphere_water__time_integral_of_precipitation_mass_flux":"RAINRATE"
        }
