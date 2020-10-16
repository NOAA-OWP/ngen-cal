import pytest
from math import inf
from typing import TYPE_CHECKING
import pandas as pd # type: ignore
if TYPE_CHECKING:
    from pandas import DataFrame
from ngen_cal.objectives import *

#A data frame of "perfectly simulated" data
perfect_data = pd.DataFrame({'Simulated_cms':[0,1,2,3,4,5], 'Observed_cms':[0,1,2,3,4,5]})
under_estimate = pd.DataFrame({'Simulated_cms':[0,0,0,0,0], 'Observed_cms':[1,1,1,1,1]})
#TODO deal with divide by zero in objectives
over_estimate = pd.DataFrame({'Simulated_cms':[2,2,2,2,2], 'Observed_cms':[1,1,1,1,1]})

@pytest.mark.parametrize(
"data, expected",
[
    pytest.param(perfect_data, 1.0),
    pytest.param(under_estimate, -inf),
    pytest.param(over_estimate, -inf)
]
)
def test_nse(data, expected):
    result = nash_sutcliffe(data['Simulated_cms'], data['Observed_cms'])
    assert result == expected

@pytest.mark.parametrize(
"data, expected",
[
    pytest.param(perfect_data, 1.0),
    pytest.param(under_estimate, 0.0),
    pytest.param(over_estimate, 0)
]
)
def test_nnse(data, expected):
    result = normalized_nash_sutcliffe(data['Simulated_cms'], data['Observed_cms'])
    assert result == expected

@pytest.mark.parametrize(
"data, expected",
[
    pytest.param(perfect_data, 0.0),
    pytest.param(under_estimate, -1.0),
    pytest.param(over_estimate, 1.0)
]
)
def test_peak(data, expected):
    result = peak_error_single(data['Simulated_cms'], data['Observed_cms'])
    assert result == expected

@pytest.mark.parametrize(
"data, expected",
[
    pytest.param(perfect_data, 0.0),
    pytest.param(under_estimate, -1.0),
    pytest.param(over_estimate, 1.0)
]
)
def test_volume(data, expected):
    result = volume_error(data['Simulated_cms'], data['Observed_cms'])
    assert result == expected

@pytest.mark.parametrize(
"data, expected",
[
    pytest.param(perfect_data, 0.0),
    pytest.param(under_estimate, 1.0),
    pytest.param(over_estimate, 1.0)
]
)
def test_custom(data, expected):
    result = custom(data['Simulated_cms'], data['Observed_cms'])
    assert result == expected
