import pytest
from ngen.config.formulation import Formulation
from ngen.config.sloth import SLOTH

def test_init(sloth_params):
    cfe = SLOTH(**sloth_params)


@pytest.mark.parametrize("forcing",["csv", "netcdf"], indirect=True )
def test_sloth_formulation(sloth_params, forcing):
    sloth = SLOTH(**sloth_params)
    f = {"params":sloth, "name":"bmi_cxx"}
    sloth_formulation = Formulation( **f )
    _sloth = sloth_formulation.params
    assert _sloth.name == 'bmi_c++'
    assert _sloth.model_name == 'SLOTH'
    assert _sloth.main_output_variable == 'TEST'

def test_sloth_model_params(sloth_params):
    sloth = SLOTH(**sloth_params)
    assert sloth.model_params == None
