from typing import Any, Dict, Literal, Optional, Union

from ngen.init_config import serializer_deserializer
from pydantic import Field, root_validator
from typing_extensions import override

from .utils import CSList

bmi = Literal["BMI", "bmi"]
soil_storage_model = Literal[
    "Conceptual", "conceptual", "Layered", "layered", "TopModel", "topmodel", "TOPMODEL"
]
soil_moisture_profile_option = Literal["Constant", "constant", "Linear", "linear"]
water_table_based_method = Literal["deficit_based", "flux_based"]


class SoilMoistureProfile(serializer_deserializer.IniSerializerDeserializer):
    soil_z: CSList[float]
    """
    vertical resolution of the soil moisture profile (depths from the surface)
    """

    # https://github.com/NOAA-OWP/SoilMoistureProfiles/blob/2d61b86a3d7010be93af0d67f4d01fa6d0993029/src/soil_moisture_profile.cxx#L243-L249
    soil_depth_layers: Optional[Union[CSList[float], bmi]]
    """
    Absolute depth of soil layers.
    Specify as `BMI` if the variable will be provided by another BMI module.
    Required if soil_storage_model = `layered`.
    """

    # alt: soil_params.smcmax
    # TODO: fix how lists are handled
    smcmax: Union[CSList[float], bmi]
    """
    The maximum moisture content (i.e., porosity).
    Note porosity for layered-based models vary by layers.
    """

    # alt: soil_params.b
    # b > 0
    # https://github.com/NOAA-OWP/SoilMoistureProfiles/blob/832d5a70d632d9978dec40a480e970a6b59720c5/src/soil_moisture_profile.cxx#L169C23-L169C23
    b: float = Field(gt=0)
    """
    The pore size distribution, beta exponent in Clapp-Hornberger function.
    Must be greater that 0.
    """

    # alt: soil_params.satpsi
    satpsi: float
    """saturated capillary head (saturated moisture potential)"""

    soil_storage_model: soil_storage_model
    """
    if conceptual, conceptual models are used for computing the soil moisture  profile (e.g., CFE).
    If layered, layered-based soil moisture models are used (e.g., LGAR).
    If topmodel, topmodel's variables are used.
    """
    soil_moisture_profile_option: Optional[soil_moisture_profile_option]
    """
    constant for layered-constant profile.
    linear for linearly interpolated values between two consecutive layers.
    Needed if soil_storage_model = layered.
    """

    # soil_storage_depth > 0
    # https://github.com/NOAA-OWP/SoilMoistureProfiles/blob/832d5a70d632d9978dec40a480e970a6b59720c5/src/soil_moisture_profile.cxx#L199
    soil_storage_depth: Optional[float] = Field(None, gt=0)
    """
    depth of the soil reservoir model (e.g., CFE).
    must be greater than 0.
    Note: this depth can be different from the depth of the soil moisture profile which is based on soil_z
    """

    # 6.0 default from:
    # https://github.com/NOAA-OWP/SoilMoistureProfiles/blob/832d5a70d632d9978dec40a480e970a6b59720c5/src/soil_moisture_profile.cxx#L294
    # https://github.com/NOAA-OWP/SoilMoistureProfiles/blob/832d5a70d632d9978dec40a480e970a6b59720c5/src/soil_moisture_profile.cxx#L298
    water_table_depth: float = Field(6.0, gte=0)

    # 0.4 meter default from:
    # https://github.com/NOAA-OWP/SoilMoistureProfiles/blob/832d5a70d632d9978dec40a480e970a6b59720c5/src/soil_moisture_profile.cxx#L270
    soil_moisture_fraction_depth: float = 0.4  # in meters
    """
    **user specified depth for the soil moisture fraction (default is 40 cm)
    """

    water_table_based_method: Optional[water_table_based_method]
    """
    Needed if soil_storage_model = topmodel.
    flux-based uses an iterative scheme, and deficit-based uses catchment deficit to compute soil moisture profile
    """

    # NOTE: confirm this is optional
    verbosity: Optional[Literal["high", "low", "none"]]

    @override
    def to_ini_str(self) -> str:
        data = self.dict(by_alias=True, exclude_none=True, exclude_unset=True)
        return self._to_ini_str(data)

    @root_validator(pre=True)
    @classmethod
    def _root_validator(cls, values: Dict[str, Any]):
        # soil_params.<var_name> _are_ supported, but deprecated.
        soil_params_mapping = (
            ("soil_params.b", "b"),
            ("soil_params.satpsi", "satpsi"),
            ("soil_params.smcmax", "smcmax"),
        )
        # map from the deprecated names to the supported names _if_ only the deprecated name is provided
        for alt, actual in soil_params_mapping:
            if alt in values and actual not in values:
                values[actual] = values[alt]
                # delete is not required, pydantic will ignore the values.
                # del values[alt]
        return values

    @root_validator()
    def _assert_invariants(cls, values: Dict[str, Any]):
        # https://github.com/NOAA-OWP/SoilMoistureProfiles/blob/832d5a70d632d9978dec40a480e970a6b59720c5/src/soil_moisture_profile.cxx#L273
        soil_storage_model = values["soil_storage_model"]
        soil_storage_depth = values.get("soil_storage_depth")
        if soil_storage_depth is None and soil_storage_model.lower() == "conceptual":
            raise ValueError(
                f"'soil_storage_depth' required for 'soil_storage_model': {soil_storage_model!r}"
            )

        # https://github.com/NOAA-OWP/SoilMoistureProfiles/blob/832d5a70d632d9978dec40a480e970a6b59720c5/src/soil_moisture_profile.cxx#L286
        smp_opt = values.get("soil_moisture_profile_option")
        if soil_storage_model.lower() == "layered" and smp_opt is None:
            raise ValueError(
                f"'soil_moisture_profile_option' required for 'soil_storage_model': {soil_storage_model!r}"
            )

        # https://github.com/NOAA-OWP/SoilMoistureProfiles/blob/832d5a70d632d9978dec40a480e970a6b59720c5/src/soil_moisture_profile.cxx#L313
        wtm = values.get("water_table_based_method")
        if soil_storage_model.lower() == "topmodel" and wtm is None:
            raise ValueError(
                f"'water_table_based_method' required for 'soil_storage_model': {soil_storage_model!r}"
            )

        # https://github.com/NOAA-OWP/SoilMoistureProfiles/blob/2d61b86a3d7010be93af0d67f4d01fa6d0993029/src/soil_moisture_profile.cxx#L243-L249
        sdl = values.get("soil_depth_layers")
        if sdl is None and soil_storage_model.lower() == "layered":
            raise ValueError(
                f"'soil_depth_layers' required for 'soil_storage_model': {soil_storage_model!r}"
            )

        return values

    class Config(serializer_deserializer.IniSerializerDeserializer.Config):
        no_section_headers: bool = True
        # extra space is not accounted for
        # https://github.com/NOAA-OWP/SoilMoistureProfiles/blob/2d61b86a3d7010be93af0d67f4d01fa6d0993029/src/soil_moisture_profile.cxx#L114
        space_around_delimiters: bool = False
