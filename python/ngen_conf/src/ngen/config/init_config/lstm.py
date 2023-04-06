from ngen.init_config import serializer_deserializer as serde
from pathlib import Path

from typing import Optional, Literal


# TODO: add tests
# TODO: modify once a better understanding of how LSTM is to be configured in practice. Based on the
# configs present in https://github.com/NOAA-OWP/lstm it is unclear when certain keys are required.
class LSTM(serde.YamlSerializerDeserializer):
    train_cfg_file: Path

    # TODO: not sure what other values this can be
    initial_state: Literal["zero"] = "zero"
    verbose: bool = False
    basin_name: Optional[str] = None
    basin_id: Optional[str] = None

    # NOTE: listed as post-processing / plotting only
    # lat: float
    # lon: float
    area_sqkm: float
    elev_mean: float
    slope_mean: float
    area_gages2: float
    frac_forest: float
    lai_max: float
    lai_diff: float
    gvf_max: float
    gvf_diff: float
    soil_depth_pelletier: float
    soil_depth_statsgo: float
    soil_porosity: float
    soil_conductivity: float
    max_water_content: float
    sand_frac: float
    silt_frac: float
    clay_frac: float
    carbonate_rocks_frac: float
    geol_permeability: float
    p_mean: float
    pet_mean: float
    aridity: float
    frac_snow: float
    high_prec_freq: float
    high_prec_dur: float
    low_prec_freq: float
    low_prec_dur: float

    class Config(serde.YamlSerializerDeserializer.Config):
        field_serializers = {"verbose": lambda b: int(b)}
        # descriptions source: https://github.com/NOAA-OWP/lstm/blob/63116cc6a6bbdb5537868f20ff55cc326795b570/bmi_config_files/README.md
        fields = {
            "area_sqkm": {"description": "allows bmi to adjust a weighted output"},
            "elev_mean": {
                "description": "catchment mean elevation (m) above sea level"
            },
            "slope_mean": {"description": "catchment mean slope (m km-1)"},
            "area_gages2": {"description": "catchment area (GAGESII estimate), (km2)"},
            "frac_forest": {"description": "forest fraction"},
            "lai_max": {
                "description": "maximum monthly mean of the leaf area index (based on 12 monthly means)"
            },
            "lai_diff": {
                "description": "difference between the maximum and minimum monthly mean of the leaf area index (based on 12 monthly means)"
            },
            "gvf_max": {
                "description": "maximum monthly mean of the green vegetation fraction (based on 12 monthly means)"
            },
            "gvf_diff": {
                "description": "difference between the maximum and minimum monthly mean of the green vegetation fraction (based on 12 monthly means)"
            },
            "soil_depth_pelletier": {
                "description": "depth to bedrock (maximum 50 m) (m)"
            },
            "soil_depth_statsgo": {
                "description": "soil depth (maximum 1.5 m; layers marked as water and bedrock were excluded) (m)"
            },
            "soil_porosity": {
                "description": "volumetric porosity (saturated volumetric water content estimated using a multiple linear regression based on sand and clay fraction for the layers marked as USDA soil texture class and a default value (0.9) for layers marked as organic material; layers marked as water, bedrock, and “other” were excluded)"
            },
            "soil_conductivity": {
                "description": "saturated hydraulic conductivity (estimated using a multiple linear regression based on sand and clay fraction for the layers marked as USDA soil texture class and a default value (36 cm h−1) for layers marked as organic material; layers marked as water, bedrock, and “other” were excluded) (cm h-1)"
            },
            "max_water_content": {
                "description": "maximum water content (combination of porosity and soil depth statsgo; layers marked as water, bedrock, and “other” were excluded)"
            },
            "sand_frac": {
                "description": "sand fraction (of the soil material smaller than 2mm; layers marked as organic material, water, bedrock, and “other” were excluded)"
            },
            "silt_frac": {
                "description": "silt fraction (of the soil material smaller than 2mm; layers marked as organic material, water, bedrock, and “other” were excluded)"
            },
            "clay_frac": {
                "description": "clay fraction (of the soil material smaller than 2mm; layers marked as organic material, water, bedrock, and “other” were excluded)"
            },
            "carbonate_rocks_frac": {
                "description": "fraction of the catchment area characterized as “carbonate sedimentary rocks”. GLiM"
            },
            "geol_permeability": {"description": ""},
            "p_mean": {"description": "mean daily precipitation (mm day-1)"},
            "pet_mean": {
                "description": "mean daily PET, estimated by N15 using Priestley-Taylor formulation calibrated for each catchment (mm day-1)"
            },
            "aridity": {
                "description": "aridity (PET /P, ratio of mean PET, estimated by N15 using Priestley-Taylor formulation calibrated for each catchment, to mean precipitation)"
            },
            "frac_snow": {
                "description": "fraction of precipitation falling as snow (i.e., on days colder than 0 C)"
            },
            "high_prec_freq": {
                "description": "frequency of high precipitation days (≥5 times mean daily precipitation) (days yr-1)"
            },
            "high_prec_dur": {
                "description": "average duration of high precipitation events (number of consecutive days ≥5 times mean daily precipitation)"
            },
            "low_prec_freq": {
                "description": "frequency of dry days (< 1mmday-1) (days yr-1)"
            },
            "low_prec_dur": {
                "description": "average duration of dry periods (number of consecutive days < 1mmday-1) (days)"
            },
        }
