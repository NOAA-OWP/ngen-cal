from ngen.config.formulation import Formulation
from ngen.config.soil_freeze_thaw import SoilFreezeThaw


def test_init(soil_freeze_thaw_params):
    SoilFreezeThaw(**soil_freeze_thaw_params)


def test_name_map(soil_freeze_thaw_params):
    soil_freeze_thaw = SoilFreezeThaw(**soil_freeze_thaw_params)
    assert soil_freeze_thaw.name_map["ground_temperature"] == "TG"


def test_soil_freeze_thaw_formulation(soil_freeze_thaw_params):
    soil_freeze_thaw = SoilFreezeThaw(**soil_freeze_thaw_params)
    f = {"params": soil_freeze_thaw, "name": "bmi_c++"}
    soil_freeze_thaw_formulation = Formulation(**f)
    _soil_freeze_thaw = soil_freeze_thaw_formulation.params
    assert _soil_freeze_thaw.name == "bmi_c++"
    assert _soil_freeze_thaw.model_name == "SoilFreezeThaw"
    serialized = _soil_freeze_thaw.dict(by_alias=True)
    assert serialized["model_type_name"] == "SoilFreezeThaw"
