"""
This module contains functions to read output files from calibration 
and validation runs, and generate a variery of plots.

@author: Xia Feng
"""

import copy
from functools import reduce
import glob
from math import log
import os
import subprocess
from typing import Dict, List, TYPE_CHECKING, Optional, Union

import numpy as np 
import pandas as pd 

import ngen.cal.metric_functions as mf
import ngen.cal.plot_functions as plf

if TYPE_CHECKING:
    from ngen.cal.agent import Agent
    from ngen.cal import Evaluatable  

__all__ = ['plot_calib_output',
           'plot_valid_output',
           'plot_cost_func',
          ]


def plot_calib_output(
    i: int, 
    calibration_object: 'Evaluatable', 
    agent: 'Agent', 
    eval_range: Optional[List[str]] = None,
) -> None:
    """Plot streamflow and other model output as well as metrics for calibration run.

    Parameters
    ----------
    calibration_object : catchment object 
    meta : meta object 
    eval_range : evaluation time period for calibration run

    Returns
    ----------
    None 

    """
    # Output files from different runs
    control_run = calibration_object.basinID + '_output_iteration_0000.csv'
    control_run = os.path.join(agent.output_iter_path, control_run)
    best_run = calibration_object.basinID + '_output_best_iteration.csv'
    best_run = os.path.join(agent.job.workdir, best_run)
    last_run = calibration_object.basinID + '_output_last_iteration.csv'
    last_run = os.path.join(agent.job.workdir, last_run)

    # Read output
    df_control_run = pd.read_csv(control_run)
    df_control_run['Time'] = pd.DatetimeIndex(df_control_run['Time'])
    df_control = df_control_run[['Time', calibration_object.streamflow_name]]
    df_control = df_control.rename(columns={calibration_object.streamflow_name: 'Control Run'})
    df_control.set_index('Time', inplace=True)
    df_best_run = pd.read_csv(best_run)
    df_best = df_best_run[['Time',calibration_object.streamflow_name]]
    df_best = df_best.rename(columns={calibration_object.streamflow_name: 'Best Run'})
    df_best['Time'] = pd.DatetimeIndex(df_best['Time'])
    df_best.set_index('Time', inplace=True)
    df_last_run = pd.read_csv(last_run)[['Time',calibration_object.streamflow_name]]
    df_last = df_last_run[['Time',calibration_object.streamflow_name]]
    df_last = df_last.rename(columns={calibration_object.streamflow_name: 'Last Run'})
    df_last['Time'] = pd.DatetimeIndex(df_last['Time'])
    df_last.set_index('Time', inplace=True)
    dfs1 = [calibration_object.observed, df_control, df_best, df_last]
    df_merged = reduce(lambda left, right: pd.merge(left, right, left_index=True, right_index=True, how='right'), dfs1)
    df_merged = df_merged.rename(columns={'obs_flow': 'Observation'})
    df_merged[['Control Run','Best Run','Last Run']] = df_merged[['Control Run','Best Run','Last Run']] 
    if df_merged.empty:
        print("WARNING: can't merge different runs")
    if eval_range:
        df_merged = df_merged.loc[eval_range[0]:eval_range[1]]
    df_merged.reset_index(inplace=True)
    df_merged = df_merged.rename(columns={'index': 'Time'})
    df_merged = mf.treat_values(df_merged, remove_neg = True)
    df_merged_copy1 = copy.deepcopy(df_merged)
     
    # Plot hydrograph
    fig_path = agent.plot_iter_path
    if calibration_object.save_plot_iter_flag:
        plotfile = os.path.join(fig_path, calibration_object.basinID + '_hydrograph_iteration_' + str('{:04d}').format(i) + '.png')  
    else: 
        plotfile = os.path.join(fig_path, calibration_object.basinID + '_hydrograph_iteration.png')  
    title  = 'Hydrograph at Iteration = ' + str(i) + '\n' + calibration_object.station_name
    plf.plot_streamflow(df_merged_copy1, plotfile, title)

    # Plot scatterplot of streamflow from observation and other runs
    if calibration_object.save_plot_iter_flag:
        plotfile = os.path.join(fig_path, calibration_object.basinID + '_scatterplot_streamflow_iteration_' + str('{:04d}').format(i) + '.png')  
    else: 
        plotfile = os.path.join(fig_path, calibration_object.basinID + '_scatterplot_streamflow_iteration.png')  
    title = 'Scatterplot of Streaflow at Iteration = ' + str(i) + '\n' + calibration_object.station_name
    df_merged_copy2 = copy.deepcopy(df_merged)
    plf.scatterplot_streamflow(df_merged_copy2, plotfile, title)

    # Plot flow duration curve from observation and other runs
    if calibration_object.save_plot_iter_flag:
        plotfile = os.path.join(fig_path, calibration_object.basinID + '_fdc_iteration_' + str('{:04d}').format(i) + '.png')  
    else: 
        plotfile = os.path.join(fig_path, calibration_object.basinID + '_fdc_iteration.png')  
    title  = 'Flow Duration Curve at Iteration = ' + str(i) + '\n' + calibration_object.station_name
    df_merged_copy3 = copy.deepcopy(df_merged)
    plf.plot_fdc_calib(df_merged_copy3, plotfile, title)

    # Plot time series of streamflow and precipitation 
    if calibration_object.save_plot_iter_flag:
        plotfile = os.path.join(fig_path, calibration_object.basinID + '_streamflow_precip_iteration_' + str('{:04d}').format(i) + '.png')
    else:
        plotfile = os.path.join(fig_path, calibration_object.basinID + '_streamflow_precip_iteration.png')
    title  = 'Streamflow and Total Precipitation at Iteration = ' + str(i) + '\n' + calibration_object.station_name
    df_merged_copy4 = copy.deepcopy(df_merged)
    plf.plot_streamflow_precipitation(df_merged_copy4, agent.df_precip, plotfile, title)

    # Plot scatterplot between objective function and iteration
    if calibration_object.save_plot_iter_flag:
        plotfile = os.path.join(fig_path, calibration_object.basinID + '_objfun_iteration_' + str('{:04d}').format(i) +'.png')  
    else:
        plotfile = os.path.join(fig_path, calibration_object.basinID + '_objfun_iteration.png')  
    title  = 'Scatterplot of Objective Function vs Iteration ' + '\n' + calibration_object.station_name
    plf.scatterplot_objfun(calibration_object.metric_iter_file, plotfile, "objFunVal", int(calibration_object.best_params), title)

    # Plot scatterplot between metrics and iteration
    if calibration_object.save_plot_iter_flag:
        plotfile = os.path.join(fig_path, calibration_object.basinID + '_metric_iteration_' + str('{:04d}').format(i) +'.png')  
    else: 
        plotfile = os.path.join(fig_path, calibration_object.basinID + '_metric_iteration.png')  
    title  = 'Scatterplot of Metrics vs Iteration ' + '\n' + calibration_object.station_name
    plf.scatterplot_var(calibration_object.metric_iter_file, plotfile, int(calibration_object.best_params), title)    

    # Plot scatterplot between metrics and objective function
    if calibration_object.save_plot_iter_flag:
        plotfile = os.path.join(fig_path, calibration_object.basinID + '_metric_objfun_' + str('{:04d}').format(i) +'.png')  
    else:
        plotfile = os.path.join(fig_path, calibration_object.basinID + '_metric_objfun.png')  
    title  = 'Scatterplot of Metrics vs Objectiv Function ' + '\n' + calibration_object.station_name
    plf.scatterplot_objfun_metric(calibration_object.metric_iter_file, plotfile, int(calibration_object.best_params), title)    

    # Plot scatterplot between parameters and iteration
    if calibration_object.save_plot_iter_flag:
        plotfile = os.path.join(fig_path, calibration_object.basinID + '_param_iteration_' + str('{:04d}').format(i) +'.png')  
    else:
        plotfile = os.path.join(fig_path, calibration_object.basinID + '_param_iteration.png')  
    title  = 'Scatterplot of Parameters vs Iteration ' + '\n' + calibration_object.station_name
    plf.scatterplot_var(calibration_object.param_iter_file, plotfile, int(calibration_object.best_params), title)    

    # Plot scatterplot between parameters and iteration
    if agent.algorithm !='dds':
        plf.scatterplot_var(calibration_object.param_iter_file, plotfile, int(calibration_object.best_params), title)    
        plot_cost_func(calibration_object, agent, os.path.join(agent.workdir, calibration_object.cost_iter_file), agent.algorithm, calib_iter=False)

def plot_valid_output(
    calibration_object: 'Evaluatable',
    agent: 'Agent',
    time_period: Optional[Dict[str,str]] = None,
) -> None:
    """Plot streamflow and other model output as well as metrics for validation run.

    Parameters
    ----------
    calibration_object : catchment object 
    calibration_object : calibration_object object 
    time_period : calib, valid and full time periods 

    Returns
    ----------
    None

    """
    # Output files from different validation runs
    control_run = os.path.join(agent.valid_path, calibration_object.basinID + '_output_valid_control.csv')
    best_run = os.path.join(agent.valid_path, calibration_object.basinID + '_output_valid_best.csv')

    # Read output
    df_control_run = pd.read_csv(control_run)
    df_control_run['Time'] = pd.DatetimeIndex(df_control_run['Time'])
    df_control = df_control_run[['Time', calibration_object.streamflow_name]]
    df_control = df_control.rename(columns={calibration_object.streamflow_name: 'Control Run'})
    df_control.set_index('Time', inplace=True)
    df_best_run = pd.read_csv(best_run)
    df_best = df_best_run[['Time', calibration_object.streamflow_name]]
    df_best_run['Time'] = pd.DatetimeIndex(df_best_run['Time'])
    df_best = df_best.rename(columns={calibration_object.streamflow_name: 'Best Run'})
    df_best['Time'] = pd.DatetimeIndex(df_best['Time'])
    df_best.set_index('Time', inplace=True)

    dfs1 = [calibration_object.observed, df_control, df_best]
    df_merged = reduce(lambda left, right: pd.merge(left, right, left_index=True, right_index=True, how='right'), dfs1)
    df_merged = df_merged.rename(columns={'obs_flow': 'Observation'})
    df_merged[['Control Run','Best Run']] = df_merged[['Control Run','Best Run']] 
    df_merged.reset_index(inplace=True)
    df_merged = df_merged.rename(columns={'index': 'Time'})
    df_merged = mf.treat_values(df_merged, remove_neg = True)
    df_merged_copy1 = copy.deepcopy(df_merged)

    # Plot hydrograph
    fig_path = agent.valid_path_plot
    plotfile = os.path.join(fig_path, calibration_object.basinID + '_hydrograph_valid_run.png')
    title  = 'Hydrograph during Calibration and Validation period'  + '\n' + calibration_object.station_name
    plf.plot_streamflow(df_merged_copy1, plotfile, title, calibration_object.evaluation_range[0], calibration_object.evaluation_range[1],
                        calibration_object.valid_evaluation_range[0], calibration_object.valid_evaluation_range[1])

    # Plot flow duration curve
    df_merged_copy2 = copy.deepcopy(df_merged)
    plotfile = os.path.join(fig_path, calibration_object.basinID + '_fdc_valid_run.png')
    title  = 'Flow Duration Curve during Calibration and Validation period'  + '\n' + calibration_object.station_name
    plf.plot_fdc_valid(df_merged_copy2, plotfile, title, time_period)

    # Plot time series of streamflow and precipitation 
    df_merged_copy3 = copy.deepcopy(df_merged)
    plotfile = os.path.join(fig_path, calibration_object.basinID + '_streamflow_precip_valid_run.png')
    title  = 'Streamflow and Total Precipitation during Calibration and Validation Period ' + '\n' + calibration_object.station_name
    plf.plot_streamflow_precipitation(df_merged_copy3, agent.df_precip, plotfile, title, calibration_object.evaluation_range[0], 
        calibration_object.evaluation_range[1], calibration_object.valid_evaluation_range[0], calibration_object.valid_evaluation_range[1])

    # Plot metrics
    metric_control = os.path.join(agent.valid_path, calibration_object.basinID + '_metrics_valid_control.csv')
    mdf_control = pd.read_csv(metric_control)
    metric_best = os.path.join(agent.valid_path, calibration_object.basinID + '_metrics_valid_best.csv')
    mdf_best = pd.read_csv(metric_best)
    mdf = pd.concat([mdf_control, mdf_best], ignore_index=True)
    plotfile = os.path.join(fig_path, calibration_object.basinID + '_barplot_metrics_valid_run.png')
    title  = 'Metrics from Different Simulation Time Period'  + '\n' + calibration_object.station_name
    plf.barplot_metric(mdf, plotfile, title)

def plot_cost_func(
    calibration_object: 'Evaluatable', 
    agent: 'Agent', 
    cost_hist_file: Union[str, os.PathLike], 
    algorithm: str, 
    calib_iter: Optional[bool] = False,
) -> None: 
    """Plot convergence curve.

    Parameters
    ----------
    calibration_object : Evaluatable object 
    agent : Agent object 
    cost_hist_file : File containing global best and local best ost function values at each iteration
    algorithm : Optimzation algorithm
    calib_iter : Whether plot for each iteration or after all iterations are finished, default False

    Returns
    ----------
    None

    """
    if calib_iter:
        plotfile = os.path.join(agent.workdir, calibration_object.basinID + '_cost_iter.png')
    else:
        plotfile = os.path.join(agent.workdir, calibration_object.basinID + '_cost_hist.png')
    title  = algorithm.upper() + ' Convergence Curve ' + '\n' + calibration_object.station_name
    plf.plot_cost_hist(cost_hist_file, plotfile, title)
