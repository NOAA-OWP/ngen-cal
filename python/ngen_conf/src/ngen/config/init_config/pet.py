from enum import Enum
from typing import Literal, Union

from ngen.init_config import serializer_deserializer as serde
from pydantic import validator


class PetMethod(int, Enum):
    """
    evapotranspiration (ET) module,
    Version 1.0 by Fred L. Ogden, NOAA-NWS-OWP, May, 2020.
    includes five different methods to calculate ET, from Chow, Maidment & Mays Textbook, and UNFAO Penman-Monteith:

    1. energy balance method
    2. aerodynamic method
    3. combination method, which combines 1 & 2.
    4. Priestley-Taylor method, which assumes the ratio between 1 & 2, and only calculates 1.
    5. Penman-Monteith method, which requires a value of canopy resistance term, and does not rely on 1 or 2. This subroutine requires a considerable amount of meteorological data as input.
      a) temperature and (relative-humidity or specific humidity) and the heights at which they are measured.
      b) near surface wind speed measurement and the height at which it was measured.
      c) the ambient atmospheric temperature lapse rate
      d) the fraction of the sky covered by clouds
      e) (optional) the height above ground to the cloud base. If not provided, then assumed.
      f) the day of the year (1-366) and time of day (UTC only!)
      g) the skin temperature of the earth's surface.
      h) the zero-plane roughness height of the atmospheric boundary layer assuming log-law behavior (from land cover)
      i) the average root zone soil temperature, or near-surface water temperature in the case of lake evaporation.
      j) the incoming solar (shortwave) radiation. If not provided it is computed from d,e,f, using an updated method similar to the one presented in Bras, R.L. Hydrology. Requires value of the Linke atmospheric turbidity factor, which varies from 2 for clear mountain air to 5 for smoggy air. According to Hove & Manyumbu 2012, who calculated values over Zimbabwe that varied from 2.14 to 3.71. Other values exist in the literature.
    NOTE THE VALUE OF evapotranspiration_params.zero_plane_displacement_height COMES FROM LAND COVER DATA.
    Taken from: https://websites.pmc.ucsc.edu/~jnoble/wind/extrap/

    source: https://github.com/NOAA-OWP/evapotranspiration/blob/0a66999db9695bccf4c1e35d904aa86f04e6cacf/README.md?plain=1#L32-L53
    """

    energy_balance = 1
    aerodynamic = 2
    energy_balance_aerodynamic_combo = 3
    priestley_taylor = 4
    penman_monteith = 5


class PET(
    serde.IniSerializerDeserializer,
):
    verbose: bool
    pet_method: PetMethod
    forcing_file: Literal["BMI"] = "BMI"
    run_unit_tests: bool = False  # bool; serialize as int
    yes_aorc: bool  # bool; serialize as int
    yes_wrf: bool  # bool; serialize as int
    wind_speed_measurement_height_m: float  # 10.0 m
    humidity_measurement_height_m: float  # 2.0
    vegetation_height_m: float  # 0.12
    zero_plane_displacement_height_m: float  # 0.0003
    momentum_transfer_roughness_length: float  # 0.0
    heat_transfer_roughness_length_m: float
    surface_longwave_emissivity: float
    surface_shortwave_albedo: float
    cloud_base_height_known: bool  # serialize in all caps
    latitude_degrees: float
    longitude_degrees: float
    site_elevation_m: float
    time_step_size_s: int
    num_timesteps: int
    shortwave_radiation_provided: bool  # bool; serialize as int

    @validator("pet_method", pre=True)
    def _coerce_pet_method(
        cls, value: Union[str, int, PetMethod]
    ) -> Union[int, PetMethod]:
        if isinstance(value, (PetMethod, int)):
            return value
        return int(value)

    class Config(serde.IniSerializerDeserializer.Config):
        space_around_delimiters = False
        no_section_headers = True
        field_type_serializers = {bool: lambda b: int(b), PetMethod: lambda e: e.value}
        field_serializers = {"cloud_base_height_known": lambda b: str(b).upper()}
