import pytest
from pathlib import Path
from ngen.config.conf_validation import *

@pytest.fixture()
def data():
    test_dir = Path(__file__).parent
    test_file = test_dir/'data/test_config.json'
    with open(test_file) as fp:
        data = json.load(fp)
    data['routing']['t_route_config_file_with_path'] = test_dir/data['routing']['t_route_config_file_with_path']
    return data

def test_catchment_nexus():
    test_dir = Path(__file__).parent
    test_file = test_dir/'data/hydrofabric/test_catchment_config.geojson'
    subset = "cat-67,cat-27"
    catch_pair, catch_sub = validate_catchment(test_file,subset)

    test_file = test_dir/'data/hydrofabric/test_nexus_config.geojson'
    subset = "nex-26,nex-68"
    nexus_pair, nexus_sub = validate_nexus(test_file,subset)

    validate_catchmentnexus(catch_pair,nexus_pair,catch_sub,nexus_sub)

def test_ngen_realization_config(data):
    g = NgenRealization(**data)



