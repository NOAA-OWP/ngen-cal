import pytest
from typing import Generator
from pathlib import Path

from ngen_cal import Configuration

"""
    Test suite for reading and manipulating ngen configration files
"""
_current_dir = Path(__file__).resolve().parent

@pytest.fixture
def conf() -> Generator[Configuration, None, None]:
    """
        Staging of a generator to test
    """
    test_config_file = _current_dir.joinpath('data/example_realization_config.json')
    test_calibraiton_file = ''
    yield Configuration(test_config_file, test_calibraiton_file)

def test_configuration(conf: Configuration):
    """
        Test configuration is properly constructed
    """
    assert conf.data != None
    assert len(conf._catchments) != 0
