from __future__ import annotations

from pydantic import BaseModel, Field, root_validator
from typing import Sequence, Mapping, Optional

class Parameter(BaseModel, allow_population_by_field_name = True):
    """
        The data class for a given parameter
    """
    name: str = Field(alias='param')
    min: float
    max: float
    init: float
    alias: Optional[str]

    @root_validator
    def _set_alias(cls, values: dict) -> dict:
        alias = values.get('alias', None)
        if alias is None:
            values['alias'] = values['name']
        return values

Parameters = Sequence[Parameter]
