from __future__ import annotations

import importlib
from typing import Any, Type, Union
from types import ModuleType
from copy import deepcopy


__SENTINEL = object()
__MERGE_SENTINEL = object()
__HASATTR_SENTINEL = object()


def get_attr(
    __o: object, __name: str, __default: object = __SENTINEL
) -> Union[Any, object]:
    value = __o
    partial_attrs = __name.split(".")

    for attr in partial_attrs:
        try:
            value = getattr(value, attr)
        except AttributeError:
            if __default == __SENTINEL:
                raise
            return __default
    return value


def has_attr(__o: object, __name: str) -> bool:
    return get_attr(__o, __name, __HASATTR_SENTINEL) == __HASATTR_SENTINEL


def merge_class_attr(
    __t: Type[object], __name: str, __default: object = __SENTINEL
) -> Union[Any, object]:
    """
    Walk a type's mro from back to front and merge or retrieve a _deep copy_ of a class attribute.
    Mergable attribute types (including subtypes) are, lists, dictionaries, and sets. Attributes are
    deep copied to avoid modifying class attributes inplace.

    Nested attribute retrieval is supported by providing the attribute to retrieve separated by `.`
    (i.e. to get `Foo.bar.baz`, `merge_class_attr(Foo, "bar.baz")`).

    Collection type class attributes that are explicitly empty and a type or subtype of the
    accumulated merge object, are not merged. Instead, the accumulated merge object is set to a copy
    of the empty collection for the next iteration.

    Raises
    ------
    AttributeError
        Raises if default not provided and no attribute does not exist
    """
    mro = __t.mro()

    final: Union[object, Any] = __MERGE_SENTINEL

    # unique id of source collection.
    # its healthy to think of this as a pointer to a source collection.
    # before merging mutable collections, we need to verify that a subtype's class variable
    # reference does not match a super type's class variable reference. this is required to avoid
    # _over extending_ or noop updates.
    #
    # for example, a class `Foo` has a *class variable* `bar` with the value `[1, 2, 3]`.
    # a subclass `Baz(Foo)` is defined and does not specify a value for `bar`
    # (i.e. `class Baz(Foo): ...`). this means, `Baz` contains a reference to `Foo`'s `bar`
    # *class variable*. thus, `id(Foo.bar) == id(Baz.bar)`. consequently, if we do not keep track of
    # `Foo`'s `bar` id (think of this like `&Foo.baz`), when merging `Baz`'s `bar`, we could
    # _over update_, meaning instead of skipping the merge, we merge and now have
    # `[1, 2, 3, 1, 2, 3]`. therefore, before merging, we need to verify that a subtype's class
    # variable reference does not match a super type's class variable reference.
    src_id: int

    collection_types = (list, dict, set)

    # walk mro backwards merging from back to front. this mean, for example, parent types would
    # override grandparent types.
    for cls in mro[::-1]:
        value = get_attr(cls, __name, __MERGE_SENTINEL)
        if value == __MERGE_SENTINEL:
            continue

        # overwrite;
        # we know that either:
        # - value is not a type we support merging
        # - or, previous final was not a type we support merging
        # - or, value and final are not covariant
        if (
            not isinstance(value, collection_types)
            or not isinstance(final, collection_types)
            or not isinstance(value, type(final))
        ):
            # see above note at initialization
            # think of this as `&Foo.bar`
            src_id = id(value)
            # deep copy to avoid modifying mutable collections inplace
            final = deepcopy(value)

        # value is *explicitly* empty and a list, dict, or set type, dont merge
        elif not value:
            src_id = id(value)
            final = value.copy()

        # value is covariant to final and final is covariant to dict or set
        elif isinstance(value, (dict, set)):
            if id(value) == src_id:
                continue

            final.update(value)

        # value is covariant to final and final is covariant to list or set
        elif isinstance(value, list):
            if id(value) == src_id:
                continue

            final.extend(value)

    if final == __MERGE_SENTINEL:
        if __default == __SENTINEL:
            raise AttributeError(
                f"{__t.__name__} object nor it's super classes have no attribute {__name!r}"
            )
        return __default

    return final


def try_import(mod: str, extras_require_name: str) -> ModuleType:
    try:
        return importlib.import_module(mod)
    except ImportError as e:
        raise ImportError(
            f"{mod!r} package is missing. Try reinstalling using 'pip install ngen.init_config[{extras_require_name}]'"
        ) from e
