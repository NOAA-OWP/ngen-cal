import configparser
from io import StringIO
from collections import OrderedDict

from pydantic import BaseModel

from .utils import try_import
from ._constants import NO_SECTIONS


def to_namelist_str(m: BaseModel) -> str:
    f90nml = try_import("f90nml", extras_require_name="namelist")

    # NOTE: Cast to OrderedDict to guarantee group-name ordering
    # dicts are ordered in python >= 3.7, however f90nml does an isinstance OrderedDict check
    namelist = f90nml.Namelist(OrderedDict(m.dict(by_alias=True)))
    return str(namelist)


def to_ini_str(m: BaseModel, space_around_delimiters: bool = True) -> str:
    cp = configparser.ConfigParser(interpolation=None)
    # cp.optionxform = str
    cp.read_dict(m.dict(by_alias=True))
    with StringIO() as s:
        cp.write(s, space_around_delimiters=space_around_delimiters)
        # truncate extra newline character configparser adds to end of file
        return s.getvalue()[:-1]


def to_ini_no_section_header_str(
    m: BaseModel, space_around_delimiters: bool = True
) -> str:
    cp = configparser.ConfigParser(interpolation=None)
    data = {NO_SECTIONS: m.dict(by_alias=True)}
    cp.read_dict(data)
    with StringIO() as s:
        cp.write(s, space_around_delimiters=space_around_delimiters)
        buff = s.getvalue()
        # drop the [NO_SECTION] header and truncate extra newline character configparser adds to end
        # of file
        return buff[buff.find("\n") + 1 : -1]


def to_yaml_str(m: BaseModel) -> str:
    yaml = try_import("yaml", extras_require_name="yaml")

    # see: https://github.com/yaml/pyyaml/issues/234
    # solution from https://github.com/yaml/pyyaml/issues/234#issuecomment-765894586
    # hopefully this is resolved in the future, it would be nice to try and use yaml.CDumper instead
    # of yaml.Dumper
    class Dumper(yaml.Dumper):
        def increase_indent(self, flow=False, *args, **kwargs):
            # this resolves how lists are indented. without this, they are indented inline with keys
            return super().increase_indent(flow=flow, indentless=False)

    data = m.dict(by_alias=True)
    return yaml.dump(
        data,
        Dumper=Dumper,
    )


def to_toml_str(m: BaseModel) -> str:
    tomli_w = try_import("tomli_w", extras_require_name="toml")
    data = m.dict(by_alias=True)
    return tomli_w.dumps(data)
