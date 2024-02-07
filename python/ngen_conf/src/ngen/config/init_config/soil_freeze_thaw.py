from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from ngen.init_config import serializer_deserializer
from pydantic import root_validator
from typing_extensions import override

from .utils import FloatUnitPair
from .value_unit_pair import ListUnitPair, ValueUnitPair

m = Literal["m"]
m_per_m = Literal["m/m"]
k = Literal["K"]
empty = Literal[""]
# empty string is equivalent to h / hr
time_unit = Literal["s", "sec", "", "h", "hr", "d", "day"]


class IceFractionScheme(str, Enum):
    # TODO: cite papers
    Schaake = "Schaake"
    Xinanjiang = "Xinanjiang"

    def __str__(self) -> str:
        return self.value


class SoilFreezeThaw(serializer_deserializer.IniSerializerDeserializer):
    """
    Validate and programmatically interacting with SoilFreezeThaw configuration files.
    """

    verbosity: Optional[Literal["high", "low", "none"]]

    smcmax: FloatUnitPair[m_per_m]
    """
    state variable maximum soil moisture content (porosity)

    deprecated, but field can be specified as `soil_params.smcmax`
    """

    b: FloatUnitPair[empty]
    """
    state variable pore size distribution, beta exponent in ClappHornberger characteristic function
    Unit: m

    deprecated, but field can be specified as `soil_params.b`
    """

    satpsi: FloatUnitPair[m]
    """
    state variable saturated capillary head (saturated moisture potential)
    Unit: m

    deprecated, but field can be specified as `soil_params.satpsi`
    """

    quartz: FloatUnitPair[empty]
    """
    state variable soil quartz content, used in soil thermal conductivity function of PetersLidard
    Unit: m

    deprecated, but field can be specified as `soil_params.quartz`
    """

    # NOTE: it is okay to have either Schaake[] or _just_ Schaake
    # NOTE: as of NOAA-OWP/SoilFreezeThaw@84b7d12621aa53619d2843c8fcdbbe01ae4925aa Schaake[] or Schaake work
    ice_fraction_scheme: ValueUnitPair[IceFractionScheme, empty]
    """
    coupling variable runoff scheme used in the soil reservoir models (e.g. CFE)
    """

    # TODO: verify that only meters are allowed
    soil_z: ListUnitPair[float, m]
    """
    (1D array) m spatial resolution vertical resolution of the soil column (computational domain of
    the SFT model)
    """

    # TODO: verify that only kelvin is allowed
    soil_temperature: ListUnitPair[float, k]
    """(1D array)spatial resolution initial soil temperature for the discretized column
    Unit: K
    """

    soil_moisture_content: Optional[ListUnitPair[float, empty]] = None
    """
    (1D array) spatial resolution initial soil total (liquid + ice) moisture content for the
    discretized column

    if soil_moisture_bmi is `False`, `soil_moisture_content` must be provided.
    """

    soil_liquid_content: Optional[ListUnitPair[float, empty]] = None
    """
    (1D array) spatial resolution initial soil liquid moisture content for the discretized column

    if soil_moisture_bmi is `False`, `soil_liquid_content` must be provided.
    """

    bottom_boundary_temp: Optional[ListUnitPair[float, k]] = None
    """
    boundary condition temperature at the bottom boundary (BC) of the domain, if not specified, the
    default BC is zerogeothermal flux
    Unit: K
    """

    top_boundary_temp: Optional[ListUnitPair[float, k]] = None
    """
    boundary condition temperature at the top/surface boundary of the domain, if not specified, then
    other options include: 1) read from a file, or 2) provided through coupling
    Unit: K
    """

    soil_moisture_bmi: bool = False
    """
    coupling variable If true soil_moisture_profile is set by the SoilMoistureProfile module through
    the BMI; if false then config file must provide soil_moisture_content and soil_liquid_content

    if soil_moisture_bmi is `False`, `soil_moisture_content` must be provided.
    """

    end_time: Union[ValueUnitPair[int, time_unit], ValueUnitPair[float, time_unit]]
    """
    Simulation duration. This can also be though of as the total number of simulation time steps.
    Valid time units are:
        s, sec, h, hr, d, day
    Example:
        end_time=12[h]
    Default unit is hour if unit is not provided (e.g. end_time=12[]).
    """

    dt: Union[ValueUnitPair[int, time_unit], ValueUnitPair[float, time_unit]]
    """
    Size of simulation time step.
    Valid time units are:
        s, sec, h, hr, d, day
    Example:
        dt=1[h]
    Default unit is hour if unit is not provided (e.g. dt=1[]).
    """

    @root_validator(pre=True)
    @classmethod
    def _root_validator(cls, values: Dict[str, Any]):
        cls._validate_soil_moisture_params(values)
        # soil_params.<var_name> _are_ supported, but deprecated.
        soil_params_mapping = (
            ("soil_params.b", "b"),
            ("soil_params.satpsi", "satpsi"),
            ("soil_params.smcmax", "smcmax"),
            ("soil_params.quartz", "quartz"),
        )
        # map from the deprecated names to the supported names _if_ only the deprecated name is provided
        for alt, actual in soil_params_mapping:
            if alt in values and actual not in values:
                values[actual] = values[alt]
                # delete is not required, pydantic will ignore the values.
                # del values[alt]
        return values

    @classmethod
    def _validate_soil_moisture_params(cls, values: Dict[str, Any]) -> None:
        """Validate required fields are present if `soil_moisture_bmi` is `False`."""
        if values["soil_moisture_bmi"]:
            return

        def fmt_error(l: List[str]) -> str:
            if len(l) < 3:
                return " and ".join(l)
            return f'{", ".join(l[:-1])}, and {l[-1]}'

        errors: List[str] = []
        for field in ("soil_moisture_content", "soil_liquid_content"):
            if values.get(field, False) == False:
                errors.append(f"`{field}`")
        if errors:
            ValueError(
                f"{fmt_error(errors)} are required when `soil_moisture_bmi` is not set or `False`"
            )

    @override
    def to_ini_str(self) -> str:
        data = self.dict(by_alias=True, exclude_none=True, exclude_unset=True)
        return self._to_ini_str(data)

    class Config(serializer_deserializer.IniSerializerDeserializer.Config):
        field_type_serializers = {bool: lambda b: int(b)}
        no_section_headers: bool = True
        # extra space is not accounted for
        # https://github.com/NOAA-OWP/SoilFreezeThaw/blob/c674deadb27a2fa9bff79ff2f18dac9501a18fc9/src/soil_freeze_thaw.cxx#L134C5-L134C16
        space_around_delimiters: bool = False
