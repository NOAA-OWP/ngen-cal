import pytest
from typing import TYPE_CHECKING

from ngen.cal.search import dds

if TYPE_CHECKING:
    from ngen.cal.calibration_cathment import CalibrationCatchment
    from ngen.cal.agent import Agent

"""
    Test suite for calibrtion search algorithms
"""

@pytest.mark.usefixtures("catchment", "agent")
def test_dds(catchment: 'CalibrationCatchment', agent: 'Agent') -> None:
    """
        Test dds is callable
    """
    ret = dds(1, 2, catchment, agent)
    assert catchment.best_score == 0.0
    assert catchment.best_params == '2'
