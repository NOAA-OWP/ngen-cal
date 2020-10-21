import pytest
from typing import TYPE_CHECKING

from ..search import dds

if TYPE_CHECKING:
    from ngen_cal.meta import CalibrationMeta
    from ngen_cal.calibration_cathment import CalibrationCatchment

"""
    Test suite for calibrtion search algorithms
"""

@pytest.mark.usefixtures("catchment", "meta")
def test_dds(catchment: 'CalibrationCatchment', meta: 'CalibrationMeta') -> None:
    """
        Test dds is callable
    """
    ret = dds(1, 2, catchment, meta)
    assert meta.best_score == -1
    assert meta.best_params == '0'
