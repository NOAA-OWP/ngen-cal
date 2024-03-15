from ngen.config.formulation import Formulation
from ngen.config.soil_moisture_profile import SoilMoistureProfile


def test_init(soil_moisture_profile_params):
    SoilMoistureProfile(**soil_moisture_profile_params)


def test_name_map(soil_moisture_profile_params):
    soil_moisture_profile = SoilMoistureProfile(**soil_moisture_profile_params)
    assert soil_moisture_profile.name_map["soil_storage"] == "SOIL_STORAGE"
    assert soil_moisture_profile.name_map["soil_storage_change"] == "SOIL_STORAGE_CHANGE"


def test_soil_moisture_profile_formulation(soil_moisture_profile_params):
    soil_moisture_profile = SoilMoistureProfile(**soil_moisture_profile_params)
    f = {"params": soil_moisture_profile, "name": "bmi_c++"}
    soil_moisture_profile_formulation = Formulation(**f)
    _soil_moisture_profile = soil_moisture_profile_formulation.params
    assert _soil_moisture_profile.name == "bmi_c++"
    assert _soil_moisture_profile.model_name == "SoilMoistureProfile"
    serialized = _soil_moisture_profile.dict(by_alias=True)
    assert serialized["model_type_name"] == "SoilMoistureProfile"
