# Entry point to validating NGen realization files

from pathlib import Path
import sys, os, json
from ngen.config.configurations import Forcing, Time, Routing
from ngen.config.realization import NgenRealization, Realization, CatchmentRealization
from ngen.config.catchment import NGenCatchment
from ngen.config.formulation import Formulation
from ngen.config.cfe import CFE
from ngen.config.sloth import SLOTH
from ngen.config.noahowp import NoahOWP
from ngen.config.multi import MultiBMI

from ngen.cal.calibration_cathment import CalibrationCatchment, AdjustableCatchment

def validate_catchment(catch,catch_subset):

    # Validate the catchment config
    with open(catch) as fp:
        data = json.load(fp)
    ngen_realization = NGenCatchment(**data)

    # Validate catchment subset config

    pass

def validate_nexus(conf):

    raise NotImplemented

    # Validate the nexus config
    # with open(conf) as fp:
    #     data = json.load(fp)
    # ngen_realization = NgenRealization(**data)

    # Validate the nexus subset config

    pass

def validate_realization(conf):

    #Read the calibration specific info
    with open(conf) as fp:
        data = json.load(fp)
    ngen_realization = NgenRealization(**data)

    pass

if __name__ == "__main__":
    # 0 ngen 
    # 1 ./data/catchment_data.geojson 
    # 2 "all" 
    # 3 ./data/nexus_data.geojson 
    # 4 "all" 
    # 5 ./data/refactored_example_realization_config.json

    # Get realization file
    # python conf_validation.py realization.json
    catchment_file = sys.argv[1]
    catchment_subset_file = sys.argv[2]
    validate_catchment(catchment_file,catchment_subset_file)

    nexus_file = sys.argv[3]
    nexus_subset_file = sys.argv[4]
    validate_nexus(nexus_file,nexus_subset_file)

    rel_file = sys.argv[5]
    validate_realization(rel_file)

