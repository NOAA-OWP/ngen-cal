import pytest
from typing import Generator
from pathlib import Path
from copy import deepcopy
from .utils import config

from ngen_cal.calibration_cathment import CalibrationCatchment

"""
    Test suite for calibratable_catchment
"""

@pytest.fixture
def catchment() -> Generator[CalibrationCatchment, None, None]:
    """
        A hy_features catchment implementing the calibratable interface
    """
    id = 'test-catchment'
    catchment = deepcopy(config)['catchments'][id]
    return(CalibrationCatchment(id, catchment))

def test_df(catchment):
    """
        Test the catchments proper construction of the parameter dataframe
    """
    assert catchment.df.iloc[0]['param'] == 'some_param'
    assert catchment.df.iloc[0]['0'] == 0.5
    assert catchment.df.iloc[0]['min'] == 0.0
    assert catchment.df.iloc[0]['max'] == 1.0

def test_output(catchment):
    """
        Test proper handling of non-existent output
    """
    catchment.output = None
    with pytest.raises(RuntimeError):
        out = catchment.output

def test_observed(catchment):
    """
        Test proper handling of non-existent output
    """
    catchment.observed = None
    with pytest.raises(RuntimeError):
        obs = catchment.observed
