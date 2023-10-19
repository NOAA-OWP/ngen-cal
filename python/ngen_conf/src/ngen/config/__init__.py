from ._version import __version__

# Monkey patch some types required to support python 3.7
try:
    from typing import Literal
except ImportError:
    import typing
    from typing_extensions import Literal
    typing.Literal = Literal

# Monkey patch pydantic to allow schema serialization of PyObject types to string
from pydantic import PyObject
def pyobject_schema(cls, field_schema):
            field_schema['type'] = 'string'

PyObject.__modify_schema__ = classmethod(pyobject_schema)
