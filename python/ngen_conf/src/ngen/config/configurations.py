from enum import Enum
from datetime import datetime
from pydantic import BaseModel, DirectoryPath, FilePath, conint, Field
from typing import Union, Optional

PosInt = conint(gt=0)

class Forcing(BaseModel, smart_union=True):
    """Model for ngen forcing component inputs
    """

    class Provider(str, Enum):
        """Enumeration of the supported NGEN forcing provider strings
        """
        CSV = "CsvPerFeature"
        NetCDF = "FIXME"
    
    #required
    file_pattern: Union[FilePath, str]
    path: DirectoryPath
    #reasonable? default
    provider: Provider = Field(Provider.CSV, const=True)

class Time(BaseModel):
    """Model for ngen time configuraiton components
    """
    #required
    start_time: datetime
    end_time: datetime
    #reasonable default (defacto, actually???)
    output_interval: PosInt = 3600

    #FIXME https://github.com/samuelcolvin/pydantic/issues/2277
    #Until 1.10, it looks like nested encoder config doesn't apply
    #so you have to define the encoder at the top level object that
    #will be serialized...
    class Config:
        #override how datetime format looks in .json()
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")
        }

class Routing(BaseModel):
    """Model for ngen routing configuration information
    """
    #required
    config: FilePath = Field(alias='t_route_config_file_with_path')
    #optional/not used TODO make default None?
    path: Optional[str] = Field('', alias='t_route_connection_path') #TODO deprecate this field?

    def dict(self, *kwargs):
        #Can override the `dict` call so we ALWAYS `use_aliases` when this model
        #is serialized
        kwargs.setdefault('use_aliases', True)
        return super().dict(**kwargs)