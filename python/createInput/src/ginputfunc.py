""" 
This module contains a variety of functions to create different input files. 

@author: Xia Feng
"""

import copy
import datetime
import glob
import json
import os
import re
import sys
import shutil
import subprocess
from fileinput import FileInput
from functools import partial
from typing import List, Union
from pathlib import Path

import geopandas as gpd
import pandas as pd
import yaml


__all__ = [
           'create_walk_file',
           'create_cfe_input',
           'create_noah_input',
           'create_sft_smp_input',
           'create_lasam_input',
           'change_topmodel_input',
           'create_troute_config',
           'create_realization_file',
           'create_calib_config_file',
          ]


def create_walk_file(
    gageID: str, 
    gpkg_file: Union[str, Path], 
    walk_file: Union[str, Path],
)->None:

    """ Create crosswalk file

    Parameters
    ----------
    gageID : stream gage ID at the outlet of basin
    gpkg_file : hydrofabric GeoPackage file
    walk_file : crosswalk file

    Returns 
    ----------
    None

    """

    df_cat = gpd.read_file(gpkg_file, layer='divides')
    df_cat.set_index('divide_id', inplace=True)
    df_nexus = gpd.read_file(gpkg_file, layer='nexus')
    df_nexus.set_index('id', inplace=True)
    df_flowpaths = gpd.read_file(gpkg_file, layer='flowpaths')
    df_flowpaths = df_flowpaths.sort_values('hydroseq')
    df_flowpaths.set_index('toid', inplace=True)

    gageid = []
    cw = {}
    for x in df_cat.index:
        hu = df_nexus.loc[df_cat.loc[x, 'toid'], 'hl_uri']
        if hu == 'NA' or not hu.startswith('Gages'): 
            catcw = {x: {"Gage_no": ""}}
        elif hu.startswith('Gages'):  
            if len(hu.split(','))>1 and gageID in hu:   
                gage=gageID
            else:
                gage = hu.split('-')[1]
            gageid.append(gage) 
            if gage == gageID:
                subdf = df_flowpaths.loc[[df_cat.loc[x, 'toid']]]
                if subdf.shape[0] == 1:
                    catcw = {x: {"Gage_no": gage}}
                else: 
                    # Select nearest one among multiple catchments draining to the gage 
                    if subdf['id'][-1].replace('wb','cat') == x:
                         print(x)
                         catcw = {x: {"Gage_no": gage}}
                    else:
                         catcw = {x: {"Gage_no": ""}}
            else:
                catcw = {x: {"Gage_no": ""}}
        cw.update(catcw)
    if len(set(gageid))>1:    
        print('more than 1 gage found, please check')
    with open(walk_file, 'w') as outfile:
        json.dump(cw, outfile, indent=4, separators=(", ", ": "), sort_keys=False)


def create_cfe_input(
    catids: List[str],  
    attr_file: Union[str, Path],
    cfe_input_dir: Union[str, Path],
)->None:

    """ Create BMI initial configuration file for CFE with Schakke infiltration and runoff scheme

    Parameters
    ----------
    catids : catchment IDs in the basin
    attr_file : file containing model parameter attributes
    cfe_input_dir: directory to save configuration files

    Returns
    ----------
    None

    Note
    ----------
    User needs to compute GIUH using other software like R whitebox package following the example 
    https://github.com/NOAA-OWP/SoilMoistureProfiles/blob/ajk/basin_workflow/basin_workflow/giuh_twi/giuh.R
    and replace the fixed GIUH assigned in this code with the calculated value.  

    """

    os.makedirs(cfe_input_dir, exist_ok=True)

    # Read hydrofabric attribute file
    dfa = pd.read_parquet(attr_file)
    dfa.set_index("divide_id", inplace=True)
 
    # Create bmi config files
    for catID in catids:
        cfe_bmi_file = os.path.join(cfe_input_dir, catID + "_bmi_config_cfe.txt")
        f = open(cfe_bmi_file, "w")
        f.write("%s" %("forcing_file=BMI\n"))
        f.write("%s" %("surface_partitioning_scheme=Schaake\n"))
        f.write("%s" %("soil_params.depth=2.0[m]\n"))
        f.write("%s" %("soil_params.b=" + str(dfa.loc[catID]['bexp_soil_layers_stag=1']) + "[]\n"))
        f.write("%s" %("soil_params.satdk=" + str(dfa.loc[catID]['dksat_soil_layers_stag=1']) + "[m s-1]\n"))
        f.write("%s" %("soil_params.satpsi=" + str(dfa.loc[catID]['psisat_soil_layers_stag=1']) + "[m]\n"))
        f.write("%s" %("soil_params.slop=" + str(dfa.loc[catID]['slope']) + "[m/m]\n"))
        f.write("%s" %("soil_params.smcmax=" + str(dfa.loc[catID]['smcmax_soil_layers_stag=1']) + "[m/m]\n"))
        f.write("%s" %("soil_params.wltsmc=" + str(dfa.loc[catID]['smcwlt_soil_layers_stag=1']) + "[m/m]\n"))
        f.write("%s" %("soil_params.expon=1.0[]\n"))
        f.write("%s" %("soil_params.expon_secondary=1.0[]\n"))
        f.write("%s" %("refkdt=" + str(dfa.loc[catID]['refkdt']) + "\n"))
        f.write("%s" %("max_gw_storage=" + str(dfa.loc[catID]['gw_Zmax']/1000.) + "[m]\n"))
        f.write("%s" %("Cgw=" + str(dfa.loc[catID]['gw_Coeff']*3600*1e-6) + "[m h-1]\n"))
        f.write("%s" %("expon=" + str(dfa.loc[catID]['gw_Expon']) + "[]\n"))
        f.write("%s" %("gw_storage=0.3[m/m]\n"))
        f.write("%s" %("alpha_fc=0.33\n"))
        f.write("%s" %("soil_storage=0.5[m/m]\n"))
        f.write("%s" %("K_nash=0.03[]\n"))
        f.write("%s" %("K_lf=0.01[]\n"))
        f.write("%s" %("nash_storage=0.0,0.0\n"))
        f.write("%s" %("num_timesteps=1\n"))
        f.write("%s" %("verbosity=1\n"))
        f.write("%s" %("DEBUG=0\n"))
        f.write("%s" %("giuh_ordinates=0.55,0.25,0.2\n"))
        f.close()


def create_noah_input(
    catids: List[str],
    time_period: dict,
    attr_file: Union[str, Path],
    param_dir_source: Union[str, Path],
    noah_input_dir: Union[str, Path],
)->None:

    """ Create BMI configuration file for Noah-OWP-Modular

    Parameters
    ----------
    catids : catchment IDs in the basin
    time_period : simulation and evaluation time period
    param_dir_source : source directory containing Noah-OWP-Modular parameter files
    noah_input_dir: directory to save configuration files

    Returns
    ----------
    None

    """

    # Create symlink for parameter directory
    os.makedirs(noah_input_dir, exist_ok=True)
    param_dir_symlink = os.path.join(noah_input_dir, os.path.basename(param_dir_source))
    if not os.path.exists(param_dir_symlink):
        os.symlink(param_dir_source, param_dir_symlink)

    # Read hydrofabric attribute file
    dfa = pd.read_parquet(attr_file)
    dfa.set_index("divide_id", inplace=True)

    # Files for the calibration and validation run
    for run_name in ['calib','valid']:
        if time_period['run_time_period'][run_name][0] and time_period['run_time_period'][run_name][1]:
            # Date
            startdate = time_period['run_time_period'][run_name][0]
            startdate = datetime.datetime.strptime(startdate, "%Y-%m-%d %H:%M:%S") + datetime.timedelta(hours=1)
            startdate = startdate.strftime("%Y%m%d%H%M")
            enddate = datetime.datetime.strptime(time_period['run_time_period'][run_name][1], "%Y-%m-%d %H:%M:%S").strftime("%Y%m%d%H%M")

            # Specify options for namelist file
            for catID in catids:
                tslp = dfa.loc[catID]['slope_mean']
                azimuth = dfa.loc[catID]['aspect_c_mean']
                lat = dfa.loc[catID]['Y']
                lon = dfa.loc[catID]['X']
                isltype = dfa.loc[catID]["ISLTYP"]
                vegtype = dfa.loc[catID]["IVGTYP"]
                sfctype = 2 if vegtype ==16 else 1 
                nom_lst = ['&timing',
                           "  " + "dt".ljust(19) +  "= 3600.0" + "                       ! timestep [seconds]",
                           "  " + "startdate".ljust(19) + "= " + "'" + startdate + "'" + "               ! UTC time start of simulation (YYYYMMDDhhmm)",
                           "  " + "enddate".ljust(19) + "= " + "'" + enddate + "'" + "               ! UTC time end of simulation (YYYYMMDDhhmm)",
                           "  " + "forcing_filename".ljust(19) + "= '.'" + "                          ! file containing forcing data",
                           "  " + "output_filename".ljust(19) + "= '.'",
                           '/',
                           "",
                           '&parameters',
                           "  " + "parameter_dir".ljust(19) + "= " + "'" + param_dir_symlink + "'",
                           "  " + "general_table".ljust(19) + "= 'GENPARM.TBL'" + "                ! general param tables and misc params",
                           "  " + "soil_table".ljust(19) + "= 'SOILPARM.TBL'" + "               ! soil param table",
                           "  " + "noahowp_table".ljust(19) + "= 'MPTABLE.TBL'" + "                ! model param tables (includes veg)",
                           "  " + "soil_class_name".ljust(19) + "= 'STAS'" + "                       ! soil class data source - 'STAS' or 'STAS-RUC'",
                           "  " + "veg_class_name".ljust(19) + "= 'USGS'" + "                       ! vegetation class data source - 'MODIFIED_IGBP_MODIS_NOAH' or 'USGS'",
                           '/',
                           "",
                           '&location',
                           "  " + "lat".ljust(19) + "= " + str(lat) + "            ! latitude [degrees]  (-90 to 90)",
                           "  " + "lon".ljust(19) + "= " + str(lon) + "           ! longitude [degrees] (-180 to 180)",
                           "  " + "terrain_slope".ljust(19) + "= " + str(tslp) + "           ! terrain slope [degrees]",
                           "  " + "azimuth".ljust(19) + "= " + str(azimuth) + "           ! terrain azimuth or aspect [degrees clockwise from north]",
                           '/',
                           "",
                           "&forcing",
                           "  " + "ZREF".ljust(19) + "= 10.0" + "                         ! measurement height for wind speed (m)",
                           "  " + "rain_snow_thresh".ljust(19) + "= 0.5" + "                          ! rain-snow temperature threshold (degrees Celcius)",
                           "/",
                           "",
                           "&model_options",
                           "  " + "precip_phase_option".ljust(34) + "= 6",
                           "  " + "snow_albedo_option".ljust(34) + "= 1",
                           "  " + "dynamic_veg_option".ljust(34) + "= 4",
                           "  " + "runoff_option".ljust(34) + "= 3",
                           "  " + "drainage_option".ljust(34) + "= 8",
                           "  " + "frozen_soil_option".ljust(34) + "= 1",
                           "  " + "dynamic_vic_option".ljust(34) + "= 1",
                           "  " + "radiative_transfer_option".ljust(34) + "= 3",
                           "  " + "sfc_drag_coeff_option".ljust(34) + "= 1",
                           "  " + "canopy_stom_resist_option".ljust(34) + "= 1",
                           "  " + "crop_model_option".ljust(34) + "= 0",
                           "  " + "snowsoil_temp_time_option".ljust(34) + "= 3",
                           "  " + "soil_temp_boundary_option".ljust(34) + "= 2",
                           "  " + "supercooled_water_option".ljust(34) + "= 1",
                           "  " + "stomatal_resistance_option".ljust(34) + "= 1",
                           "  " + "evap_srfc_resistance_option".ljust(34) + "= 4",
                           "  " + "subsurface_option".ljust(34) + "= 2",
                           "/",
                           "",
                           "&structure",
                           "  " + "isltyp".ljust(17) + "= " + str(isltype) + "              ! soil texture class",
                           "  " + "nsoil".ljust(17) + "= 4              ! number of soil levels",
                           "  " + "nsnow".ljust(17) + "= 3              ! number of snow levels",
                           "  " + "nveg".ljust(17) + "= 27             ! number of vegetation type",
                           "  " + "vegtyp".ljust(17) + "= " + str(vegtype) + "             ! vegetation type",
                           "  " + "croptype".ljust(17) + "= 0              ! crop type (0 = no crops; this option is currently inactive)",
                           "  " + "sfctyp".ljust(17) + "= " + str(sfctype) + "              ! land surface type, 1:soil, 2:lake",
                           "  " + "soilcolor".ljust(17) + "= 4              ! soil color code",
                           "/",
                           "",
                           "&initial_values",
                           "  " + "dzsnso".ljust(10) + "= 0.0, 0.0, 0.0, 0.1, 0.3, 0.6, 1.0      ! level thickness [m]",
                           "  " + "sice".ljust(10) + "= 0.0, 0.0, 0.0, 0.0                     ! initial soil ice profile [m3/m3]",
                           "  " + "sh2o".ljust(10) + "= 0.3, 0.3, 0.3, 0.3                     ! initial soil liquid profile [m3/m3]",
                           "  " + "zwt".ljust(10) + "= -2.0                                   ! initial water table depth below surface [m]",
                           "/",
                           ]
               
                namelst = os.path.join(noah_input_dir, '{}'.format(catID) + '_' + run_name + '.input')
                with open(namelst, 'w') as outfile:
                    outfile.writelines('\n'.join(nom_lst))
                    outfile.write("\n")


def create_sft_smp_input(
    catids: List[str],  
    model: str, 
    attr_file: Union[str, Path],
    cfe_dir: Union[str, Path],
    forcing_dir: Union[str, Path], 
    sft_dir: Union[str, Path], 
    smp_dir: Union[str, Path], 
)->None:

    """ Create BMI configuration file for soil freeze and thaw module, and soil moisture profiles

    Parameters
    ----------
    catids : catchment IDs in the basin
    model: model and module combination 
    attr_file : file containing model parameter attributes
    cfe_dir : directory containing cfe bmi configuration files 
    forcing_dir : directory containing forcing files 
    sft_dir : directory for writing sft bmi configuration files 
    smp_dir : directory for writing smp bmi configuration files

    Returns 
    ----------
    None

    """

    os.makedirs(sft_dir, exist_ok=True)
    os.makedirs(smp_dir, exist_ok=True)

    # Read attribute file to obtain quartz
    dfa = pd.read_parquet(attr_file)
    dfa.set_index('divide_id', inplace=True)

    # Ice fraction scheme
    if model in ['cfe_noah_sft', 'lasam_noah_sft']:
        icefscheme = 'Schaake'
    elif model in ['cfe_xaj_noah_sft']:
        icefscheme = 'Xinanjiang'

    # Create bmi config files
    for catID in catids:

        # Read cfe file
        cfe_bmi_file = os.path.join(cfe_dir, catID + '*.txt')
        df = pd.read_table(cfe_bmi_file,  delimiter='=', names=["Params","Values"], index_col=0)

        # Obtain annual mean surface temperature as proxy for initial soil temperature
        fdf = pd.read_table(os.path.join(forcing_dir, catID + '.csv'),  delimiter=',')
        mtemp = round(fdf['T2D'].mean(), 2)

        # Create sft list
        sft_lst = ['verbosity=none', 'soil_moisture_bmi=1', 'end_time=1.[d]', 'dt=1.0[h]', 
                   'soil_params.smcmax=' + df.loc['soil_params.smcmax'][0], 
                   'soil_params.b=' + df.loc['soil_params.b'][0], 
                   'soil_params.satpsi=' + df.loc['soil_params.satpsi'][0], 
                   'soil_params.quartz=' + str(dfa.loc[catID]['quartz']) +'[]', 
                   'ice_fraction_scheme=' + icefscheme, 'soil_z=0.1,0.3,1.0,2.0[m]',
                   'soil_temperature=' + ','.join([str(mtemp)]*4) + '[K]',
                  ]
        sft_bmi_file = os.path.join(sft_dir, catID + '_bmi_config_sft.txt')
        with open(sft_bmi_file, "w") as f:
            f.writelines('\n'.join(sft_lst))

        # Create smp list
        smp_lst = ['verbosity=none', 
               'soil_params.smcmax=' + df.loc['soil_params.smcmax'][0], 
               'soil_params.b=' + df.loc['soil_params.b'][0], 
               'soil_params.satpsi=' + df.loc['soil_params.satpsi'][0], 
               'soil_z=0.1,0.3,1.0,2.0[m]']
        if model in ['cfe_noah_sft', 'cfe_xaj_noah_sft']:
            smp_lst += ['soil_storage_model=conceptual', 'soil_storage_depth=2.0']
        elif model in ['lasam_noah_sft']:
            smp_lst += ['soil_storage_model=layered', 'soil_moisture_profile_option=constant', 'soil_depth_layers=2.0', 'water_table_depth=10[m]']
        smp_bmi_file = os.path.join(smp_dir, catID + '_bmi_config_smp.txt')
        with open(smp_bmi_file, "w") as f:
            f.writelines('\n'.join(smp_lst))


def create_lasam_input(
    catids: List[str],
    cfe_bmi_dir: Union[str, Path], 
    soil_param_file: str,
    soil_class_file: Union[str, Path],
    lasam_bmi_dir: Union[str, Path], 
)->None:

    """ Create BMI configuration file for Lumped Arid and Semi-arid Model 

    Parameters
    ----------
    catids : catchment IDs in the basin
    cfe_bmi_dir : directory for the cfe bmi configuration file 
    soil_param_file : soil hydraulic parameter file 
    soil_class_file : soil texture class file 
    lasam_bmi_dir : directory for the lasam bmi configuration file 

    Returns 
    ----------
    None

    """

    os.makedirs(lasam_dir, exist_ok=True)

    # Create lasam list
    lasam_lst = ['verbosity=none',
                'soil_params_file=' + soil_param_file,
               'layer_thickness=200.0[cm]',
               'initial_psi=2000.0[cm]',
               'timestep=300[sec]',
               'endtime=1000[hr]',
               'forcing_resolution=3600[sec]',
               'ponded_depth_max=0[cm]',
               'use_closed_form_G=false',
               'layer_soil_type=',
               'max_soil_types=25',
               'wilting_point_psi=15495.0[cm]',
               'giuh_ordinates=',
               'sft_coupled=true',
               'soil_z=10,30,100.0,200.0[cm]',
               'calib_params=true',
               ]

    # Read soil class file
    df_soil = pd.read_csv(soil_class_file)
    df_soil.set_index("id", inplace=True)

    # Create bmi config file
    for catID in catids:
        cfe_file_catID = glob.glob(os.path.join(cfe_bmi_dir, catID + '*.txt'))[0]
        df = pd.read_table(cfe_file_catID,  delimiter='=', names=["Params","Values"], index_col=0)
        lasam_lst_catID = lasam_lst.copy()
        lasam_lst_catID[9] = lasam_lst_catID[9] + str(df_soil.loc[catID]['category'])
        lasam_lst_catID[12] = lasam_lst_catID[12] + df.loc['giuh_ordinates'][0]
        lasam_bmi_file = os.path.join(lasam_bmi_dir, catID + '_bmi_config_lasam.txt')

        with open(lasam_bmi_file, "w") as f:
            f.writelines('\n'.join(lasam_lst_catID))


def change_topmodel_input(
    catID: str, 
    runfile: Union[str, Path], 
    paramsfile: Union[str, Path], 
    subcatfile: Union[str, Path], 
    inputDir: Union[str, Path],
)->None:

    """ change options in TOPMODEL input file

    Parameters
    ----------
    catID : catchment ID
    runfile : specify paths for forcing, subcat, parameters, topmodel output and hyd output
    paramsfile : parameter file
    subcatfile : subcat file
    inputDir : directory for storing input files

    Returns 
    ----------
    None   

    """

    # Copy
    new_runfile = os.path.join(inputDir, '{}'.format(catID) + '_topmodel.run')
    shutil.copy(runfile, new_runfile)
    new_params = os.path.join(inputDir, '{}'.format(catID) + '_topmodel_params.dat')
    shutil.copy(paramsfile, new_params)
    new_subcat = os.path.join(inputDir, '{}'.format(catID) + '_topmodel_subcat.dat')
    shutil.copy(subcatfile, new_subcat)

    # read runfile
    with open(new_runfile, 'r') as infile:
         list_lines = infile.readlines()
    lst_lines = copy.deepcopy(list_lines)

    # Change directory in runfile
    topmod_out = os.path.join(os.path.dirname(os.path.dirname(inputDir)), '{}'.format(catID) + '_topmod.out')
    hyd_out = os.path.join(os.path.dirname(os.path.dirname(inputDir)), '{}'.format(catID) + '_hyd.out')
    filePath = [os.path.join(os.path.dirname(inputDir), '{}'.format(catID) + '_forcing.csv'),
                new_subcat, new_params, topmod_out, hyd_out]

    for i in range(0,5):
        lst_lines[i+2] = filePath[i] + '\n'

    # Save file
    with open(new_runfile, 'w') as outfile:
        outfile.writelines(lst_lines)


def create_troute_config(
    gpkg_file: Union[str, Path],
    rt_cfg_file:  Union[str, Path],
    start_date: str,
    nts: int,
    #reformat_dir: Union[str, Path],
)->None:

    """ Create routing configuration YAML file

    Parameters
    ----------
    gpkg_file :  GeoPackage hydrofabric file
    rt_cfg_file : t-route configuration YAML file
    start_date :  start date for restart run 
    nts : number of timesteps
    reformat_dir : directory for the reformatted nexus output files

    Returns
    ----------
    None

    """

    # bmi_parameters 
    bmi_param = {"flowpath_columns": ["id", "toid", "lengthkm"],
                 "attributes_columns": ['attributes_id', 
                                        'rl_gages',
                                        'rl_NHDWaterbodyComID',
                                        'MusK',
                                        'MusX',
                                        'n',
                                        'So',
                                        'ChSlp',
                                        'BtmWdth',
                                        'nCC',
                                        'TopWdthCC',
                                        'TopWdth'],
                 "waterbody_columns": ['hl_link', 
                                       'ifd',
                                       'LkArea',
                                       'LkMxE',
                                       'OrificeA',
                                       'OrificeC',
                                       'OrificeE',
                                       'WeirC',
                                       'WeirE',
                                       'WeirL'],
                 "network_columns": ['network_id', 'hydroseq', 'hl_uri'],
                }

    # log_parameters
    log_param = {"showtiming": True, "log_level": 'DEBUG'}

    # network_topology_parameters
    columns = {"key": "id",  
               "downstream": "toid",
               "dx": "lengthkm",
               "n": "n",
               "ncc": "nCC",
               "s0": "So",
               "bw": "BtmWdth",
               "waterbody": "rl_NHDWaterbodyComID",
               "gages": "rl_gages",
               "tw": "TopWdth",
               "twcc": "TopWdthCC",
               "musk": "MusK",
               "musx": "MusX",
               "cs": "ChSlp",
               "alt": "alt",
              }

    dupseg = ["717696", "1311881", "3133581", "1010832", "1023120", "1813525", 
              "1531545", "1304859", "1320604", "1233435", "11816", "1312051",
              "2723765", "2613174", "846266", "1304891", "1233595", "1996602", 
              "2822462", "2384576", "1021504", "2360642", "1326659", "1826754",
              "572364", "1336910", "1332558", "1023054", "3133527", "3053788",  
              "3101661", "2043487", "3056866", "1296744", "1233515", "2045165", 
              "1230577", "1010164", "1031669", "1291638", "1637751",
             ]

    nwtopo_param = {"supernetwork_parameters": {"network_type": "HYFeaturesNetwork",
                                                "geo_file_path": gpkg_file, 
                                                "columns": columns, 
                                                "duplicate_wb_segments": dupseg},
                    "waterbody_parameters": {"break_network_at_waterbodies": True,
                                             "level_pool": {"level_pool_waterbody_parameter_file_path": gpkg_file}},
                   }

    # compute_parameters
    res_da = {"reservoir_persistence_da":{"reservoir_persistence_usgs": False,
                                           "reservoir_persistence_usace": False},
              "reservoir_rfc_da": {"reservoir_rfc_forecasts": False,
                                   "reservoir_rfc_forecasts_time_series_path": None,
                                   "reservoir_rfc_forecasts_lookback_hours": 28,
                                   "reservoir_rfc_forecasts_offset_hours": 28,
                                   "reservoir_rfc_forecast_persist_days": 11},
              "reservoir_parameter_file": None,
             }
    
    stream_da = {"streamflow_nudging": False,
                 "diffusive_streamflow_nudging": False,
                 "gage_segID_crosswalk_file": None,
                }

    comp_param = {"parallel_compute_method": "by-subnetwork-jit-clustered",
                 "subnetwork_target_size": 10000,
                 "cpu_pool": 16,
                 "compute_kernel": "V02-structured",
                 "assume_short_ts": True,
                 "restart_parameters": {"start_datetime": start_date},
                 "forcing_parameters": {"qts_subdivisions": 12,
                                        "dt": 300,
                                        "qlat_input_folder": ".",
                                        "qlat_file_pattern_filter": "nex-*", 
                                        "nts": nts, 
                                        "max_loop_size": divmod(nts*300, 3600)[0]+1},
                 "data_assimilation_parameters": {"usgs_timeslices_folder": None,
                                                  "usace_timeslices_folder": None,
                                                  "timeslice_lookback_hours": 48, 
                                                  "qc_threshold": 1, 
                                                  "streamflow_da": stream_da,
                                                  "reservoir_da": res_da},  
                 }

    # output_parameters
    output_param = {'stream_output': {'stream_output_directory': ".",
                                      'stream_output_time': divmod(nts*300, 3600)[0]+1,
                                      'stream_output_type': '.nc',
                                      'stream_output_internal_frequency': 60, 
                                       },
                   }

    # Combine all parameters
    config = {"bmi_parameters": bmi_param, 
              "log_parameters": log_param,
              "network_topology_parameters": nwtopo_param,
              "compute_parameters": comp_param,
              "output_parameters": output_param,
             }

    # Save configuration into yaml file
    with open(rt_cfg_file, 'w') as file:
        yaml.dump(config, file, sort_keys=False, default_flow_style=False, indent=4)


def create_realization_file(
    workdir: Union[str, Path], 
    lib_file: dict, 
    bmi_dir: dict, 
    forcing_dir: Union[str, Path], 
    realization_file: Union[str, Path],
    model: str, 
    time_period: dict, 
    rt_dict: dict,
)-> None:

    """ Create realization file for the specified model and module

    Parameters
    ----------
    workdir : basin directory for storing all the files 
    lib_file : library file for different model or module
    bmi_dir : directory for different model or module to store BMI files 
    forcing_dir : directory to store foricng files
    realization_file : model realization configuration file
    model: model and module combination 
    time_period : simulation and evaluation time period
    rt_dict : routing model source file directory and configuration file  

    Returns 
    ----------
    None

    """

    # Create symlinks for libraries
    lib_mod = {} 
    for key, value in lib_file.items(): 
        lib_mod_link = os.path.join(workdir, 'Input/' + os.path.basename(value))
        lib_mod.update({key: lib_mod_link})
        if not os.path.exists(lib_mod_link): 
            os.symlink(value, lib_mod_link)

    # noah 
    if model in ["cfe_noah", "topmodel_noah", "cfe_noah_sft", "lasam_noah_sft", "cfe_xaj_noah", "cfe_xaj_noah_sft"]:
        noah_dict = {"name": "bmi_fortran", 
                     "params": {"name": "bmi_fortran", 
                                "model_type_name": "NoahOWP", 
                                "main_output_variable": "QINSUR",
                                "library_file": lib_mod['noah'],
                                "init_config": os.path.join(bmi_dir['noah'], '{{id}}_calib.input'),
                                "allow_exceed_end_time": True, "fixed_time_step": False, "uses_forcing_file": False,
                                "variables_names_map": {
                                    "PRCPNONC": "atmosphere_water__liquid_equivalent_precipitation_rate",
                                    "Q2": "atmosphere_air_water~vapor__relative_saturation",
                                    "SFCTMP": "land_surface_air__temperature",
                                    "UU": "land_surface_wind__x_component_of_velocity",
                                    "VV": "land_surface_wind__y_component_of_velocity",
                                    "LWDN": "land_surface_radiation~incoming~longwave__energy_flux",
                                    "SOLDN": "land_surface_radiation~incoming~shortwave__energy_flux",
                                    "SFCPRS": "land_surface_air__pressure"}}}
    # cfe 
    if model in ["cfe_noah", "cfe_noah_sft", "cfe_xaj_noah", "cfe_xaj_noah_sft"]:
        cfe_dict = {"name": "bmi_c",
                    "params": {"name": "bmi_c", 
                               "model_type_name": "CFE", 
                               "main_output_variable": "Q_OUT",
                               "library_file": lib_mod['cfe'],
                               "init_config": os.path.join(bmi_dir['cfe'], '{{id}}_bmi_config_cfe.txt'), 
                               "allow_exceed_end_time": True, "fixed_time_step": False, "uses_forcing_file": False,
                               "variables_names_map": {
                                   "atmosphere_water__liquid_equivalent_precipitation_rate": "QINSUR",
                                   "water_potential_evaporation_flux": "EVAPOTRANS"},
                               "registration_function": "register_bmi_cfe"}}
        if model in ["cfe_noah", "cfe_xaj_noah"]:
            items = {"ice_fraction_schaake": "sloth_ice_fraction_schaake",
                     "ice_fraction_xinanjiang": "sloth_ice_fraction_xinanjiang",
                     "soil_moisture_profile": "sloth_smp"}
            var_name_map= cfe_dict["params"]["variables_names_map"]
            var_name_map.update(items)
            cfe_dict["params"]["variables_names_map"] = var_name_map 

    # topmodel
    if model in ["topmodel_noah"]:
        topm_dict = {"name": "bmi_c",
                     "params": {"name": "bmi_c", 
                                "model_type_name": "TOPMODEL", 
                                "main_output_variable": "Qout",
                                "library_file": lib_mod['topmodel'],
                                "init_config": os.path.join(bmi_dir['topmodel'], '{{id}}_topmodel.run'),
                                "allow_exceed_end_time": True, "fixed_time_step": False, "uses_forcing_file": False,
                                "variables_names_map": {
                                    "atmosphere_water__liquid_equivalent_precipitation_rate": "QINSUR",
                                    "water_potential_evaporation_flux": "EVAPOTRANS"},
                                "registration_function": "register_bmi_topmodel"}}

    # sloth
    if model in ["cfe_noah", "topmodel_noah", "cfe_xaj_noah"]:
        sloth_dict = {"name": "bmi_c++",
                      "params": {"name": "bmi_c++", 
                                 "model_type_name": "SLOTH", 
                                 "main_output_variable": "z", 
                                 "library_file": lib_mod['sloth'], 
                                 "init_config": '/dev/null',
                                 "allow_exceed_end_time": True, 
                                 "fixed_time_step": False, 
                                 "uses_forcing_file": False,
                                 "model_params": {
                                     "sloth_ice_fraction_schaake(1,double,m,node)": 0.0,
                                     "sloth_ice_fraction_xinanjiang(1,double,1,node)": 0.0,
			             "sloth_smp(1,double,1,node)": 0.0}}}

    elif model in ["cfe_noah_sft", "cfe_xaj_noah_sft"]:
        sloth_dict = {"name": "bmi_c++",
                      "params": {"name": "bmi_c++", 
                                 "model_type_name": "SLOTH",
                                 "main_output_variable": "z", 
                                 "library_file": lib_mod['sloth'],
                                 "init_config": '/dev/null',
                                 "allow_exceed_end_time": True, 
                                 "fixed_time_step": False, 
                                 "uses_forcing_file": False,
                                 "model_params": {
                                     "soil_moisture_wetting_fronts(1,double,1,node)": 0.0,
		                     "soil_thickness_layered(1,double,1,node)": 0.0,
		             	     "soil_depth_wetting_fronts(1,double,1,node)": 0.0,
				     "num_wetting_fronts(1,int,1,node)": 1.0,
			             "Qb_topmodel(1,double,1,node)": 0.0,
				     "Qv_topmodel(1,double,1,node)": 0.0,
				     "global_deficit(1,double,1,node)": 0.0}}}
    
    elif model in ["lasam_noah_sft"]:
        sloth_dict = {"name": "bmi_c++",
                      "params": {"name": "bmi_c++",
                                 "model_type_name": "SLOTH",
                                 "main_output_variable": "z",
                                 "library_file": lib_mod['sloth'],
                                 "init_config": '/dev/null',
                                 "allow_exceed_end_time": True,
                                 "fixed_time_step": False,
                                 "uses_forcing_file": False,
                                 "model_params": {
                                     "sloth_soil_storage(1,double,m,node)" : 1.0E-10,
                                     "sloth_soil_storage_change(1,double,m,node)" : 0.0,
                                     "Qb_topmodel(1,double,1,node)": 0.0,
                                     "Qv_topmodel(1,double,1,node)": 0.0,
                                     "global_deficit(1,double,1,node)": 0.0,
                                     "potential_evapotranspiration_rate(1,double,1,node)": 0.0}}}

    # sft
    if model in ["cfe_noah_sft", "lasam_noah_sft", "cfe_xaj_noah_sft"]:
        sft_dict = {"name": "bmi_c++",
                    "params": {"name": "bmi_c++",
                               "model_type_name": "SFT", 
                               "main_output_variable": "num_cells",
                               "library_file": lib_mod['sft'],
                               "init_config": os.path.join(bmi_dir['sft'], '{{id}}_bmi_config_sft.txt'),
                               "allow_exceed_end_time": True, 
                               "uses_forcing_file": False,
                               "variables_names_map": {"ground_temperature" : "TGS"}}}

    # smp
    if model in ["cfe_noah_sft", "cfe_xaj_noah_sft"]:
        smp_dict = {"name": "bmi_c++",
                    "params": {"name": "bmi_c++", 
                               "model_type_name": "SMP", 
                               "main_output_variable": "soil_water_table",
                               "library_file": lib_mod['smp'],
                               "init_config": os.path.join(bmi_dir['smp'], '{{id}}_bmi_config_smp.txt'),
                               "allow_exceed_end_time": True,
                               "uses_forcing_file": False,
                               "variables_names_map": {
                                   "soil_storage": "SOIL_STORAGE",
				   "soil_storage_change": "SOIL_STORAGE_CHANGE"}}}

    elif model in ["lasam_noah_sft"]:
         smp_dict = {"name": "bmi_c++",
                    "params": {"name": "bmi_c++",
                               "model_type_name": "SMP",
                               "main_output_variable": "soil_water_table",
                               "library_file": lib_mod['smp'],
                               "init_config": os.path.join(bmi_dir['smp'], '{{id}}_bmi_config_smp.txt'),
                               "allow_exceed_end_time": True,
                               "uses_forcing_file": False,
                               "variables_names_map": {
                                   "soil_storage" : "sloth_soil_storage",
                                   "soil_storage_change" : "sloth_soil_storage_change",
                                   "soil_moisture_wetting_fronts" : "soil_moisture_wetting_fronts",
                                   "soil_depth_wetting_fronts" : "soil_depth_wetting_fronts",
                                   "num_wetting_fronts" : "soil_num_wetting_fronts"}}}

    # lasam
    if model in ["lasam_noah_sft"]:
        lasam_dict = {"name": "bmi_c++",
                      "params": {"name": "bmi_c++",
                                 "model_type_name": "LASAM",
                                 "main_output_variable": "precipitation_rate",
                                 "library_file": lib_mod['lasam'],
                                 "init_config": os.path.join(bmi_dir['lasam'], '{{id}}_bmi_config_lasam.txt'),
                                 "allow_exceed_end_time": True,
                                 "uses_forcing_file": False,
                                 "variables_names_map": {
                                     "precipitation_rate" : "QINSUR",
                                     "potential_evapotranspiration_rate": "EVAPOTRANS"}}}

    # Combine configurations
    if model in ["cfe_noah", "cfe_xaj_noah"]:
        model_type_name = "NoahOWP_CFE"
        main_output_variable = "Q_OUT"        
        sub_module = [noah_dict, *[cfe_dict, sloth_dict]]

    elif model == "topmodel_noah":
        model_type_name = "NoahOWP_TOPMODEL"
        main_output_variable = "Qout"        
        sub_module = [noah_dict, topm_dict]

    elif model in ["cfe_noah_sft", "cfe_xaj_noah_sft"]:
        model_type_name = "NoahOWP_CFE_SK_SFT_SMP" if model== "cfe_noah_sft" else "NoahOWP_CFE_XAJ_SFT_SMP"
        main_output_variable = "Q_OUT"
        output_variables = ["soil_ice_fraction", "TGS", "RAIN_RATE", "DIRECT_RUNOFF", "GIUH_RUNOFF", "NASH_LATERAL_RUNOFF",
	                    "DEEP_GW_TO_CHANNEL_FLUX", "Q_OUT", "SOIL_STORAGE",  "ice_fraction_schaake", "POTENTIAL_ET", "ACTUAL_ET", "soil_moisture_fraction"]
        output_header_fields = ["soil_ice_fraction", "ground_temperature", "rain_rate", "direct_runoff", "giuh_runoff", "nash_lateral_runoff",
                                "deep_gw_to_channel_flux", "q_out", "soil_storage", "ice_fraction_schaake", "PET", "AET", "soil_moisture_fraction"]
        if model=="cfe_xaj_noah_sft":
            output_variables[9] = "ice_fraction_xinanjiang"
            output_header_fields[9] = "ice_fraction_xinanjiang"
        sub_module = [sloth_dict, noah_dict, smp_dict, sft_dict, cfe_dict]

    elif model == "lasam_noah_sft":
        model_type_name = "NoahOWP_LASAM_SFT_SMP"
        main_output_variable = "total_discharge"
        output_variables = ["soil_ice_fraction", "TGS", "precipitation", "potential_evapotranspiratio", "actual_evapotranspiration", 
                            "soil_storage", "surface_runoff", "giuh_runoff", "groundwater_to_stream_recharge",  "percolation", "total_discharge", 
                            "infiltration", "EVAPOTRAN", "soil_moisture_fraction"] 
        output_header_fields = ["soil_ice_fraction", "ground_temperature", "rain_rate", "PET_rate", "actual_ET",  
                                "soil_storage", "direct_runoff", "giuh_runoff", "deep_gw_to_channel_flux", "soil_to_gw_flux", "q_out",
                                "infiltration", "PET_NOM", "soil_moisture_fraction"]
        sub_module = [sloth_dict, noah_dict, smp_dict, sft_dict, lasam_dict]

    gbmain = {"name": "bmi_multi", 
              "params": {"name": "bmi_multi", "model_type_name": model_type_name, "init_config": "",
                         "allow_exceed_end_time": False, "fixed_time_step": False, 
                         "uses_forcing_file": False,
                         "main_output_variable": main_output_variable}}
    if model in ["cfe_noah_sft", "lasam_noah_sft", "cfe_xaj_noah_sft"]:
        gbmain["params"]["output_variables"] = output_variables
        gbmain["params"]["output_header_fields"] = output_header_fields
    gbmain["params"]["modules"] = sub_module

    # global configuration
    g = {"global": {"formulations": [gbmain],
                    "forcing": {"file_pattern": ".*{{id}}.*.csv", "path": forcing_dir, "provider": "CsvPerFeature"}}}

    # time object
    t = {"time": {"start_time": time_period['run_time_period']['calib'][0],
                  "end_time": time_period['run_time_period']['calib'][1], "output_interval": 3600}}
    g.update(t)

    # routing object 
    g.update(rt_dict)

    # save configuration into json file 
    with open(realization_file, 'w') as outfile:
        json.dump(g, outfile, indent=4, separators=(", ", ": "), sort_keys=False)


def create_calib_config_file(
    calib_params_file: Union[str, Path], 
    workdir: Union[str, Path], 
    general_dict: dict,
    model_dict: dict, 
    config_yaml_file: Union[str, Path], 
)->None: 

    """ Create configuration YAML file for calibration run

    Parameters
    ----------
    calib_params_file : file containing min, max and init values of calibration parameters
    workdir : basin directory for storing all the files 
    general_dict : general settings  
    model_dict : model settings 
    config_yaml_file : configuration YAML file  

    Returns 
    ----------
    None

    """

    # Extract calibration params range 
    df_params = pd.read_fwf(calib_params_file).copy()
    df_params.set_index('param', inplace=True)
    calib_params = df_params.groupby('model').groups

    params_range_dict = {}
    for k, v in calib_params.items():
        params_range = []
        for m in v:   
            params_range.append({'name': m, 'min': float(df_params.query('model==@k').loc[m]['min']), 
                                 'max': float(df_params.query('model==@k').loc[m]['max']), 
                                 'init': float(df_params.query('model==@k').loc[m]['init'])})
        params_range_dict.update({k: params_range})

    # Create configuration 
    basin_yaml = {'general': general_dict}
    basin_yaml.update(params_range_dict)

    # Create symlink for ngen executable
    ngen_file_link = os.path.join(workdir, 'Input/' + os.path.basename(model_dict['binary'])[0:4])
    if not os.path.exists(ngen_file_link):
        os.symlink(model_dict['binary'], ngen_file_link)

    model_dict['binary'] = ngen_file_link
    basin_yaml['model'] = model_dict
    basin_yaml['model']['params'] = params_range_dict 

    # Save configuration into yaml file
    with open(config_yaml_file, 'w') as file:
        yaml.dump(basin_yaml, file, sort_keys=False, default_flow_style=False, indent=2)
