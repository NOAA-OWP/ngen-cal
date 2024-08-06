from __future__ import annotations

import sys

# see: https://docs.python.org/3.8/library/typing.html#typing.get_args
# get_args and get_origin were added in 3.8
# TODO: remove once we drop 3.7 support
if sys.version_info >= (3, 8):
    from typing import get_args, get_origin
else:
    from typing_extensions import get_args, get_origin

from typing import (
    Any,
    Callable,
    Dict,
    Type,
    TypeVar,
    Union,
)

from pydantic import BaseModel
from typing_extensions import TypeAlias

M = TypeVar("M", bound=BaseModel)
JsonSerializablePrimitives: TypeAlias = Union[int, float, str, bool, None]

FnJsonSerializable: TypeAlias = Callable[[Any], JsonSerializablePrimitives]
FieldSerializers: TypeAlias = Dict[str, FnJsonSerializable]
TypeSerializers: TypeAlias = Dict[Type[Any], FnJsonSerializable]


def flatten_args(t: type[object]) -> tuple[type[object], ...]:
    """Flatten and deduplicate nested type hints. Order is preserved. In line with `get_args`'
    behavior, `typing.Union` are excluded.

    Example:
    ```python
    flatten_args(Union[Dict[str, Any], Tuple[str, str], None]) == (dict, str, typing.Any, tuple, type(None))
    ```
    """
    # NOTE: python 3.7 >= dictionaries are ordered
    flat: dict[type[object], None] = {}
    horizon: list[type[object]] = [t]

    while True:
        if not horizon:
            break

        t = horizon.pop()
        origin = get_origin(t)
        args = get_args(t)

        if origin is None and not args:
            flat[t] = None
            continue

        if origin is not None and origin is not Union:
            flat[origin] = None

        # extend in reverse order.
        # pop, pops from the back, so to retain ordering, we need to extend in reverse.
        horizon.extend(args[::-1])

    return tuple(flat)
