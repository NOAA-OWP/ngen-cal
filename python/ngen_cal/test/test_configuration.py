import pytest
from typing import Generator
from pathlib import Path
import json

from ..configuration import Configuration
from .utils import config

"""
    Test suite for reading and manipulating ngen configration files
"""

@pytest.fixture(scope="session")
def realization_config(tmpdir_factory):
    """
        Fixture to provide a staged testing input files
    """
    fn = tmpdir_factory.mktemp("data").join("realization_config.json")
    with(open(fn, 'w')) as fp:
        json.dump(config, fp)
    return fn

@pytest.fixture
def conf(realization_config) -> Generator[Configuration, None, None]:
    """
        Staging of a generator to test
    """
    yield Configuration(realization_config)

def test_config_file(conf: Configuration, realization_config):
    """
        Test configuration property `config_file`
    """
    assert conf.config_file == realization_config

def test_catchments(conf: Configuration):
    """
        Ensure that only the catchment marked with "calibration" is used in the configuration
    """
    assert len(conf.catchments) == 1
    assert conf.catchments[0].id == 'test-catchment'
