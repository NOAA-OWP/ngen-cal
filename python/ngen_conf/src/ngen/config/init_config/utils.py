from __future__ import annotations

import re
from enum import Enum

from typing import (
    TYPE_CHECKING,
    Any,
    List,
    Generic,
    TypeVar,
)

from pydantic import validator
from pydantic.generics import GenericModel
from typing_extensions import Self

if TYPE_CHECKING:
    from pydantic.typing import AbstractSetIntStr, DictStrAny, MappingIntStrAny

L = TypeVar("L", bound=str)

# matches a number that can contain an e or E and a unit contained in square brackets examples:
# 2[m] -> group 0: 2 group 2: m
# 2.0[m] -> group 0: 2.0 group 2: m
# 4.05[] -> group 0: 4.05 group 2: ""
# 2e5[m] -> group 0: 2 group 1 e5 group 2: m
# 1.8e-05[m h-1] -> group 0: 1.8 group 1: e-05 group 2: m h-1
_FLOAT_UNIT_PAIR_RE_PATTERN = r"([-]?\d*\.\d+|[-]?\d+)([Ee][-+]?\d+)?\[([^\]]*)\]"
_FLOAT_UNIT_PAIR_RE = re.compile(_FLOAT_UNIT_PAIR_RE_PATTERN)


def _parse_float_unit_str(s: str) -> tuple[float, str]:
    match = _FLOAT_UNIT_PAIR_RE.search(s)

    if match is None:
        raise ValueError(f"no match in str: {s!r}")

    # examples
    #   2[m] -> ("2", "", "m")
    #   2.0E5[m] -> ("2.0", "E5", "m")
    number, exp, unit = match.groups()
    if exp is not None:
        number += exp

    number = float(number)
    return number, unit


class FloatUnitPair(GenericModel, Generic[L]):
    value: float
    unit: L

    @classmethod
    def __modify_schema__(cls, field_schema: dict[str, Any]):
        field_schema.update(
            type="string",
            pattern=_FLOAT_UNIT_PAIR_RE_PATTERN,
            examples=["2[m]", "4.05[m]", "1.8e-05[m h-1]"],
        )

    @classmethod
    def validate(cls: type[Self], value: Any) -> Self:
        if isinstance(value, FloatUnitPair):
            return value

        if isinstance(value, dict):
            v = value["value"]
            u = value["unit"]
            value = f"{v}[{u}]"

        if not isinstance(value, str):
            raise TypeError(f"invalid type: '{type(value)}'")

        value, unit = _parse_float_unit_str(value)
        return cls(value=value, unit=unit)

    def __repr__(self):
        return repr(str(self))

    def __str__(self):
        return f"{self.value}[{self.unit}]"

    def dict(
        self,
        *,
        include: AbstractSetIntStr | MappingIntStrAny | None = None,
        exclude: AbstractSetIntStr | MappingIntStrAny | None = None,
        by_alias: bool = False,
        skip_defaults: bool | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> DictStrAny:
        return str(self)


def serialize_enum_value(e: Enum) -> Any:
    return e.value


V = TypeVar("V")


class CSList(GenericModel, Generic[V]):
    """
    Wrapper around a List[V] that coerces a comma separated string of Vs
    (e.g. "1,2,3") into a List[V] (e.g. [1, 2, 3]). The `dict` method is
    overridden to return the inner list of Vs instead of {"__root__": [Vs...]}.
    As a result, using a CSList[V] as a field type in anther pydantic model
    behaves as if it were a List[V] with the added functionality of coercing a
    comma separated string into a list of Vs.

    The features this model provides could easily be achieved using a field
    level validator, so in some ways this is provided as a convenience. This
    model is most useful when a field can be multiple types (union type). It
    alleviates the need to implement a complex field level validator that
    handles all possible union type members.
    """

    __root__: List[V]

    @validator("__root__", pre=True)
    @classmethod
    def _validate_value(cls, value):
        if isinstance(value, str):
            return value.split(",")
        return value

    def __repr__(self) -> str:
        return str(self.__root__)

    def __str__(self) -> str:
        return repr(self)

    def dict(
        self,
        *,
        include: AbstractSetIntStr | MappingIntStrAny | None = None,
        exclude: AbstractSetIntStr | MappingIntStrAny | None = None,
        by_alias: bool = False,
        skip_defaults: bool | None = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> "DictStrAny":
        return ",".join(map(str, self.__root__))
