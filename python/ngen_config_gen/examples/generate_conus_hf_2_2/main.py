import geopandas as gpd
import pandas as pd

from ngen.config_gen.file_writer import DefaultFileWriter
from ngen.config_gen.hook_providers import DefaultHookProvider
from ngen.config_gen.generate import generate_configs
from ngen.config_gen.mappings import LinkedData_2_2

from ngen.config_gen.models.cfe import Cfe
from ngen.config_gen.models.pet import Pet

if __name__ == "__main__":
    # NOTICE: https://lynker-spatial.s3-us-west-2.amazonaws.com/copyright.html
    # LICENSE: https://opendatacommons.org/licenses/odbl/1-0/
    # or pass local file paths instead
    hf_file = "https://lynker-spatial.s3-us-west-2.amazonaws.com/hydrofabric/v2.2/conus/conus_nextgen.gpkg"

    hf: gpd.GeoDataFrame = gpd.read_file(hf_file, layer="divides")
    hf_lnk_data: pd.DataFrame = pd.read_parquet(hf_file, layer="divide-attributes")
    # NOTE: remap HF 2.2 'divide-attributes' names to HF 2.0 names so they are
    # compatible with existing hooks
    hf_lnk_data = hf_lnk_data.rename(columns=LinkedData_2_2.conus, errors="ignore")
    # Non-conus mappings available also:
    #   LinkedData_2_2.hi
    #   LinkedData_2_2.pr
    #   LinkedData_2_2.vi
    #   LinkedData_2_2.ak

    hook_provider = DefaultHookProvider(hf=hf, hf_lnk_data=hf_lnk_data)
    # files will be written to ./config
    file_writer = DefaultFileWriter("./config/")

    generate_configs(
        hook_providers=hook_provider,
        hook_objects=[Cfe, Pet],
        file_writer=file_writer,
    )
