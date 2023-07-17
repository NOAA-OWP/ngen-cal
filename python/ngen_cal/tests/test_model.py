import pytest
from typing import TYPE_CHECKING
from ngen.cal.ngen import Ngen
if TYPE_CHECKING:
    from ngen.cal.model import EvaluationOptions
    from pydantic import DirectoryPath

"""
    Test suite for reading and manipulating ngen configration files
"""

def test_update(eval: 'EvaluationOptions') -> None:
    """
        Test score update function with a worse score
    """
    eval._best_score = 0.5
    i = 1
    score = 1.0
    log = False
    eval.update(i, score, log)
    assert eval.best_score == 0.5
    assert eval.best_params == '0'

def test_update_1(eval: 'EvaluationOptions') -> None:
    """
        Test score update function with a better score
    """
    eval._best_score = 1
    i = 1
    score = 0.1
    log = False
    eval.update(i, score, log)
    assert eval.best_score == 0.1
    assert eval.best_params == '1'

def test_restart(ngen_config: 'Ngen') -> None:
    """
        Test restarting from minimal meta, no logs available
        should "restart" at iteration 0
    """
    iteration = ngen_config.restart()
    assert iteration == 0

def test_restart_1(ngen_config: 'Ngen', eval: 'EvaluationOptions', workdir: 'DirectoryPath') -> None:
    """
        Test retarting from serialized logs
    """
    eval._best_score = 1
    ngen_config.adjustables[0]._best_score = 1
    eval._best_params_iteration = "1"
    ngen_config.adjustables[0]._best_params = "1"
    eval.write_param_log_file(2)
    
    #make sure the catchment param df is saved before trying to restart
    ngen_config.adjustables[0].check_point(workdir)

    iteration = ngen_config.restart()
    assert iteration == 3
    assert ngen_config.adjustables[0].eval_params.best_score == 1
    assert ngen_config.adjustables[0].eval_params.best_params == '1'

#TODO test calibration_set/uniform
#TODO test multiple explicit -- test_restart_1 uses explicit but only validates a single catchment
def test_explicit(explicit_catchments) -> None:
    """
        Test that a set of independt, explicity handled catchments operates as intended
    """


    pass