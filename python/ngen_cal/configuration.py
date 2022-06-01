from __future__ import annotations #for pydnaitc 

import logging

#Typing, datamodel
from pydantic import BaseModel, Field, DirectoryPath
from datetime import datetime
from pathlib import Path
from typing import Optional, Union
try: #to get literal in python 3.7, it was added to typing in 3.8
    from typing import Literal
except ImportError:
    from typing_extensions import Literal

#local components for composing configuration
from .strategy import Estimation, Sensitivity
from .model import PosInt
from .ngen import Ngen

import logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s,%(msecs)d %(levelname)s: %(message)s",
    datefmt="%H:%M:%S")

class General(BaseModel):
    """
        General ngen-cal configuration requirements
    """
    #required fields
    strategy: Union[Estimation, Sensitivity] = Field(discriminator='type')
    iterations: int
    #TODO make this optional, but co-dependent???
    evaluation_start: datetime
    evaluation_stop: datetime
    #Fields with reasonable defaults
    restart: bool = False
    start_iteration: PosInt = 0
    workdir: DirectoryPath = Path("./")
    name: str = "ngen-calibration"
    #Optional fields
    log_file: Optional[Path]
    parameter_log_file: Optional[Path]
    objective_log_file: Optional[Path]
    random_seed: Optional[int]


class NoModel(BaseModel):
    """
        A simple empty model data class for testing
    """
    type: Literal['none']

class Model(BaseModel):
    """
        Composition data class for defining a model configuration
    """
    model: Union[Ngen, NoModel] = Field(discriminator='type')
