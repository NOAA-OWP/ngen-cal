from pydantic import BaseModel, DirectoryPath, conint
from typing import Optional, Tuple
from datetime import datetime
from pathlib import Path
from abc import ABC, abstractmethod

# additional constrained types
PosInt = conint(gt=-1)

class Configurable(ABC):
    """
        Abastract interface for wrapping configurable external models
        for use in the ngen-cal package
    """

    @abstractmethod
    def get_binary() -> str:
        """Get the binary string to execute

        Returns:
            str: The binary name or path used to execute the Configurable model
        """
    
    @abstractmethod
    def get_args() -> str:
        """Get the args to pass to the binary

        Returns:
            str: Preconfigured arg string to pass to the binary upon execution
        """

    @abstractmethod
    def update_config(*args, **kwargs):
        pass

class EvaluationOptions(BaseModel):
    """
        A data class holding evaluation parameters
    """
    #TODO make this optional, but co-dependent???
    evaluation_start: Optional[datetime]
    evaluation_stop: Optional[datetime]
    _eval_range: Tuple[datetime, datetime] = None

    class Config:
        """Override configuration for pydantic BaseModel
        """
        underscore_attrs_are_private = True
        use_enum_values = True

    def __init__(self, **kwargs):
        """
        
        """
        super().__init__(**kwargs)
        if self.evaluation_start and self.evaluation_stop:
            self._eval_range = (self.evaluation_start, self.evaluation_stop)
        else: #TODO figure out open/close range???
            self._eval_range=None

class ModelExec(BaseModel, Configurable):
    """
        The data class for a given model, which must also be Configurable
    """
    binary: str
    args: Optional[str]
    workdir: DirectoryPath = Path("./")
    eval_params: EvaluationOptions

    def get_binary(self)->str:
        """Get the binary string to execute

        Returns:
            str: The binary name or path used to execute the Configurable model
        """
        return self.binary

    def get_args(self)->str:
        """Get the args to pass to the binary

        Returns:
            str: Preconfigured arg string to pass to the binary upon execution
        """
        return self.args
