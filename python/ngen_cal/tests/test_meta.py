import pytest
import pandas as pd # type: ignore
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ngen.cal.meta import CalibrationMeta

"""
    Test suite for reading and manipulating ngen configration files
"""

@pytest.mark.usefixtures("meta", "realization_config")
def test_update_config(meta: 'CalibrationMeta', realization_config: str) -> None:
    """
        Ensure that update config properly updates and serializes the config
    """
    i = 0
    params = pd.DataFrame({"model":"CFE","0":4.2, "param":"some_param"}, index=[0])
    id = 'tst-1'
    meta.update_config(i, params, id)
    with open(realization_config) as fp:
        data = json.load(fp)
    assert data['catchments'][id]['formulations'][0]['params']['model_params']['some_param'] == 4.2

#FIXME expand update unit tests...specifically that optmizing min/max and values
#is consistent, for example
