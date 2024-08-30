from __future__ import annotations

import io
import pathlib
import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Literal,
    Protocol,
    runtime_checkable,
)

import typing_extensions
from pydantic import Field, root_validator, validator

import ngen.init_config.serializer_deserializer as serde
from ngen.config.path_pair.path_pair import path_pair
from ngen.config.path_pair import PathPair

if TYPE_CHECKING:
    from typing_extensions import Self


@runtime_checkable
class _Readliner(Protocol):
    """
    A type that implements a `readline` method.
    For example a `io.TextIOWrapper` or `io.StringIO`:

        with open("file.txt") as fp:
            line = fp.readline()
    """

    def readline(self, size: int = -1, /) -> str: ...


def _maybe_into_readliner(obj: Any) -> _Readliner | None:
    if isinstance(obj, _Readliner):
        return obj
    elif isinstance(obj, str):
        return io.StringIO(obj)
    elif isinstance(obj, bytes):
        # assume utf-8 encoding
        obj = obj.decode()
        return io.StringIO(obj)
    else:
        return None


def _verify_topmodel_str(s: str, field_name: str) -> None:
    assert (
        len(s.encode()) < 256
    ), f"`{field_name}` must be less that 256 bytes in length"


class TopModelSubcat(serde.GenericSerializerDeserializer):
    # 1 for ngen
    num_sub_catchments: int = Field(gt=0)
    # unused
    imap: int = 1
    # TODO: serialize as int
    yes_print_output: Literal[0, 1] = 0
    subcat: str
    # number of topodex histogram values
    num_topodex_values: int = Field(gt=0)
    # catchment area as % to whole catchment (set to 1) for ngen
    area: float = 1.0
    # NOTE: only 1 value accepted for ngen; might need to change in the future
    # NOTE: length is equal to `num_topodex_values`
    dist_area_lnaotb: List[float]
    # NOTE: only 1 value accepted for ngen; might need to change in the future
    # NOTE: length is equal to `num_topodex_values`
    lnaotb: List[float]
    # should be 1 for ngen
    num_channels: int = Field(1, gt=0)
    # NOTE: length is equal to `num_channels`
    cum_dist_area_with_dist: List[float]
    # NOTE: length is equal to `num_channels`
    dist_from_outlet: List[float]

    @typing_extensions.override
    @classmethod
    def parse_obj(cls: type[Self], obj: Any) -> Self:
        if (r := _maybe_into_readliner(obj)) is not None:
            return cls._parse(r)
        return super().parse_obj(obj)

    @staticmethod
    def _verify_num_sub_catchments(n: int) -> None:
        if n > 1:
            warnings.warn(
                "`num_sub_catchments` > 1, set to 1 for use with NextGen Framework",
                UserWarning,
            )

    @root_validator
    @classmethod
    def _verify(cls, values: dict[str, Any]) -> dict[str, Any]:
        cls._verify_num_sub_catchments(values["num_sub_catchments"])
        _verify_topmodel_str(values["subcat"], "subcat")

        # verify `num_topodex_values` == len(`dist_area_lnaotb`) == len(`lnaotb`)
        num_topodex_values = values["num_topodex_values"]
        dist_area_lnaotb = values["dist_area_lnaotb"]
        lnaotb = values["lnaotb"]
        assert (
            num_topodex_values == len(dist_area_lnaotb)
        ), f"`got {len(dist_area_lnaotb)} `dist_area_lnaotb` records, expected {num_topodex_values} (`num_topodex_values`)"
        assert (
            num_topodex_values == len(lnaotb)
        ), f"`got {len(lnaotb)} `lnaotb` records, expected {num_topodex_values} (`num_topodex_values`)"

        # verify `num_channels` == len(`cum_dist_area_with_dist`) == len(`dist_from_outlet`)
        num_channels = values["num_channels"]
        cum_dist_area_with_dist = values["cum_dist_area_with_dist"]
        dist_from_outlet = values["dist_from_outlet"]
        assert (
            num_channels == len(cum_dist_area_with_dist)
        ), f"`got {len(cum_dist_area_with_dist)} `cum_dist_area_with_dist` records, expected {num_channels} (`num_channels`)"
        assert (
            num_channels == len(dist_from_outlet)
        ), f"`got {len(dist_from_outlet)} `dist_from_outlet` records, expected {num_channels} (`num_channels`)"

        return values

    @classmethod
    def _parse(cls, reader: _Readliner) -> Self:
        # 1 1 1
        # Extracted study basin: Taegu Pyungkwang River
        # 1 1
        # 0.000001 9.382756
        # 1
        # 0.0 500.
        # NOTE: only parsing handled here, invariants enforced in validators
        data = {}
        cat_imap_out_str = reader.readline()
        assert (
            cat_imap_out_str != ""
        ), "missing `num_sub_catchments` `imap` `yes_print_output`"
        cat_imap_out = cat_imap_out_str.split(" ")
        assert (
            len(cat_imap_out) == 3
        ), f"incorrect number of fields in `num_sub_catchments` `imap` `yes_print_output` line, got {len(cat_imap_out)}"

        data["num_sub_catchments"] = int(cat_imap_out[0])
        data["imap"] = int(cat_imap_out[1])
        data["yes_print_output"] = int(cat_imap_out[2])

        assert data["num_sub_catchments"] > 0, "`num_sub_catchments` must be > 0"

        # drop trailing newline
        title = reader.readline().rstrip("\r\n")
        data["subcat"] = title

        ntopo_area_str = reader.readline()
        assert ntopo_area_str != "", "missing `num_topodex_values` `area`"
        ntopo_area = ntopo_area_str.split(" ")
        assert (
            len(ntopo_area) == 2
        ), f"incorrect number of fields in `num_topodex_values` `area`, got {len(ntopo_area)}"
        data["num_topodex_values"] = int(ntopo_area[0])
        data["area"] = float(ntopo_area[1])

        assert data["num_topodex_values"] > 0, "`num_topodex_values` must be > 0"

        dist_area_lnaotb: list[float] = []
        lnaotb: list[float] = []
        for _ in range(data["num_topodex_values"]):
            distarea_lnaotb_str = reader.readline()
            assert distarea_lnaotb_str != "", "missing `dist_area_lnaotb` `lnaotb`"
            distarea_lnaotb = distarea_lnaotb_str.split(" ")
            assert (
                len(distarea_lnaotb) == 2
            ), f"incorrect number of fields in `dist_area_lnaotb` `lnaotb`, got {len(ntopo_area)}"
            dist_area_lnaotb.append(float(distarea_lnaotb[0]))
            lnaotb.append(float(distarea_lnaotb[1]))
        data["dist_area_lnaotb"] = dist_area_lnaotb
        data["lnaotb"] = lnaotb

        num_channels_str = reader.readline()
        assert num_channels_str != "", "missing `num_channels`"
        data["num_channels"] = int(num_channels_str)
        assert (
            data["num_channels"] > 0
        ), f"`num_channels` must be > 0, got {data['num_channels']}"

        cumdist_distfromoutlet_str = reader.readline()
        assert (
            cumdist_distfromoutlet_str != ""
        ), "missing `cum_dist_area_with_dist` `dist_from_outlet`"
        cumdist_distfromoutlet = cumdist_distfromoutlet_str.split(" ")
        assert (
            len(cumdist_distfromoutlet) == 2 * data["num_channels"]
        ), f"incorrect number of fields in `cum_dist_area_with_dist` `dist_from_outlet`, got {len(cumdist_distfromoutlet )}, expected {data['num_channels'] * 2}"

        data["cum_dist_area_with_dist"] = cumdist_distfromoutlet[::2]
        data["dist_from_outlet"] = cumdist_distfromoutlet[1::2]
        return cls(**data)

    @typing_extensions.override
    def to_str(self, *_) -> str:
        # 1 1 1
        # Extracted study basin: Taegu Pyungkwang River
        # 2 1
        # 0.000001 9.382756
        # 0.000001 9.382756
        # 2
        # 0.0 500. 0.0 500.
        dist_and_lnaotb = "\n".join(
            f"{dist_area_lnaotb} {lnaotb}"
            for dist_area_lnaotb, lnaotb in zip(self.dist_area_lnaotb, self.lnaotb)
        )

        dist_and_outlet = " ".join(
            f"{cum_dist_area_with_dist} {dist_from_outlet}"
            for cum_dist_area_with_dist, dist_from_outlet in zip(
                self.cum_dist_area_with_dist, self.dist_from_outlet
            )
        )
        return f"""{self.num_sub_catchments} {self.imap} {self.yes_print_output}
{self.subcat}
{self.num_topodex_values} {self.area}
{dist_and_lnaotb}
{self.num_channels}
{dist_and_outlet}"""

    @typing_extensions.override
    def to_file(self, p: pathlib.Path, *_) -> None:
        p.write_text(self.to_str())

    @typing_extensions.override
    @classmethod
    def from_str(cls, s: str, *_) -> Self:
        return cls.parse_obj(s)

    @typing_extensions.override
    @classmethod
    def from_file(cls, p: pathlib.Path, *_) -> Self:
        return cls.parse_file(p)


class TopModelParams(serde.GenericSerializerDeserializer):
    subcat: str
    """ info_string character title of subcatment; often same as model title"""
    szm: float
    """ meters parameter_fixed rainfall-runoff exponential scaling parameter for the decline of transmissivity with increase in storage deficit; units of depth"""
    t0: float
    """ meters/hour parameter_adjustable  downslope transmissivity when the soil is just saturated to the surface"""
    td: float
    """ hours parameter_adjustable rainfall-runoff unsaturated zone time delay per unit storage deficit"""
    chv: float
    """ meters/hour parameter_fixed overland flow average channel flow velocity"""
    rv: float
    """ meters/hour parameter_fixed overland flow internal overland flow routing velocity"""
    srmax: float
    """ meters parameter_adjustable rainfall-runoff maximum root zone storage deficit"""
    q0: float
    """ meters/hour state  initial subsurface flow per unit area"""
    sr0: float
    """ meters state  initial root zone storage deficit below field capacity"""
    infex: Literal[0, 1] = 0
    """boolean option green-ampt set to 1 to call subroutine to do infiltration excess calcs; not usually appropriate in catchments where Topmodel is applicable (shallow highly permeable soils); default to 0"""
    xk0: float
    """meters/hour parameter_adjustable rainfall-runoff surface soil hydraulic conductivity"""
    hf: float
    """meters parameter_adjustable green-ampt wetting front suction for G&A soln."""
    dth: float
    """parameter_adjustable green-ampt water content change across the wetting front; dimensionless"""

    @validator("infex", pre=True)
    @classmethod
    def _coerce_infex(cls, value: str | int):
        return int(value)

    @root_validator
    @classmethod
    def _verify(cls, values: dict[str, Any]) -> dict[str, Any]:
        _verify_topmodel_str(values["subcat"], "subcat")
        return values

    class Config(serde.GenericSerializerDeserializer.Config):
        fields = {"q0": {"alias": "Q0"}}

    @typing_extensions.override
    @classmethod
    def parse_obj(cls: type[Self], obj: Any) -> Self:
        if (r := _maybe_into_readliner(obj)) is not None:
            return cls._parse(r)
        return super().parse_obj(obj)

    @classmethod
    def _parse(cls, reader: _Readliner) -> Self:
        # Extracted study basin: Taegu Pyungkwang River
        # 0.032 5.0 50. 3600.0 3600.0 0.05 0.0000328 0.002 0 1.0 0.02 0.1
        title = reader.readline().rstrip("\r\n")

        rest_str = reader.readline()
        rest = rest_str.split(" ")
        assert (
            len(rest) == 12
        ), f"wrong number of parameters expected 12, got {len(rest)}"
        fields = (
            "szm",
            "t0",
            "td",
            "chv",
            "rv",
            "srmax",
            "Q0",
            "sr0",
            "infex",
            "xk0",
            "hf",
            "dth",
        )
        data: dict[str, str] = dict(zip(fields, rest))
        data["subcat"] = title
        return cls(**data)  # type: ignore

    @typing_extensions.override
    def to_str(self, *_) -> str:
        # Extracted study basin: Taegu Pyungkwang River
        # 0.032 5.0 50. 3600.0 3600.0 0.05 0.0000328 0.002 0 1.0 0.02 0.1
        # SAFETY: Changed in version 3.7: Dictionary order is guaranteed to be
        # insertion order. This behavior was an implementation detail of
        # CPython from 3.6.
        # https://docs.python.org/3.12/library/stdtypes.html#dict
        values = (
            str(getattr(self, field))
            for field in self.__fields__.keys()
            if field != "subcat"
        )
        return f"{self.subcat}\n{' '.join(values)}"

    @typing_extensions.override
    def to_file(self, p: pathlib.Path, *_) -> None:
        p.write_text(self.to_str())

    @typing_extensions.override
    @classmethod
    def from_str(cls, s: str, *_) -> Self:
        return cls.parse_obj(s)

    @typing_extensions.override
    @classmethod
    def from_file(cls, p: pathlib.Path, *_) -> Self:
        return cls.parse_file(p)


class Topmodel(serde.GenericSerializerDeserializer):
    stand_alone: Literal[0, 1] = 0
    title: str
    # NOTE: never used with ngen
    input: pathlib.Path = pathlib.Path("/dev/null")
    if TYPE_CHECKING:
        subcat: PathPair[TopModelSubcat]
        params: PathPair[TopModelParams]
    else:
        subcat: path_pair(
            TopModelSubcat,
            serializer=lambda o: o.to_str().encode(),
            deserializer=TopModelSubcat.parse_obj,
        )
        params: path_pair(
            TopModelParams,
            serializer=lambda o: o.to_str().encode(),
            deserializer=TopModelParams.parse_obj,
        )
    output: pathlib.Path = pathlib.Path("/dev/null")
    hyd: pathlib.Path = pathlib.Path("/dev/null")

    @validator("stand_alone", pre=True)
    @classmethod
    def _coerce_stand_along(cls, value: str | int):
        value = int(value)
        if value > 0:
            warnings.warn(
                "set `stand_alone=0` for use with the NextGen Framework", UserWarning
            )
        return value

    @validator("subcat", pre=True)
    def _coerce_topmodel_subcat_into_pathpair(cls, value: Any) -> Any:
        return cls._maybe_coerce_into_pathpair(TopModelSubcat, value)

    @validator("params", pre=True)
    def _coerce_topmodel_params_into_pathpair(cls, value: Any) -> Any:
        return cls._maybe_coerce_into_pathpair(TopModelParams, value)

    @staticmethod
    def _maybe_coerce_into_pathpair(ty: type, value: Any) -> Any:
        if isinstance(value, ty):
            return PathPair[ty].with_object(value)
        return value

    @typing_extensions.override
    @classmethod
    def parse_obj(cls: type[Self], obj: Any) -> Self:
        if (r := _maybe_into_readliner(obj)) is not None:
            return cls._parse(r)
        return super().parse_obj(obj)

    @classmethod
    def _parse(cls, reader: _Readliner) -> Self:
        # 1
        # Taegu Pyungkwang River Catchment: Calibration Data
        # data/inputs.dat
        # data/subcat.dat
        # data/params.dat
        # topmod.out
        # hyd.out
        data = {}

        stand_alone = reader.readline().rstrip("\r\n")
        assert stand_alone != "", "missing `stand_alone`"
        data["stand_alone"] = stand_alone

        title = reader.readline().rstrip("\r\n")
        data["title"] = title

        inputs = reader.readline().rstrip("\r\n")
        assert inputs != "", "missing `inputs.dat`"
        data["input"] = inputs

        subcat = reader.readline().rstrip("\r\n")
        assert subcat != "", "missing `subcat.dat`"
        data["subcat"] = subcat

        params = reader.readline().rstrip("\r\n")
        assert params != "", "missing `params.dat`"
        data["params"] = params

        output = reader.readline().rstrip("\r\n")
        assert output != "", "missing `topmod.out`"
        data["output"] = output

        hyd = reader.readline().rstrip("\r\n")
        assert hyd != "", "missing `hyd.out`"
        data["hyd"] = hyd

        return cls(**data)  # type: ignore

    @typing_extensions.override
    def to_str(self, *_) -> str:
        # 1
        # Taegu Pyungkwang River Catchment: Calibration Data
        # data/inputs.dat
        # data/subcat.dat
        # data/params.dat
        # topmod.out
        # hyd.out
        return f"""{self.stand_alone}
{self.title}
{self.input}
{self.subcat}
{self.params}
{self.output}
{self.hyd}"""

    @typing_extensions.override
    def to_file(self, p: pathlib.Path, *_) -> None:
        p.write_text(self.to_str())

    @typing_extensions.override
    @classmethod
    def from_str(cls, s: str, *_) -> Self:
        return cls.parse_obj(s)

    @typing_extensions.override
    @classmethod
    def from_file(cls, p: pathlib.Path, *_) -> Self:
        return cls.parse_file(p)
