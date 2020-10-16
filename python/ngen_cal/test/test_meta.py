import pytest
import pandas as pd # type: ignore
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..meta import CalibrationMeta

"""
    Test suite for reading and manipulating ngen configration files
"""

@pytest.mark.usefixtures("meta", "realization_config")
def test_update_config(meta: 'CalibrationMeta', realization_config: str) -> None:
    """
        Ensure that update config properly updates and serializes the config
    """
    i = 0
    params = pd.DataFrame({"0":4.2, "param":"some_param"}, index=[0])
    id = 'test-catchment'
    meta.update_config(i, params, id)
    with open(realization_config) as fp:
        data = json.load(fp)
    assert data['catchments'][id]['formulations'][0]['params']['some_param'] == 4.2

@pytest.mark.usefixtures("meta")
def test_update(meta: 'CalibrationMeta') -> None:
    """
        Test score update function with a worse score
    """
    meta._best_score = 0.5
    i = 1
    score = 1.0
    log = False
    meta.update(i, score, log)
    assert meta.best_score == 0.5
    assert meta.best_params == '0'

@pytest.mark.usefixtures("meta")
def test_update_1(meta: 'CalibrationMeta') -> None:
    """
        Test score update function with a better score
    """
    meta._best_score = 1
    i = 1
    score = 0.1
    log = False
    meta.update(i, score, log)
    assert meta.best_score == 0.1
    assert meta.best_params == '1'

@pytest.mark.usefixtures("meta")
def test_restart(meta: 'CalibrationMeta') -> None:
    """
        Test restarting from minimal meta, no logs available
        should "restart" at iteration 0
    """
    iteration = meta.restart()
    assert iteration == 0

@pytest.mark.usefixtures("meta")
def test_restart_1(meta: 'CalibrationMeta') -> None:
    """
        Test retarting from serialized logs
    """
    meta._best_score = 1
    meta._best_param_iteration = "1"
    meta.write_param_log_file(2)
    #make sure the catchment param df is saved before trying to restart
    meta._config.catchments[0].check_point(meta._workdir)

    iteration = meta.restart()
    assert iteration == 3
    assert meta.best_score == 1
    assert meta.best_params == '1'
