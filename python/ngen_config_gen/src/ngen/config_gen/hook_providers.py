# TODO: check when runtime_checkable was introduced
from typing import Any, Dict, Protocol, Union, runtime_checkable
from typing_extensions import Self

import geopandas as gpd
import pandas as pd

from .hooks import HydrofabricHook, HydrofabricLinkedDataHook


@runtime_checkable
class HookProvider(Protocol):
    def provide_hydrofabric_data(self, hook: HydrofabricHook):
        ...

    def provide_hydrofabric_linked_data(self, hook: HydrofabricLinkedDataHook):
        ...


class DefaultHookProvider(HookProvider):
    def __init__(self, hf: gpd.GeoDataFrame, hf_lnk_data: pd.DataFrame):
        self.__hf = hf.sort_values("divide_id")
        self.__hf_lnk = hf_lnk_data.sort_values("divide_id")

        # TODO: should this be a warning?
        assert len(self.__hf) == len(
            self.__hf_lnk
        ), "hydrofabric and hydrofabric link data have differing number of records"

        self.hf_iter = self.__hf.iterrows()
        self.hf_lnk_iter = self.__hf_lnk.iterrows()

        self.hf_row: Union[Dict[str, Any], None] = None
        self.hf_lnk_row: Union[Dict[str, Any], None] = None

    def provide_hydrofabric_data(self, hook: HydrofabricHook):
        if self.hf_row is None:
            raise RuntimeError("hook provider has no data")
        # TODO: figure out how to get this
        version = "2.0"
        divide_id = self.hf_row["divide_id"]

        hook.hydrofabric_hook(version, divide_id, self.hf_row)

    def provide_hydrofabric_linked_data(self, hook: HydrofabricLinkedDataHook):
        if self.hf_lnk_row is None:
            raise RuntimeError("hook provider has no data")
        # TODO: figure out how to get this
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
