from __future__ import annotations #for pydnaitc

import logging

#Typing, datamodel
from pydantic import BaseModel, Field, DirectoryPath
from pathlib import Path
from typing_extensions import Literal
from typing import Any, Dict, Optional, List, Union
from types import ModuleType, FunctionType

#local components for composing configuration
from .strategy import Estimation, Sensitivity
from .model import PosInt
from .ngen import Ngen
from .utils import PyObjectOrModule, type_as_import_string

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
    #Fields with reasonable defaults
    restart: bool = False
    start_iteration: PosInt = 0
    workdir: DirectoryPath = Path("./")
    name: str = "ngen-calibration"
    #Optional fields
    log: Optional[bool] = False
    parameter_log_file: Optional[Path]
    objective_log_file: Optional[Path]
    random_seed: Optional[int]
    plugins: List[PyObjectOrModule] = Field(default_factory=list)
    plugin_settings: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    class Config(BaseModel.Config):
        # properly serialize plugins
        json_encoders = {
            type: type_as_import_string,
            ModuleType: lambda mod: mod.__name__,
            FunctionType: type_as_import_string,
        }

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
