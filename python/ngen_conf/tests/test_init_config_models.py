from __future__ import annotations

import warnings

import pytest
from ngen.init_config import utils

from ngen.config.init_config.cfe import CFE
from ngen.config.init_config.lgar import Lgar
from ngen.config.init_config.noahowp import NoahOWP
from ngen.config.init_config.pet import PET
from ngen.config.init_config.soil_freeze_thaw import SoilFreezeThaw
from ngen.config.init_config.soil_moisture_profile import SoilMoistureProfile
from ngen.config.init_config.topmodel import Topmodel, TopModelSubcat, TopModelParams

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


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


def test_soil_moisture_profile(soil_moisture_profile_init_config: str):
    o = SoilMoistureProfile.from_ini_str(soil_moisture_profile_init_config)
    assert o.to_ini_str() == soil_moisture_profile_init_config


def test_lgar(lgar_init_config: str):
    o = Lgar.from_ini_str(lgar_init_config)
    assert o.to_ini_str() == lgar_init_config


def test_topmodel_subcat(topmodel_subcat_config: str):
    model = TopModelSubcat.parse_obj(topmodel_subcat_config)
    assert model.to_str() == topmodel_subcat_config


def test_topmodel_params(topmodel_params_config: str):
    model = TopModelParams.parse_obj(topmodel_params_config)
    assert model.to_str() == topmodel_params_config


def test_topmodel(topmodel_config: str):
    model = Topmodel.parse_obj(topmodel_config)
    assert model.to_str() == topmodel_config


def test_topmodel_deserialize_and_serialize_linked_configs(
    topmodel_config: str,
    topmodel_subcat_config_path: Path,
    topmodel_params_config_path: Path,
    topmodel_subcat_config: str,
    topmodel_params_config: str,
):
    model = Topmodel.parse_obj(topmodel_config)

    # update paths to avoid resolution issues.
    # paths are relative to `_topmodel_config_path` (see conftest.py)
    # left unchanged, paths will not resolve correctly unless `pytest` is run
    # from the directory that contains `_topmodel_config_path`.
    # this fixes that
    model.subcat = model.subcat.with_path(topmodel_subcat_config_path)
    model.params = model.params.with_path(topmodel_params_config_path)

    # read from file and deserialize into `pydantic` model
    assert model.subcat.read(), f"failed to deserialize from file {topmodel_subcat_config_path!s}"
    assert model.params.read(), f"failed to deserialize from file {topmodel_params_config_path!s}"

    assert model.subcat.serialize() == topmodel_subcat_config.encode()
    assert model.params.serialize() == topmodel_params_config.encode()

def test_topmodel_initialize_fields_with_path_pair_instances(
    topmodel_subcat_config: str,
    topmodel_params_config: str,
):
    from ngen.config.path_pair import PathPair

    subcat = TopModelSubcat.parse_obj(topmodel_subcat_config)
    params = TopModelParams.parse_obj(topmodel_params_config)

    model = Topmodel(
        title="title",
        subcat=PathPair[TopModelSubcat].with_object(subcat),
        params=PathPair[TopModelParams].with_object(params),
    )

    assert model.subcat.inner is not None
    assert model.subcat.inner == subcat
    assert model.params.inner is not None
    assert model.params.inner == params

def test_topmodel_initialize_fields_with_non_path_pair_instances(
    topmodel_subcat_config: str,
    topmodel_params_config: str,
):
    subcat = TopModelSubcat.parse_obj(topmodel_subcat_config)
    params = TopModelParams.parse_obj(topmodel_params_config)

    model = Topmodel(
        title="title",
        subcat=subcat, # type: ignore
        params=params # type: ignore
    )

    assert model.subcat.inner is not None
    assert model.subcat.inner == subcat
    assert model.params.inner is not None
    assert model.params.inner == params
