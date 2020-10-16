import pytest
from typing import Generator
from pathlib import Path
from copy import deepcopy
import json
import pandas as pd # type: ignore

from ..configuration import Configuration
from ..meta import CalibrationMeta
from ..calibration_cathment import CalibrationCatchment

from .utils import config

@pytest.fixture(scope="session")
def realization_config(tmpdir_factory) -> str:
    """
        Fixture to provide a staged testing input files
    """
    fn = tmpdir_factory.mktemp("data").join("realization_config.json")
    with(open(fn, 'w')) as fp:
        json.dump(config, fp)
    return fn

@pytest.fixture
def conf(realization_config) -> Generator[Configuration, None, None]:
    """
        Staging of a generator to test
    """
    yield Configuration(realization_config)

@pytest.fixture
def meta(conf, tmpdir_factory) -> Generator[CalibrationMeta, None, None]:
    """
        build up a meta object to test
    """
    bin = "echo"
    args = "ngen args"
    workdir = tmpdir_factory.mktemp("workdir")
    m = CalibrationMeta(conf, workdir, bin, args, "test_0")
    yield m

@pytest.fixture
def catchment() -> Generator[CalibrationCatchment, None, None]:
    """
        A hy_features catchment implementing the calibratable interface
    """
    id = 'test-catchment'
    data = deepcopy(config)['catchments'][id] # type: ignore
    catchment = CalibrationCatchment(id, data)
    now = pd.Timestamp.now().round('H')
    ts = pd.DataFrame({'obs_flow':[1,2,3,4,5]}, index=pd.date_range(now, periods=5, freq='H'))
    catchment.output = ts
    catchment.observed = ts.rename(columns={"obs_flow":"sim_flow"})
    return catchment
