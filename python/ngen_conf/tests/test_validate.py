from pathlib import Path
from pydantic import BaseModel
from ngen.config.validate import validate_paths


class B(BaseModel):
    b: Path


class A(BaseModel):
    a: Path
    b: B


def test_validate_positive():
    positive = A(a=__file__, b=B(b=__file__))
    val = validate_paths(positive)
    assert len(val) == 0


def test_validate_negative():
    negative = A(a="some-fake-path", b=B(b="some-fake-path"))
    val = validate_paths(negative)
    assert len(val) == 2
    assert val[0].model == negative
    assert val[1].model == negative.b
