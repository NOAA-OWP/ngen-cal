"""
This file reads input configuration file and creates the data and files files
for executing calibration and validation runs for difference NextGen formulations.

Example usage: python create_input.py input.config

@author: Xia Feng
"""

import argparse
import configparser
import copy
from datetime import timedelta
import os
import sys
import shutil
import time

import geopandas as gpd
import pandas as pd

from createInput import ginputfunc as gfun

def main():
    # Create command line parser to supply input config file 
    parser = argparse.ArgumentParser()
    parser.add_argument('input_config', nargs=1, type=str, help='input configuration file') 
    args = parser.parse_args()

    # Read input config file
    config  = configparser.ConfigParser()
    config.read(args.input_config)

    # General section
    section = 'General'
    basin = config.get(section, 'basin')
    model = config.get(section, 'model')
    run_type = config.get(section, 'run_type')
    main_dir = config.get(section, 'main_dir')

    # Calibration section
    section = 'Calibration'
    start_iteration = config.getint(section, 'start_iteration')
    number_iteration = config.getint(section, 'number_iteration')
    restart = config.getint(section, 'restart')
    objective = config.get(section, 'objective_function')
    algorithm = config.get(section, 'optimization_algorithm')
    swarm_size = config.getint(section, 'swarm_size')
    c1 = config.getfloat(section, 'c1')
    c2 = config.getfloat(section, 'c2')
    w = config.getfloat(section, 'w')
    save_plot_iter = config.getint(section, 'save_plot_iter')
    save_output_iter = config.getint(section, 'save_output_iter')
    save_plot_iter_freq  = config.getint(section, 'save_plot_iter_freq')
    calib_start_period = config.get(section, 'calib_start_period')
    calib_end_period = config.get(section, 'calib_end_period')
    calib_eval_start_period = config.get(section, 'calib_eval_start_period')
    calib_eval_end_period = config.get(section, 'calib_eval_end_period')
    valid_start_period = config.get(section, 'valid_start_period')
    valid_end_period = config.get(section, 'valid_end_period')
    valid_eval_start_period = config.get(section, 'valid_eval_start_period')
    valid_eval_end_period = config.get(section, 'valid_eval_end_period')
    full_eval_start_period = config.get(section, 'full_eval_start_period')
    full_eval_end_period = config.get(section, 'full_eval_end_period')
    threshold = config.get(section, 'streamflow_threshold')
    threshold = float(threshold) if threshold else None
    site_name = config.get(section, 'station_name')
    user_email = config.get(section, 'user_email')

    # DataFile section
    section = 'DataFile'
    forcing_dir = config.get(section, 'forcing_dir')
    obsflow_dir = config.get(section, 'obs_dir')
    hydrofab_dir = config.get(section, 'hydrofab_dir')
    cfe_dir = config.get(section, 'cfe_dir')
    topmd_dir = config.get(section, 'topmd_dir') 
    noah_params_dir = config.get(section, 'noah_parameter_dir')
    attr_file = config.get(section, 'attributes_file')
    calib_params_file = config.get(section, 'calib_parameter_file')
    lasam_soil_param = config.get(section, 'lasam_soil_parameter_file')
    lasam_soil_class = config.get(section, 'lasam_soil_class_file')
    ngen_exe_file = config.get(section, 'ngen_exe_file')
    cfe_lib = config.get(section, 'cfe_lib')
    sloth_lib = config.get(section, 'sloth_lib')
    topmd_lib = config.get(section, 'topmd_lib')
    noah_lib = config.get(section, 'noah_lib')
    sft_lib = config.get(section, 'sft_lib')
    smp_lib = config.get(section, 'smp_lib')
    lasam_lib = config.get(section, 'lasam_lib')

    # Time period 
    time_period={"run_time_period": {"calib": [calib_start_period, calib_end_period], 
                                     "valid": [valid_start_period, valid_end_period]}, 
                 "evaluation_time_period": {"calib": [calib_eval_start_period, calib_eval_end_period],
                                            "valid": [valid_eval_start_period, valid_eval_end_period],
                                            "full": [full_eval_start_period, full_eval_end_period ]}}

    # General settings 
    strategy = {'type': 'estimation', 'algorithm': algorithm} 
    if algorithm == 'pso': 
        strategy.update({'parameters': {'pool': swarm_size, 'particles': swarm_size, 'options': {'c1': c1, 'c2':c2, 'w':w}}})
    if algorithm == 'gwo':
        strategy.update({'parameters': {'pool': swarm_size, 'particles': swarm_size}})
    general_cfg = {'strategy': strategy, 'name': run_type, 'log': True, 'workdir': None, 'yaml_file': None,
                   'start_iteration': start_iteration, 'iterations': number_iteration, 'restart': restart}

    # Library files
    library_file = {
                    'cfe_noah': {'cfe': cfe_lib, 'noah': noah_lib, 'sloth': sloth_lib}, 
                    'topmodel_noah': {'tomodel': topmd_lib, 'noah': noah_lib, 'sloth': sloth_lib}, 
                    'cfe_noah_sft': {'cfe': cfe_lib, 'noah': noah_lib, 'sft': sft_lib, 'smp': smp_lib, 'sloth': sloth_lib},
                    'lasam_noah_sft': {'lasam': lasam_lib, 'noah': noah_lib, 'sft': sft_lib, 'smp': smp_lib, 'sloth': sloth_lib},
                    'cfe_xaj_noah': {'cfe': cfe_lib, 'noah': noah_lib, 'sloth': sloth_lib}, 
                    'cfe_xaj_noah_sft': {'cfe': cfe_lib, 'noah': noah_lib, 'sft': sft_lib, 'smp': smp_lib, 'sloth': sloth_lib},
                   }
    lib_file = library_file[model]

    # Create Input directory 
    run_dir = os.path.join(main_dir, '_'.join([objective, algorithm]))
    work_dir = os.path.join(run_dir, model + '/' + basin)
    input_dir = os.path.join(work_dir, 'Input/') 
    os.makedirs(input_dir, exist_ok=True)

    # Extract hydrofabric files
    gpkg_file = os.path.join(hydrofab_dir, 'gauge_'+ basin +'.gpkg')
    catids = gpd.read_file(gpkg_file, layer='divides')['divide_id'].tolist()
    cat_file = os.path.join(input_dir, os.path.basename(gpkg_file)) 
    nexus_file = os.path.join(input_dir, os.path.basename(gpkg_file)) 
    walk_file = input_dir + '{}'.format(basin) + '_crosswalk.json'
    if not os.path.exists(cat_file):
        os.symlink(gpkg_file, cat_file)
    gfun.create_walk_file(basin, gpkg_file, walk_file)

    # Extract forcing files
    forcing_path = os.path.join(input_dir, 'forcing')
    os.makedirs(forcing_path, exist_ok=True)
    for catID in catids:
        ffile = os.path.join(forcing_dir, catID + '.csv')
        if not os.path.exists(os.path.join(forcing_path, os.path.basename(ffile))):
            os.symlink(ffile, os.path.join(forcing_path, os.path.basename(ffile)))

    # Extract streamflow observtion 
    if obsflow_dir:
        obs = pd.read_csv(os.path.join(obsflow_dir, basin + '_hourly_discharge.csv'))[['dateTime','q_cms']]
        obs = obs.rename(columns={'dateTime': 'value_date', 'q_cms': 'obs_flow'})
        obsflow_file =  input_dir + '{}'.format(basin) + '_hourly_discharge.csv'
        obs.to_csv(obsflow_file, index=False)
    else:
        obsflow_file = None

    # Create cfe input
    cfe_input_dir = os.path.join(input_dir, 'cfe_input')
    if model in ['cfe', 'cfe_noah', 'cfe_noah_sft', 'cfe_xaj_noah', 'cfe_xaj_noah_sft']:
        gfun.create_cfe_input(catids, gpkg_file, attr_file, cfe_input_dir)

    # Create noah input
    noah_input_dir = os.path.join(input_dir, 'noah_input')
    if model in ['cfe_noah', 'topmodel_noah', 'cfe_noah_sft', 'lasam_noah_sft', 'cfe_xaj_noah', 'cfe_xaj_noah_sft']:
        gfun.create_noah_input(catids, time_period, gpkg_file, attr_file, noah_params_dir, noah_input_dir)

    # Create sft and smp input
    sft_dir = os.path.join(input_dir, 'sft_input')
    smp_dir = os.path.join(input_dir, 'smp_input')
    if model in ['cfe_noah_sft', 'lasam_noah_sft', 'cfe_xaj_noah_sft']:
        gfun.create_sft_smp_input(catids, model, attr_file, cfe_dir, forcing_dir, sft_dir, smp_dir)

    # Create lasam input 
    lasam_dir = os.path.join(input_dir, 'lasam_input')
    if model in ['lasam_noah_sft']:
        gfun.create_lasam_input(catids, cfe_dir, lasam_soil_param, lasam_soil_class, lasam_dir)

    # Extract topmodel input
    topmd_input_dir = os.path.join(input_dir, 'topmodel_input')
    if model in ['topmodel', 'topmodel_noah']:
        os.makedirs(topmd_input_dir, exist_ok=True)
        for catID in catids:
            run_file = os.path.join(topmd_dir, 'topmod_{}'.format(catID) + '.run')
            params_file = os.path.join(topmd_dir, 'params_{}'.format(catID) + '.dat')
            subcat_file = os.path.join(topmd_dir, 'subcat_{}'.format(catID) + '.dat')
            gfun.change_topmodel_input(catID, run_file, params_file, subcat_file, topmd_input_dir)

    # Create routing configuration file
    run_configs = ['_troute_config_calib.yaml', '_troute_config_valid_control.yaml', '_troute_config_valid_best.yaml']
    for file_name, run_name in zip(run_configs, ['calib','valid','valid']): 
        routing_config_file = os.path.join(work_dir + '/Input', '{}'.format(basin) + file_name)
        if len(time_period['run_time_period'][run_name][0])!=0 & len(time_period['run_time_period'][run_name][0]):
            run_range = pd.to_datetime(time_period['run_time_period'][run_name])
            nts = len(pd.date_range(start=run_range[0], end=run_range[1], freq='5T'))-1
            gfun.create_troute_config(gpkg_file, routing_config_file, time_period['run_time_period'][run_name][0], nts)

    # Create model realization file
    realization_file = work_dir + '/{}'.format(basin) + '_realization_config_bmi_calib.json' 
    routing_config_file = os.path.join(work_dir + '/Input', '{}'.format(basin) + run_configs[0])
    bmi_dir = {"cfe": cfe_input_dir, "topmodel": topmd_input_dir, "noah": noah_input_dir, 'sft': sft_dir, 'smp': smp_dir, 'lasam': lasam_dir}
    rt_dict = {"routing": {"t_route_config_file_with_path": routing_config_file}} 
    gfun.create_realization_file(work_dir, lib_file, bmi_dir, forcing_path, realization_file, model, time_period, rt_dict)

    # Create calibration configuration file 
    calib_config_file = os.path.join(work_dir + '/Input', '{}'.format(basin) + '_config_calib.yaml')
    model_dict = {'type': 'ngen', 'binary': ngen_exe_file, 'realization': realization_file, 'catchments': cat_file, 'nexus': nexus_file,
                  'crosswalk':  walk_file, 'obsflow': obsflow_file, 'strategy': 'uniform', 'params': None,
                  'eval_params': {'objective': objective, 
                                  'evaluation_start': time_period['evaluation_time_period'][run_type][0],
                                  'evaluation_stop': time_period['evaluation_time_period'][run_type][1], 
                                  'valid_start_time': time_period['run_time_period']['valid'][0],
                                  'valid_end_time': time_period['run_time_period']['valid'][1],
                                  'valid_eval_start_time': time_period['evaluation_time_period']['valid'][0],
                                  'valid_eval_end_time': time_period['evaluation_time_period']['valid'][1],
                                  'full_eval_start_time': time_period['evaluation_time_period']['full'][0],
                                  'full_eval_end_time': time_period['evaluation_time_period']['full'][1],
                                  'save_output_iter': save_output_iter,
                                  'save_plot_iter': save_plot_iter,
                                  'save_plot_iter_freq': save_plot_iter_freq,
                                  'basinID': basin, 
                                  'threshold': threshold, 
                                  'site_name': 'USGS ' + basin + ": " + site_name,
                                  'user': user_email}} 
    general_dict = general_cfg.copy()
    general_dict['workdir'] = work_dir 
    general_dict['yaml_file'] = calib_config_file 
    gfun.create_calib_config_file(calib_params_file, work_dir, general_dict, model_dict, calib_config_file)


if __name__ == "__main__":
   main()
