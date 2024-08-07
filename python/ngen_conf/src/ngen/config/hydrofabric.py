from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, validator
from geojson_pydantic import FeatureCollection, Point,  MultiPolygon
import re

# match str that ends with a '-' followed by digits
_TOID_REGEX_STR = ".\w+-\d+$"
_TOID_REGEX = re.compile(_TOID_REGEX_STR)

def validate_toid(value: str) -> str:
    if _TOID_REGEX.search(value) is None:
        raise ValueError(f"Invalid 'toid' property value: {value!r}")
    return value

class CatchmentFeatureProperty(BaseModel):
    id : Optional[str] = None
    toid: str
    areasqkm : float
    _validate_toid = validator("toid", allow_reuse=True)(validate_toid)

class NexusFeatureProperty(BaseModel):
    id : Optional[str] = None
    toid: str
    _check_toid = validator("toid", allow_reuse=True)(validate_toid)

CatchmentGeoJSON = FeatureCollection[MultiPolygon, CatchmentFeatureProperty]
NexusGeoJSON     = FeatureCollection[Point, NexusFeatureProperty]
