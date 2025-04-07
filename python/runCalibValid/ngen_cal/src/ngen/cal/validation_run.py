"""
This module contains function to execute validation control and best runs. 

@author: Xia Feng
"""

import os
import shutil
import subprocess
from typing import TYPE_CHECKING

import pandas as pd

from .plot_output import plot_valid_output
from .search import _execute, _calc_metrics
from .utils import pushd, complete_msg 

if TYPE_CHECKING:
    from ngen.cal.agent import Agent


def run_valid_ctrl_best(agent: 'Agent') -> None:
    """Execute validation control and best runs, calculate metrics and produce plots.

    Parameters
    ----------
    agent : Agent object

    Returns
    ----------
    None

    """
    print("---Start " + agent.run_name + "---")
    shutil.copy(agent.realization_file, os.path.join(agent.job.workdir, os.path.basename(agent.realization_file)))

    # Calculate metrics
    for calibration_object in agent.model.adjustables:
        with pushd(agent.job.workdir):
            _execute(agent)
            time_period = {'calib': calibration_object.evaluation_range, 'valid': calibration_object.valid_evaluation_range, 
                           'full': calibration_object.full_evaluation_range}
            metrics = pd.DataFrame()
            for key, value in time_period.items():
                result = _calc_metrics(calibration_object.output, calibration_object.observed, value, calibration_object.threshold)
                tmp = {**{'run': agent.run_name, 'period': key}, **result}
                metrics = pd.concat([metrics, pd.DataFrame([tmp])], ignore_index=True)
                calibration_object.write_valid_metric_file(agent.workdir, agent.run_name, metrics)

            # Save and move output
            calibration_object.save_valid_output(calibration_object.basinID, agent.run_name, agent.valid_path, agent.job.workdir, agent.valid_path_output)

            # Plot
            if agent.run_name=='valid_best':
                plot_valid_output(calibration_object, agent, time_period)

            # Indicate completion 
            calibration_object.write_run_complete_file(agent.run_name, agent.workdir)
            complete_msg(calibration_object.basinID, agent.run_name, agent.workdir, calibration_object.user)
