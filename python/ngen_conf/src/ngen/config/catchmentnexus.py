from pydantic import BaseModel, validator
from typing import List, Optional
from enum import Enum

def check_in_accepted(val, accepted):
    if val not in accepted:
        raise ValueError(f'Not an acceptable option. Options are {accepted}')

def validate_point(coordinates):     
    assert len(coordinates) == 2, 'Must supply a single Point and Point must have exactly two dimensions'   

def validate_linestring(coordinates):
    assert len(coordinates) > 1, 'Must supply at least two points in LineString'
    assert [len(jpoint) == 2 for j,jpoint in enumerate(coordinates)], 'Each element in LineString must be a 2-D point' 
    
def validate_polygon(coordinates):        
    assert len(coordinates) > 2, f'Polygon must have at least 3 points\nBad Polygon: {coordinates}'
    for j,jpoint in enumerate(coordinates):
        assert len(jpoint) == 2, f'Polygon must be made up of 2-D points\nBad Point: {jpoint}'


class CRSProperty(BaseModel):
    """
    Model for CRS properties field in catchment or nexus data config
    """    
    name: str

    @validator('name')
    def check_properties(cls,val):
        accepted = ["urn:ogc:def:crs:OGC:1.3:CRS84"]
        check_in_accepted(val, accepted)
        
class CRS(BaseModel):
    """
    Model for CRS field in catchment or nexus data config
    """
    type: str
    properties: CRSProperty

    @validator('type')
    def check_type(cls,val):
        accepted = ["name"]
        check_in_accepted(val, accepted)

class Geom(BaseModel):
    """
    Model for geometry field in catchment or nexus data config
    """    

    class GeomType(str,Enum):
        """
        Enumeration of the Type object
        """        

    type: str
    coordinates: list

    @validator('type')
    def check_geom_type(cls,val):
        accepted = ['Point','LineString','Polygon','MultiPoint','MultiLineString','MultiPolygon']
        check_in_accepted(val, accepted)
        return val

    @validator('coordinates')
    def GeomCoordinates(cls,val,values):
        """
        Check the coordinates and make sure they are in a proper list format based on the type
        """
        type = values['type']
        if type == 'Point':
            validate_point(val)
        elif type == 'LineString': 
           validate_linestring(val)
        elif type == 'Polygon':
            validate_polygon(val[0])
        elif type == 'MultiPoint':
            assert len(val[0]) > 1, 'Must supply at least two Points'
            [validate_point(jpoint) for j,jpoint in enumerate(val[0])]
        elif type == 'MultiLineString':
            assert len(val[0]) > 1, 'Must supply at least two LineStrings'
            assert [validate_linestring(jlinestring) for j,jlinestring in enumerate(val[0])]
        elif type == 'MultiPolygon':
            for j,jpoly in enumerate(val):
                validate_polygon(jpoly[0])
        else: # Shouldn't be possible
            raise Exception(f'Validator is broken!')

class FeatProperties(BaseModel):
    """
    Model for Feature Properties in catchment or nexus data config
    """
    areasqkm: Optional[float]
    toid: str

class Features(BaseModel):
    """
    Model for Feature in catchment or nexus data config
    """
    type: str
    id: str
    properties: FeatProperties
    geometry: Geom

class NGenCatchmentNexus(BaseModel):
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