import geopandas as gpd
import pandas as pd

from ngen.config_gen.file_writer import DefaultFileWriter
from ngen.config_gen.hook_providers import DefaultHookProvider
from ngen.config_gen.generate import generate_configs

from ngen.config_gen.models.cfe import Cfe
from ngen.config_gen.models.pet import Pet

if __name__ == "__main__":
    # or pass local file paths instead
    hf_file = "https://lynker-spatial.s3.amazonaws.com/v20.1/gpkg/nextgen_09.gpkg"
    hf_lnk_file = "https://lynker-spatial.s3.amazonaws.com/v20.1/model_attributes/nextgen_09.parquet"

    hf: gpd.GeoDataFrame = gpd.read_file(hf_file, layer="divides")
    hf_lnk_data: pd.DataFrame = pd.read_parquet(hf_lnk_file)

    hook_provider = DefaultHookProvider(hf=hf, hf_lnk_data=hf_lnk_data)
    # files will be written to ./config
    file_writer = DefaultFileWriter("./config/")

    generate_configs(
        hook_providers=hook_provider,
        hook_objects=[Cfe, Pet],
        file_writer=file_writer,
    )
