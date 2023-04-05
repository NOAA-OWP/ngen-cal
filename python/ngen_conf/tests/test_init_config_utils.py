import pytest
from pydantic import BaseModel, ValidationError

from ngen.config.init_config.utils import _parse_float_unit_str, FloatUnitPair

from typing import Literal, Tuple

re_input_validation = [
    ("-2[m]", (-2.0, "m")),
    ("2[m]", (2.0, "m")),
    ("2e5[m]", (2e5, "m")),
    ("2.0[m]", (2.0, "m")),
    ("4.05[]", (4.05, "")),
    ("0.00000338[m s-1]", (0.00000338, "m s-1")),
    ("0.355[m]", (0.355, "m")),
    ("1.0[m/m]", (1.0, "m/m")),
    ("0.439[m/m]", (0.439, "m/m")),
    ("0.066[m/m]", (0.066, "m/m")),
    ("1.0[]", (1.0, "")),
    ("0.25[m]", (0.25, "m")),
    ("1.8e-05[m h-1]", (1.8e-05, "m h-1")),
    ("6.0[]", (6.0, "")),
    ("6.0E10[]", (6.0e10, "")),
    ("0.125[m/m]", (0.125, "m/m")),
    ("0.33[]", (0.33, "")),
    ("0.585626[m/m]", (0.585626, "m/m")),
    ("0.03[]", (0.03, "")),
    ("0.01[]", (0.01, "")),
]


@pytest.mark.parametrize("input, validation", re_input_validation)
def test_parse_float_unit_str(input: str, validation: Tuple[float, str]):
    assert _parse_float_unit_str(input) == validation


def test_float_unit_pair_any_unit_str():
    validation = "42.0[some-unit]"
    o = FloatUnitPair[str].validate(validation)
    assert o.dict() == validation


def test_float_unit_pair_mm_unit():
    validation = "42.0[mm]"
    MM_Model = FloatUnitPair[Literal["mm"]]
    o = MM_Model.validate(validation)
    assert o.dict() == validation

    with pytest.raises(ValidationError):
        should_fail = "42[failures]"
        MM_Model.validate(should_fail)


class Foo(BaseModel):
    # should accept any string as a `unit`
    field: FloatUnitPair[str]


class Bar(BaseModel):
    # should only accept `mm` as a `unit` argument
    field: FloatUnitPair[Literal["mm"]]


def test_embedded_float_unit_pair():
    o = Foo(field="42.0[some-unit]")
    assert o.dict()["field"] == "42.0[some-unit]"


def test_embedded_and_constrained_float_unit_pair():
    o = Bar(field="42.0[mm]")
    assert o.dict()["field"] == "42.0[mm]"


def test_float_unit_pair_has_correct_schema():
    schema = Foo.schema()
    assert schema["properties"]["field"]["type"] == "string"
