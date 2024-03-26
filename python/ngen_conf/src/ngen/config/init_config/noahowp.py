import warnings
from datetime import datetime
from enum import Enum
from pathlib import Path, PosixPath, WindowsPath
from typing import ClassVar, Dict, List, Literal, Union

from ngen.init_config import core
from ngen.init_config import serializer_deserializer as serde
from pydantic import BaseModel, root_validator, validator

from .noahowp_options import (
    CanopyStomResistOption,
    CropModelOption,
    DrainageOption,
    DynamicVegOption,
    DynamicVicOption,
    EvapSrfcResistanceOption,
    FrozenSoilOption,
    PrecipPhaseOption,
    RadiativeTransferOption,
    RunoffOption,
    SfcDragCoeffOption,
    SnowAlbedoOption,
    SnowsoilTempTimeOption,
    SoilTempBoundaryOption,
    StomatalResistanceOption,
    SubsurfaceOption,
    SupercooledWaterOption,
)
from .utils import serialize_enum_value
from .validators import validate_str_len_lt

MODIFIED_IGBP_MODIS_NOAH_NVEG = 20
USGS_NVEG = 27


def _set_nveg_based_on_veg_class_name(parameters: "Parameters", structure: "Structure"):
    # don't set if `nveg` is provided
    if structure.nveg is not None:
        return

    veg_class_name = parameters.veg_class_name
    if veg_class_name == "MODIFIED_IGBP_MODIS_NOAH":
        structure.nveg = MODIFIED_IGBP_MODIS_NOAH_NVEG
    elif veg_class_name == "USGS":
        structure.nveg = USGS_NVEG
    else:
        raise ValueError("Unreachable")


class NoahOWP(serde.NamelistSerializerDeserializer):
    timing: "Timing"
    parameters: "Parameters"
    location: "Location"
    forcing: "Forcing"
    model_options: "ModelOptions"
    structure: "Structure"
    initial_values: "InitialValues"

    class Config(serde.NamelistSerializerDeserializer.Config):
        # NOTE: must explicitly specify Path subtype (i.e. `PosixPath`) here b.c.
        # `field_type_serializers` does an explicit type check, not a subtypes (covariant)
        # check.
        field_type_serializers = {
            # serialize Path types using a str cast. this ensures paths are properly escaped.
            PosixPath: lambda p: str(p),
            WindowsPath: lambda p: str(p),
        }

    @root_validator
    def _validate(cls, values: Dict[str, BaseModel]) -> Dict[str, BaseModel]:
        parameters: Parameters = values["parameters"] # type: ignore
        structure: Structure = values["structure"] # type: ignore
        _set_nveg_based_on_veg_class_name(parameters, structure)
        return values


class Timing(core.Base):
    dt: float
    startdate: datetime
    enddate: datetime
    forcing_filename: Path
    output_filename: Path

    # format: YYYYMMDDHHmm (e.g. 199801010630)
    # source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/DomainType.f90#L15
    _datetime_format: ClassVar[str] = "%Y%m%d%H%M"

    _validate_str_len = validator(
        "forcing_filename", "output_filename", pre=True, allow_reuse=True
    )(validate_str_len_lt(257))

    @validator("startdate", "enddate", pre=True)
    def _validate_dates(cls, value: Union[datetime, str]):
        if isinstance(value, datetime):
            return value
        return datetime.strptime(value, cls._datetime_format)

    class Config(core.Base.Config):
        field_serializers = {
            "startdate": lambda d: d.strftime(Timing._datetime_format),
            "enddate": lambda d: d.strftime(Timing._datetime_format),
        }


class Parameters(core.Base):
    parameter_dir: Path
    general_table: str = "GENPARM.TBL"
    soil_table: str = "SOILPARM.TBL"
    noahowp_table: str = "MPTABLE.TBL"
    soil_class_name: Literal["STAS", "STAS-RUC"]
    veg_class_name: Literal["MODIFIED_IGBP_MODIS_NOAH", "USGS"]

    _validate_str_len = validator(
        "parameter_dir",
        "general_table",
        "soil_table",
        "noahowp_table",
        pre=True,
        allow_reuse=True,
    )(validate_str_len_lt(257))

    class Config(core.Base.Config):
        def _serialize_parameter_dir(p: Path) -> str:
            if isinstance(p, WindowsPath):
                return rf"{str(p)}\\"
            return f"{str(p)}/"

        # `parameter_dir` should end in platform specific '/'
        field_serializers = {"parameter_dir": _serialize_parameter_dir}
        fields = {
            "parameter_dir": {"description": "directory path containing table files"},
            "general_table": {"description": "general param tables and misc params"},
            "soil_table": {"description": "soil param table"},
            "noahowp_table": {"description": " noah-mp related param tables"},
            "soil_class_name": {"description": "soil class data source"},
            "veg_class_name": {"description": "vegetation class data source"},
        }


class Location(core.Base):
    lat: float
    lon: float
    terrain_slope: float
    azimuth: float

    class Config(core.Base.Config):
        fields = {
            "lat": {"description": "latitude [degrees]"},
            "lon": {"description": "longitude [degrees]"},
            "terrain_slope": {"description": "terrain slope [degrees]"},
            "azimuth": {
                "description": "terrain azimuth or aspect [degrees clockwise from north]"
            },
        }


class Forcing(core.Base):
    zref: float  #               = 10.0
    rain_snow_thresh: float  #   = 1.0

    class Config(core.Base.Config):
        allow_population_by_field_name = True
        fields = {
            "zref": {
                "alias": "ZREF",
                "description": "measurement height for wind speed [m]",
            },
            "rain_snow_thresh": {
                "description": "rain-snow temperature threshold [degrees C]"
            },
        }


class ModelOptions(core.Base):
    # option bounds translated from
    # https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/OptionsType.f90#L11
    precip_phase_option: PrecipPhaseOption
    snow_albedo_option: SnowAlbedoOption
    dynamic_veg_option: DynamicVegOption
    runoff_option: RunoffOption
    drainage_option: DrainageOption
    frozen_soil_option: FrozenSoilOption
    dynamic_vic_option: DynamicVicOption
    radiative_transfer_option: RadiativeTransferOption
    sfc_drag_coeff_option: SfcDragCoeffOption
    canopy_stom_resist_option: CanopyStomResistOption
    crop_model_option: CropModelOption
    snowsoil_temp_time_option: SnowsoilTempTimeOption
    soil_temp_boundary_option: SoilTempBoundaryOption
    supercooled_water_option: SupercooledWaterOption
    stomatal_resistance_option: StomatalResistanceOption
    evap_srfc_resistance_option: EvapSrfcResistanceOption
    subsurface_option: SubsurfaceOption

    class Config(core.Base.Config):
        # TODO: consider serializing all enum's using their value unless otherwise specified
        field_serializers = {
            "precip_phase_option": serialize_enum_value,
            "snow_albedo_option": serialize_enum_value,
            "dynamic_veg_option": serialize_enum_value,
            "runoff_option": serialize_enum_value,
            "drainage_option": serialize_enum_value,
            "frozen_soil_option": serialize_enum_value,
            "dynamic_vic_option": serialize_enum_value,
            "radiative_transfer_option": serialize_enum_value,
            "sfc_drag_coeff_option": serialize_enum_value,
            "canopy_stom_resist_option": serialize_enum_value,
            "crop_model_option": serialize_enum_value,
            "snowsoil_temp_time_option": serialize_enum_value,
            "soil_temp_boundary_option": serialize_enum_value,
            "supercooled_water_option": serialize_enum_value,
            "stomatal_resistance_option": serialize_enum_value,
            "evap_srfc_resistance_option": serialize_enum_value,
            "subsurface_option": serialize_enum_value,
        }


class LandSurfaceType(int, Enum):
    """
    land surface type, 1: soil, 2: lake
    source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/NamelistRead.f90#L37
    """

    soil = 1
    lake = 2


class Structure(core.Base):
    isltyp: int  #    = 1
    nsoil: int  #     = 4
    nsnow: int  #     = 3
    # if not provided, `nveg` derived from Parameters `veg_class_name` field
    nveg: int = None
    vegtyp: int  #    = 1
    # crop type (SET TO 0, no crops currently supported)
    # source: https://github.com/NOAA-OWP/noah-owp-modular/blob/30d0f53e8c14acc4ce74018e06ff7c9410ecc13c/src/NamelistRead.f90#L36
    croptype: int = 0
    sfctyp: LandSurfaceType  #    = 1
    soilcolor: int  # = 4

    class Config(core.Base.Config):
        field_serializers = {"sfctyp": serialize_enum_value}
        fields = {
            "isltyp": {"description": "soil texture class"},
            "nsoil": {"description": "number of soil levels"},
            "nsnow": {"description": "number of snow levels"},
            "nveg": {"description": "number of vegetation types"},
            "vegtyp": {"description": "vegetation type modis"},
            "croptype": {
                "description": "crop type (0 = no crops); crop type (SET TO 0, no crops currently supported)"
            },
            "sfctyp": {"description": "land surface type, 1:soil, 2:lake"},
            "soilcolor": {"description": "soil color code"},
        }


class InitialValues(core.Base):
    dzsnso: List[float]  # =  0.0,  0.0,  0.0,  0.1,  0.3,  0.6,  1.0
    sice: List[float]  # =  0.0,  0.0,  0.0,  0.0
    sh2o: List[float]  # =  0.3,  0.3,  0.3,  0.3
    zwt: float  # =  -2.0

    class Config(core.Base.Config):
        fields = {
            "dzsnso": {"description": "snow/soil level thickness [m]"},
            "sice": {"description": "initial soil ice profile [m^3/m^3]"},
            "sh2o": {"description": "initial soil liquid profile [m^3/m^3]"},
            "zwt": {"description": "initial water table depth below surface [m]"},
        }


NoahOWP.update_forward_refs()
