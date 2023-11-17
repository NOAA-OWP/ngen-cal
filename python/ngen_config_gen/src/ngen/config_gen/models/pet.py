# TODO: check when runtime_checkable was introduced
from typing import Any, Dict
from pydantic import BaseModel

from ngen.config.init_config.pet import PET as PetConfig, PetMethod


class Pet:
    def __init__(self):
        self.data = {}
        self.__version = None

    def _set_version(self, version: str):
        if self.__version is None:
            self.__version = version
        elif self.__version != version:
            raise RuntimeError(
                f'mismatched versions. current="{self.__version}" new="{version}"'
            )

    def _version(self) -> str:
        if self.__version is None:
            raise RuntimeError("no version set")
        return self.__version

    def _v2_linked_data_hook(self, data: Dict[str, Any]):
        # NOTE typo in forcing metadata name
        self.data["longitude_degrees"] = data["X"]
        self.data["latitude_degrees"] = data["Y"]
        self.data["site_elevation_m"] = data["elevation_mean"]

    def hydrofabric_linked_data_hook(
        self, version: str, divide_id: str, data: Dict[str, Any]
    ) -> None:
        self._set_version(version)
        if self._version() == "2.0":
            self._v2_linked_data_hook(data)
        else:
            raise RuntimeError("only support v2 hydrofabric")

    def _v2_defaults(self) -> None:
        # TODO: this was from old code, not sure what to do here
        # if not bool(values["yes_aorc"]):
        #     return values
        self.data["yes_wrf"] = False
        self.data["wind_speed_measurement_height_m"] = 10.0
        self.data["humidity_measurement_height_m"] = 10.0
        self.data["shortwave_radiation_provided"] = False
        self.data["time_step_size_s"] = 3600
        self.data["num_timesteps"] = 720
        self.data["cloud_base_height_known"] = False

        self.data["verbose"] = True
        # TODO: think of how to get user input for fields like this
        self.data["pet_method"] = PetMethod.energy_balance
        # TODO: revisit this. I think this is telling it to use BMI
        self.data["yes_aorc"] = True

        # TODO: FIGURE OUT HOW TO GET THESE PARAMETERS
        # BELOW PARAMETERS MAKE NO SENSE
        self.data["vegetation_height_m"] = 0.12
        self.data["zero_plane_displacement_height_m"] = 0.0003
        self.data["momentum_transfer_roughness_length"] = 0.0
        self.data["heat_transfer_roughness_length_m"] = 0.1
        self.data["surface_longwave_emissivity"] = 42.0
        self.data["surface_shortwave_albedo"] = 7.0

    def build(self) -> BaseModel:
        return PetConfig(**self.data)

    def visit(self, hook_provider: "HookProvider") -> None:
        hook_provider.provide_hydrofabric_linked_data(self)

        if self._version() == "2.0":
            self._v2_defaults()
        else:
            raise RuntimeError("only support v2 hydrofabric")
