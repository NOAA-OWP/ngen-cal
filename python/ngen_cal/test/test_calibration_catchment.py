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

@pytest.mark.usefixtures("catchment2")
def test_output(catchment2: 'CalibrationCatchment', mocker) -> None:
    """
        Test proper handling of non-existent output
    """
    mock = mocker.patch('builtins.open')
    mock.mock_open.side_effect = FileNotFoundError()
    output = catchment2.output
    assert output == None

@pytest.mark.usefixtures("catchment")
def test_observed(catchment: 'CalibrationCatchment') -> None:
    """
        Test proper handling of non-existent output
    """
    catchment.observed = None
    with pytest.raises(RuntimeError):
        obs = catchment.observed
