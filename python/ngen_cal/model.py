from pydantic import BaseModel, DirectoryPath, conint
from typing import Optional
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

class ModelExec(BaseModel, Configurable):
    """
        The data class for a given model, which must also be Configurable
    """
    binary: str
    args: Optional[str]
    workdir: DirectoryPath = Path("./")

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