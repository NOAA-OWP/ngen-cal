from ngen.config.formulation import Formulation
from ngen.config.lgar import LGAR


def test_init(lgar_params):
    LGAR(**lgar_params)


def test_name_map(lgar_params):
    lgar = LGAR(**lgar_params)
    assert lgar.name_map["precipitation_rate"] == "QINSUR"
    assert lgar.name_map["potential_evapotranspiration_rate"] == "EVAPOTRANS"


def test_lgar_formulation(lgar_params):
    lgar = LGAR(**lgar_params)
    f = {"params": lgar, "name": "bmi_c++"}
    lgar_formulation = Formulation(**f)
    _lgar = lgar_formulation.params
    assert _lgar.name == "bmi_c++"
    assert _lgar.model_name == "LGAR"
    serialized = _lgar.dict(by_alias=True)
    assert serialized["model_type_name"] == "LGAR"
