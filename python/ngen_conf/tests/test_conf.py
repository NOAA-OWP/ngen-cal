from pathlib import Path
from ngen.config.conf_validation import *

def test_catchment_nexus():
    test_dir = Path(__file__).parent
    test_file = test_dir/'data/test_catchment_config.geojson'
    subset = "cat-67,cat-27"
    catch_pair, catch_sub = validate_catchment(test_file,subset)

    test_file = test_dir/'data/test_nexus_config.geojson'
    subset = "nex-26,nex-68"
    nexus_pair, nexus_sub = validate_nexus(test_file,subset)

    validate_catchmentnexus(catch_pair,nexus_pair,catch_sub,nexus_sub)

def test_ngen_realization_config():
    test_dir = Path(__file__).parent
    test_file = test_dir/'data/test_realization_config.json'
    validate_realization(test_file)



