from __future__ import annotations

import configparser

from typing import Any, Dict, Type

from .typing import M
from .utils import try_import
from ._constants import NO_SECTIONS


def from_ini_str(ini_str: str, m: Type[M]) -> M:
    cp = configparser.ConfigParser(interpolation=None)
    # cp.optionxform = str
    cp.read_string(ini_str)
    values = {
        section_name: dict(cp.items(section_name)) for section_name in cp.sections()
    }
    return m.parse_obj(values)


def from_ini_no_section_header_str(ini_str: str, m: Type[M]) -> M:
    cp = configparser.ConfigParser(interpolation=None)
    cp.read_string(f"[{NO_SECTIONS}]\n" + ini_str)

    # only NO_SECTIONS should be present
    assert len(cp.sections()) == 1

    values = dict(cp.items(NO_SECTIONS))
    return m.parse_obj(values)


def from_namelist_str(nl_str: str, m: Type[M]) -> M:
    f90nml = try_import("f90nml", extras_require_name="namelist")
    parser = f90nml.Parser()
    data: f90nml.Namelist = parser.reads(nl_str)
    # SAFETY: python 3.7 >= dict ordering is preserved
    return m.parse_obj(data.todict())


def from_yaml_str(yaml_str: str, m: Type[M]) -> M:
    yaml = try_import("yaml", extras_require_name="yaml")
    try:
        from yaml import CLoader as Loader
    except ImportError:
        from yaml import Loader

    data: Dict[str, Any] = yaml.load(yaml_str, Loader=Loader)
    return m.parse_obj(data)


def from_toml_str(toml_str: str, m: Type[M]) -> M:
    tomli = try_import("tomli", extras_require_name="toml")

    data: Dict[str, Any] = tomli.loads(toml_str)
    return m.parse_obj(data)
