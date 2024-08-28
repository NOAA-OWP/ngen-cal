from __future__ import annotations

from ngen.cal.ngen import _params_as_df
import pandas as pd

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Mapping
    from ngen.cal.parameter import Parameter

def test_multi_params(multi_model_shared_params: Mapping[str, list[Parameter]]):
    # This is essentially the path the params go through from
    # creation in model.py to update in search.py
    params = _params_as_df(multi_model_shared_params)
    params = pd.DataFrame(params).rename(columns={'init':'0'})
    # create new iteration from old
    params['1'] = params['0']
    #update the parameters by index
    idx1 = 'a'
    idx2 = 'c'
    params.loc[idx1, '1'] = 0.5
    pa = params[ params['model'] == 'A' ].loc[idx1]
    pb = params[ params['model'] == 'B' ].loc[idx1]
    pc = params[ params['model'] == 'C' ].loc[idx2]

    assert pa.drop('model').equals( pb.drop('model') )
    # ensure unique params/alias are not modifed by selection
    assert pa.loc['1'] != pc.loc['1']

def test_multi_params2(multi_model_shared_params2: Mapping[str, list[Parameter]]):
    # This is essentially the path the params go through from
    # creation in model.py to update in search.py
    params = _params_as_df(multi_model_shared_params2)
    params = pd.DataFrame(params).rename(columns={'init':'0'})
    # create new iteration from old
    params['1'] = params['0']
    #update the parameters by index
    params.loc['a', '1'] = 0.5
    pa = params[ params['model'] == 'A' ].drop('model', axis=1).loc['a']
    pb = params[ params['model'] == 'B' ].drop('model', axis=1).loc['a']
    assert pa.equals( pb )
