from __future__ import annotations

from typing import Any, Protocol, runtime_checkable
from typing_extensions import Self

import geopandas as gpd
import pandas as pd

from .hooks import HydrofabricHook, HydrofabricLinkedDataHook


@runtime_checkable
class HookProvider(Protocol):
    """
    A `HookProvider` is a visitor that provides hook data.
    When a hook is passed to a `HookProvider` method, it _should_ call the associated hook function
    providing it with the requisite data.
    For example, an implementation of the `provide_hydrofabric_data` method _should_ call the
    `hydrofabric_hook` method on the passed in `hook` object.

    See `DefaultHookProvider` for a default implementation.
    """

    def provide_hydrofabric_data(self, hook: HydrofabricHook):
        ...

    def provide_hydrofabric_linked_data(self, hook: HydrofabricLinkedDataHook):
        ...


class DefaultHookProvider(HookProvider):
    """
    `DefaultHookProvider` is an iterable object that provides hook objects with data.
    Each iteration of the instance provides hook data for a given `divide_id`.

    Both `hf` and `hf_lnk_data` inputs must contain the same number of features
    (both are the same length) and contain the same `divide_id` fields.

    Parameters
    ----------
    hf: a Hydrofabric `divides` layers GeoDataFrame
    hf_lnk_data: Hydrofabric linked data DataFrame
    """

    def __init__(self, hf: gpd.GeoDataFrame, hf_lnk_data: pd.DataFrame):
        self.__hf = hf.sort_values("divide_id")
        self.__hf_lnk = hf_lnk_data.sort_values("divide_id")

        # TODO: should this be a warning?
        assert len(self.__hf) == len(
            self.__hf_lnk
        ), "hydrofabric and hydrofabric link data have differing number of records"

        self.hf_iter = self.__hf.iterrows()
        self.hf_lnk_iter = self.__hf_lnk.iterrows()

        self.hf_row: dict[str, Any] | None = None
        self.hf_lnk_row: dict[str, Any] | None = None

    def provide_hydrofabric_data(self, hook: HydrofabricHook):
        if self.hf_row is None:
            raise RuntimeError("hook provider has no data")
        # TODO: figure out how to get this (@aaraney)
        version = "2.0"
        divide_id = self.hf_row["divide_id"]

        hook.hydrofabric_hook(version, divide_id, self.hf_row)

    def provide_hydrofabric_linked_data(self, hook: HydrofabricLinkedDataHook):
        if self.hf_lnk_row is None:
            raise RuntimeError("hook provider has no data")
        # TODO: figure out how to get this (@aaraney)
        version = "2.0"
        divide_id = self.hf_lnk_row["divide_id"]

        hook.hydrofabric_linked_data_hook(version, divide_id, self.hf_lnk_row)

    def __iter__(self) -> Self:
        return self

    def __next__(self):
        # NOTE: StopIteration will be raised when next can no longer be called.
        # this should always be the _first_ iterator.
        # If length of iterator guarantee changes, this will also need to change.
        _, hf_row = next(self.hf_iter)
        self.hf_row = hf_row.to_dict()
        _, hf_lnk_row = next(self.hf_lnk_iter)
        self.hf_lnk_row = hf_lnk_row.to_dict()
        return self
