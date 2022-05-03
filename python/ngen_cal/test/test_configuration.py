import pytest
from typing import TYPE_CHECKING, Generator

from .utils import config

if TYPE_CHECKING:
    from ..configuration import Configuration
"""
    Test suite for reading and manipulating ngen configration files
"""

# TODO determmine if any unit tests of General config are appropriate
# pydantic is thoroughly tested upstream, but it may be a good idea to
# write some simple tests around the defaults
# may also want to implment some testing around the Model union/parsing

# @pytest.mark.usefixtures("conf", "realization_config")
# def test_config_file(conf: 'Configuration', realization_config: str) -> None:
#     """
#         Test configuration property `config_file`
#     """
#     assert conf.config_file == realization_config

# @pytest.mark.usefixtures("conf")
# def test_catchments(conf: 'Configuration') -> None:
#     """
#         Ensure that only the catchment marked with "calibration" is used in the configuration
#     """
#     assert len(conf.catchments) == 1
#     assert conf.catchments[0].id == 'test-catchment'
