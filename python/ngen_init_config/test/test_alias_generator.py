import pytest
from typing import Tuple

from ngen.init_config.alias_generator import (
    camel_case,
    kabab_case,
    pascal_case,
    screaming_kabab_case,
    screaming_snake_case,
    snake_case,
)

cases = [
    "ThisThing",
    "thisThing",
    "this_thing",
    "THIS_THING",
    "this-thing",
    "THIS-THING",
]
expected = [
    (cases),
]


@pytest.mark.parametrize("test", cases)
@pytest.mark.parametrize("expected", expected)
def test_alias_generator_variants(
    test: str, expected: Tuple[str, str, str, str, str, str, str, str]
):
    assert pascal_case(test) == expected[0]
    assert camel_case(test) == expected[1]
    assert snake_case(test) == expected[2]
    assert screaming_snake_case(test) == expected[3]
    assert kabab_case(test) == expected[4]
    assert screaming_kabab_case(test) == expected[5]
