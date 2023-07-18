from pathlib import Path
from ngen.config.realization import NgenRealization
from ngen.config.utils import pushd

def test_ngen_global_realization():
    """ TODO write a test of serializing to json and then reading the result back and validating???
    with open("generated.json", 'w') as fp:
        fp.write( g.json(by_alias=True, exclude_none=True, indent=4))
    """
    test_dir = Path(__file__).parent
    test_file = test_dir/'data/test_config.json'
    with pushd(test_file.parent):
        NgenRealization.parse_file(test_file)
