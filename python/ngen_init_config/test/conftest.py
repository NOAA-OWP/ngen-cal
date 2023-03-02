from pytest import fixture
from pathlib import Path
from typing import Any, Dict

TEST_DIR = Path(__file__).parent
DATA_DIR = TEST_DIR / "data"

__INI_CONFIG = "test.ini"
__INI_NO_HEADER_CONFIG = "test_no_header.ini"
__INI_NO_SPACES_CONFIG = "test_no_space_around_delimiters.ini"
__YAML_CONFIG = "test.yaml"
__NAMELIST_CONFIG = "test.namelist"
__TOML_CONFIG = "test.toml"


@fixture
def test_data_as_dict() -> Dict[str, Any]:
    return {
        "lists": {
            "int_list": [1, 2],
            "float_list": [1.0, 2.0],
            "str_list": ["a", "b"],
            "bool_list": [True, False],
        },
        "key_object": {"key": "value"},
    }


@fixture
def ini_test() -> str:
    return (DATA_DIR / __INI_CONFIG).read_text()


@fixture
def ini_no_header_test() -> str:
    return (DATA_DIR / __INI_NO_HEADER_CONFIG).read_text()


@fixture
def ini_no_spaces_around_delimiter_test() -> str:
    return (DATA_DIR / __INI_NO_SPACES_CONFIG).read_text()


@fixture
def yaml_test() -> str:
    return (DATA_DIR / __YAML_CONFIG).read_text()


@fixture
def namelist_test() -> str:
    return (DATA_DIR / __NAMELIST_CONFIG).read_text()


@fixture
def toml_test() -> str:
    return (DATA_DIR / __TOML_CONFIG).read_text()
