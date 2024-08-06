from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Generic, List, Optional, Type, TypeVar, Union

from pydantic import validator
from pydantic.generics import GenericModel
from typing_extensions import Self, override

if TYPE_CHECKING:
    from pydantic.typing import AbstractSetIntStr, DictStrAny, MappingIntStrAny

V = TypeVar("V")
"""The type of `ValueUnitPair`'s `value` field."""
U = TypeVar("U")
"""The type of `ValueUnitPair`'s `unit` field."""


_VAL_UNIT_RE = re.compile(r"(.*)\[(.*)\]")


class ValueUnitPair(GenericModel, Generic[V, U]):
    value: V
    unit: U

    @override
    @classmethod
    def validate(cls: type[Self], value: Any) -> Self:
        if isinstance(value, ValueUnitPair):
            # return a shallow copy. this also validates / coerces mismatching generic types
            return cls(value=value.value, unit=value.unit)

        # unpack kwargs like arguments into expected string form
        if isinstance(value, dict):
            v = value.get("value", Ellipsis)
            u = value.get("unit", Ellipsis)
            if v == Ellipsis or u == Ellipsis:
                raise ValueError(f"cannot coerce value='{value!r}' into {cls.__name__}")
            return cls(value=v, unit=u)

        # cannot further coerce / validate value
        if not isinstance(value, str):
            raise ValueError(f"cannot coerce value='{value!r}' into {cls.__name__}")

        match = _VAL_UNIT_RE.search(value)

        if match is None:
            raise ValueError(f"no match in str: {value!r}")

        # examples
        #   2[m] -> ("2", "m")
        #   1,2,3,4[m/m] -> ("1,2,3,4", "m/m")
        value, unit = match.groups()
        return cls(value=value, unit=unit)

    @override
    @classmethod
    def parse_obj(cls: type[Self], obj: Any) -> Self:
        return cls.validate(obj)

    def _serialize(self) -> str:
        return f"{str(self.value)}[{str(self.unit)}]"

    @override
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
        return self._serialize()


# NOTE: type constraint could be relaxed in the future, but would need modification
T = TypeVar("T", str, int, float, bool)
"""The type of `ListUnitPair`'s list items. Constrained to non-nullable json primitive types."""


class ListUnitPair(ValueUnitPair[List[T], U], Generic[T, U]):
    @validator("value", pre=True)
    def _coerce_values(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, list):
            return value
        if not isinstance(value, str):
            raise ValueError(f"cannot coerce value='{value!r}' into list")

        return value.split(",") if value else []

    @override
    def _serialize(self) -> str:
        values = ",".join(map(str, self.value))
        return f"{values}[{str(self.unit)}]"
