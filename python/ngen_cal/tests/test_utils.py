from types import ModuleType, FunctionType

from ngen.cal.utils import PyObjectOrModule, type_as_import_string
from pydantic import BaseModel


class Foo(BaseModel):
    mod: PyObjectOrModule

    class Config(BaseModel.Config):
        # properly serialize plugins
        json_encoders = {
            FunctionType: type_as_import_string,
            type: type_as_import_string,
            ModuleType: lambda mod: mod.__name__,
        }


def test_create_from_py_objs_and_mods():
    import sys

    mod = sys.modules[__name__]
    assert Foo(mod=mod).mod == mod

    def some_fn(): ...

    assert Foo(mod=some_fn).mod == some_fn


def test_create_from_str():
    import sys

    mod = sys.modules[__name__]
    assert Foo(mod=__name__).mod == mod

    import pathlib

    assert Foo(mod="pathlib.Path").mod == pathlib.Path


def test_serialize():
    import sys

    mod = sys.modules[__name__]
    assert Foo(mod=mod).json() == f'{{"mod": "{__name__}"}}'

    assert Foo(mod=str).json() == '{"mod": "builtins.str"}'


def test_schema():
    assert Foo.schema()["properties"]["mod"]["type"] == "string"
