import pytest
from ngen.config.formulation import Formulation
from ngen.config.noahowp import NoahOWP

def test_init(noahowp_params):
    noahowp = NoahOWP(**noahowp_params)

def test_name_map_default(noahowp_params):
    noahowp = NoahOWP(**noahowp_params)
    assert noahowp.name_map["UU"] == 'land_surface_wind__x_component_of_velocity'

def test_name_map_override(noahowp_params):
    noahowp_params['name_map'] = {"atmosphere_water__liquid_equivalent_precipitation_rate":"RAINRATE"}
    noahowp = NoahOWP(**noahowp_params)
    assert noahowp.name_map["atmosphere_water__liquid_equivalent_precipitation_rate"] == 'RAINRATE'

def test_noahowp_formulation(noahowp_params):
    noahowp = NoahOWP(**noahowp_params)
    f = {"params":noahowp, "name":"bmi_fortran"}
    noahowp_formulation = Formulation( **f )
    _noahowp = noahowp_formulation.params
    assert _noahowp.name == 'bmi_fortran'
    assert _noahowp.model_name == 'NoahOWP'
