import json
import pytest
from pathlib import Path
from ngen.config.realization import Realization, NgenRealization

@pytest.fixture()
def data():
    test_dir = Path(__file__).parent
    test_file = test_dir/'test_config.json'
    with open(test_file) as fp:
        data = json.load(fp)
    data['routing']['t_route_config_file_with_path'] = test_dir/data['routing']['t_route_config_file_with_path']
    data['global']['forcing']['path'] = test_dir/data['global']['forcing']['path']
    return data

def test_ngen_global_realization(data):
    g = NgenRealization(**data)
    """ TODO write a test of serializing to json and then reading the result back and validating???
    with open("generated.json", 'w') as fp:
        fp.write( g.json(by_alias=True, exclude_none=True, indent=4))
    """