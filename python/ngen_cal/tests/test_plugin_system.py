from __future__ import annotations

from types import ModuleType
from typing import TYPE_CHECKING

from ngen.cal import hookimpl
from ngen.cal._plugin_system import setup_plugin_manager

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path
    from typing import Callable

    import pandas as pd
    from hypy.nexus import Nexus

    from ngen.cal.configuration import General


def test_setup_plugin_manager():
    import sys

    # this will be used to load function hookimpl's
    mod = sys.modules[__name__]
    plugins = [mod, ClassBasedPlugin]

    pm = setup_plugin_manager(plugins)

    from ngen.cal import PROJECT_SLUG

    assert pm.project_name == PROJECT_SLUG

    assert len(pm.get_plugins()) == len(plugins)

    def contains(plug: Callable | ModuleType) -> bool:
        if isinstance(plug, ModuleType):
            return plug in plugins
        return plug.__class__ in plugins

    plugs = list(filter(contains, pm.get_plugins()))
    assert len(plugs) == len(plugins), f"expected len(plugs)={len(plugins)}, plugs={plugs}"


@hookimpl
def ngen_cal_configure(config: General) -> None: ...


@hookimpl
def ngen_cal_start() -> None:
    """Called when first entering the calibration loop."""


@hookimpl
def ngen_cal_finish() -> None:
    """Called after exiting the calibration loop."""

@hookimpl
def ngen_cal_model_output() -> None:
    """Test model output plugin"""

@hookimpl
def ngen_cal_model_post_iteration(path: Path, iteration: int) -> None:
    """Test model post iteration"""

class ClassBasedPlugin:
    @hookimpl
    def ngen_cal_configure(self, config: General) -> None: ...

    @hookimpl
    def ngen_cal_start(self) -> None:
        """Called when first entering the calibration loop."""

    @hookimpl
    def ngen_cal_finish(self) -> None:
        """Called after exiting the calibration loop."""

    @hookimpl
    def ngen_cal_model_output(self) -> None:
        """Test model output plugin"""

    @hookimpl
    def ngen_cal_model_post_iteration(self, path: Path, iteration: int) -> None:
        """Test model post iteration"""

    @hookimpl
    def ngen_cal_model_observations(
        self,
        nexus: Nexus,
        start_time: datetime,
        end_time: datetime,
        simulation_interval: pd.Timedelta,
    ) -> pd.Series:
        """Test observation plugin"""
