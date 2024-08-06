from __future__ import annotations

from typing import Any, Collection, Dict, Iterable, Protocol, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .hook_providers import HookProvider

from .hooks import BuilderVisitable
from .file_writer import FileWriter


class DivideIdHookObject:
    def __init__(self):
        self.__divide_id: str | None = None

    def hydrofabric_hook(
        self, version: str, divide_id: str, data: dict[str, Any]
    ) -> None:
        self.__divide_id = divide_id

    def visit(self, hook_provider: HookProvider) -> None:
        hook_provider.provide_hydrofabric_data(self)

    def divide_id(self) -> str | None:
        return self.__divide_id


class BuilderVisitableFn(Protocol):
    """Some function that returns a BuilderVisitable object."""

    def __call__(self) -> BuilderVisitable:
        ...


def generate_configs(
    hook_providers: Iterable[HookProvider],
    hook_objects: Collection[BuilderVisitableFn],
    file_writer: FileWriter,
):
    div_hook_obj = DivideIdHookObject()
    for hook_prov in hook_providers:
        # retrieve current divide id
        div_hook_obj.visit(hook_prov)
        divide_id = div_hook_obj.divide_id()
        assert divide_id is not None

        for v_fn in hook_objects:
            bld_vbl = v_fn()
            bld_vbl.visit(hook_prov)
            model = bld_vbl.build()
            file_writer(divide_id, model)
