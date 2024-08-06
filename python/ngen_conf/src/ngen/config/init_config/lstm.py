from __future__ import annotations

from ngen.init_config import serializer_deserializer as serde
from pydantic import Extra
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

    # NOTE: other fields will likely need to be added in the future.
    # See: https://github.com/NOAA-OWP/ngen-cal/pull/49/files#r1265465514 for context
    lat: float
    lon: float
    area_sqkm: float
    elev_mean: float
    slope_mean: float

    class Config(serde.YamlSerializerDeserializer.Config):
        field_serializers = {"verbose": lambda b: int(b)}
        # descriptions source: https://github.com/NOAA-OWP/lstm/blob/63116cc6a6bbdb5537868f20ff55cc326795b570/bmi_config_files/README.md
        fields = {
            "area_sqkm": {"description": "allows bmi to adjust a weighted output"},
            "elev_mean": {
                "description": "catchment mean elevation (m) above sea level"
            },
            "slope_mean": {"description": "catchment mean slope (m km-1)"},
        }
