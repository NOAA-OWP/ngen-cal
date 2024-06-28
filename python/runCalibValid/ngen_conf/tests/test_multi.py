import pytest
from ngen.config.formulation import Formulation
from ngen.config.multi import MultiBMI

def test_init(multi_params):
    multi = MultiBMI(**multi_params)

def test_name_map(multi_params):
    multi = MultiBMI(**multi_params)
    _t = multi.modules[-1].params.name_map["atmosphere_water__liquid_equivalent_precipitation_rate"]
    assert _t == "QINSUR"
    _t = multi.modules[0].params.name_map["UU"]
    assert _t == 'land_surface_wind__x_component_of_velocity'

def test_name_map_override(multi_params):
    multi_params['modules'][-1]['params']['name_map'].update( {"atmosphere_water__liquid_equivalent_precipitation_rate":"RAINRATE"} )
    multi_params['modules'][0]['params']['name_map'].update( {"UU":"WIND_U"} )
    multi = MultiBMI(**multi_params)
    _t = multi.modules[-1].params.name_map["atmosphere_water__liquid_equivalent_precipitation_rate"]
    assert _t == "RAINRATE"
    _t =  multi.modules[0].params.name_map["UU"]
    assert _t == "WIND_U"

def test_no_lib(multi_params):
    multi = MultiBMI(**multi_params)
    assert "library" not in multi.dict().keys()

def test_multi_formulation(multi_params):
    multi = MultiBMI(**multi_params)
    multi_formulation = Formulation( name=multi.name, params=multi )
    _multi = multi_formulation.params
    assert _multi.name == 'bmi_multi'
    assert _multi.model_name == 'NoahOWP_CFE'
