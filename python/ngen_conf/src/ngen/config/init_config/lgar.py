from pathlib import Path
from typing import Literal, Optional, Union

from ngen.init_config import serializer_deserializer
from pydantic import Field
from typing_extensions import override

from .utils import CSList, FloatUnitPair
from .value_unit_pair import ListUnitPair


class Lgar(serializer_deserializer.IniSerializerDeserializer):
    forcing_file: Optional[Path]
    """
    provides precipitation and PET inputs

    only required if you are running in standalone mode (outside of NextGen).
    """

    soil_params_file: Path
    """
    provides soil types with van Genuchton parameters
    """

    layer_thickness: Union[ListUnitPair[float, Literal["cm"]], CSList[float]]
    """
    individual layer thickness (not absolute)
    Unit: cm
    """

    initial_psi: Union[float, FloatUnitPair[Literal["cm"]]]
    """
    >=0	cm	capillary head
    used to initialize layers with a constant head
    Unit: cm
    """

    ponded_depth_max: Union[float, FloatUnitPair[Literal["cm"]]]
    """
    >=0	cm	maximum surface ponding
    the maximum amount of water unavailable for surface drainage, default is set to zero
    Unit: cm
    """

    timestep: FloatUnitPair[Literal["s", "sec", "min", "minute", "h", "hr"]]
    """
    >0	sec/min/hr	temporal resolution
    timestep of the model
    Unit: "s", "sec", "min", "minute", "h", "hr"
    """

    forcing_resolution: FloatUnitPair[Literal["s", "sec", "min", "minute", "h", "hr"]]
    """
    sec/min/hr temporal resolution
    timestep of the forcing data
    Unit: "s", "sec", "min", "minute", "h", "hr"
    """

    endtime: FloatUnitPair[Literal["s", "sec", "min", "minute", "h", "hr", "d", "day"]]
    """
    >0 sec, min, hr, d	simulation duration
    time at which model simulation ends
    Unit: "s", "sec", "min", "minute", "h", "hr", "d", "day"
    """

    layer_soil_type: CSList[int]
    """
    layer soil type (read from the database file soil_params_file)
    """

    max_soil_types: int = Field(15, gt=1)
    """
    maximum number of soil types read from the file soil_params_file (default is set to 15)
    """

    wilting_point_psi: Union[float, FloatUnitPair[Literal["cm"]]]
    """
    wilting point (the amount of water not available for plants) used in computing AET
    Unit: cm
    """

    use_closed_form_g: bool = Field(False, alias="use_closed_form_G")
    """
    determines whether the numeric integral or closed form for G is used; a value of true will use the closed form.
    This defaults to false.
    """

    giuh_ordinates: CSList[float]
    """
    GIUH ordinates (for giuh based surface runoff)
    """

    verbosity: Literal["high", "low", "none"] = "none"
    """
    controls IO (screen outputs and writing to disk)
    """

    sft_coupled: bool
    """
    model coupling impacts hydraulic conductivity couples LASAM to SFT.
    Coupling to SFT reduces hydraulic conducitivity, and hence infiltration, when soil is frozen.
    """

    soil_z: Union[ListUnitPair[float, Literal["cm"]], CSList[float]]
    """
    vertical resolution of the soil column (computational domain of the SFT model)
    Unit: cm
    """

    calib_params: bool = False
    """
    calibratable params flag
    impacts soil properties	If set to true, soil smcmax, smcmin, vg_m, and vg_alpha are calibrated.
    defualt is false.
    vg = van Genuchten, SMC= soil moisture content
    """

    @override
    def to_ini_str(self) -> str:
        data = self.dict(by_alias=True, exclude_none=True, exclude_unset=True)
        return self._to_ini_str(data)

    class Config(serializer_deserializer.IniSerializerDeserializer.Config):
        no_section_headers: bool = True
        # extra space is not accounted for
        # https://github.com/NOAA-OWP/LGAR-C/blob/5aad0f501faba8cb53c6692787c96cba04489eaa/src/lgar.cxx#L190
        space_around_delimiters: bool = False
        field_type_serializers = {bool: lambda b: str(b).lower()}
        preserve_key_case: bool = True
