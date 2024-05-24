from __future__ import annotations

from typing import TYPE_CHECKING

import pluggy

from ngen.cal import PROJECT_SLUG

if TYPE_CHECKING:
    from ngen.cal.configuration import General

hookspec = pluggy.HookspecMarker(PROJECT_SLUG)


@hookspec
def ngen_cal_configure(config: General) -> None:
    """
    Called before calibration begins.
    This allow plugins to perform initial configuration.

    Plugins' configuration data should be provided using the
    `plugins_settings` field in the `ngen.cal` configuration file.
    By convention, the name of the plugin should be used as top level key in
    the `plugin_settings` dictionary.
    """
    # NOTE: not sure if we should just provide `General.plugin_settings`?
    #       likewise, not sure if we should also pass the `model_conf`?
    #       i am not inclined to just add things to add things.
    #       for now, lets stick with `General` config until we _need_ more.


@hookspec
def ngen_cal_start() -> None:
    """Called when first entering the calibration loop."""


@hookspec
def ngen_cal_finish(exception: Exception | None) -> None:
    """
    Called after exiting the calibration loop.
    Plugin implementations are guaranteed to be called even if an exception is
    raised during the calibration loop.
    `exception` will be non-none if an exception was raised during calibration.
    """
