"""
This is main script to execute validation control run using the default model 
parameter set and validation best run using the best calibrated parameter set.

@author: Xia Feng
"""

import argparse
from os import chdir
from pathlib import Path

import yaml

from ngen.cal.agent import Agent
from ngen.cal.configuration import General
from ngen.cal.validation_run import run_valid_ctrl_best 

def main(general: General, model_conf):

    # Seed the random number generators if requested
    if( general.random_seed is not None):
        import random
        random.seed(general.random_seed)
        import numpy as np
        np.random.seed(general.random_seed)

    print("Starting Validation Run")

    # Initialize agent
    agent = Agent(model_conf, general.valid_path, general, general.log, general.restart)
    
    # Execcute validation control and best simulation
    run_valid_ctrl_best(agent)


if __name__ == "__main__":

    # Create command line parser 
    parser = argparse.ArgumentParser(description='Run Validation in NGEN architecture.')
    parser.add_argument('config_file', type=Path,
                        help='The configuration yaml file for catchments to be operated on')

    args = parser.parse_args()
    
    with open(args.config_file) as file:
        conf = yaml.safe_load(file)
    
    general = General(**conf['general'])

    # Change directory to workdir
    chdir(general.workdir)

    main(general, conf['model'])
