import pytest
from typing import Generator
from pathlib import Path
import pandas as pd
import json
import os

from ..search import dds
from ..calibration_cathment import CalibrationCatchment
from ..meta import CalibrationMeta
from ..configuration import Configuration

"""
    Test suite for calibrtion search algorithms
"""
_current_dir = Path(__file__).resolve().parent

_calibraiton_test_params = """
{"test-catchment":
    {
        "calibration":
        [
            {"param":"some_param", "min":0.0, "max":10.0, "init":5.0}
        ]
    }
}
"""


@pytest.fixture
def calibratable() -> Generator[CalibrationCatchment, None, None]:
    """
        Staging of a generator to test
    """
    params = json.loads(_calibraiton_test_params)
    calibrate = CalibrationCatchment("test-catchment", params)
    now = pd.Timestamp.now().round('H')
    test_data = pd.DataFrame({'obs_flow':[1,2,3,4,5]}, index=pd.date_range(now, periods=5, freq='H'))
    calibrate.output = test_data
    calibrate.observed = test_data.rename(columns={"obs_flow":"sim_flow"})
    yield calibrate

    os.remove(_current_dir/calibrate.check_point_file)


@pytest.fixture
def calibration_meta() -> Generator[CalibrationMeta, None, None]:
    """

    """
    test_config_file = _current_dir.joinpath('data/example_realization_config.json')
    test_calibraiton_file = Path('')
    conf = Configuration(test_config_file, test_calibraiton_file)
    meta = CalibrationMeta(conf, _current_dir, 'echo', 'none', 'test-catchment')
    yield meta

    os.remove(meta._log_file)
    os.remove(meta._objective_log_file)
    os.remove(meta._param_log_file)


def test_dds(calibratable: CalibrationCatchment, calibration_meta: CalibrationMeta):
    """
        Test dds is callable
    """
    ret = dds(1, 2, calibratable, calibration_meta)
    assert calibration_meta.best_score == -1
    assert calibration_meta.best_params == '0'
