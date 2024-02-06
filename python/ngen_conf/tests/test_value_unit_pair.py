import typing

import pydantic
import pytest
from ngen.config.init_config.value_unit_pair import ListUnitPair, ValueUnitPair


@pytest.mark.parametrize(
    "ty, value, unit",
    (
        (int, 42, "m"),
        (float, 42.0, "m"),
        (str, "42", "m"),
        (bool, True, "m"),
    ),
)
def test_value_unit_pair_initialization(ty: type, value, unit: str):
    o = ValueUnitPair[ty, typing.Literal[unit]](value=value, unit=unit)
    assert o.value == value
    assert o.unit == unit
    assert type(o.value) == type(value)
    assert type(o.unit) == type(unit)


@pytest.mark.parametrize(
    "ty, value, unit",
    (
        (int, "not a number", "m"),
        (float, 2j, "m"),
        (str, 2j, "m"),
        (bool, 2j, "m"),
    ),
)
def test_value_unit_pair_initialization_negative(ty: type, value, unit: str):
    with pytest.raises(pydantic.ValidationError):
        ValueUnitPair[ty, typing.Literal[unit]](value=value, unit=unit)


@pytest.mark.parametrize(
    "ty, value, unit, expected",
    (
        (int, 42, "m", "42[m]"),
        (float, 42.0, "m", "42.0[m]"),
        (str, "42", "m", "42[m]"),
        (bool, True, "m", "True[m]"),
    ),
)
def test_value_unit_pair_serialize(ty: type, value, unit: str, expected: str):
    o = ValueUnitPair[ty, typing.Literal[unit]](value=value, unit=unit)
    assert o.dict() == expected


@pytest.mark.parametrize(
    "serial, expected",
    (
        ("42[m]", ValueUnitPair[int, typing.Literal["m"]](value=42, unit="m")),
        ("42.0[m]", ValueUnitPair[float, typing.Literal["m"]](value=42.0, unit="m")),
        ("42[m]", ValueUnitPair[str, typing.Literal["m"]](value="42", unit="m")),
        ("True[m]", ValueUnitPair[bool, typing.Literal["m"]](value=True, unit="m")),
    ),
)
def test_value_unit_pair_from_str(serial: str, expected: ValueUnitPair):
    assert expected.parse_obj(serial) == expected


@pytest.mark.parametrize(
    "ty, value, unit",
    (
        (int, [1, 2, 3], "m"),
        (float, [1.0, 2.0, 3.0], "m"),
        (str, ["a", "b", "c"], "m"),
        (bool, [True, False, True], "m"),
    ),
)
def test_list_unit_pair_initialization(ty: type, value, unit: str):
    o = ListUnitPair[ty, typing.Literal[unit]](value=value, unit=unit)
    assert o.value == value
    assert o.unit == unit
    assert type(o.value) == type(value)
    assert type(o.unit) == type(unit)


@pytest.mark.parametrize(
    "ty, value, unit, expected",
    (
        (int, [], "m", "[m]"),
        (int, [1, 2, 3], "m", "1,2,3[m]"),
        (int, "", "m", "[m]"),
        (int, "1,2,3", "m", "1,2,3[m]"),
        (int, "   1,2,3", "m", "1,2,3[m]"),
        (int, "1,2,3   ", "m", "1,2,3[m]"),
        (int, "   1,2,3   ", "m", "1,2,3[m]"),
    ),
)
def test_list_unit_pair_serialize(ty: type, value, unit: str, expected: str):
    o = ListUnitPair[ty, typing.Literal[unit]](value=value, unit=unit)
    assert o.dict() == expected


def test_generic_bounds_are_upheld():
    m = typing.Literal["m"]
    o = ValueUnitPair[str, m](value="42", unit="m")
    assert isinstance(o.value, str)

    o2 = ValueUnitPair[int, m].parse_obj(o)
    assert isinstance(o2.value, int)


def test_generic_bounds_are_upheld_when_composed():
    class Outer(pydantic.BaseModel):
        inner: ValueUnitPair[int, typing.Literal["m"]]

    o = ValueUnitPair[str, typing.Literal["m"]](value="42", unit="m")
    o2 = Outer(inner=o)
    assert isinstance(o2.inner.value, int)


def test_generic_bounds_are_upheld_negative():
    m = typing.Literal["m"]
    o = ValueUnitPair[str, m](value="not coercible to int", unit="m")
    assert isinstance(o.value, str)

    with pytest.raises(pydantic.ValidationError):
        ValueUnitPair[int, m].parse_obj(o)
