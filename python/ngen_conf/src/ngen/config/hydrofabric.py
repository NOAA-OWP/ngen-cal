
from typing import List, Literal
from pydantic import BaseModel, validator
from geojson_pydantic import FeatureCollection, Point,  MultiPolygon
import re

# match str that ends with a '-' followed by digits
_TOID_REGEX_STR = ".\D+-\d+$"
_TOID_REGEX = re.compile(_TOID_REGEX_STR)
    
class CatchmentFeatureProperty(BaseModel):
    toid: str
    areasqkm : float

    @validator('toid')
    def _validate_prefix(cls, value: str) -> str:
        if _TOID_REGEX.search(value) is None:
            raise ValueError(f"Invalid 'toid' property value: {value!r}")
        return value
    
    _validate_prefix = validator("toid", allow_reuse=True)(_validate_prefix)
    
class NexusFeatureProperty(BaseModel):
    toid: str

    @validator('toid')
    def _check_prefix(cls, value: str) -> str:
        if _TOID_REGEX.search(value) is None:
            raise ValueError(f"Invalid 'toid' property value: {value!r}")
        return value
    
    _check_prefix = validator("toid", allow_reuse=True)(_check_prefix)

CatchmentGeoJSON = FeatureCollection[MultiPolygon, CatchmentFeatureProperty]
NexusGeoJSON     = FeatureCollection[Point, NexusFeatureProperty]