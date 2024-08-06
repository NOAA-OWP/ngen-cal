from __future__ import annotations

from contextlib import contextmanager
from os import getcwd, chdir
from typing import Callable, TYPE_CHECKING
from types import ModuleType
from pydantic import errors as pydantic_errors
from pydantic.validators import str_validator
if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any
    from pydantic.typing import CallableGenerator

@contextmanager
def pushd(path: Path) -> None:
    """Change working directory to `path` for duration of the context

    Args:
        path (Path): path to cd to
    """
    #save current working dir
    cwd = getcwd()
    #change to new path
    chdir(path)
    try:
        yield #yield context
    finally:
        #when finished, return to original working dir
        chdir(cwd)

def import_from_string(path: str) -> Any:
    """Import an object or module from a string."""
    from importlib import import_module

    path = path.strip(" ")

    try:
        return import_module(path)
    except ImportError:
        ...

    try:
        module_path, class_name = path.rsplit(".", 1)
    except ValueError as e:
        raise ImportError(f'"{path}" doesn\'t look like a module path') from e

    module = import_module(module_path)
    if not class_name:
        return module
    try:
        return getattr(module, class_name)
    except AttributeError as e:
        raise ImportError(
            f'Module "{module_path}" does not define a "{class_name}" attribute'
        ) from e


class PyObjectOrModule:
    """
    Pydantic field type representing an object (e.g. class or function) or module.
    If given a string, this type will import the object or module using importlib.
    """
    validate_always = True

    @classmethod
    def __get_validators__(cls) -> CallableGenerator:
        yield cls.validate

    @classmethod
    def validate(cls, value: Any) -> Any:
        if isinstance(value, (Callable, ModuleType)):
            return value

        try:
            value = str_validator(value)
        except pydantic_errors.StrError:
            raise pydantic_errors.PyObjectError(
                error_message="value is neither a valid import path nor a valid callable"
            )

        try:
            return import_from_string(value)
        except ImportError as e:
            raise pydantic_errors.PyObjectError(error_message=str(e))

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema['type'] = 'string'

def type_as_import_string(t: type) -> str:
    import inspect
    mod = inspect.getmodule(t)
    return f"{mod.__name__}.{t.__qualname__}"
