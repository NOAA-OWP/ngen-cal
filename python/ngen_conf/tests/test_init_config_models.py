import warnings

import pytest
from ngen.init_config import utils

from ngen.config.init_config.cfe import CFE
from ngen.config.init_config.noahowp import NoahOWP
from ngen.config.init_config.pet import PET
from ngen.config.init_config.soil_freeze_thaw import SoilFreezeThaw


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


SOIL_TYPE_WATER = 14
VEG_USGS_WATER = 16
VEG_MODIS_WATER = 17

does_warn_cases = (
    ("USGS", VEG_USGS_WATER, SOIL_TYPE_WATER + 1),
    ("USGS", VEG_USGS_WATER + 1, SOIL_TYPE_WATER),
    ("MODIFIED_IGBP_MODIS_NOAH", VEG_MODIS_WATER, SOIL_TYPE_WATER + 1),
    ("MODIFIED_IGBP_MODIS_NOAH", VEG_MODIS_WATER + 1, SOIL_TYPE_WATER),
)


@pytest.mark.parametrize("veg_class,veg_type,soil_type", does_warn_cases)
def test_noah_owp_does_warns_if_soil_or_veg_type_are_water_but_not_both(
    noah_owp_init_config: str,
    veg_class: str,
    veg_type: int,
    soil_type: int,
):
    o = NoahOWP.from_namelist_str(noah_owp_init_config)
    o.parameters.veg_class_name = veg_class
    o.structure.vegtyp = veg_type
    o.structure.isltyp = soil_type

    # ensure warning _is_ emitted
    with pytest.warns():
        NoahOWP.from_namelist_str(o.to_namelist_str())


does_not_warn_cases = (
    # positive cases
    ("USGS", VEG_USGS_WATER, SOIL_TYPE_WATER),
    ("MODIFIED_IGBP_MODIS_NOAH", VEG_MODIS_WATER, SOIL_TYPE_WATER),
    # negative cases
    ("USGS", VEG_USGS_WATER + 1, SOIL_TYPE_WATER + 1),
    ("MODIFIED_IGBP_MODIS_NOAH", VEG_MODIS_WATER + 1, SOIL_TYPE_WATER + 1),
)


@pytest.mark.parametrize("veg_class,veg_type,soil_type", does_not_warn_cases)
def test_noah_owp_does_not_warns_if_soil_and_veg_type_are_water_or_neither_water(
    noah_owp_init_config: str,
    veg_class: str,
    veg_type: int,
    soil_type: int,
):
    o = NoahOWP.from_namelist_str(noah_owp_init_config)
    o.parameters.veg_class_name = veg_class
    o.structure.vegtyp = veg_type
    o.structure.isltyp = soil_type

    # ensure warning is not emitted
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        NoahOWP.from_namelist_str(o.to_namelist_str())

    # WATER = 14
    # o.parameters.veg_class_name = "USGS"
    # o.structure.isltyp = WATER
    # VEG_USGS_WATER = 16
    # o.structure.vegtyp = VEG_USGS_WATER + 1

    # # ensure warning is not emitted
    # with pytest.warns():
    #     NoahOWP.from_namelist_str(o.to_namelist_str())

    # o.parameters.veg_class_name = "MODIFIED_IGBP_MODIS_NOAH"
    # o.structure.isltyp = WATER
    # VEG_MODIS_WATER = 17
    # o.structure.vegtyp = VEG_MODIS_WATER

    # assert o.to_namelist_str() == noah_owp_init_config


def test_soil_freeze_thaw(soil_freeze_thaw_init_config: str):
    o = SoilFreezeThaw.from_ini_str(soil_freeze_thaw_init_config)
    assert o.to_ini_str() == soil_freeze_thaw_init_config
