from __future__ import annotations

from typing import Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..hook_providers import HookProvider

from pydantic import BaseModel

from ngen.config.init_config.cfe import CFE as CFEConfig
from ngen.config.init_config.utils import FloatUnitPair

# LSTM, Topmod
METERS = "m"
M_PER_M = "m/m"
M_PER_S = "m s-1"
M_PER_H = "m h-1"
EMPTY = ""


class Cfe:
    """
    Some fields are not available from currently provided data providers (e.g. hydrofabric linked data).
    As such, some fields have been given default values that _really_ shouldn't be.
    Default values were selected based on the linked script.
    https://github.com/NOAA-OWP/cfe/blob/bedc81b6fc047fc9a33e42e08e8ece3d342e96c3/README.md?plain=1#L56-L57
    Listed below are the fields and their default values.
        alpha_fc = 0.33
        # NOTE: giuh should be available in the Hydrofabric linked data in 2024.
        giuh_ordinates = [0.06, 0.51, 0.28, 0.12, 0.03]
        gw_storage = 0.5
        k_lf = 0.01
        k_nash = 0.03
        nash_storage = [0.0, 0.0]
        soil_params_depth = 2.0
        soil_params_expon = 1.0
        soil_params_expon_secondary = 1.0
        soil_storage = 0.667


    Parameter mappings from the hydrofabric linked data to CFE init config variables were informed
    by luciana's deprecated script for generating CFE init configs
    https://github.com/NOAA-OWP/cfe/blob/bedc81b6fc047fc9a33e42e08e8ece3d342e96c3/params/src/generate_giuh_per_basin_params.py#L298
    """

    def __init__(self):
        self.data: dict[str, FloatUnitPair[str] | list[float]] = {}

    def hydrofabric_linked_data_hook(
        self, version: str, divide_id: str, data: dict[str, Any]
    ) -> None:
        """
        Implements `ngen.config_gen.hooks.hydrofabric_linked_data_hook`.
        """
        # beta exponent on Clapp-Hornberger (1978) soil water relations
        # NOTE: it seems all values each layer of `bexp_soil_layers_stag` are the same.
        self.data["soil_params_b"] = FloatUnitPair(
            value=data["bexp_soil_layers_stag=1"],
            unit=EMPTY,
        )

        # saturated hydraulic conductivity
        # NOTE: it seems all values each layer of `dksat_soil_layers_stag` are the same.
        self.data["soil_params_satdk"] = FloatUnitPair(
            value=data["dksat_soil_layers_stag=1"],
            unit=M_PER_S,
        )

        # saturated capillary head
        # NOTE: it seems all values each layer of `psisat_soil_layers_stag` are the same.
        self.data["soil_params_satpsi"] = FloatUnitPair(
            value=data["psisat_soil_layers_stag=1"],
            unit=METERS,
        )

        # this factor (0-1) modifies the gradient of the hydraulic head at the soil bottom. 0=no-flow.
        self.data["soil_params_slop"] = FloatUnitPair(value=data["slope"], unit=M_PER_M)

        # saturated soil moisture content
        # NOTE: it seems all values each layer of `smcmax_soil_layers_stag` are the same.
        self.data["soil_params_smcmax"] = FloatUnitPair(
            value=data["smcmax_soil_layers_stag=1"],
            unit=M_PER_M,
        )

        # wilting point soil moisture content
        # NOTE: it seems all values each layer of `smcwlt_soil_layers_stag` are the same.
        self.data["soil_params_wltsmc"] = FloatUnitPair(
            value=data["smcwlt_soil_layers_stag=1"],
            unit=M_PER_M,
        )

        # maximum storage in the conceptual reservoir
        self.data["max_gw_storage"] = FloatUnitPair(value=data["gw_Zmax"], unit=METERS)

        # the primary outlet coefficient
        self.data["cgw"] = FloatUnitPair(value=data["gw_Coeff"], unit=M_PER_H)

        # exponent parameter (1.0 for linear reservoir)
        self.data["expon"] = FloatUnitPair(value=data["gw_Expon"], unit=EMPTY)

    def _v2_defaults(self) -> None:
        """
        See class level documentation for the rational and source of default values.
        """
        # https://github.com/NOAA-OWP/cfe/blob/bedc81b6fc047fc9a33e42e08e8ece3d342e96c3/README.md?plain=1#L56-L57
        self.data["soil_params_expon"] = FloatUnitPair(value=1.0, unit=EMPTY)
        self.data["soil_params_expon_secondary"] = FloatUnitPair(value=1.0, unit=EMPTY)

        # soil depth
        # 2m soil horizon
        self.data["soil_params_depth"] = FloatUnitPair(value=2.0, unit=METERS)

        # initial condition for groundwater reservoir - it is the ground water as a decimal fraction of
        # the maximum groundwater storage (max_gw_storage) for the initial timestep
        self.data["gw_storage"] = FloatUnitPair(value=0.5, unit=M_PER_M)  # 50%

        # field capacity
        self.data["alpha_fc"] = FloatUnitPair(value=0.33, unit=EMPTY)

        # TODO: fixme
        # initial condition for soil reservoir - it is the water in the soil as a decimal fraction of
        # maximum soil water storage (smcmax * depth) for the initial timestep
        self.data["soil_storage"] = FloatUnitPair(value=0.667, unit=M_PER_M)

        # number of Nash lf reservoirs (optional, defaults to 2, ignored if storage values present)
        self.data["k_nash"] = FloatUnitPair(value=0.03, unit=EMPTY)

        # Nash Config param - primary reservoir
        self.data["k_lf"] = FloatUnitPair(value=0.01, unit=EMPTY)

        # Nash Config param - secondary reservoir
        self.data["nash_storage"] = [0.0, 0.0]

        # Giuh ordinates in dt time steps
        # NOTE: these should be available in the Hydrofabric linked data in 2024.
        self.data["giuh_ordinates"] = [0.06, 0.51, 0.28, 0.12, 0.03]

    def build(self) -> BaseModel:
        """
        Build and return an instance of `ngen.config.init_config.pet.PetConfig`.
        """
        return CFEConfig(__root__=self.data)

    def visit(self, hook_provider: HookProvider) -> None:
        """
        Call associated `hook_provider` methods for all hooks implemented by Self.
        """
        hook_provider.provide_hydrofabric_linked_data(self)
        self._v2_defaults()
