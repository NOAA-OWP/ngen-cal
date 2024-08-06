from __future__ import annotations

import configparser
from collections import OrderedDict
from io import StringIO
from typing import Any, Dict, List, Union

from typing_extensions import TypeAlias

from ._constants import NO_SECTIONS
from .utils import try_import


def to_namelist_str(d: dict[str, Any]) -> str:
    """Serialize a dictionary as an namelist formatted string."""
    f90nml = try_import("f90nml", extras_require_name="namelist")

    # NOTE: Cast to OrderedDict to guarantee group-name ordering
    # dicts are ordered in python >= 3.7, however f90nml does an isinstance OrderedDict check
    namelist = f90nml.Namelist(OrderedDict(d))
    # drop eol chars
    return str(namelist).rstrip()


_NON_NONE_JSON_PRIMITIVES: TypeAlias = Union[str, float, int, bool]
NON_NONE_JSON_DICT: TypeAlias = Dict[
    str,
    Union[
        _NON_NONE_JSON_PRIMITIVES,
        "NON_NONE_JSON_DICT",
        List[_NON_NONE_JSON_PRIMITIVES],
        List["NON_NONE_JSON_DICT"],
    ],
]
"""Dictionary of non-None json serializable types."""


def to_ini_str(
    d: dict[str, NON_NONE_JSON_DICT],
    *,
    space_around_delimiters: bool = True,
    preserve_key_case: bool = False,
) -> str:
    """
    Serialize a dictionary as an ini formatted string.
    Note: this function does not support serializing `None` values.
    `None` values must either be discarded or transformed into an appropriate type before using this
    function.

    Parameters
    ----------
    d : Dict[str, NON_NONE_JSON_DICT]
        dictionary of sections and their contents to serialize
    space_around_delimiters : bool, optional
        include spaces around `=` signs, by default True
    preserve_key_case : bool, optional
        preserve case of keys, by default False
    """
    cp = configparser.ConfigParser(interpolation=None)
    if preserve_key_case:
        cp.optionxform = str
    cp.read_dict(d)
    with StringIO() as s:
        cp.write(s, space_around_delimiters=space_around_delimiters)
        # drop eol chars configparser adds to end of file
        return s.getvalue().rstrip()


def to_ini_no_section_header_str(
    d: NON_NONE_JSON_DICT,
    space_around_delimiters: bool = True,
    preserve_key_case: bool = False,
) -> str:
    """
    Serialize a dictionary as an ini-_like_ formatted string.
    Does not include a section header in the output string.
    Note: this function does not support serializing `None` values.
    `None` values must either be discarded or transformed into an appropriate type before using this
    function.

    Parameters
    ----------
    d : Dict[str, NON_NONE_JSON_DICT]
        dictionary to serialize
    space_around_delimiters : bool, optional
        include spaces around `=` signs, by default True
    preserve_key_case : bool, optional
        preserve case of keys, by default False
    """
    cp = configparser.ConfigParser(interpolation=None)
    if preserve_key_case:
        cp.optionxform = str
    data = {NO_SECTIONS: d}
    cp.read_dict(data)
    with StringIO() as s:
        cp.write(s, space_around_delimiters=space_around_delimiters)
        buff = s.getvalue()
        # drop the [NO_SECTION] header and drop eol chars configparser adds to
        # end of file
        return buff[buff.find("\n") + 1 :].rstrip()


def to_yaml_str(d: dict[str, Any]) -> str:
    """Serialize a dictionary as a yaml formatted string."""
    yaml = try_import("yaml", extras_require_name="yaml")

    # see: https://github.com/yaml/pyyaml/issues/234
    # solution from https://github.com/yaml/pyyaml/issues/234#issuecomment-765894586
    # hopefully this is resolved in the future, it would be nice to try and use yaml.CDumper instead
    # of yaml.Dumper
    class Dumper(yaml.Dumper):
        def increase_indent(self, flow=False, *args, **kwargs):
            # this resolves how lists are indented. without this, they are indented inline with keys
            return super().increase_indent(flow=flow, indentless=False)

    # drop eol chars
    return yaml.dump(d, Dumper=Dumper).rstrip()


def to_toml_str(d: dict[str, Any]) -> str:
    """Serialize a dictionary as a toml formatted string."""
    tomli_w = try_import("tomli_w", extras_require_name="toml")
    # drop eol chars
    return tomli_w.dumps(d).rstrip()
