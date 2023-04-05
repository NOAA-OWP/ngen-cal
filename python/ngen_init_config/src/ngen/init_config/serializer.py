from pathlib import Path

from .core import Base
from .utils import merge_class_attr
from ._serlializers import (
    to_namelist_str,
    to_ini_str,
    to_ini_no_section_header_str,
    to_yaml_str,
    to_toml_str,
)


class IniSerializer(Base):
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

    class Config(Base.Config):
        no_section_headers: bool = False
        space_around_delimiters: bool = True
        preserve_key_case: bool = False

    def to_ini(self, p: Path) -> None:
        with open(p, "w") as f:
            if self._no_section_headers:
                f.write(
                    to_ini_no_section_header_str(
                        self,
                        space_around_delimiters=self._space_around_delimiters,
                        preserve_key_case=self._preserve_key_case,
                    )
                )
                return

            f.write(
                to_ini_str(
                    self,
                    space_around_delimiters=self._space_around_delimiters,
                    preserve_key_case=self._preserve_key_case,
                )
            )

    def to_ini_str(self) -> str:
        if self._no_section_headers:
            return to_ini_no_section_header_str(
                self,
                space_around_delimiters=self._space_around_delimiters,
                preserve_key_case=self._preserve_key_case,
            )

        return to_ini_str(
            self,
            space_around_delimiters=self._space_around_delimiters,
            preserve_key_case=self._preserve_key_case,
        )

    @property
    def _space_around_delimiters(self) -> bool:
        return merge_class_attr(type(self), "Config.space_around_delimiters", True)  # type: ignore

    @property
    def _no_section_headers(self) -> bool:
        return merge_class_attr(type(self), "Config.no_section_headers", False)  # type: ignore

    @property
    def _preserve_key_case(self) -> bool:
        return merge_class_attr(type(self), "Config.preserve_key_case", False)  # type: ignore


class NamelistSerializer(Base):
    """Blanket implementation for serializing into FORTRAN namelist format. The `f90nml` package is
    used to handle serialization. `f90nml` is not included in default installations of
    `ngen.init_config`. Install `ngen.init_config` with `f90nml` using the extra install option,
    `namelist`.

    Fields are serialized using their alias, if provided.
    """

    def to_namelist(self, p: Path) -> None:
        with open(p, "w") as f:
            f.write(to_namelist_str(self))

    def to_namelist_str(self) -> str:
        return to_namelist_str(self)


class YamlSerializer(Base):
    """Blanket implementation for serializing from yaml format. The `PyYAML` package is used to
    handle serialization. `PyYAML` is not included in default installations of `ngen.init_config`.
    Install `ngen.init_config` with `PyYAML` using the extra install option, `yaml`.

    Fields are serialized using their alias, if provided.
    """

    def to_yaml(self, p: Path) -> None:
        with open(p, "w") as f:
            f.write(to_yaml_str(self))

    def to_yaml_str(self) -> str:
        return to_yaml_str(self)


class TomlSerializer(Base):
    """Blanket implementation for serializing from `toml` format. The `tomli_w` package is used to
    handle serialization. `tomli_w` is not included in default installations of `ngen.init_config`.
    Install `ngen.init_config` with `tomli_w` using the extra install option, `toml`.

    Fields are serialized using their alias, if provided.
    """

    def to_toml(self, p: Path) -> None:
        with open(p, "w") as f:
            f.write(to_toml_str(self))

    def to_toml_str(self) -> str:
        return to_toml_str(self)


class JsonSerializer(Base):
    """Blanket implementation for serializing to `json` format. This functionality is provided by
    `pydantic`. See `pydantic`'s documentation for other configuration options.

    Fields are serialized using their alias, if provided.
    """

    def to_json(self, p: Path, *, indent: int = 0) -> None:
        options = {} if not indent else {"indent": indent}
        with open(p, "w") as f:
            f.write(self.json(by_alias=True, **options))

    def to_json_str(self, *, indent: int = 0) -> str:
        options = {} if not indent else {"indent": indent}
        return self.json(by_alias=True, **options)
