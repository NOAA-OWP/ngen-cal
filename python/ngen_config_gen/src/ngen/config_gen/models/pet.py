from __future__ import annotations

from typing import Any, TYPE_CHECKING
from pydantic import BaseModel

if TYPE_CHECKING:
    from ..hook_providers import HookProvider

from ngen.config.init_config.pet import PET as PetConfig, PetMethod


class Pet:
    """
    Note, currently the following parameters are hardcoded.
    In the future these _will_ be derived from hydrofabric linked data.
        vegetation_height_m = 0.12
        zero_plane_displacement_height_m = 0.0003
        momentum_transfer_roughness_length = 0.0
        heat_transfer_roughness_length_m = 0.1
        surface_longwave_emissivity = 42.0
        surface_shortwave_albedo = 7.0

    Aside, to generate configuration files with a non-default `PetMethod` use `functools.partial` to
    accomplish this:
    For example:
        ```
        from functools import partial
        pet_w_aerodynamic = partial(Pet, method=PetMethod.aerodynamic)
        ```
    """

    def __init__(self, method: PetMethod = PetMethod.energy_balance):
        self.data: dict[str, bool | float | int | str] = {}
        self.__pet_method = method

    def hydrofabric_linked_data_hook(
        self, version: str, divide_id: str, data: dict[str, Any]
    ) -> None:
        """
        Implements `ngen.config_gen.hooks.hydrofabric_linked_data_hook`.

        Raises
        ------
        RuntimeError
            Only hydrofabric 2.0 is supported. Raises if version != 2.0. This will change in future.
        """
        if version != "2.0":
            raise RuntimeError("only support v2 hydrofabric")

        self.data["longitude_degrees"] = data["centroid_x"]
        self.data["latitude_degrees"] = data["centroid_y"]
        self.data["site_elevation_m"] = data["mean.elevation"]

    def _v2_defaults(self) -> None:
        self.data["yes_wrf"] = False
        self.data["wind_speed_measurement_height_m"] = 10.0
        self.data["humidity_measurement_height_m"] = 10.0
        self.data["shortwave_radiation_provided"] = False
        self.data["time_step_size_s"] = 3600
        self.data["num_timesteps"] = 720
        self.data["cloud_base_height_known"] = False

        self.data["verbose"] = True
        self.data["pet_method"] = self.__pet_method
        # TODO: revisit this. I think this is telling it to use BMI (@aaraney)
        self.data["yes_aorc"] = True

        # TODO: FIGURE OUT HOW TO GET THESE PARAMETERS (@aaraney)
        # BELOW PARAMETERS MAKE NO SENSE
        self.data["vegetation_height_m"] = 0.12
        self.data["zero_plane_displacement_height_m"] = 0.0003
        self.data["momentum_transfer_roughness_length"] = 0.0
        self.data["heat_transfer_roughness_length_m"] = 0.1
        self.data["surface_longwave_emissivity"] = 42.0
        self.data["surface_shortwave_albedo"] = 7.0

    def build(self) -> BaseModel:
        """
        Build and return an instance of `ngen.config.init_config.pet.PetConfig`.
        """
        return PetConfig(**self.data)

    def visit(self, hook_provider: HookProvider) -> None:
        """
        Call associated `hook_provider` methods for all hooks implemented by Self.

        Raises
        ------
        RuntimeError
            Only hydrofabric 2.0 is supported. Raises if version != 2.0. This will change in future.
        """
        hook_provider.provide_hydrofabric_linked_data(self)
        self._v2_defaults()
