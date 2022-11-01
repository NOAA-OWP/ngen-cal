from pathlib import Path
import matplotlib.pylab as plt
from ngen.cal import plot_objective, plot_stuff, plot_obs, plot_output, plot_parameter_space

workdir = Path("../data/calibration")

objective_log = workdir/'ngen-calibration_objective.txt'

catchment_data = workdir/'catchment_data.geojson'
nexus_data = workdir/'nexus_data.geojson'
x_walk = workdir/'crosswalk.json'
config = workdir/'realization_config.json'
params = workdir/'cat-87_calibration_df_state.parquet'

output = workdir/'cat-87_output.csv_last'
plot_objective(objective_log)
#plot_stuff(workdir, catchment_data, nexus_data, x_walk, config)

plot_obs('cat-87', catchment_data, nexus_data, x_walk)
plot_output(output)
plot_parameter_space(params)
plt.show()
