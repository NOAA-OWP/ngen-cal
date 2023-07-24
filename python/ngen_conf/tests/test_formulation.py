import pytest
from pydantic import BaseModel
from typing import Type
from ngen.config.formulation import Formulation

from ngen.config.cfe import CFE
from ngen.config.sloth import SLOTH
from ngen.config.topmod import Topmod
from ngen.config.noahowp import NoahOWP
from ngen.config.lstm import LSTM
from ngen.config.multi import MultiBMI

fixture_expected_type = (
    ("cfe_params", CFE),
    ("sloth_params", SLOTH),
    ("topmod_params", Topmod),
    ("noahowp_params", NoahOWP),
    ("lstm_params", LSTM),
    ("multi_params", MultiBMI),
)


@pytest.mark.parametrize("fixture_name, expected_type", fixture_expected_type)
def test_correct_forumulation_subtype_is_deserialized(
    fixture_name: str, expected_type: Type[BaseModel], request: pytest.FixtureRequest
):
    params = request.getfixturevalue(fixture_name)
    input_data = {"name": "test_formulation", "params": params}

    m = Formulation(**input_data)
    assert isinstance(
        m.params, expected_type
    ), f"expected: {expected_type.__name__!r}, got {type(m.params).__name__!r}"


initialized_fixture_expected_type = (
    ("cfe", CFE),
    ("sloth", SLOTH),
    ("topmod", Topmod),
    ("noahowp", NoahOWP),
    ("lstm", LSTM),
    ("multi", MultiBMI),
)


@pytest.mark.parametrize("fixture_name, expected_type", initialized_fixture_expected_type)
def test_correct_forumulation_subtype_is_initialized(
    fixture_name: str, expected_type: Type[BaseModel], request: pytest.FixtureRequest
):
    params = request.getfixturevalue(fixture_name)
    input_data = {"name": "test_formulation", "params": params}

    m = Formulation(**input_data)

    assert isinstance(
        m.params, expected_type
    ), f"expected: {expected_type.__name__!r}, got {type(m.params).__name__!r}"
