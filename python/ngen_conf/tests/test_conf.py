import pytest, json
from pathlib import Path
from ngen.config.realization import NgenRealization
from ngen.config.hydrofabric import NGenNexusFile, NGenCatchmentFile

@pytest.fixture()
def catchmentdata():
    test_dir = Path(__file__).parent
    test_file = test_dir/'data/hydrofabric/test_catchment_config.geojson'
    with open(test_file) as fp:
        catchmentdata = json.load(fp)
    return catchmentdata

def test_catchment(catchmentdata):
    NGenCatchmentFile(**catchmentdata)  

@pytest.fixture()
def nexusdata():
    test_dir = Path(__file__).parent
    test_file = test_dir/'data/hydrofabric/test_nexus_config.geojson'
    with open(test_file) as fp:
        nexusdata = json.load(fp)
    return nexusdata

def test_nexus(nexusdata):
    NGenNexusFile(**nexusdata)   

@pytest.fixture()
def realizationdata():
    test_dir = Path(__file__).parent
    test_file = test_dir/'data/test_config.json'
    with open(test_file) as fp:
        realizationdata = json.load(fp)
    realizationdata['routing']['t_route_config_file_with_path'] = test_dir/realizationdata['routing']['t_route_config_file_with_path']
    return realizationdata

def test_ngen_realization_config(realizationdata):
    g = NgenRealization(**realizationdata)


  





