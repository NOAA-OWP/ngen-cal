import sys
from typing import List

from ngen.config.formulation import Formulation


def get_module_names(formulation: Formulation) -> List[str]:
    """
    Get name of all modules in a formulation (e.g. "NoahOWP").
    """
    modules = set()
    if isinstance(formulation.params, MultiBMI):
        for mod in formulation.params.modules:
            if isinstance(mod.params, MultiBMI):
                modules.update(set(get_module_names(mod)))
            else:
                modules.add(mod.params.model_name)
    else:
        return [formulation.params.model_name]
    return list(modules)


if __name__ == "__main__":
    import geopandas as gpd
    import pandas as pd

    from functools import partial
    from pathlib import Path

    from ngen.config.realization import NgenRealization
    from ngen.config.multi import MultiBMI

    from ngen.config_gen.hook_providers import DefaultHookProvider
    from ngen.config_gen.file_writer import DefaultFileWriter
    from ngen.config_gen.generate import generate_configs

    parent_dir = Path(__file__).parent
    config = NgenRealization.parse_file(
        parent_dir / "example_bmi_multi_realization_config.json"
    )

    start_time = config.time.start_time
    end_time = config.time.end_time

    assert len(config.global_config.formulations) == 1, "ensembles are not supported"
    formulation = config.global_config.formulations[0]
    modules = get_module_names(formulation)

    noaa_owp_dir = Path(__file__).parent.parent / "noaa_owp"
    sys.path.append(str(noaa_owp_dir))

    from noaa_owp import NoahOWP
    from ngen.config_gen.models.cfe import Cfe
    from ngen.config_gen.models.pet import Pet

    param_table_dir = Path(parent_dir / "parameters/")

    noah_owp = partial(
        NoahOWP,
        parameter_dir=param_table_dir,
        start_time=start_time,
        end_time=end_time,
    )

    mod_map = {
        # "SLOTH": None,
        "NoahOWP": noah_owp,
        "CFE": Cfe,
        "PET": Pet,
    }

    hf_file = "/Users/austinraney/Downloads/nextgen_09.gpkg"  # or "https://lynker-spatial.s3.amazonaws.com/v20/gpkg/nextgen_09.gpkg"
    hf_lnk_file = "/Users/austinraney/Downloads/nextgen_09.parquet"  # or "https://lynker-spatial.s3.amazonaws.com/v20/model_attributes/nextgen_09.parquet"

    hf: gpd.GeoDataFrame = gpd.read_file(hf_file, layer="divides")
    hf_lnk_data: pd.DataFrame = pd.read_parquet(hf_lnk_file)

    subset = [
        "cat-1529608",
        "cat-1537245",
        "cat-1529607",
        "cat-1536906",
        "cat-1527290",
    ]

    hf = hf[hf["divide_id"].isin(subset)]
    hf_lnk_data = hf_lnk_data[hf_lnk_data["divide_id"].isin(subset)]

    hook_provider = DefaultHookProvider(hf=hf, hf_lnk_data=hf_lnk_data)
    file_writer = DefaultFileWriter(parent_dir / "./config/")

    hook_objects = [mod_map.get(mod) for mod in modules if mod_map.get(mod) is not None]

    generate_configs(
        hook_providers=hook_provider,
        hook_objects=hook_objects,
        file_writer=file_writer,
    )
