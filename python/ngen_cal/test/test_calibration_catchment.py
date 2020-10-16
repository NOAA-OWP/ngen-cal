import pytest
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ngen_cal.calibration_cathment import CalibrationCatchment

"""
    Test suite for calibratable_catchment
"""

@pytest.mark.usefixtures("catchment")
def test_df(catchment: 'CalibrationCatchment') -> None:
    """
        Test the catchments proper construction of the parameter dataframe
    """
    assert catchment.df.iloc[0]['param'] == 'some_param'
    assert catchment.df.iloc[0]['0'] == 0.5
    assert catchment.df.iloc[0]['min'] == 0.0
    assert catchment.df.iloc[0]['max'] == 1.0

@pytest.mark.usefixtures("catchment")
def test_output(catchment: 'CalibrationCatchment') -> None:
    """
        Test proper handling of non-existent output
    """
    catchment.output = None
    with pytest.raises(RuntimeError):
        out = catchment.output

@pytest.mark.usefixtures("catchment")
def test_observed(catchment: 'CalibrationCatchment') -> None:
    """
        Test proper handling of non-existent output
    """
    catchment.observed = None
    with pytest.raises(RuntimeError):
        obs = catchment.observed
