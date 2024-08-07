from __future__ import annotations

from types import ModuleType
from typing import TYPE_CHECKING, Callable

from typing_extensions import assert_never

if TYPE_CHECKING:
    from pluggy import PluginManager

import pluggy

# see `_hookspec` module for available hooks
from ngen.cal import PROJECT_SLUG, _hookspec


def setup_plugin_manager(plugins: list[Callable | ModuleType]) -> PluginManager:
    pm = pluggy.PluginManager(PROJECT_SLUG)
    pm.add_hookspecs(_hookspec)

    for plugin in plugins:
        if isinstance(plugin, Callable):
            pm.register(plugin())
        elif isinstance(plugin, ModuleType):
            pm.register(plugin)
        else:
            assert_never(plugin)

    return pm

def setup_scoped_plugin_manager(spec: type, plugins: list[Callable]) -> PluginManager:
    pm = pluggy.PluginManager(PROJECT_SLUG)
    pm.add_hookspecs(spec)

    for plugin in plugins:
        assert not isinstance(plugin, ModuleType), "function plugins"
        if isinstance(plugin, Callable):
            pm.register(plugin())
        else:
            assert_never(plugin)

    return pm
