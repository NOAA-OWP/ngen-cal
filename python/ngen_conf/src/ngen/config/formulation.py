from __future__ import annotations

from pydantic import BaseModel, validator
from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from pathlib import Path

class Formulation(BaseModel, smart_union=True):
    """
    Model of an ngen formulation.

    Note, during object creation if the `params` field is deserialized (e.g. `params`'s value is a
    dictionary), the `name` field is required. If `name` *is not* 'bmi_multi', the `model_type_name`
    field is also required. Neither are required if a concrete known formulation instance is
    provided.
    """
    #TODO make this an enum?
    name: str
    params:  KnownFormulations

    @validator("params", pre=True)
    def _validate_params(
        cls, value: dict[str, Any] | KnownFormulations
    ) -> dict[str, Any] | KnownFormulations:
        if isinstance(value, BaseModel):
            return value

        if isinstance(value, dict):
            name = value.get("name")
            if name == "bmi_multi":
                return value

            # non-bmi multi subtypes must specify their `name` and `model_type_name` fields when _deserializing_.
            # note: this does not apply if a subtype instance is provided
            if name is None and ("model_type_name" not in value or "model_name" not in value):
                raise ValueError("'name' and 'model_type_name' fields are required when deserializing _into_ a 'Formulation'.")
        return value

    def resolve_paths(self, relative_to: Path | None=None):
        self.params.resolve_paths(relative_to)

#NOTE To avoid circular import and support recrusive modules
#note that `params` is one of KnownFormulations,
#of which MultiBMI may be one of those.
#A MultiBMI has a sequence of Formulation objects, making a recursive type
# So we defer type cheking and importing the KnownFormulations until after
#MultiBMI is defined, then update_forward_refs()
from .all_formulations import KnownFormulations
Formulation.update_forward_refs()
