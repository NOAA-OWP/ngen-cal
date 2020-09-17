import pytest
from typing import Generator
from pathlib import Path
import pandas as pd

from ngen_cal.search import dds
from ngen_cal.calibration_cathment import CalibrationCatchment

"""
    Test suite for calibrtion search algorithms
"""
_current_dir = Path(__file__).resolve().parent

@pytest.fixture
def calibratable() -> Generator[CalibrationCatchment, None, None]:
    """
        Staging of a generator to test
    """

    yield CalibrationCatchment("test-calibratable")

def test_dds(calibratable: CalibrationCatchment):
    """
        Test dds is callable
    """
    ret = dds(1, 2, calibratable, 'echo', 'log')
    assert conf.data != None
    assert len(conf._catchments) != 0
