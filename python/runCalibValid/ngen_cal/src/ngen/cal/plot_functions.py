"""
This module contains functions to plot output files from calibration and vallidation runs.
@author: Xia Feng
"""

import math
import os
import scipy.stats as sp
from typing import Dict, List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

__all__ = ['plot_streamflow',
           'plot_streamflow_precipitation',
           'scatterplot_streamflow',
           'plot_output',
           'scatterplot_objfun',
           'trim_axs',
           'scatterplot_var',
           'scatterplot_objfun_metric',
           'barplot_metric',
           'plot_fdc_calib',
           'plot_fdc_valid',
           'plot_cost_hist',
          ]


def plot_streamflow(
    df: pd.DataFrame, 
    plotfile: Union[str, os.PathLike], 
    title: Optional[str] = None, 
    start_calib: Optional[str] = None, 
    end_calib: Optional[str] = None,
    start_valid: Optional[str] = None, 
    end_valid: Optional[str] = None,
) -> None:
    """Plot hydrograph during calibration or validation time period.

    Parameters
    ----------
    df : Streamflow time series from observation and different runs
    plotfile : Image file name
    title : Gage station name
    start_calib, end_calib : Starting and ending date for calibration time period
    start_valid, end_valid : Starting and ending date for validation time period

    Returns: 
    ----------
    None
    """

    print('---Plotting Streamflow Time Series---')

    # Obtain column names
    colname = list(df.columns)

    # Change date column to datetime dtype
    ts = pd.DatetimeIndex(df[colname[0]])
    df['Dates'] = ts

    # Plot
    df = df.iloc[24:] # remove first day with possible big values
    max0 = math.ceil(pd.melt(df, id_vars=['Time'], value_vars=colname[1:])['value'].max()) * 1.02
    cols = ['black', 'blue', 'orange', 'tab:green'] # ['k','C1','C0','C3']
    fig, ax = plt.subplots(figsize=(10, 6), dpi=120, tight_layout=True)

    for x in colname[1:]:
        ax.plot(df.Dates, df[x], c=cols[colname[1:].index(x)], label=x, linewidth=0.8)

    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.set(ylim=(0, max0))
    ax.set_xlabel('Date', fontsize=15)
    ax.set_ylabel(r'$\mathsf{Streamflow}\ (\mathsf{m^3}/\mathsf{s})$', fontsize=15)
    for label in ax.get_xticklabels(which='major'):
        label.set(rotation=30, horizontalalignment='right')

    if title is not None:
        ax.set_title(title, fontsize=16)

    if start_calib is not None and end_calib is not None and start_valid is not None and end_valid is not None:
         ax.axvline(x=pd.DatetimeIndex([start_calib]), color="0.8", linestyle="--", linewidth=3)
         ax.axvline(x=pd.DatetimeIndex([end_calib]), color="0.8", linestyle="--", linewidth=3)
         if end_calib != start_valid:
             ax.axvline(x=pd.DatetimeIndex([start_valid]), color="0.8", linestyle="--", linewidth=3)
         ax.axvline(x=pd.DatetimeIndex([end_valid]), color="0.8", linestyle="--", linewidth=3)

    ax.grid(True, color='0.8', linewidth=0.4)
    ax.legend(loc='upper right', fontsize=12, frameon=False)

    fig.savefig(plotfile)
    plt.close()


def plot_streamflow_precipitation(
    df: pd.DataFrame,
    dfp: pd.DataFrame,
    plotfile: Union[str, os.PathLike],
    title: Optional[str] = None,
    start_calib: Optional[str] = None,
    end_calib: Optional[str] = None,
    start_valid: Optional[str] = None,
    end_valid: Optional[str] = None,
) -> None:
    """Plot streamflow and precipitation during calibration or validation time period.

    Parameters
    ----------
    df : Streamflow time series from Observation and different runs
    dfp : Precipitation forcing time series 
    plotfile : Image file name
    title : Gage station name
    start_calib, end_calib : Starting and ending date for calibration time period
    start_valid, end_valid : Starting and ending date for validation time period

    Returns: 
    ----------
    None

    """
    print('---Plotting Streamflow Time Series with Precipitation---')

    # Obtain column names
    colname = list(df.columns)

    # Change date column to datetime dtype
    ts = pd.DatetimeIndex(df[colname[0]])
    df['Dates'] = ts
    ts = pd.DatetimeIndex(dfp[colname[0]])
    dfp['Dates'] = ts

    # Plot
    df = df.iloc[24:] # remove first day with possible big values
    max0 = math.ceil(pd.melt(df, id_vars=colname[0], value_vars=colname[1:])['value'].max()) * 1.02
    maxp = math.ceil(dfp['RAINRATE'].max())
    if maxp > 500: 
        yint2 = 100
    elif maxp > 200 and maxp <= 500: 
        yint2 = 80
    elif maxp > 100 and maxp <= 200: 
        yint2 = 50
    elif maxp > 50 and maxp <= 100:
        yint2 = 20
    elif maxp > 10 and maxp <= 50:
        yint2 = 5
    else:
        yint2 = 2
    ytk2  = range(0, 5*maxp+yint2, yint2) 
    label2 = [x if x <maxp+yint2 else '' for x in ytk2]
    cols = ['black', 'blue', 'orange', 'tab:green', 'purple'] # ['k','C1','C0','C3']

    fig, ax = plt.subplots(figsize=(10, 6), dpi=120, tight_layout=True)

    lnlst =[]
    for i, x in enumerate(colname[1:]):
        lnlst.append(ax.plot(df.Dates, df[x], c=cols[colname[1:].index(x)], label=x, linewidth=0.8))

    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.set(ylim=(0, max0))
    ax.set_xlabel('Date', fontsize=15)
    ax.set_ylabel(r'$\mathsf{Streamflow}\ (\mathsf{m^3}/\mathsf{s})$', fontsize=15)
    for label in ax.get_xticklabels(which='major'):
        label.set(rotation=30, horizontalalignment='right')

    if title is not None:
        ax.set_title(title, fontsize=16)

    if start_calib is not None and end_calib is not None and start_valid is not None and end_valid is not None:
         ax.axvline(x=pd.DatetimeIndex([start_calib]), color="0.8", linestyle="--", linewidth=3)
         ax.axvline(x=pd.DatetimeIndex([end_calib]), color="0.8", linestyle="--", linewidth=3)
         if end_calib != start_valid:
             ax.axvline(x=pd.DatetimeIndex([start_valid]), color="0.8", linestyle="--", linewidth=3)
         ax.axvline(x=pd.DatetimeIndex([end_valid]), color="0.8", linestyle="--", linewidth=3)

    ax.grid(True, color='0.8', linewidth=0.4)

    # Add secondary y-axis for precipitation 
    ax2 = ax.twinx()
    ln3 = ax2.plot(dfp.Dates, dfp['RAINRATE'], color=cols[-1], label='Precipitation', linewidth=0.8)
    #ax2.invert_yaxis()
    ax2.set_ylim(ax2.get_ylim()[::-1])
    ax2.set_ylabel('Total Precipitation (mm/h)', color='k', fontsize=14)
    ax2.set_yticks(ytk2)
    ax2.set_yticklabels(label2)

    # Generate common legend
    if len(lnlst)==3:
        lns = lnlst[0] + lnlst[1] + lnlst[2]  + ln3
    else:
        lns = lnlst[0] + lnlst[1] + lnlst[2] + lnlst[3] + ln3
    labs = [l.get_label() for l in lns]
    ax.legend(lns, labs, loc='center left', frameon=False)

    fig.savefig(plotfile)
    plt.close()


def scatterplot_streamflow(
    df: pd.DataFrame, 
    plotfile: Union[str, os.PathLike], 
    title: Optional[str] = None,
) -> None:
    """Plot scatterplot of streamflow between observation and other runs.

    Parameters
    ----------
    df : Streamflow time series from Observation and different runs
    plotfile : Image file
    title : Gage station name

    Returns:
    None

    """
    print('---Plotting Scatterplot of Streamflow between Observation and Other Runs---')

    # Obtain column names and value range
    colname = list(df.columns)
    df = df.iloc[24:] # remove first day with possible big values
    max0 = math.ceil(pd.melt(df, id_vars=['Time'], value_vars=colname[1:])['value'].max()) * 1.02

    # Plot
    cols = ['b', 'orange','tab:green']  
    fig, ax = plt.subplots(figsize=(10.8, 7.2), tight_layout=True)

    for x in colname[2:]:
       ax.scatter(df['Observation'], df[x], s=60, label=x, facecolors='none', edgecolors=cols[colname[2:].index(x)], marker ='o')
    ax.plot([0, 1], [0, 1], transform=ax.transAxes, c='k')

    ax.set(xlim=(0, max0), ylim=(0, max0))
    ax.tick_params(axis='both', which='major', labelsize=15)
    ax.set_xlabel(r'$\mathsf{Observed}\ \mathsf{Streamflow}\ (\mathsf{m^3}/\mathsf{s})$', fontsize=18)
    ax.set_ylabel(r'$\mathsf{Simulated}\ \mathsf{Streamflow}\ (\mathsf{m^3}/\mathsf{s})$', fontsize=18)
    if title is not None:
       ax.set_title(title, fontsize=18, weight='bold')

    ax.grid(True, color='0.7', linewidth=0.5)
    ax.legend(loc='upper left', fontsize=18, markerscale=1.5, frameon=False) 

    fig.savefig(plotfile)
    plt.close()


def plot_output(
    df: pd.DataFrame, 
    plotfile: Union[str, os.PathLike], 
    output_name: List[str], 
    title: Optional[str] = None,
) -> None:
    """Plot different model output variables compared with observation.

    Parameters
    ----------
    df : Contains model output variables from Observation, Control Run, and Best Run
    plotfile : Image file
    output_name : Model output variable names
    title : Gage station name

    Returns: 
    ----------
    None

    """
    print('---Plotting Output from Different Runs---')

    # Change date column to datetime dtype
    ts = pd.DatetimeIndex(df['Time'])
    ts_utc = ts.tz_localize("UTC")
    df['Dates'] = ts_utc

    # Plot
    colname = output_name[1:]
    if 'Q_OUT' in output_name:
        ylabels = [r'$\mathsf{Streamflow}\ (\mathsf{m^3}/\mathsf{s})$', r'$\mathsf{Direct}\ \mathsf{Runoff}\ (\mathsf{m^3}/\mathsf{s})$',
                   r'$\mathsf{GIUH}\ \mathsf{Runoff}\ (\mathsf{m^3}/\mathsf{s})$', r'$\mathsf{Lateral}\ \mathsf{Runoff}\ (\mathsf{m^3}/\mathsf{s})$',
                   r'$\mathsf{Baseflow}\ (\mathsf{m^3}/\mathsf{s})$', r'$\mathsf{Precipitation}\ (\mathsf{mm}/\mathsf{h})$']
    if 'Qout' in output_name:
        ylabels = [r'$\mathsf{Streamflow}\ (\mathsf{m^3}/\mathsf{s})$', r'$\mathsf{Total}\ \mathsf{Discharge}\ (\mathsf{m^3}/\mathsf{s})$',
                   r'$\mathsf{Overland}\ \mathsf{Flow}\ (\mathsf{m^3}/\mathsf{s})$', r'$\mathsf{Baseflow}\ (\mathsf{m^3}/\mathsf{s})$',
                   r'$\mathsf{Recharge}\ \mathsf{Flow}\ (\mathsf{m^3}/\mathsf{s})$', r'$\mathsf{Precipitation}\ (\mathsf{mm}/\mathsf{h})$']

    lab1 = ['Control Run','Best Run', 'Observation']
    lab2 = ['','']
    x = lambda i: lab1 if i!=5 else lab2
    y = lambda i: max1 if i!=5 else max2

    # Specify y-axis range
    list1= [x + '_Control' for x in colname[0:4]]
    list2= [x + '_Best' for x in colname[0:4]]
    list1.extend(list2)
    df = df.iloc[24:] # remove first day with possible big values
    max1= math.ceil(pd.melt(df, id_vars=['Time'], value_vars=[*list1, 'Observation'])['value'].max())*1.04
    max2 = math.ceil(df[colname[5] + '_Control'].max())*1.02

    # Plot
    cols = ['b','r','k']
    fig, ax = plt.subplots(figsize=(8.5, 11.5), nrows=6, ncols=1, sharex=True)
    for i in range(len(colname)):
        lab = x(i)
        maxval = y(i)
        ax[i].plot(df['Dates'], df[[colname[i]+'_Control']], c=cols[0], label=lab[0], linewidth=1)
        ax[i].plot(df['Dates'], df[[colname[i]+'_Best']], c=cols[1], label=lab[1], linewidth=1)
        if (i==0):
            ax[i].plot(df['Dates'], df[['Observation']], c=cols[2], label=lab[2], linewidth=1)
            ax[i].legend(loc='upper left', fontsize=10, frameon=False)

        ax[i].set_ylim(0, maxval)
        ax[i].set_ylabel(ylabels[i])
        ax[i].tick_params(axis='both', which='major', labelsize=10)
        ax[i].grid(True, color='0.7', linewidth=0.5)
        if (i==5):
            ax[i].set_xlabel('Date', fontsize=18)
            ax[i].xaxis.set_label_coords(.5, -.5)
            for label in ax[i].get_xticklabels(which='major'):
                label.set(rotation=30, horizontalalignment='right')

    # Set common x-axis label and title
    fig.add_subplot(111, frameon=False)
    plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
    plt.suptitle(title, size=18, weight='bold')

    plt.subplots_adjust(left=0.1, right=0.97, bottom=0.09, top=0.92, hspace=0.1)
    fig.savefig(plotfile)
    plt.close()


def scatterplot_objfun(
    metric_file: Union[str, os.PathLike], 
    plotfile: Union[str, os.PathLike], 
    objective_fun_column: str, 
    best_iteration: Optional[int] = None, 
    title: Optional[str] = None,
) -> None:
    """Scatterplot between objective function and iteration.

    Parameters
    ----------
    metric_file : File containing metrics including objective function at each iteration
    plotfile : Image file
    best_iteration : Best iteration
    title : Gage station name

    Returns: 
    ----------
    None

    """
    print('---Plotting Scatterplot between Objective Funtion and Iteration---')

    # Read file
    df = pd.read_csv(metric_file)

    # Plot
    fig, ax = plt.subplots(dpi=150, tight_layout=True)
    ax.plot(df.loc[:,['iteration']], df.loc[:,[objective_fun_column]], marker='o', markersize=5, linewidth=0)

    if best_iteration is not None:
       bestpt, = ax.plot(best_iteration, df.loc[df['iteration'] == best_iteration, [objective_fun_column]], 'r*', markersize=10)
       ax.legend(handles=[bestpt], labels=["Best Iteration"], loc="upper right", frameon=False)

    ax.set_xlabel('Iteration', fontsize=15)
    ax.set_ylabel('Objective Function', fontsize=15)
    if title is not None:
       ax.set_title(title, weight='bold', fontsize=12)
    else:
       ax.set_title("Scatterplot of Objective Function vs Iteration", weight='bold')
    ax.grid(True, color='0.7', linewidth=0.6)

    fig.savefig(plotfile)
    plt.close()


def trim_axs(axs, N: int):
    """Reduce *axs* to *N* Axes. All further Axes are removed from the figure."""
    axs = axs.flat
    for ax in axs[N:]:
        ax.remove()
    return axs[:N]


def scatterplot_var(
    var_file: Union[str, os.PathLike], 
    plotfile: Union[str, os.PathLike], 
    best_iteration: Optional[int] = None, 
    title: Optional[str] = None,
) -> None:
    """Scatterplot between variables (metrics or parameters) and iteration.

    Parameters
    ----------
    var_file : File containing calibration metrics or parameters for each iteration
    plotfile : Image file
    best_iteration : Best iteration
    title : Gage station name

    Returns:
    ----------
    None

    """
    print('---Plotting Scatterplot between Variables and Iteration---')

    # Read file
    df = pd.read_csv(var_file)
    allcols = list(df.columns)[1:]

    # Define figure arguments
    if len(allcols) > 15 and len(allcols) < 20:
        cols = 5
    elif len(allcols) > 6 and len(allcols) <= 15: 
        cols = 5
    else:
        cols = 3
    rows = math.ceil((len(allcols) - 1)/cols)

    # Plot
    fig, axs = plt.subplots(rows, cols, figsize=(12, 8), dpi=105, sharex=True)
    axs = trim_axs(axs, len(allcols))
    for ax, varname in zip(axs, allcols):
        ax.plot(df.loc[:,['iteration']], df.loc[:,[varname]], marker='o', markersize=3, linewidth=0)
        if best_iteration is not None:
            bestpt, = ax.plot(best_iteration, df.loc[df['iteration']==best_iteration, [varname]], 'ro', markersize=5)
            if varname==allcols[0]:
                ax.legend(handles=[bestpt], labels=["Best Iteration"], loc='upper right', frameon=False)

        ax.set_xlim(left=0, right=len(df.index))
        ax.set_title(varname) if len(varname) < 20 else ax.set_title('_'.join(varname.split('_')[:2]))
        ax.grid(True, color='0.7', linewidth=0.6)

    # Set common x- and y-axis labels
    fig.add_subplot(111, frameon=False)
    plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
    plt.xlabel("Iteration", fontsize=16)

    plt.suptitle(title, size=20, weight='bold')
    plt.subplots_adjust(left=0.06, right=0.95, bottom=0.08, top=0.86, hspace=0.25, wspace=0.38)
    plt.savefig(plotfile)
    plt.close()


def scatterplot_objfun_metric(
    var_file: Union[str, os.PathLike],
    plotfile: Union[str, os.PathLike],
    best_iteration: Optional[int] = None,
    title: Optional[str] = None,
) -> None:
    """Scatterplot between objective function and evaluation metric.

    Parameters:
    ----------
    var_file : File containing calibration metrics for each iteration
    plotfile : Image file
    best_iteration : Best iteration
    title : Gage station name

    Returns: 
    ----------
    None

    """
    print('---Plotting Scatterplot between Objective Function and Metric---')

    # Read file
    df = pd.read_csv(var_file)
    objcol = list(df.columns)[1]
    allcols = list(df.columns)[2:]
    idx = df[df.iteration==best_iteration].index

    # Define figure arguments
    figsize = (12, 8)
    cols = 4
    rows = math.ceil(len(allcols)/cols)

    # Plot
    fig, axs = plt.subplots(rows, cols, figsize=figsize, dpi=105, sharex=True)
    axs = trim_axs(axs, len(allcols))
    for ax, varname in zip(axs, allcols):
        ax.plot(df.loc[:,[objcol]], df.loc[:,[varname]], marker='o', markersize=3, linewidth=0)
        if best_iteration is not None:
            bestpt, = ax.plot(df.loc[idx,[objcol]], df.loc[idx, [varname]], 'ro', markersize=5)
            if varname==allcols[0]:
                ax.legend(handles=[bestpt], labels=["Best Iteration"], loc='lower right', frameon=False)

        ax.set_xlim(left=0, right=df[objcol].max()*1.2)
        ax.tick_params(axis='both', which='major', labelsize=9)
        ax.set_title(varname)
        ax.grid(True, color='0.7', linewidth=0.6)

    # Set common x- and y-axis labels
    fig.add_subplot(111, frameon=False)
    plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
    plt.xlabel("Objective Function", fontsize=16)

    plt.suptitle(title, size=20, weight='bold')
    plt.subplots_adjust(left=0.06, right=0.95, bottom=0.08, top=0.85, hspace=0.25, wspace=0.38)

    plt.savefig(plotfile)
    plt.close()


def barplot_metric(
    df: pd.DataFrame, 
    plotfile: Union[str, os.PathLike],
    title: Optional[str] = None,
) -> None:
    """Barplot of evaluation metrics from different runs.

    Parameters:
    ----------
    df : Streamflow time series from Observation and different runs
    plotfile : Image file
    title : Gage station name, optional

    Returns:
    ----------
    None

    """
    print('---Plotting Barplot of Metrics---')

    # Set index
    allcols = list(df.columns)
    df.set_index(allcols[0:2], inplace=True)
    allcols = list(df.columns)

    # Specify figure arguments
    figsize = (12, 8)
    cols = 4
    rows = math.ceil(len(allcols)/cols)
    runtp = list(df.index.get_level_values(0).unique())
    labels = list(df.index.get_level_values(1).unique())
    width = 0.35
    x = np.arange(len(labels))
    xwidth = [x - width/2, x + width/2]

    # Plot
    fig, axs = plt.subplots(rows, cols, figsize=figsize, dpi=105, sharex=False)
    axs = trim_axs(axs, len(allcols))
    for ax, varname in zip(axs, allcols):
        if varname==allcols[-1]:
            label0 = [x.split('_')[1] for x in runtp]
        else:
            label0 = ["",""]
        for i in range(len(runtp)):
            ax.bar(xwidth[i], df.loc[(runtp[i], labels),varname].values.tolist(), width, label=label0[i])

        ax.set_xticks(x)
        if allcols.index(varname) in range(len(allcols)-cols, len(allcols)):
            ax.set_xticklabels(labels)
        else:
            ax.set_xticklabels("")

        ax.set_title(varname)
        if varname==allcols[-1]:
            ax.legend(bbox_to_anchor=(1, 0.8, 0.15, 0.15), fontsize=12)

    # Set common x- and y-axis labels
    fig.add_subplot(111, frameon=False)
    plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
    plt.xlabel("Simulation Time Period", weight='bold', fontsize=16)

    plt.suptitle(title, size=20, weight='bold')
    plt.subplots_adjust(left=0.06, right=0.89, bottom=0.08, top=0.85, hspace=0.25, wspace=0.35)

    plt.savefig(plotfile)
    plt.close()


def plot_fdc_calib(
    df: pd.DataFrame, 
    plotfile: Union[str, os.PathLike], 
    title: Optional[str] = None,
) -> None:
    """Plot flow duration curve of observation and simulations.

    Parameters:
    ----------
    df : Contains model output variables from Observation, Control Run, and Best Run
    plotfile : Image file
    title : Gage station name, optional

    Returns: 
    ----------
    None

    """
    print('---Plotting FDC of Observation and Other Runs---')

    # Figure arguments
    colname = list(df.columns)[1:]
    df = df.iloc[24:] # remove first day with possible big values
    max0 = math.ceil(pd.melt(df, id_vars=[df.columns[0]], value_vars=colname[1:])['value'].max()) * 1.02

    # Plot
    cols = ['k', 'b', 'orange', 'tab:green']
    fig, ax = plt.subplots(figsize=(10, 6), nrows=1, ncols=1)
    for i in range(len(colname)):
        data  = np.sort(df[colname[i]])[::-1]
        ranks = len(data) - sp.rankdata(data, method='min') + 1
        prob = np.array([(ranks[i]*100/(len(data))) for i in range(len(data))])
        ax.plot(prob, data, c=cols[i], label=colname[i], linewidth=2, alpha=1)

    ax.set(xlim=(0, 100))
    ax.tick_params(axis='both', which='major', labelsize=12)
    ax.grid(True, color='0.7', linewidth=0.5)
    ax.set_yscale('log')
    ax.set_ylabel(r'$\mathsf{Streamflow}\ (\mathsf{m^3}/\mathsf{s})$', fontsize=16)
    ax.legend(loc='lower left', fontsize=13, markerscale=2, frameon=False)

    # Set common x- and y-axis labels
    fig.add_subplot(111, frameon=False)
    plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
    plt.xlabel('Exceedence Probability (%)', weight='normal', fontsize=16)

    plt.suptitle(title, size=16, weight='bold')
    plt.subplots_adjust(left=0.07, right=0.97, bottom=0.09, top=0.85, wspace=0.05)
    fig.savefig(plotfile)
    plt.close()


def plot_fdc_valid(
    df: pd.DataFrame, 
    plotfile: Union[str, os.PathLike], 
    title: Optional[str] = None, 
    time_period: Optional[Dict[str,str]] = None,
) -> None:
    """Plot flow duration curve of observation and simulations.

    Parameters:
    ----------
    df : Contains model output variables from Observation, Control Run, and Best Run
    plotfile : Image file
    title : Gage station name
    time_period : Simulation time period

    Returns: 
    None

    """
    print('---Plotting FDC of Observation and Other Runs---')

    # Figure arguments
    colname = list(df.columns)[1:]
    df = df.iloc[24:] # remove initial big values
    max0 = math.ceil(pd.melt(df, id_vars=[df.columns[0]], value_vars=colname[1:])['value'].max()) * 1.02

    # Plot
    cols = ['k', 'b', 'orange', 'tab:green'] # cols = ['k','C1','C0','C3']
    keys = list(time_period.keys())
    df.set_index(df.columns[0], inplace=True)
    fig, ax = plt.subplots(figsize=(12.2, 5.8), nrows=1, ncols=3, sharey=True)
    for key, value in time_period.items():
        df_copy = df.copy()
        df_sub = df_copy[value[0]:value[1]]
        j = keys.index(key)
        for i in range(len(colname)):
            data  = np.sort(df_sub[colname[i]])[::-1]
            ranks = len(data) - sp.rankdata(data, method='min') + 1
            prob = np.array([(ranks[i]*100/(len(data))) for i in range(len(data))])
            ax[j].plot(prob, data, c=cols[i], label=colname[i], linewidth=1, alpha=1)

        ax[j].set(xlim=(0, 100))
        ax[j].set_yscale('log')
        ax[j].tick_params(axis='both', which='major', labelsize=10)
        ax[j].set_title(key, fontsize=12, weight='normal')
        ax[j].grid(True, color='0.7', linewidth=0.5)
        if (j==0):
            ax[j].legend(loc='lower left', fontsize=13, markerscale=2, frameon=False)

    # Set common x- and y-axis labels
    fig.add_subplot(111, frameon=False)
    plt.tick_params(labelcolor='none', which='both', top=False, bottom=False, left=False, right=False)
    plt.xlabel('Exceedence Probability (%)', weight='normal', fontsize=16)
    plt.ylabel(r'$\mathsf{Streamflow}\ (\mathsf{m^3}/\mathsf{s})$', weight='normal', fontsize=16)

    plt.suptitle(title, size=18, weight='bold')
    plt.subplots_adjust(left=0.07, right=0.97, bottom=0.09, top=0.82, wspace=0.05)
    fig.savefig(plotfile)
    plt.close()


def plot_cost_hist(
    cost_file: Union[str, os.PathLike], 
    plotfile: Union[str, os.PathLike], 
    title: Optional[str] = None,
    algorithm: Optional[str] = None,
    calib_iter: Optional[bool] = False,
) -> None:
    """Plot convergence curve.

    Parameters:
    ----------
    cost_file : File containing global best and mean local best cost at each iteration
    plotfile : Image file 
    title : Figure title 
    algorithm : Optimzation algorithm
    calib_iter : Whether plot for each iteration or after all iterations are finished, default False

    Returns:
    ----------
    None

    """
    print('---Plotting Convergence Curve for Global and Local Best Values---')

    
    # Read file
    df = pd.read_csv(cost_file)
    df.pop('iteration')

    # Plot args
    colname = df.columns
    cost_name = {'global_best': 'Global Best'}
    cols = {'global_best': 'r'}
    markers = {'global_best': 'o'}
    if not calib_iter :
        cost_name.update({'mean_local_best': 'Mean Local Best'})
        cols.update({'mean_local_best': 'b'})
        markers.update({'mean_local_best': '^'})
        if algorithm == "gwo":
            cost_name.update({'mean_leader_best': 'Mean Leader Best'})
            cols.update({'mean_leader_best': 'y'})
            markers.update({'mean_leader_best': 'd'})

    # Plot
    fig, ax = plt.subplots(dpi=150, tight_layout=True)
    for x in colname:
        ax.plot(np.arange(0,len(df)), df[x], c=cols[x], label=cost_name[x], linewidth=1)

    ax.set_xlabel('Iteration', fontsize=15)
    ax.set_ylabel('Objective Function', fontsize=15)
    ax.legend(fontsize=10, loc="upper right", frameon=False)
    if title is not None:
       ax.set_title(title, weight='bold', fontsize=10)
    else:
       ax.set_title("Convergence Curve", weight='bold')
    ax.grid(True, color='0.7', linewidth=0.6)

    fig.savefig(plotfile)
    plt.close()
