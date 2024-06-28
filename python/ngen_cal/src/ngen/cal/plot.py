import geopandas as gpd
import pandas as pd
import json
import matplotlib.pyplot as plt
import re
from datetime import datetime
from typing import TYPE_CHECKING
from datetime import datetime

from hypy.hydrolocation import NWISLocation # type: ignore
from hypy.nexus import Nexus # type: ignore

from .calibration_cathment import CalibrationCatchment

if TYPE_CHECKING:
    from pathlib import Path

def plot_objective(objective_log_file: 'Path'):
    """
        Plot the objective funtion
    """

    data = pd.read_csv(objective_log_file, names=['iteration', 'objective'], index_col=0)
    plt.figure()
    data.plot()

def plot_stuff(workdir, catchment_data, nexus_data, cross_walk, config_file):

    catchments = []
    #Read the catchment hydrofabric data
    catchment_hydro_fabric = gpd.read_file(catchment_data)
    catchment_hydro_fabric.set_index('id', inplace=True)
    nexus_hydro_fabric = gpd.read_file(nexus_data)
    nexus_hydro_fabric.set_index('id', inplace=True)

    x_walk = pd.read_json(cross_walk, dtype=str)

    #Read the calibration specific info
    with open(config_file) as fp:
        data = json.load(fp)
    try:
        start_t = data['time']['start_time']
        end_t = data['time']['end_time']
    except KeyError as e:
        raise(RuntimeError("Invalid time configuration: {} key missing from {}".format(e.args[0], config_file)))

    #Setup each calibration catchment
    for id, catchment in data['catchments'].items():
        if 'calibration' in catchment.keys():
            try:
                fabric = catchment_hydro_fabric.loc[id]
            except KeyError:
                #TODO log WARNING:
                continue
            try:
                nwis = x_walk[id]['Gage_no']
            except KeyError:
                raise(RuntimeError("Cannot establish mapping of catchment {} to nwis location in cross walk".format(id)))
            try:
                nexus_data = nexus_hydro_fabric.loc[fabric['toid']]
            except KeyError:
                raise(RuntimeError("No suitable nexus found for catchment {}".format(id)))

            #establish the hydro location for the observation nexus associated with this catchment
            location = NWISLocation(nwis, nexus_data.name, nexus_data.geometry)
            nexus = Nexus(nexus_data.name, location, id)
            catchments.append(CalibrationCatchment(workdir, id, nexus, start_t, end_t, catchment))

    for catchment in catchments:
        c_id = catchment.id
        n_id = catchment.outflow.id
        ax = catchment_hydro_fabric.plot()
        nexus_hydro_fabric.plot(ax=ax, color='r')

        ax2 = catchment.observed.plot(label='observed')
        catchment.output.plot(ax=ax2, label='simulated')

def plot_obs(id, catchment_data, nexus_data, cross_walk, start_dt, end_dt):
    obs_dict = get_obs(id, catchment_data, nexus_data, cross_walk, start_dt, end_dt)
    for nwis in obs_dict:
        plt.figure()
        obs_dict[nwis].plot(title='Observation at USGS {}'.format(nwis))

def get_obs(id, catchment_data, nexus_data, cross_walk, start_dt, end_dt):
    #Read the catchment hydrofabric data
    catchment_hydro_fabric = gpd.read_file(catchment_data)
    catchment_hydro_fabric.set_index('id', inplace=True)
    nexus_hydro_fabric = gpd.read_file(nexus_data)
    nexus_hydro_fabric.set_index('id', inplace=True)
    #x_walk = pd.read_json(cross_walk, dtype=str)
    x_walk = pd.Series()
    with open(cross_walk) as fp:
        data = json.load(fp)
        for xwid, values in data.items():
            gage = values.get('Gage_no')
            if gage:
                if not isinstance(gage, str):
                    gage = gage[0]
                if gage != "":
                    x_walk[xwid.replace('wb-', 'cat-')] = gage
    try:
        fabric = catchment_hydro_fabric.loc[id]
    except KeyError:
        raise(RuntimeError("No data for id {}".format(id)))
    try:
        nwis = x_walk[id]
    except KeyError:
        raise(RuntimeError("Cannot establish mapping of catchment {} to nwis location in cross walk".format(id)))
    if not isinstance(nwis, str):
        nwis = nwis[0]
    try:
        nexus_data = nexus_hydro_fabric.loc[fabric['toid']]
    except KeyError:
        raise(RuntimeError("No suitable nexus found for catchment {}".format(id)))

    #establish the hydro location for the observation nexus associated with this catchment
    location = NWISLocation(nwis, nexus_data.name, nexus_data.geometry)
    nexus = Nexus(nexus_data.name, location, id)
    #use the nwis location to get observation data
    #TODO/FIXME make a more general hydrofabric object
    obs = nexus._hydro_location.get_data(start_dt, end_dt)
    #make sure data is hourly
    obs = obs.set_index('value_time')['value'].resample('1H').nearest()
    obs = obs * 0.028316847 #convert to m^3/s
    obs.rename('obs_flow', inplace=True)
    r = {}
    r[nwis] = obs
    return r

def plot_output(output_file: 'Path'):
    output = get_output_flow(output_file)
    plt.figure()
    output.plot(title='simulated flow')

def get_output_flow(output_file: 'Path'):
    #output = pd.read_csv(output_file, usecols=["Time", "Flow"], parse_dates=['Time'], index_col='Time')
    #output.rename(columns={'Flow':'sim_flow'}, inplace=True)
    try: #catchment csv file
        output = pd.read_csv(output_file, parse_dates=['Time'], index_col='Time')
        original_output_vars = ['Rainfall', 'Direct Runoff', 'GIUH Runoff', 'Lateral Flow', 'Base Flow', 'Total Discharge']
    except: #nexus csv file
        output = pd.read_csv(output_file, parse_dates=['Time'], index_col='Time', names=["Timestep", "Time", "Flow"])
        original_output_vars = ['Flow']
    #output[original_output_vars].plot(subplots=True)
    #original_output_vars.extend( [])
    # CHECK OUT GIUH ORDINATES/INPUT/USAGE
    return output['Flow']

#assumes a column "Time" or times in the first column
def get_time_range_from_csv(output_file: 'Path'):
    output = None
    try:
        output = pd.read_csv(output_file, parse_dates=['Time'], index_col='Time')
    except:
        output = pd.read_csv(output_file, parse_dates={"Time": [0]}, index_col='Time')
    return (output.first_valid_index(), output.last_valid_index())

def get_precip_one_file(output_file: 'Path'):
    output = pd.read_csv(output_file, parse_dates=['Time'], index_col='Time')
    original_output_vars = ['Rainfall', 'Direct Runoff', 'GIUH Runoff', 'Lateral Flow', 'Base Flow', 'Total Discharge']
    if "RAINRATE" in output:
        return output['RAINRATE']
    elif "APCP_Surface" in output:
        return output['APCP_Surface']
    elif "atmosphere_water__liquid_equivalent_precipitation_rate" in output:
        return output['atmosphere_water__liquid_equivalent_precipitation_rate']
    else:
        raise(RuntimeError("No recognized precip data in provided file!"))

def get_precip_files_list(output_files: list, catchment_data: str):
    totals = None
    catchment_hydro_fabric = gpd.read_file(catchment_data)
    catchment_hydro_fabric.set_index('id', inplace=True)
    for f in output_files:
        output = get_precip_one_file(f)
        id = re.sub(r".*(cat-[0-9]+)[^0-9]*", "\\1", f.name)
        try:
            fabric = catchment_hydro_fabric.loc[id]
        except KeyError:
            raise(RuntimeError(f"No catchment hydrofabric data for id {id}"))
        try:
            areasqkm = fabric['areasqkm']
        except:
            try:
                areasqkm = fabric['area_sqkm']
            except:
                raise(RuntimeError("Failed to get catchment area, cannot compute precip contributions."))
        output = output * (areasqkm*1000000/3600)
        print(f"For catchment {id} with area {areasqkm} added {output.sum()} m^3 of precip.")
        if totals is None:
            totals = output
        else:
            totals = totals.add(output)
    return totals

def get_routed_output_flow(output_file: 'Path', id: str, start_dt: datetime, end_dt: datetime):
    id = re.sub(r"^cat-([0-9]+)[^0-9]*", "\\1", id)
    df = pd.read_hdf(output_file)
    df.index = df.index.map(lambda x: 'wb-'+str(x))
    df.columns = pd.MultiIndex.from_tuples(df.columns)
    
    #df = df.loc[self._eval_nexus.contributing_catchments[0].replace('cat', 'wb')] # TODO should contributing_catchments be singular??? assuming it is for now...
    df = df.loc['wb-'+id]
    output = df.xs('q', level=1, drop_level=False)
    #This is a hacky way to get the time index...pass the time around???
    dt_range = pd.date_range(start_dt, end_dt, len(output.index)).round('min')
    output.index = dt_range
    #this may not be strictly nessicary...I think the _evalutate will align these...
    output = output.resample('1H').first()
    output.name="sim_flow"
    return output


def plot_parameter_space(path: 'Path'):
    params = pd.read_parquet(path)
    params.drop(columns=['min', 'max', 'sigma', 'model'], inplace=True)
    params.set_index('param', inplace=True)

    params.T.plot(subplots=True)

#TODO: Doesn't really work for a single catchment file (unrouted output), though most of the pieces are there.
def plot_hydrograph_cal(id, catchment_data, nexus_data, cross_walk, start_dt, end_dt, catchment_output: list, routing_output: 'Path' = None, subtitle: str = None, output_labels: list = None, output_colors: list = None, cumsum: bool = False):
    catchment_output = list(catchment_output)

    data_start_dt = datetime.fromisoformat(start_dt)
    data_end_dt = datetime.fromisoformat(end_dt)
    if len(catchment_output) > 0:
        (data_start_dt, data_end_dt) = get_time_range_from_csv(catchment_output[0])
    
    obs_dict = get_obs(id, catchment_data, nexus_data, cross_walk, start_dt, end_dt)
    #obs_dict = { 'X': pd.Series() } # Use this if obs service is down or to save resources
    for nwis in obs_dict:
        if routing_output is not None:
            if isinstance(routing_output, list):
                output = []
                for output_file in routing_output:
                    output.append(get_routed_output_flow(output_file, id, data_start_dt, data_end_dt))
            else:
                output = get_routed_output_flow(routing_output, id, data_start_dt, data_end_dt)
                output = [output]
        else:
            output = get_output_flow(catchment_output[0])
            output = [output]
        #output.rename('sim_flow', inplace=True)
        precip = get_precip_files_list(catchment_output, catchment_data)
        precip.rename('precip')
        #print(precip)
        #print(obs_dict[nwis])
        return plot_hydrograph(output, obs_dict[nwis], precip, f"Gage {nwis}", subtitle, start_dt=start_dt, end_dt=end_dt, output_colors=output_colors, output_labels=output_labels, cumsum=cumsum)

def plot_hydrograph(outputs: list, obs, precip, title, subtitle: str = None, start_dt: datetime = None, end_dt: datetime = None, output_labels: list = None, output_colors: list = None, cumsum: bool = False):
    if start_dt is not None:
        outputs2 = []
        for output in outputs:
            output = output.loc[start_dt:]
            outputs2.append(output)
        outputs = outputs2
        precip = precip.loc[start_dt:]
        obs = obs.loc[start_dt:]
    if end_dt is not None:
        outputs2 = []
        for output in outputs:
            output = output.loc[:end_dt]
            outputs2.append(output)
        outputs = outputs2
        precip = precip.loc[:end_dt]
        obs = obs.loc[:end_dt]
    if cumsum:
        outputs2 = []
        for output in outputs:
            output = output.cumsum()
            outputs2.append(output)
        outputs = outputs2
        precip = precip.cumsum()
        obs = obs.cumsum()

    fig, ax = plt.subplots()

    ax2 = ax.twinx()

    ax.invert_yaxis()
    ax.yaxis.set_label_position("right")
    ax.yaxis.tick_right()
    ax.bar(precip.index, precip, color="lightgray", width=0.042, linewidth=0, label="Precip")

    ax2.yaxis.set_label_position("left")
    ax2.yaxis.tick_left()
    ax2.plot(obs, color="blue", label="Obs")
    for i, output in enumerate(outputs):
        label = f"Simulated {i+1}" if output_labels is None else output_labels[i]
        if output_colors is None:
            ax2.plot(output, label=label)
        else:
            ax2.plot(output, label=label, color=output_colors[i])
    #ax.legend(loc='best')
    ax2.set_ylabel("Flow ($m^3$/s)")
    #ax2.legend(loc='best')
    ax.set_ylabel("Precip ($m^3$/s)")
    fig.autofmt_xdate(rotation=45)
    #plt.title("Title String", fontsize=14)
    fig.text(.1,.95,title,fontsize=14,ha='left')
    if None != "":
        fig.text(.1,.9,subtitle,fontsize=10,ha='left')

    # legend fix from https://stackoverflow.com/a/57484812/489116
    lines_labels = [ax.get_legend_handles_labels() for ax in fig.axes]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
    fig.legend(lines, labels, ncol=2)

    #plt.show()
    return fig
        