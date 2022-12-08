from pydantic import BaseModel, Field

class Formulation(BaseModel, smart_union=True):
    """Model of an ngen formulation
    """
    #TODO make this an enum?
    name: str
    params:  "KnownFormulations" = Field(descriminator="model_name")

    def resolve_paths(self):
        self.params.resolve_paths()

#NOTE To avoid circular import and support recrusive modules
#note that `params` is one of KnownFormulations, 
#of which MultiBMI may be one of those.  
#A MultiBMI has a sequence of Formulation objects, making a recursive type
# So we defer type cheking and importing the KnownFormulations until after
#MultiBMI is defined, then update_forward_refs()
from .all_formulations import KnownFormulations
Formulation.update_forward_refs()