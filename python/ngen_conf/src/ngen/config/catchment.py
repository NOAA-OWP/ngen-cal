from pydantic import BaseModel, Field, validator
from typing import List
from enum import Enum

def check_in_accepted(val, accepted):
    if val not in accepted:
        raise ValueError(f'Not an acceptable option. Options are {accepted}')

class CRSProperty(BaseModel):
    """
    Model for CRS properties field in catchment data config
    """    

    name: str

    @validator('name')
    def check_properties(cls,val):
        accepted = ["urn:ogc:def:crs:OGC:1.3:CRS84"]
        check_in_accepted(val, accepted)
        
class CRS(BaseModel):
    """
    Model for CRS field in catchment data config
    """
        
    type: str
    properties: CRSProperty

    @validator('type')
    def check_type(cls,val):
        accepted = ["name"]
        check_in_accepted(val, accepted)

class Geom(BaseModel):
    """
    Model for geometry field in catchment data config
    """    

    type: str
    coordinates: list

    @validator('type')
    def check_geom_type(cls,val):
        accepted = ['Point','LineString','MultiPoint','MultiLineString','MultiPolygon']
        check_in_accepted(val, accepted)

    @validator('coordinates')
    def GeomCoordinates(cls,val):
        """
        Check the coordinates and make sure they are in a proper list format based on the type
        """
        if val == 'Point':
            assert len(val) == 1, 'Must supply a single point'
            assert len(val[0]) == 2, 'Point must have exactly two dimensions'
        elif val == 'LineString': 
            #TODO
            pass
        elif val == 'MultiPoint':
            #TODO
            pass
        elif val == 'MultiLineString':
            #TODO
            pass
        elif val == 'MultiPolygon':
            #TODO
            pass
        else: # Shouldn't be possible
            pass
        
class FeatProperties(BaseModel):
    areasqkm: float
    toid: str

class Features(BaseModel):

    type: str
    id: str
    properties: FeatProperties
    geometry: Geom

class NGenCatchment(BaseModel):
    """
    Model for catchment data file
    """
    class Type(str,Enum):
        """
        Enumeration of the catchment object types
        """        
        Feature = "Feature"
        FeatCollection = "FeatureCollection"

    # required
    type: Type
    name: str
    crs: CRS
    # Need to loop through all features supplied in config
    features: List[Features]