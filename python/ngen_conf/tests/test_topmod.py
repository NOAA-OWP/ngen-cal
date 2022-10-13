import pytest
from ngen.config.formulation import Formulation
from ngen.config.topmod import Topmod

def test_init(topmod_params):
    topmod = Topmod(**topmod_params)

def test_name_map_default(topmod_params):
    topmod = Topmod(**topmod_params)
    assert topmod.name_map["atmosphere_water__liquid_equivalent_precipitation_rate"] == 'QINSUR'

def test_name_map_override(topmod_params):
    topmod_params['name_map'] = {"atmosphere_water__liquid_equivalent_precipitation_rate":"RAINRATE"}
    topmod = Topmod(**topmod_params)
    assert topmod.name_map["atmosphere_water__liquid_equivalent_precipitation_rate"] == 'RAINRATE'

@pytest.mark.parametrize("forcing",["csv", "netcdf"], indirect=True )
def test_topmodformulation(topmod_params, forcing):
    topmod = Topmod(**topmod_params)
    f = {"params":topmod, "name":"bmi_c"}
    topmodformulation = Formulation( **f )
    _topmod = topmodformulation.params
    assert _topmod.name == 'bmi_c'
    assert _topmod.model_name == 'TOPMODEL'

def test_topmodmodel_params(topmod_params):
    topmod = Topmod(**topmod_params)
    assert topmod.model_params
    assert topmod.model_params.szm == 42
    assert topmod.model_params.t0 == 0.42
