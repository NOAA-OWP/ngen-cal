import pytest
from ngen.config.formulation import Formulation
from ngen.config.lstm import LSTM

def test_init(lstm_params):
    lstm = LSTM(**lstm_params)

def test_name_map(lstm_params):
    lstm = LSTM(**lstm_params)
    _t = lstm.name_map["atmosphere_water__time_integral_of_precipitation_mass_flux"]
    assert _t == "RAINRATE"

def test_no_lib(lstm_params):
    lstm = LSTM(**lstm_params)
    assert "library" not in lstm.dict().keys()

def test_lstm_formulation(lstm_params, forcing):
    lstm = LSTM(**lstm_params)
    f = {"params":lstm, "name":"bmi_python"}
    lstm_formulation = Formulation( **f )
    _lstm = lstm_formulation.params
    assert _lstm.name == 'bmi_python'
    assert _lstm.model_name == 'LSTM'
    serialized = _lstm.dict(by_alias=True)
    print(serialized)
    assert serialized['model_type_name'] == 'LSTM'
