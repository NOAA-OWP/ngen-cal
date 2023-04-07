
from typing import List, Literal
from pydantic import BaseModel, validator
from geojson_pydantic import FeatureCollection, Point,  MultiPolygon
import re

# match str that ends with a '-' followed by digits
_TOID_REGEX_STR = ".\w+-\d+$"
_TOID_REGEX = re.compile(_TOID_REGEX_STR)

@validator('toid')
def _validate_toid(cls, value: str) -> str:
    if _TOID_REGEX.search(value) is None:
        raise ValueError(f"Invalid 'toid' property value: {value!r}")
    return value
    
class CatchmentFeatureProperty(BaseModel):
    toid: str
    areasqkm : float
    _validate_toid = validator("toid", allow_reuse=True)(_validate_toid)

class NexusFeatureProperty(BaseModel):
    toid: str
    _check_toid = validator("toid", allow_reuse=True)(_validate_toid)

CatchmentGeoJSON = FeatureCollection[MultiPolygon, CatchmentFeatureProperty]
NexusGeoJSON     = FeatureCollection[Point, NexusFeatureProperty]