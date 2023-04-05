import pytest
from ngen.init_config import (
    IniSerializerDeserializer,
    NamelistSerializerDeserializer,
    YamlSerializerDeserializer,
    TomlSerializerDeserializer,
    JsonSerializerDeserializer,
)
from ngen.init_config.core import Base
from typing import Any, Callable, Dict, List


class Lists(Base):
    bool_list: List[bool]
    float_list: List[float]
    int_list: List[int]
    str_list: List[str]


class KeyObject(Base):
    key: str


class Model(
    NamelistSerializerDeserializer,
    YamlSerializerDeserializer,
    TomlSerializerDeserializer,
    JsonSerializerDeserializer,
):
    lists: Lists
    key_object: KeyObject


@pytest.mark.parametrize(
    "test_file_fixture, deserializer",
    [
        # NOTE: `from_ini_str` is not included. python's `configparser` library does not natively support lists
        # see: https://en.wikipedia.org/wiki/INI_file#Comparison_of_INI_parsers
        ("yaml_test", Model.from_yaml_str),
        ("namelist_test", Model.from_namelist_str),
        ("toml_test", Model.from_toml_str),
        ("json_test", Model.from_json_str),
    ],
)
def test_deserialize(
    test_file_fixture: str,
    deserializer: Callable[[str], Model],
    test_data_as_dict: Dict[str, Any],
    request: pytest.FixtureRequest,
):
    test_data = request.getfixturevalue(test_file_fixture)
    o = deserializer(test_data)
    assert o.dict() == test_data_as_dict


def test_serialize(toml_test: str, yaml_test: str, namelist_test: str, json_test: str):
    # NOTE: `to_ini_str` is not included. python's `configparser` library does not natively support lists
    o = Model.from_toml_str(toml_test)
    assert o.to_yaml_str() == yaml_test

    namelist_str = o.to_namelist_str()
    # f90nml does not add a newline character
    # TODO: investigate if it should.
    assert len(namelist_str) + 1 == len(namelist_test)
    assert namelist_str == namelist_test[:-1]

    assert o.to_toml_str() == toml_test

    # read in file has newline character.
    assert o.to_json_str(indent=2) == json_test[:-1]


# NOTE: python's `configparser` library does not natively support lists, only support bool, int,
# float, str. see: https://en.wikipedia.org/wiki/INI_file#Comparison_of_INI_parsers
class IniModel(IniSerializerDeserializer):
    b: bool
    i: int
    f: float
    s: str


class IniWithHeaderModel(IniSerializerDeserializer):
    h: IniModel

    class Config(IniSerializerDeserializer.Config):
        field_type_serializers = {bool: lambda b: str(b).lower()}


class IniNoHeaderModel(IniModel):
    class Config(IniSerializerDeserializer.Config):
        no_section_headers = True
        field_type_serializers = {bool: lambda b: str(b).lower()}


class IniNoSpacesAroundDelimiterModel(IniWithHeaderModel):
    class Config(IniWithHeaderModel.Config):
        space_around_delimiters = False


class IniCaseSensitiveKeys(IniSerializerDeserializer):
    UPPER: bool
    lower: bool

    class Config(IniSerializerDeserializer.Config):
        no_section_headers = True
        preserve_key_case = True


@pytest.mark.parametrize(
    "test_file_fixture, deserializer, expected",
    [
        # NOTE: `from_ini_str` is not included. python's `configparser` library does not natively support lists
        # see: https://en.wikipedia.org/wiki/INI_file#Comparison_of_INI_parsers
        (
            "ini_test",
            IniWithHeaderModel.from_ini_str,
            IniWithHeaderModel(h=IniModel(b=True, i=1, f=1.0, s="test")),
        ),
        (
            "ini_no_spaces_around_delimiter_test",
            IniNoSpacesAroundDelimiterModel.from_ini_str,
            IniNoSpacesAroundDelimiterModel(h=IniModel(b=True, i=1, f=1.0, s="test")),
        ),
        (
            "ini_no_header_test",
            IniNoHeaderModel.from_ini_str,
            IniNoHeaderModel(b=True, i=1, f=1.0, s="test"),
        ),
    ],
)
def test_deserialize_from_ini(
    test_file_fixture: str,
    deserializer: Callable[[str], Model],
    expected: IniSerializerDeserializer,
    request: pytest.FixtureRequest,
):
    test_data = request.getfixturevalue(test_file_fixture)
    o = deserializer(test_data)
    assert o == expected


@pytest.mark.parametrize(
    "expected_fixture_name, deserialized",
    [
        (
            "ini_test",
            IniWithHeaderModel(h=IniModel(b=True, i=1, f=1.0, s="test")),
        ),
        (
            "ini_no_spaces_around_delimiter_test",
            IniNoSpacesAroundDelimiterModel(h=IniModel(b=True, i=1, f=1.0, s="test")),
        ),
        (
            "ini_no_header_test",
            IniNoHeaderModel(b=True, i=1, f=1.0, s="test"),
        ),
    ],
)
def test_serialize_to_ini(
    expected_fixture_name: str,
    deserialized: IniSerializerDeserializer,
    request: pytest.FixtureRequest,
):
    expected: str = request.getfixturevalue(expected_fixture_name)
    # ignore line comments
    expected = "\n".join(
        line
        for line in expected.split("\n")
        if not line.startswith(";") or line.startswith("#")
    )

    assert deserialized.to_ini_str() == expected


def test_case_sensitivity_key_to_ini():
    o = IniCaseSensitiveKeys(UPPER=True, lower=False)

    s = o.to_ini_str()
    lines = s.split("\n")[:-1]
    assert lines == ["UPPER = True", "lower = False"]
