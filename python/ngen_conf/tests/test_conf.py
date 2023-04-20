import pytest, json
from pathlib import Path
from ngen.config.realization import NgenRealization
from ngen.config.hydrofabric import CatchmentGeoJSON, NexusGeoJSON

@pytest.fixture()
def testdir():
    testdir = Path(__file__).parent
    return testdir

@pytest.fixture()
def catchmentdata(testdir):
    test_file = testdir/'data/hydrofabric/test_catchment_config.geojson'
    with open(test_file) as fp:
        catchmentdata = json.load(fp)
    return catchmentdata

@pytest.fixture()
def nexusdata(testdir):
    test_file = testdir/'data/hydrofabric/test_nexus_config.geojson'
    with open(test_file) as fp:
        nexusdata = json.load(fp)
    return nexusdata

@pytest.fixture()
def realizationdata(testdir):
    test_file = testdir/'data/test_config.json'
    with open(test_file) as fp:
        realizationdata = json.load(fp)
    realizationdata['routing']['t_route_config_file_with_path'] = testdir/realizationdata['routing']['t_route_config_file_with_path']
    return realizationdata

def test_catchment(catchmentdata):
    CatchmentGeoJSON(**catchmentdata)  

def test_nexus(nexusdata):
    NexusGeoJSON(**nexusdata)   

def test_ngen_realization_config(realizationdata):
    g = NgenRealization(**realizationdata)


  





