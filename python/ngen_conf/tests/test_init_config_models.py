from ngen.config.init_config.cfe import CFE
from ngen.config.init_config.lgar import Lgar
from ngen.config.init_config.noahowp import NoahOWP
from ngen.config.init_config.pet import PET
from ngen.config.init_config.soil_freeze_thaw import SoilFreezeThaw
from ngen.config.init_config.soil_moisture_profile import SoilMoistureProfile
from ngen.init_config import utils


def test_cfe(cfe_init_config: str):
    assert utils.merge_class_attr(CFE, "Config.space_around_delimiters") is False
    assert utils.merge_class_attr(CFE, "Config.no_section_headers") is True
    o = CFE.from_ini_str(cfe_init_config)
    assert o.to_ini_str() == cfe_init_config


def test_pet(pet_init_config: str):
    assert utils.merge_class_attr(PET, "Config.space_around_delimiters") is False
    assert utils.merge_class_attr(PET, "Config.no_section_headers") is True
    o = PET.from_ini_str(pet_init_config)
    assert o.to_ini_str() == pet_init_config


def test_noah_owp(noah_owp_init_config: str):
    o = NoahOWP.from_namelist_str(noah_owp_init_config)
    assert o.to_namelist_str() == noah_owp_init_config


def test_soil_freeze_thaw(soil_freeze_thaw_init_config: str):
    o = SoilFreezeThaw.from_ini_str(soil_freeze_thaw_init_config)
    assert o.to_ini_str() == soil_freeze_thaw_init_config


def test_soil_moisture_profile(soil_moisture_profile_init_config: str):
    o = SoilMoistureProfile.from_ini_str(soil_moisture_profile_init_config)
    assert o.to_ini_str() == soil_moisture_profile_init_config

def test_lgar(lgar_init_config: str):
    o = Lgar.from_ini_str(lgar_init_config)
    assert o.to_ini_str() == lgar_init_config
