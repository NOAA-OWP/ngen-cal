from __future__ import annotations

from . import serializer as ser
from . import deserializer as de


class IniSerializerDeserializer(ser.IniSerializer, de.IniDeserializer):
    """Blanket implementation for deserializing from and serializing into ini format. Python's
    standard library `configparser` package is used to handle serialization and deserialization.

    Fields are serialized using their alias, if provided.

    Subtype specific configuration options:
        Optionally provide configuration options in `Config` class of types that inherits from
        `IniSerializerDeserializer`.

        - `no_section_headers`: bool
            If True, output ini will not have section headers (default: `False`)
        - `space_around_delimiters`: bool
            If True, delimiters between keys and values are surrounded by spaces (default: `True`)
    """

    class Config(ser.IniSerializer.Config):  # type: ignore
        no_section_headers: bool = False
        space_around_delimiters: bool = True


class NamelistSerializerDeserializer(ser.NamelistSerializer, de.NamelistDeserializer):
    """Blanket implementation for deserializing from and serializing into FORTRAN namelist format.
    The `f90nml` package is used to handle serialization and deserialization. `f90nml` is not
    included in default installations of `ngen.init_config`. Install `ngen.init_config` with
    `f90nml` using the extra install option, `namelist`.

    Fields are serialized using their alias, if provided.
    """

    ...


class YamlSerializerDeserializer(ser.YamlSerializer, de.YamlDeserializer):
    """Blanket implementation for deserializing from and serializing into yaml format. The `PyYAML`
    package is used to handle serialization and deserialization. `PyYAML` is not included in default
    installations of `ngen.init_config`.  Install `ngen.init_config` with `PyYAML` using the extra
    install option, `yaml`.

    Fields are serialized using their alias, if provided.
    """

    ...


class TomlSerializerDeserializer(ser.TomlSerializer, de.TomlDeserializer):
    """Blanket implementation for serializing and deserializing from `toml` format. The `tomli` and
    `tomli_w` packages are used to handle deserialization and serialization respectively. `tomli`
    nor `tomli_w` are not included in default installations of `ngen.init_config`.  Install
    `ngen.init_config` with `tomli` and `tomli_w` support using the extra install option, `toml`.

    Fields are serialized using their alias, if provided.
    """

    ...


class JsonSerializerDeserializer(ser.JsonSerializer, de.JsonDeserializer):
    """Blanket implementation for serializing and deserializing to and from `json` format. This
    functionality is provided by `pydantic`. See `pydantic`'s documentation for other configuration
    options.

    Fields are serialized using their alias, if provided.
    """

    ...


class GenericSerializerDeserializer(ser.GenericSerializer, de.GenericDeserializer):
    """
    Stub for deserializing from and serializing to a generic format.
    Subclasses must implement the `to_file`, `to_str`, `from_file`, and `from_str` abstract methods.
    See `ngen.init_config.core.Base` and `pydantic`'s documentation for configuration options.
    """

    ...
