from pydantic import BaseModel, Field
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Optional
    from pathlib import Path

class Formulation(BaseModel, smart_union=True):
    """Model of an ngen formulation
    """
    #TODO make this an enum?
    name: str
    params:  "KnownFormulations" = Field(descriminator="model_name")

    def resolve_paths(self, relative_to: 'Optional[Path]'=None):
        self.params.resolve_paths(relative_to)

#NOTE To avoid circular import and support recrusive modules
#note that `params` is one of KnownFormulations, 
#of which MultiBMI may be one of those.  
#A MultiBMI has a sequence of Formulation objects, making a recursive type
# So we defer type cheking and importing the KnownFormulations until after
#MultiBMI is defined, then update_forward_refs()
from .all_formulations import KnownFormulations
Formulation.update_forward_refs()