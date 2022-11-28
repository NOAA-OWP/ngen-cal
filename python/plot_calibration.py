from pathlib import Path
import matplotlib.pylab as plt
from ngen.cal import plot_objective, plot_stuff, plot_obs, plot_output, plot_parameter_space

workdir = Path("./Output_01089100_dds_nnse_4mo_i100_csv")

objective_log = workdir/'ngen-calibration_objective.txt'

catchment_data = workdir/'01089100_catchment_data.geojson'
nexus_data = workdir/'01089100_nexus_data.geojson'
x_walk = workdir/'01089100_crosswalk.json'
config = workdir/'01089100_realization_config_bmi_calib.json'
params = workdir/'nex-10884_parameter_df_state.parquet'

output = workdir/'nex-10884_output.csv'
plot_objective(objective_log)
plot_stuff(workdir, catchment_data, nexus_data, x_walk, config)

plot_obs('cat-10883', catchment_data, nexus_data, x_walk, '2018-10-01 00:00:00', '2018-12-01 00:00:00')
plot_output(output)
plot_hydrograph('cat-10883', catchment_data, nexus_data, x_walk, '2018-10-01 00:00:00', '2018-12-01 00:00:00', output)
plt.show()
