from __future__ import annotations

from pydantic import BaseModel
from pathlib import Path
from typing import List


class MissingPath:
    def __init__(self, models: List[BaseModel], name: str, value: Path):
        """Chain of pydantic model instances the last of which `name` and `value` properties belong"""
        self.models = models
        """Pydantic model instance on which `name` and `value` properties belong"""
        self.model = models[-1]
        """Field name of `value` on `model` property"""
        self.name = name
        """Value of `name` on `model` property`"""
        self.value = value

    def __repr__(self) -> str:
        mod_names = ".".join([mod.__class__.__name__ for mod in self.models])
        return f'{mod_names}.{self.name}="{self.value!s}"'

    def __str__(self) -> str:
        mod_names = ".".join([mod.__class__.__name__ for mod in self.models])
        return (
            f'{mod_names}.{self.name}="{self.value!s}"\n'
            f'\tfile or directory at path "{self.value!s}" does not exist'
        )


def validate_paths(m: BaseModel) -> List[MissingPath]:
    """
    Recursively walk a pydantic model's fields and return a list of MissingPath
    instances for each encountered `pathlib.Path` instance that does not exist.
    The empty list means any `pathlib.Path` instances that were encountered
    exist.
    """
    paths_that_dont_exist: List[MissingPath] = []

    def rec(mod: BaseModel, visited: List[BaseModel]):
        for f_name in mod.__fields__.keys():
            f_value = getattr(mod, f_name)
            if isinstance(f_value, Path):
                if not f_value.exists():
                    paths_that_dont_exist.append(
                        MissingPath(models=[*visited, mod], name=f_name, value=f_value)
                    )
            elif isinstance(f_value, BaseModel):
                rec(f_value, [*visited, mod])

    rec(m, [])
    return paths_that_dont_exist
