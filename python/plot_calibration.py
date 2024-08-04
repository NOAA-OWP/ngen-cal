from pathlib import Path
import matplotlib.pylab as plt
from ngen.cal import plot_objective, plot_stuff, plot_obs, plot_output, plot_parameter_space, plot_hydrograph_cal, get_routed_output_flow

#workdir = Path("./Output_01089100_dgiuh_dds_nnse_4mo_i100_cdf")
workdir = Path("../cal-test/Output_parallel_dgiuh_dds_uniform_custom_16mo_i300")
#workdir = Path("./")

objective_log = workdir/'ngen-calibration_objective.txt'

catchment_data = Path('./Input/01089100_catchment_data.geojson')
nexus_data = Path('./Input/01089100_nexus_data.geojson')
x_walk = Path('./Input/01089100_crosswalk.json')
config = Path('./Input/01089100_realization_config_bmi_calib.json')
#params = workdir/'nex-10884_parameter_df_state.parquet'

#output = workdir/'nex-10884_output.csv'
catchment_output = workdir.glob("cat-*.csv")
routing_output = workdir/'flowveldepth_Ngen1.h5'
#plot_objective(objective_log)
#plot_stuff(workdir, catchment_data, nexus_data, x_walk, config)

#plot_obs('cat-10883', catchment_data, nexus_data, x_walk, '2018-10-01 00:00:00', '2019-02-01 22:00:00')
#plot_output(output)
#get_routed_output_flow(Path("./flowveldepth_Ngen1.h5"), 'cat-10883');

plot_hydrograph_cal('cat-10883', catchment_data, nexus_data, x_walk, '2018-10-01 00:00:00', '2019-02-01 22:00:00', catchment_output, routing_output, subtitle="i=100, NNSE, w/DGIUH")
#plot_parameter_space(params)
#plt.show()
