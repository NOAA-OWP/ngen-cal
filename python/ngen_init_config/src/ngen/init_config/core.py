from datetime import datetime
from functools import lru_cache
from typing import TYPE_CHECKING, Optional, Type, Union

from pydantic import BaseModel
from pydantic.main import BaseModel, _missing
from pydantic.utils import ValueItems

from .typing import FieldSerializers, TypeSerializers, flatten_args
from .utils import merge_class_attr

if TYPE_CHECKING:
    from pydantic.typing import AbstractSetIntStr, MappingIntStrAny, TupleGenerator


def _default_datetime_format(d: datetime) -> str:
    """ISO 8601 datetime string with truncated seconds (i.e. `2000-01-01T00:00:00`)

    https://en.wikipedia.org/wiki/ISO_8601
    """
    return d.isoformat(timespec="seconds")


class Base(BaseModel):
    """Pydantic `BaseModel` subclass that adds several nice to have configuration options and sane
    defaults.

    The purpose of this class is to provide useful enhancements to pydantic's `BaseModel` class for
    the use case of serializing and deserializing to and from arbitrary formats. However, these
    enhancements are generally applicable if custom field serialization is a requirement
    (i.e. `.dict()` / `.json()`).

    Defaults:
        - `datetime` field types are serialized using isoformat with truncated seconds
          (i.e. `2000-01-01T00:00:00`). Override this by providing a custom
          `Config.field_type_serializers`.

        - `Config.allow_population_by_field_name` is True, this enables programmatically creating a
          model using it's field names or aliases. See: https://docs.pydantic.dev/usage/model_config/

    Configuration options:
        Optionally provide configuration options in `Config` class of types that inherits from
        `Base`.

        See `pydantic.BaseModel` for other [inherited configuration options](https://docs.pydantic.dev/usage/model_config/).
        Of note, `ngen.init_config` provides

        - `field_type_serializers`: dict[Type[T], (value: T) -> int | float | str | bool | None ]
            Map of type to serialization function. Fields with a _matching_ type in the map will be
            serialized (i.e. `.dict()` / `.json()`) using the associated serialization function.
            Note, type comparison is invariant (i.e. `type(t) == T`), this means subtypes of T will
            not be serialized using T's serializer. Additionally, `field_serializers` take
            precedence over `field_type_serializers`.

        - `field_serializers`: dict[str, (value: T) -> int | float | str | bool | None ]
            Map of field name to serialization function. Fields with a name in the map will be
            serialized (i.e. `.dict()` / `.json()`) using using the associated serialization
            function.
    """

    class Config(BaseModel.Config):
        field_serializers: FieldSerializers
        field_type_serializers: TypeSerializers = {datetime: _default_datetime_format}

        allow_population_by_field_name = True

    def _iter(
        self,
        to_dict: bool = False,
        by_alias: bool = False,
        include: Optional[Union["AbstractSetIntStr", "MappingIntStrAny"]] = None,
        exclude: Optional[Union["AbstractSetIntStr", "MappingIntStrAny"]] = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> "TupleGenerator":
        # NOTE: majority of this code was copy pasted from `pydantic==1.10.5`. Due to `pydantic`'s
        # stability and implementation of this method, it was easier and more straightforward to go
        # this route rather than an implementation overload. For readability and maintainability,
        # sections of code that are `ngen.init_config` specific have been bookended with:
        # start / end `ngen.init_config` additions
        # comments.

        # Merge field set excludes with explicit exclude parameter with explicit overriding field set options.
        # The extra "is not None" guards are not logically necessary but optimizes performance for the simple case.
        if exclude is not None or self.__exclude_fields__ is not None:
            exclude = ValueItems.merge(self.__exclude_fields__, exclude)

        if include is not None or self.__include_fields__ is not None:
            include = ValueItems.merge(self.__include_fields__, include, intersect=True)

        allowed_keys = self._calculate_keys(
            include=include, exclude=exclude, exclude_unset=exclude_unset  # type: ignore
        )
        if allowed_keys is None and not (
            to_dict or by_alias or exclude_unset or exclude_defaults or exclude_none
        ):
            # huge boost for plain _iter()
            yield from self.__dict__.items()
            return

        value_exclude = ValueItems(self, exclude) if exclude is not None else None
        value_include = ValueItems(self, include) if include is not None else None

        # start `ngen.init_config` additions (1/2)

        # determine if the model being serialized is composed of any other `Base` model's
        uses_composition = _uses_composition(type(self))
        # get all `field_type_serializers` and inherited `field_type_serializers`
        type_serializers = _get_field_type_serializers(type(self))

        # NOTE: this call is memoized
        # get all `field_serializers` and inherited `field_serializers`
        field_serializers = _get_field_serializers(type(self))

        # end `ngen.init_config` additions (1/2)

        for field_key, v in self.__dict__.items():
            if (allowed_keys is not None and field_key not in allowed_keys) or (
                exclude_none and v is None
            ):
                continue

            if exclude_defaults:
                model_field = self.__fields__.get(field_key)
                if (
                    not getattr(model_field, "required", True)
                    and getattr(model_field, "default", _missing) == v
                ):
                    continue

            if by_alias and field_key in self.__fields__:
                dict_key = self.__fields__[field_key].alias
            else:
                dict_key = field_key

            if to_dict or value_include or value_exclude:
                # start `ngen.init_config` additions (2/2)

                # if `self` is composed of a `Base` subtype:
                #   1. take copy of `v`'s `field_type_serializers`
                #   2. monkey patch `v`'s `field_type_serializers` with `self`'s
                #   3. serialize `v` like normal (_get_value, meaning this process could cascade)
                #   4. un-monkey patch `v`'s `field_type_serializers`
                # NOTE: field serializers still take precedence
                if isinstance(v, Base) and uses_composition:
                    # check is recursive
                    has_type_serializers = _has_field_type_serializers(type(v))

                    # NOTE: I dont think we need to copy here?
                    # check is recursive
                    org_type_serializers = _get_field_type_serializers(type(v))

                    v.Config.field_type_serializers = type_serializers
                    try:
                        serial_v = self._get_value(
                            v,
                            to_dict=to_dict,
                            by_alias=by_alias,
                            include=value_include
                            and value_include.for_element(field_key),
                            exclude=value_exclude
                            and value_exclude.for_element(field_key),
                            exclude_unset=exclude_unset,
                            exclude_defaults=exclude_defaults,
                            exclude_none=exclude_none,
                        )
                    finally:
                        # ensure that type serializers are returned to their original state and not
                        # corrupted
                        if not has_type_serializers:
                            del v.Config.field_type_serializers
                        else:
                            v.Config.field_type_serializers = org_type_serializers

                    v = serial_v

                # change how we serialize based on key name or value type
                # `field_serializers` *always* take precedence over `field_type_serializers`
                elif field_key in field_serializers:
                    fn = field_serializers[field_key]
                    v = fn(v)

                # NOTE: covariant types are not equal
                elif type(v) in type_serializers:
                    fn = type_serializers[type(v)]
                    v = fn(v)
                # end `ngen.init_config` additions (2/2)

                else:
                    v = self._get_value(
                        v,
                        to_dict=to_dict,
                        by_alias=by_alias,
                        include=value_include and value_include.for_element(field_key),
                        exclude=value_exclude and value_exclude.for_element(field_key),
                        exclude_unset=exclude_unset,
                        exclude_defaults=exclude_defaults,
                        exclude_none=exclude_none,
                    )
            yield dict_key, v


def _get_field_type_serializers(t: Type[Base]) -> TypeSerializers:
    return merge_class_attr(t, "Config.field_type_serializers", {})  # type: ignore


def _has_field_type_serializers(t: Type[Base]) -> bool:
    return bool(_get_field_serializers(t))


@lru_cache(maxsize=None)
def _get_field_serializers(t: Type[Base]) -> FieldSerializers:
    return merge_class_attr(t, "Config.field_serializers", {})  # type: ignore


@lru_cache(maxsize=None)
def _uses_composition(cls: Type[Base]) -> bool:
    for v in cls.__fields__.values():
        flat_type_hints = flatten_args(v.type_)
        for t in flat_type_hints:
            # ensure `t` is a type not an instance. e.g. a flattened Literal will contain non
            # instance type members.
            if isinstance(t, type) and issubclass(t, Base):
                return True
    return False
