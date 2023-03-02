from typing import Any, Dict, Type

from .typing import M


def case_insensitive_keys(cls: Type[M], values: Dict[str, Any]) -> Dict[str, Any]:
    """pydantic root validator that case insensitively remaps input `values` keys to model alias, if
    present, or field names.
    """
    keys = cls.__fields__.values()
    keys_map = {k.alias.casefold(): k.alias for k in keys}

    # NOTE: only guarantees remapping defined fields to their case insensitive representation;
    # e.g. if `Config.extra = "allow"`, undefined fields will be included as is.
    remapped: Dict[str, Any] = {}
    for k, v in values.items():
        try:
            key = keys_map[k.casefold()]
            remapped[key] = v
        except KeyError:
            remapped[k] = v

    return remapped
