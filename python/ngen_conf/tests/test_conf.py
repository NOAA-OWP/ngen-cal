import pytest
from pathlib import Path
from ngen.config.realization import NgenRealization
from ngen.config.hydrofabric import CatchmentGeoJSON, NexusGeoJSON
from ngen.config.utils import pushd

@pytest.fixture()
def testdir():
    testdir = Path(__file__).parent
    return testdir

def test_catchment(testdir: Path):
    test_file = testdir/'data/hydrofabric/test_catchment_config.geojson'
    CatchmentGeoJSON.parse_file(test_file)

def test_nexus(testdir: Path):
    test_file = testdir/'data/hydrofabric/test_nexus_config.geojson'
    NexusGeoJSON.parse_file(test_file)

def test_ngen_realization_config(testdir: Path):
    test_file = testdir/'data/test_config.json'
    with pushd(test_file.parent):
        NgenRealization.parse_file(test_file)
