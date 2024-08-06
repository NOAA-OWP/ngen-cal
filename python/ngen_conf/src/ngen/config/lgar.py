from __future__ import annotations

from pydantic import Field

from .bmi_formulation import BMICxx


class LGAR(BMICxx):
    """A BMIC++ implementation for LGAR module"""

    registration_function: str = "none"
    main_output_variable: str = "precipitation_rate"
    model_name: str = Field("LGAR", const=True, alias="model_type_name")

    _variable_names_map = {
        # QINSUR from noah owp modular
        "precipitation_rate": "QINSUR",
        # EVAPOTRANS from noah owp modular
        "potential_evapotranspiration_rate": "EVAPOTRANS",
    }
