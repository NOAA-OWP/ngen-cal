from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, Mapping, Sequence, Any
from pathlib import Path

from datetime import datetime
from .configurations import Forcing, Time, Routing
from .formulation import Formulation

class Realization(BaseModel):
    """Simple model of a Realization, containing formulations and forcing
    """
    formulations: Sequence[Formulation]
    forcing: Forcing
    calibration: Optional[ Mapping[ str, Sequence[ Any ]] ]

    def resolve_paths(self, relative_to: Optional['Path']=None):
        for f in self.formulations:
            f.resolve_paths(relative_to)
        if self.forcing :
            self.forcing.resolve_paths(relative_to)

class CatchmentRealization(Realization):
    forcing: Optional[Forcing]

class NgenRealization(BaseModel):
    """A complete ngen realization confiiguration model, including global and catchment overrides
    """
    global_config: Realization = Field(alias='global')
    time: Time
    routing: Optional[Routing]
    #FIXME have not tested catchments...
    catchments: Optional[ Mapping[str, CatchmentRealization] ] = {}
    # added in https://github.com/NOAA-OWP/ngen/pull/531
    output_root: Optional[Path]

    #FIXME https://github.com/samuelcolvin/pydantic/issues/2277
    #Until 1.10, it looks like nested encoder config doesn't apply
    #so you have to define the encoder at the top level object that
    #will be serialized...
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.strftime("%Y-%m-%d %H:%M:%S")
        }

    def resolve_paths(self, relative_to: Optional['Path']=None):
        """resolve possible relative paths in configuration
        """
        self.global_config.resolve_paths(relative_to)
        for k,v in self.catchments.items():
            v.resolve_paths(relative_to)
        if self.routing != None:
            self.routing.resolve_paths(relative_to)
