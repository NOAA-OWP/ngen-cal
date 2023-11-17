import geopandas as gpd
import pandas as pd


from .hook_providers import DefaultHookProvider
from .file_writer import DefaultFileWriter
from .generate import generate_configs

from .models.pet import Pet

if __name__ == "__main__":
    hf_file = "/Users/austinraney/Downloads/nextgen_09.gpkg"
    hf_lnk_file = "/Users/austinraney/Downloads/nextgen_09.parquet"

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
    file_writer = DefaultFileWriter("./config/")

    generate_configs(
        hook_providers=hook_provider,
        hook_objects=[Pet],
        file_writer=file_writer,
    )
