import pytest
from ngen.config.formulation import Formulation
from ngen.config.cfe import CFE

def test_init(cfe_params):
    cfe = CFE(**cfe_params)

def test_name_map_default(cfe_params):
    cfe = CFE(**cfe_params)
    assert cfe.name_map["atmosphere_water__liquid_equivalent_precipitation_rate"] == 'QINSUR'

def test_name_map_override(cfe_params):
    cfe_params['name_map'] = {"atmosphere_water__liquid_equivalent_precipitation_rate":"RAINRATE"}
    cfe = CFE(**cfe_params)
    assert cfe.name_map["atmosphere_water__liquid_equivalent_precipitation_rate"] == 'RAINRATE'

def test_cfe_formulation(cfe_params, forcing):
    cfe = CFE(**cfe_params)
    f = {"params":cfe, "name":"bmi_c"}
    cfe_formulation = Formulation( **f )
    _cfe = cfe_formulation.params
    assert _cfe.name == 'bmi_c'
    assert _cfe.model_name == 'CFE'

def test_cfe_model_params(cfe_params):
    cfe = CFE(**cfe_params)
    assert cfe.model_params
    assert cfe.model_params.expon == 42
    assert cfe.model_params.slope == 0.42