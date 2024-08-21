"""
Test suite for calibratable_catchment
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from ngen.cal.calibration_cathment import CalibrationCatchment


def test_df(catchment: CalibrationCatchment) -> None:
    """
    Test the catchments proper construction of the parameter dataframe
    """
    assert catchment.df.iloc[0]["param"] == "some_param"
    assert catchment.df.iloc[0]["0"] == 0.5
    assert catchment.df.iloc[0]["min"] == 0.0
    assert catchment.df.iloc[0]["max"] == 1.0


def test_output(
    catchment2: CalibrationCatchment,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Test proper handling of non-existent output
    """
    import pandas as pd

    monkeypatch.setattr(pd, "read_csv", lambda *args, **kwargs: FileNotFoundError())
    output = catchment2.output
    assert output is None


def test_observed(catchment: CalibrationCatchment) -> None:
    """
    Test proper handling of non-existent output
    """
    catchment.observed = None
    with pytest.raises(RuntimeError):
        catchment.observed


# TODO test catchment_set
# TODO test evaluation_range?
