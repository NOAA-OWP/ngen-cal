
from typing import List, Literal
from pydantic import BaseModel, validator
from geojson_pydantic import Feature, Point,  MultiPolygon

def check_in_accepted(val, accepted):
    if val not in accepted:
        raise ValueError(f'Not an acceptable option. Options are {accepted}')
    
class NexusFeatureProperty(BaseModel):
    toid: str

    @validator('toid')
    def check_prefix(cls,val):
        assert val[:3] == 'cat', "toid must be a cat id"

NexusFeature = Feature[Point, NexusFeatureProperty]

class CatchmentFeatureProperty(BaseModel):
    toid: str
    areasqkm : float

    @validator('toid')
    def check_prefix(cls,val):
        assert val[:3] == 'nex', "toid must be a nexus id"

CatchmentFeature = Feature[MultiPolygon, CatchmentFeatureProperty]

class CRSProperty(BaseModel):
    """
    Model for CRS properties field in catchment or nexus data config
    """    
    name: Literal["urn:ogc:def:crs:OGC:1.3:CRS84"]

    # Are any others accepted? If so, check with validator
    # @validator('name')
    # def check_properties(cls,val):
    #     accepted = ["urn:ogc:def:crs:OGC:1.3:CRS84"] # Are any others accepted?
    #     check_in_accepted(val, accepted)

class CRS(BaseModel):
    """
    Model for CRS field in catchment or nexus data config
    """
    type: Literal["name"]
    properties: CRSProperty

    @validator('type')
    def check_type(cls,val):
        accepted = ["name"]
        check_in_accepted(val, accepted)

class NGenCatchmentFile(BaseModel):
    """
    Model for catchment data file
    """

    # required
    type: Literal["FeatureCollection"]
    name: Literal["catchment_data"]
    crs: CRS
    features: List[CatchmentFeature]


class NGenNexusFile(BaseModel):
    """
    Model for nexus data file
    """

    # required
    type: Literal["FeatureCollection"]
    name: Literal["nexus_data"]
    crs: CRS
    features: List[NexusFeature]