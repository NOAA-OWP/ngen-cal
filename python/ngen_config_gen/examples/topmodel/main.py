from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, TypedDict
import typing_extensions

from ngen.config.init_config.topmodel import Topmodel, TopModelParams, TopModelSubcat
from ngen.config.path_pair import PathPair

if TYPE_CHECKING:
    from typing import Any

    from pydantic import BaseModel

    from ngen.config_gen.hook_providers import HookProvider


class _TwiDist4(TypedDict):
    frequency: float
    v: float


class TopmodelHooks:
    def __init__(self):
        self.data = {}
        self.subcats = {}
        self.params = {}
        self.divide_id: str = ""

    def _defaults(self) -> None:
        self.subcats["num_sub_catchments"] = 1
        self.subcats["imap"] = 1
        self.subcats["yes_print_output"] = 1
        self.subcats["subcat"] = "Extracted study basin: {cat_name}"
        # `twi_dist_4`
        self.subcats["num_topodex_values"] = 4
        self.subcats["area"] = 1
        # b.c. NextGen / HF?
        self.subcats["num_channels"] = 1

        # params
        # from: https://github.com/ajkhattak/basin_workflow/blob/ac8de7a7fcbb3d002d8967e81d3e89c23bf0e99a/basin_workflow/generate_files/configuration.py#L409C19-L409C95
        self.params["subcat"] = "Extracted study basin: {cat_name}"
        self.params["szm"] = 0.032
        self.params["t0"] = 5.0
        self.params["td"] = 50.0
        self.params["chv"] = 3600.0
        self.params["rv"] = 3600.0
        self.params["srmax"] = 0.05
        self.params["q0"] = 0.0000328
        self.params["sr0"] = 0.002
        self.params["infex"] = 0
        self.params["xk0"] = 1.0
        self.params["hf"] = 0.02
        self.params["dth"] = 0.1

        # main config
        self.data["stand_alone"] = 0

    def hydrofabric_linked_data_hook(
        self, _: str, divide_id: str, data: dict[str, Any]
    ) -> None:
        self.divide_id = divide_id

        twi_dist_4: str | list[_TwiDist4] = data["twi_dist_4"]
        if isinstance(twi_dist_4, str):
            twi_dist_4: list[_TwiDist4] = json.loads(twi_dist_4)

        # NOTE: not sure about these; need to ask Ahmad
        self.subcats["dist_area_lnaotb"] = [f["frequency"] for f in twi_dist_4]
        self.subcats["lnaotb"] = [f["v"] for f in twi_dist_4]

        # TODO:
        # self.subcats["cum_dist_area_with_dist"] =
        # self.subcats["dist_from_outlet"] =

        # params
        self.params["subcat"] = f"Extracted study basin: {divide_id}"
        # from: https://github.com/ajkhattak/basin_workflow/blob/ac8de7a7fcbb3d002d8967e81d3e89c23bf0e99a/basin_workflow/generate_files/configuration.py#L409C19-L409C95
        self.data["title"] = f"Extracted study basin: {divide_id}"

    def build(self) -> BaseModel:
        assert (
            self.divide_id != ""
        ), f"`divide_id` must not have been provided correctly in `hydrofabric_linked_data_hook`"
        subcat_path = Path(f"subcat_{self.divide_id}.dat")
        params_path = Path(f"params_{self.divide_id}.dat")
        subcat = TopModelSubcat.parse_obj(self.subcats)
        params = TopModelParams.parse_obj(self.params)
        self.data["subcat"] = PathPair[TopModelSubcat].with_object(
            subcat, path=subcat_path
        )
        self.data["params"] = PathPair[TopModelParams].with_object(
            params, path=params_path
        )
        return TopmodelWriteInnerConfigs.parse_obj(self.data)

    def visit(self, hook_provider: HookProvider) -> None: hook_provider.provide_hydrofabric_linked_data(self)
        # apply defaults
        self._defaults()


class TopmodelWriteInnerConfigs(Topmodel):
    @typing_extensions.override
    def to_file(self, p: Path, *_) -> None:
        # this is something like: f"subcat_{self.divide_id}.dat"
        self.subcat = self.subcat.with_path(p.parent / Path(self.subcat))
        self.params = self.params.with_path(p.parent / Path(self.params))
        assert self.subcat.write(), f"failed to write subcat: {Path(self.subcat)}"
        assert self.params.write(), f"failed to write params: {Path(self.params)}"
        super().to_file(p)


if __name__ == "__main__":
    import geopandas as gpd
    import pandas as pd

    from ngen.config_gen.file_writer import DefaultFileWriter
    from ngen.config_gen.generate import generate_configs
    from ngen.config_gen.hook_providers import DefaultHookProvider

    hf_file = "somepath_or_url"
    hf_lnk_file = "somepath_or_url"

    hf: gpd.GeoDataFrame = gpd.read_file(hf_file, layer="divides")
    hf_lnk_data: pd.DataFrame = pd.read_parquet(hf_lnk_file)

    hook_provider = DefaultHookProvider(hf=hf, hf_lnk_data=hf_lnk_data)
    file_writer = DefaultFileWriter("./config/")

    generate_configs(
        hook_providers=hook_provider,
        hook_objects=[TopmodelHooks],
        file_writer=file_writer,
    )
