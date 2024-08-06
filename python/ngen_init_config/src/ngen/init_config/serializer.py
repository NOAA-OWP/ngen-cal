from __future__ import annotations

import os
import pathlib

from . import core, format_serializers, utils


class IniSerializer(core.Base):
    """Blanket implementation for serializing into ini format. Python's standard library
    `configparser` package is used to handle serialization.

    Fields are serialized using their alias, if provided.

    Subtype specific configuration options:
        Optionally provide configuration options in `Config` class of types that inherits from
        `IniSerializer`.

        - `no_section_headers`: bool
            If True, output ini will not have section headers (default: `False`)
        - `space_around_delimiters`: bool
            If True, delimiters between keys and values are surrounded by spaces (default: `True`)
        - `preserve_key_case`: bool
            If True, keys will be case sensitively serialized (default: `False`)
    """

    class Config(core.Base.Config):
        no_section_headers: bool = False
        space_around_delimiters: bool = True
        preserve_key_case: bool = False

    def to_ini(self, p: pathlib.Path) -> None:
        with open(p, "w") as f:
            b_written = f.write(self.to_ini_str())
            if b_written:
                # add eol
                f.write(os.linesep)

    def to_ini_str(self) -> str:
        data = self.dict(by_alias=True)
        return self._to_ini_str(data)

    def _to_ini_str(self, data: dict) -> str:
        if self._no_section_headers:
            return format_serializers.to_ini_no_section_header_str(
                data,
                space_around_delimiters=self._space_around_delimiters,
                preserve_key_case=self._preserve_key_case,
            )

        return format_serializers.to_ini_str(
            data,
            space_around_delimiters=self._space_around_delimiters,
            preserve_key_case=self._preserve_key_case,
        )

    @property
    def _space_around_delimiters(self) -> bool:
        return utils.merge_class_attr(type(self), "Config.space_around_delimiters", True)  # type: ignore

    @property
    def _no_section_headers(self) -> bool:
        return utils.merge_class_attr(type(self), "Config.no_section_headers", False)  # type: ignore

    @property
    def _preserve_key_case(self) -> bool:
        return utils.merge_class_attr(type(self), "Config.preserve_key_case", False)  # type: ignore


class NamelistSerializer(core.Base):
    """Blanket implementation for serializing into FORTRAN namelist format. The `f90nml` package is
    used to handle serialization. `f90nml` is not included in default installations of
    `ngen.init_config`. Install `ngen.init_config` with `f90nml` using the extra install option,
    `namelist`.

    Fields are serialized using their alias, if provided.
    """

    def to_namelist(self, p: pathlib.Path) -> None:
        with open(p, "w") as f:
            b_written = f.write(self.to_namelist_str())
            if b_written:
                # add eol
                f.write(os.linesep)

    def to_namelist_str(self) -> str:
        return format_serializers.to_namelist_str(self.dict(by_alias=True))


class YamlSerializer(core.Base):
    """Blanket implementation for serializing from yaml format. The `PyYAML` package is used to
    handle serialization. `PyYAML` is not included in default installations of `ngen.init_config`.
    Install `ngen.init_config` with `PyYAML` using the extra install option, `yaml`.

    Fields are serialized using their alias, if provided.
    """

    def to_yaml(self, p: pathlib.Path) -> None:
        with open(p, "w") as f:
            b_written = f.write(self.to_yaml_str())
            if b_written:
                # add eol
                f.write(os.linesep)

    def to_yaml_str(self) -> str:
        return format_serializers.to_yaml_str(self.dict(by_alias=True))


class TomlSerializer(core.Base):
    """Blanket implementation for serializing from `toml` format. The `tomli_w` package is used to
    handle serialization. `tomli_w` is not included in default installations of `ngen.init_config`.
    Install `ngen.init_config` with `tomli_w` using the extra install option, `toml`.

    Fields are serialized using their alias, if provided.
    """

    def to_toml(self, p: pathlib.Path) -> None:
        with open(p, "w") as f:
            b_written = f.write(self.to_toml_str())
            # add eol
            if b_written:
                f.write(os.linesep)

    def to_toml_str(self) -> str:
        return format_serializers.to_toml_str(self.dict(by_alias=True))


class JsonSerializer(core.Base):
    """Blanket implementation for serializing to `json` format. This functionality is provided by
    `pydantic`. See `pydantic`'s documentation for other configuration options.

    Fields are serialized using their alias, if provided.
    """

    def to_json(self, p: pathlib.Path, *, indent: int = 0) -> None:
        with open(p, "w") as f:
            b_written = f.write(self.to_json_str(indent=indent))
            # add eol
            if b_written:
                f.write(os.linesep)

    def to_json_str(self, *, indent: int = 0) -> str:
        options = {} if not indent else {"indent": indent}
        # remove trailing eol
        return self.json(by_alias=True, **options).rstrip()
