import pytest
from typing import TYPE_CHECKING, Generator

from .utils import config

if TYPE_CHECKING:
    from ..configuration import Configuration
"""
    Test suite for reading and manipulating ngen configration files
"""

@pytest.mark.usefixtures("conf", "realization_config")
def test_config_file(conf: 'Configuration', realization_config: str) -> None:
    """
        Test configuration property `config_file`
    """
    assert conf.config_file == realization_config

@pytest.mark.usefixtures("conf")
def test_catchments(conf: 'Configuration') -> None:
    """
        Ensure that only the catchment marked with "calibration" is used in the configuration
    """
    assert len(conf.catchments) == 1
    assert conf.catchments[0].id == 'test-catchment'
